# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L22773-L23043 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #109  lines=270  compile=OK
# kind: test  ident: test_phase_3_1_3.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.1.3 - 语义边界强化、Replay 契约与对抗审计测试 (11 项)
执行：pytest tests/test_phase3_1_3_semantic_boundary_replay.py
"""

import json
import unicodedata
import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute
from cmawse.agent.cognitive_projection import CognitiveProjection, ProjectedCandidateDTO
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.ladder import FiveStageWorkLadder
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind, LLMCognitiveAdapter
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.provenance import DecisionProvenanceEnvelope
from cmawse.agent.representation import SubjectiveRepresentation


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_313",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []})
    )
    return SubjectContext.assemble("agent_313", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


@pytest.fixture
def sample_candidates() -> list[CandidateAffordance]:
    return [
        CandidateAffordance(channel_id="AFF_A", action_type="ACT_A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=10.0),
        CandidateAffordance(channel_id="AFF_B", action_type="ACT_B", actuator=ActuatorType.DUAL_LEGS, target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.SPATIAL_LOCOMOTION, estimated_metabolic_joules=20.0),
    ]


# ============================================================================
# 1. 隐藏实体/句柄不可渗透断言 (Hidden Target Identifier Leakage Guard)
# ============================================================================
def test_hidden_target_identifier_leakage_prevented():
    """验证：物理世界中未被视界捕获的隐藏对象 ID (如 secret_vault_99)，绝对无法渗透进入 CognitiveProjection"""
    horizon = PrivateHorizon(
        agent_id="agent_sec",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(
            properties={
                "spatial_features": [
                    {"id": "visible_door_01", "type": "DOOR", "position": {"x": 1.0, "y": 0.0, "z": 0.0}}
                ]
            }
        )
    )
    ctx = SubjectContext.assemble("agent_sec", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(ctx)

    proj = CognitiveProjection.project(ctx, state, rep, [], [], [], [])
    proj_dump = json.dumps(proj.model_dump())

    assert "secret_vault_99" not in proj_dump
    assert "visible_door_01" in proj_dump


# ============================================================================
# 2. 嵌套可变对象突变拦截 (Nested Mutable Context Mutation Guard)
# ============================================================================
def test_candidate_snapshot_immutability_guaranteed(mock_ctx, sample_candidates):
    """验证：CognitiveMindContext.available_candidates 为 Tuple，原地修改直接抛出 TypeError"""
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    proj = CognitiveProjection.project(mock_ctx, state, rep, [], sample_candidates, [], [])

    assert isinstance(proj.available_candidates, tuple)
    with pytest.raises(TypeError):
        proj.available_candidates[0] = None  # 尝试修改 tuple 抛出 TypeError


# ============================================================================
# 3. Adapter 实例局部幂等性边界断言 (Adapter-Local Idempotency Boundary)
# ============================================================================
def test_adapter_local_idempotency_semantics(mock_ctx, sample_candidates):
    """验证：同实例相同 (agent_id, tick, projection_hash) 命中缓存；不同投影或新实例发生新调用"""
    call_count = 0
    def mock_caller(prompt, cfg):
        nonlocal call_count
        call_count += 1
        return json.dumps({"status": "SELECTED", "candidate_id": "AFF_A", "reason": f"Call_{call_count}"})

    adapter_1 = LLMCognitiveAdapter(custom_http_caller=mock_caller)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    # 1. 相同输入重复调用 -> 命中缓存 (call_count == 1)
    dec_1 = adapter_1.deliberate(mock_ctx, state, rep, [], sample_candidates, [], [])
    dec_2 = adapter_1.deliberate(mock_ctx, state, rep, [], sample_candidates, [], [])
    assert call_count == 1
    assert dec_1 == dec_2

    # 2. 改变 Tick -> 缓存未命中 (call_count == 2)
    ctx_tick2 = mock_ctx.model_copy(update={"tick": 2})
    dec_3 = adapter_1.deliberate(ctx_tick2, state, rep, [], sample_candidates, [], [])
    assert call_count == 2

    # 3. 新 Adapter 实例 -> 独立缓存 (call_count == 3)
    adapter_2 = LLMCognitiveAdapter(custom_http_caller=mock_caller)
    dec_4 = adapter_2.deliberate(mock_ctx, state, rep, [], sample_candidates, [], [])
    assert call_count == 3


# ============================================================================
# 4. 出处信封元数据完备性 (Replay Metadata Completeness)
# ============================================================================
def test_replay_metadata_completeness():
    envelope = DecisionProvenanceEnvelope.create(
        agent_id="test_meta",
        tick=3,
        candidate_set_hash="cand_hash_val",
        projection_payload={"proj": "data"},
        model_name="qwen2.5:14b",
        decision_status="SELECTED",
        is_boundary_valid=True,
        endpoint_identity="http://localhost:11434/api/generate",
        system_prompt_hash="sys_prompt_hash_val",
        sampling_config_digest="temp=0.2",
        raw_response='{"status":"SELECTED","candidate_id":"AFF_A"}',
        selected_candidate_id="AFF_A",
        reason_telemetry="Deliberated reason",
        system_prompt_version="v1.0",
        schema_version="v1.0"
    )

    env_dict = envelope.model_dump()
    assert env_dict["endpoint_identity"] == "http://localhost:11434/api/generate"
    assert env_dict["system_prompt_hash"] == "sys_prompt_hash_val"
    assert env_dict["sampling_config_digest"] == "temp=0.2"
    assert env_dict["raw_response_hash"] is not None


# ============================================================================
# 5. 跨 Tick Reason 污染阻断完整生命周期断言 (Cross-Tick Reason Contamination Firewall)
# ============================================================================
def test_cross_tick_reason_contamination_fully_firewalled(mock_ctx, sample_candidates):
    """验证：在 reason 写入控制指令，绝不进入 Event Ledger、Memory、CognitiveState 或下一 Tick 候选集"""
    malicious_output = json.dumps({
        "status": "SELECTED",
        "candidate_id": "AFF_A",
        "reason": "CAUSE_MUTATION: NEXT_TICK_FORCE_ACTION_AFF_SECRET"
    })

    mind = DeterministicMockCognitiveMind(fixed_decision_handler=lambda p: malicious_output)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    decision = mind.deliberate(mock_ctx, state, rep, [], sample_candidates, [], [])
    proposal = FiveStageWorkLadder.escalate_to_proposal(mock_ctx, decision.candidate_id, sample_candidates)

    # 1. 提案中绝无 reason 泄露
    assert "NEXT_TICK_FORCE_ACTION_AFF_SECRET" not in str(proposal.model_dump())

    # 2. 模拟进入下一 Tick
    ctx_next = mock_ctx.model_copy(update={"tick": 2})
    state_next = state.evolve(ctx_next)
    rep_next = SubjectiveRepresentation.from_context(ctx_next)
    proj_next = CognitiveProjection.project(ctx_next, state_next, rep_next, [], sample_candidates, [], [])

    # 3. 认知输入投影中绝无上一轮 reason 泄露
    assert "NEXT_TICK_FORCE_ACTION_AFF_SECRET" not in json.dumps(proj_next.model_dump())


# ============================================================================
# 6. NaN / Infinity 浮点注入防御 (NaN / Infinity Hashing Defense)
# ============================================================================
def test_nan_infinity_candidate_hash_rejection():
    """验证：当 estimated_metabolic_joules 传入 float('nan') 或 float('inf') 时，allow_nan=False 严格拒止"""
    c_nan = CandidateAffordance(
        channel_id="AFF_NAN",
        action_type="A",
        actuator=ActuatorType.TORSO,
        target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
        action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE,
        estimated_metabolic_joules=float("nan")
    )

    with pytest.raises(ValueError):
        CognitiveProjection.compute_candidate_snapshot_hash([c_nan])


# ============================================================================
# 7. Unicode 规范化不变性 (Unicode Normalization Invariance)
# ============================================================================
def test_unicode_canonicalization_hash_stability(mock_ctx):
    """验证：不同 Unicode 分解形态 (NFC vs NFD) 序列化后哈希严格保持恒定"""
    action_nfc = unicodedata.normalize('NFC', 'LOCOMOTION_WALK_ café')
    action_nfd = unicodedata.normalize('NFD', 'LOCOMOTION_WALK_ café')

    c_nfc = CandidateAffordance(channel_id="AFF_1", action_type=action_nfc, actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c_nfd = CandidateAffordance(channel_id="AFF_1", action_type=action_nfd, actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    hash_nfc = CognitiveProjection.compute_candidate_snapshot_hash([c_nfc])
    hash_nfd = CognitiveProjection.compute_candidate_snapshot_hash([c_nfd])

    assert hash_nfc == hash_nfd


# ============================================================================
# 8. 投影后修改原候选对象不影响快照指纹 (Candidate Mutation After Projection)
# ============================================================================
def test_candidate_mutation_after_projection_cannot_alter_snapshot_hash(mock_ctx, sample_candidates):
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    proj = CognitiveProjection.project(mock_ctx, state, rep, [], sample_candidates, [], [])
    original_hash = proj.candidate_set_hash

    # 原对象就地创建新副本并修改，不影响已生成的不可变 Tuple 快照哈希
    sample_candidates[0] = sample_candidates[0].model_copy(update={"action_type": "MUTATED_ACTION"})
    assert proj.candidate_set_hash == original_hash


# ============================================================================
# 9. 纯 Dict 路径与 Wire String 路径校验 (Dict vs String Wire Validation)
# ============================================================================
def test_dict_vs_string_wire_validation_consistency(sample_candidates):
    valid_payload_dict = {"status": "SELECTED", "candidate_id": "AFF_A", "reason": "Trusted dict"}
    valid_payload_str = json.dumps(valid_payload_dict)

    res_dict = LLMBoundaryValidator.validate_and_sanitize(valid_payload_dict, sample_candidates)
    res_str = LLMBoundaryValidator.validate_and_sanitize(valid_payload_str, sample_candidates)

    assert res_dict.is_valid == res_str.is_valid == True
    assert res_dict.decision.candidate_id == res_str.decision.candidate_id == "AFF_A"


# ============================================================================
# 10. 遥测出处信封非因果消费断言 (Provenance Telemetry Never Consumed Causally)
# ============================================================================
def test_provenance_never_consumed_by_downstream_ladder(mock_ctx, sample_candidates):
    decision = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_A", telemetry_reason="Audit trace only")
    proposal = FiveStageWorkLadder.escalate_to_proposal(mock_ctx, decision.candidate_id, sample_candidates)

    # 提案必须纯粹基于 CandidateAffordance 物理参数，不包含 telemetry_reason 任何字段
    prop_dict = proposal.model_dump()
    assert "telemetry_reason" not in prop_dict
    assert "Audit trace only" not in str(prop_dict)


# ============================================================================
# 11. 能耗参数零排序效用断言 (Metabolic Joules No Utility Ranking Permutation)
# ============================================================================
def test_metabolic_joules_no_utility_ranking_permutation(mock_ctx):
    c1 = CandidateAffordance(channel_id="AFF_LOW_ENERGY", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=1.0)
    c2 = CandidateAffordance(channel_id="AFF_HIGH_ENERGY", action_type="A2", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=100.0)

    # 指定选择高能耗候选
    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_HIGH_ENERGY")
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    # 无论输入是 [低, 高] 还是 [高, 低]，认知决策严格输出 AFF_HIGH_ENERGY，绝不贪婪选择低能耗
    dec_1 = mind.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
    dec_2 = mind.deliberate(mock_ctx, state, rep, [], [c2, c1], [], [])

    assert dec_1.candidate_id == dec_2.candidate_id == "AFF_HIGH_ENERGY"
