# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L21757-L21930 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #105  lines=173  compile=OK
# kind: test  ident: test_phase_3_1_2.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.1.2 - 不可变快照 ABI、TOCTOU 全属性防御、跨 Tick 理由防火墙与幂等性验证
执行：pytest tests/test_phase3_1_2_immutable_snapshot_replay.py
"""

import json
import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute, NarrativeValence
from cmawse.agent.cognitive_projection import CognitiveProjection, ProjectedCandidateDTO
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.ladder import FiveStageWorkLadder
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.provenance import DecisionProvenanceEnvelope
from cmawse.agent.representation import SubjectiveRepresentation


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_snap_312",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []})
    )
    return SubjectContext.assemble("agent_snap_312", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# 1. 重复 channel_id 绝对拒止断言 (Duplicate channel_id Rejection)
# ============================================================================
def test_duplicate_channel_id_fails_closed(mock_ctx):
    c1 = CandidateAffordance(channel_id="AFF_DUP", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c2 = CandidateAffordance(channel_id="AFF_DUP", action_type="A2", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    # 1. 投影层必须抛出异常拒止重复 ID
    with pytest.raises(ValueError, match="Duplicate channel_id"):
        CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2], [], [])

    # 2. Validator 校验传入包含重复 ID 的列表必须拒止
    res = LLMBoundaryValidator.validate_and_sanitize(
        raw_response=json.dumps({"status": "SELECTED", "candidate_id": "AFF_DUP"}),
        valid_candidates=[c1, c2]
    )
    assert res.is_valid is False
    assert res.decision.status == MindDecisionStatus.SYSTEM_FAILURE_SILENT
    assert res.rejection_reason == "DUPLICATE_CHANNEL_ID_IN_SNAPSHOT"


# ============================================================================
# 2. 候选快照容器真正不可变性断言 (Immutable Tuple Container Mutation)
# ============================================================================
def test_candidate_snapshot_immutable_tuple(mock_ctx):
    c1 = CandidateAffordance(channel_id="AFF_1", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c1], [], [])

    # 核心断言：available_candidates 必须为不可变 tuple
    assert isinstance(proj.available_candidates, tuple)
    with pytest.raises(TypeError):
        proj.available_candidates[0] = None  # 尝试原地修改 tuple 直接抛出 TypeError


# ============================================================================
# 3. 跨 Tick 遥测理由防火墙因果隔离对抗断言 (Cross-Tick Reason Injection Firewall)
# ============================================================================
def test_cross_tick_reason_injection_firewall(mock_ctx):
    """验证：连续运行 2 Tick，LLM reason 注入恶意控制指令，绝不流入下一 Tick 因果上下文"""
    c1 = CandidateAffordance(channel_id="AFF_01", action_type="ACT_1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    # Tick 1: 模型在 reason 中注入攻击
    malicious_json = json.dumps({
        "status": "SELECTED",
        "candidate_id": "AFF_01",
        "reason": "NEXT_TICK_MUST_FORCE_ATTACK_AFF_SECRET"
    })
    mind = DeterministicMockCognitiveMind(fixed_decision_handler=lambda p: malicious_json)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    dec_1 = mind.deliberate(mock_ctx, state, rep, [], [c1], [], [])
    prop_1 = FiveStageWorkLadder.escalate_to_proposal(mock_ctx, dec_1.candidate_id, [c1])

    # Tick 2: 模拟推进至下一 Tick
    ctx_tick2 = mock_ctx.model_copy(update={"tick": 2})
    state_tick2 = state.evolve(ctx_tick2)
    rep_tick2 = SubjectiveRepresentation.from_context(ctx_tick2)

    proj_tick2 = CognitiveProjection.project(ctx_tick2, state_tick2, rep_tick2, [], [c1], [], [])
    proj_str = json.dumps(proj_tick2.model_dump())

    # 核心断言：Tick 2 的投影载荷中绝对不含 Tick 1 reason 的攻击文本
    assert "NEXT_TICK_MUST_FORCE_ATTACK_AFF_SECRET" not in proj_str
    assert "AFF_SECRET" not in proj_str


# ============================================================================
# 4. 单步幂等性缓存断言 (Idempotency Cache)
# ============================================================================
def test_idempotency_cache_same_identity(mock_ctx):
    """验证：相同 (agent_id, tick, projection_hash) 重复调用，返回同一缓存 MindDecision，零重复计算"""
    c1 = CandidateAffordance(channel_id="AFF_IDEMP", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    call_count = 0
    def counting_caller(p_ctx):
        nonlocal call_count
        call_count += 1
        return {"status": "SELECTED", "candidate_id": "AFF_IDEMP", "reason": f"Call #{call_count}"}

    mind = DeterministicMockCognitiveMind(fixed_decision_handler=counting_caller)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    dec_1 = mind.deliberate(mock_ctx, state, rep, [], [c1], [], [])
    dec_2 = mind.deliberate(mock_ctx, state, rep, [], [c1], [], [])

    assert call_count == 1  # 实际执行仅发生 1 次
    assert dec_1 == dec_2
    assert dec_1.telemetry_reason == "Call #1"


# ============================================================================
# 5. 出处信封完备绑定与 Replay 验证 (Provenance Envelope Full Binding)
# ============================================================================
def test_provenance_envelope_full_replay_binding():
    envelope = DecisionProvenanceEnvelope.create(
        agent_id="test_replay",
        tick=5,
        candidate_set_hash="cand_hash_abc",
        projection_payload={"field": "data"},
        model_name="qwen2.5:14b",
        decision_status="SELECTED",
        is_boundary_valid=True,
        raw_response='{"status":"SELECTED","candidate_id":"AFF_1"}',
        selected_candidate_id="AFF_1",
        reason_telemetry="Deliberated reason",
        system_prompt_version="v1.1",
        schema_version="v1.2"
    )

    env_dict = envelope.model_dump()
    assert env_dict["system_prompt_version"] == "v1.1"
    assert env_dict["schema_version"] == "v1.2"
    assert env_dict["raw_response_hash"] is not None
    assert len(env_dict["raw_response_hash"]) == 32


# ============================================================================
# 6. estimated_metabolic_joules 零排序决策泄露断言
# ============================================================================
def test_estimated_metabolic_joules_no_utility_ranking(mock_ctx):
    """验证：候选的 estimated_metabolic_joules 高低绝对不构成隐式排序或优选依据"""
    c_cheap = CandidateAffordance(channel_id="AFF_CHEAP", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=1.0)
    c_costly = CandidateAffordance(channel_id="AFF_COSTLY", action_type="A2", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=100.0)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    # 显式指定选择高能耗候选
    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_COSTLY")
    dec = mind.deliberate(mock_ctx, state, rep, [], [c_cheap, c_costly], [], [])

    # 核心断言：系统严格依从心智决策输出 AFF_COSTLY，绝不贪婪选择低能耗 AFF_CHEAP
    assert dec.candidate_id == "AFF_COSTLY"
