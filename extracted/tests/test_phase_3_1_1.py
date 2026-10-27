# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L20557-L20740 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #100  lines=183  compile=OK
# kind: test  ident: test_phase_3_1_1.py  version: latest of 1 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.1.1 - 快照身份绑定、TOCTOU 防御与 Replay 验证
执行：pytest tests/test_phase3_1_1_snapshot_provenance.py
"""

import json
import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute, NarrativeValence
from cmawse.agent.cognitive_projection import CognitiveProjection, ProjectedCandidateDTO
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.provenance import DecisionProvenanceEnvelope
from cmawse.agent.representation import SubjectiveRepresentation


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_snap",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []})
    )
    return SubjectContext.assemble("agent_snap", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# 任务 2 检验: Candidate Snapshot Hash 全属性敏感性断言 (Case A - Case G)
# ============================================================================
def test_candidate_snapshot_hash_attribute_sensitivity():
    c_a = CandidateAffordance(channel_id="AFF_A", action_type="ACT_A", actuator=ActuatorType.TORSO, target_id="t1", target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, narrative_status=NarrativeValence.SUPPORTED, estimated_metabolic_joules=5.0)
    c_b = CandidateAffordance(channel_id="AFF_B", action_type="ACT_B", actuator=ActuatorType.DUAL_LEGS, target_id="t2", target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.SPATIAL_LOCOMOTION, narrative_status=NarrativeValence.SUPPORTED, estimated_metabolic_joules=10.0)

    # Case A & B: 列表乱序置换 -> 哈希完全恒定
    hash_ab = CognitiveProjection.compute_candidate_snapshot_hash([c_a, c_b])
    hash_ba = CognitiveProjection.compute_candidate_snapshot_hash([c_b, c_a])
    assert hash_ab == hash_ba

    # Case C: target_id 改变 -> 哈希改变
    c_a_mod_target = c_a.model_copy(update={"target_id": "t1_modified"})
    hash_mod_target = CognitiveProjection.compute_candidate_snapshot_hash([c_a_mod_target, c_b])
    assert hash_mod_target != hash_ab

    # Case D: action_type 改变 -> 哈希改变
    c_a_mod_action = c_a.model_copy(update={"action_type": "ACT_A_MOD"})
    hash_mod_action = CognitiveProjection.compute_candidate_snapshot_hash([c_a_mod_action, c_b])
    assert hash_mod_action != hash_ab

    # Case E: metabolic_joules 改变 -> 哈希改变
    c_a_mod_joules = c_a.model_copy(update={"estimated_metabolic_joules": 99.0})
    hash_mod_joules = CognitiveProjection.compute_candidate_snapshot_hash([c_a_mod_joules, c_b])
    assert hash_mod_joules != hash_ab

    # Case F: 增加候选 AFF_C -> 哈希改变
    c_c = CandidateAffordance(channel_id="AFF_C", action_type="ACT_C", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    hash_abc = CognitiveProjection.compute_candidate_snapshot_hash([c_a, c_b, c_c])
    assert hash_abc != hash_ab

    # Case G: 删除候选 AFF_B -> 哈希改变
    hash_a_only = CognitiveProjection.compute_candidate_snapshot_hash([c_a])
    assert hash_a_only != hash_ab


# ============================================================================
# 任务 3 检验: TOCTOU 对抗测试断言 (Snapshot Identity Mismatch)
# ============================================================================
def test_toctou_snapshot_mismatch_adversarial_rejection(mock_ctx):
    """验证：LLM 基于 [AFF_A, AFF_B] 做出决策，校验时若候选集被中途篡改，必须拒止为 CANDIDATE_SNAPSHOT_MISMATCH"""
    c_a = CandidateAffordance(channel_id="AFF_A", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c_b = CandidateAffordance(channel_id="AFF_B", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_a, c_b], [], [])
    expected_hash = proj.candidate_set_hash

    raw_response = json.dumps({"status": "SELECTED", "candidate_id": "AFF_A"})

    # 模拟攻击 1: 中途删除了 AFF_B
    res_tampered_list = LLMBoundaryValidator.validate_and_sanitize(
        raw_response=raw_response,
        valid_candidates=[c_a],  # 篡改后仅剩 c_a
        expected_candidate_set_hash=expected_hash
    )
    assert res_tampered_list.is_valid is False
    assert res_tampered_list.decision.status == MindDecisionStatus.SYSTEM_FAILURE_SILENT
    assert res_tampered_list.rejection_reason == "CANDIDATE_SNAPSHOT_MISMATCH"

    # 模拟攻击 2: 候选 ID 没变，但属性被隐蔽篡改 (estimated_metabolic_joules 翻倍)
    c_b_tampered = c_b.model_copy(update={"estimated_metabolic_joules": 999.0})
    res_tampered_attr = LLMBoundaryValidator.validate_and_sanitize(
        raw_response=raw_response,
        valid_candidates=[c_a, c_b_tampered],
        expected_candidate_set_hash=expected_hash
    )
    assert res_tampered_attr.is_valid is False
    assert res_tampered_attr.decision.status == MindDecisionStatus.SYSTEM_FAILURE_SILENT
    assert res_tampered_attr.rejection_reason == "CANDIDATE_SNAPSHOT_MISMATCH"


# ============================================================================
# 任务 5 & 6 检验: Provenance 执行与 Reason 真实性断言
# ============================================================================
def test_provenance_create_and_reason_none_preservation():
    """验证：出处信封真实执行，模型未提供 reason 时 telemetry 严格保持 None，绝无伪造 'LLM Deliberated'"""
    c_a = CandidateAffordance(channel_id="AFF_A", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    raw_response = json.dumps({"status": "SELECTED", "candidate_id": "AFF_A", "reason": None})

    res = LLMBoundaryValidator.validate_and_sanitize(raw_response, [c_a])
    assert res.is_valid is True
    # 核心断言：未提供 reason 则必须为 None
    assert res.decision.telemetry_reason is None

    envelope = DecisionProvenanceEnvelope.create(
        agent_id="test_agent",
        tick=1,
        candidate_set_hash="snap_hash_123",
        projection_payload={"key": "val"},
        model_name="qwen2.5:14b",
        decision_status=res.decision.status.value,
        is_boundary_valid=res.is_valid,
        selected_candidate_id=res.decision.candidate_id,
        reason_telemetry=res.decision.telemetry_reason
    )
    env_dict = envelope.model_dump()
    assert env_dict["reason_telemetry"] is None
    assert env_dict["is_boundary_valid"] is True


# ============================================================================
# 任务 8 检验: Candidate Snapshot Hash 与 Projection Hash 关系断言
# ============================================================================
def test_candidate_snapshot_hash_vs_projection_hash_distinction(mock_ctx):
    c1 = CandidateAffordance(channel_id="AFF_1", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c2 = CandidateAffordance(channel_id="AFF_2", action_type="A2", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state_1 = InternalCognitiveState()
    rep_1 = SubjectiveRepresentation.from_context(mock_ctx)

    # 1. 原始投影
    proj_1 = CognitiveProjection.project(mock_ctx, state_1, rep_1, [], [c1, c2], [], [])
    cand_hash_1 = proj_1.candidate_set_hash
    proj_hash_1 = CognitiveProjection.compute_projection_hash(proj_1.model_dump())

    # 2. 仅改变候选内容 -> 两个哈希同时改变
    c2_mod = c2.model_copy(update={"action_type": "A2_MODIFIED"})
    proj_2 = CognitiveProjection.project(mock_ctx, state_1, rep_1, [], [c1, c2_mod], [], [])
    assert proj_2.candidate_set_hash != cand_hash_1
    assert CognitiveProjection.compute_projection_hash(proj_2.model_dump()) != proj_hash_1

    # 3. 候选集不变，仅改变生理疼痛内感受 -> candidate_snapshot_hash 保持恒定，projection_hash 改变
    ctx_pain = mock_ctx.model_copy(update={"somatic": SomaticState(energy_pool=80.0, pain=90.0)})
    rep_pain = SubjectiveRepresentation.from_context(ctx_pain)
    proj_3 = CognitiveProjection.project(ctx_pain, state_1, rep_pain, [], [c1, c2], [], [])
    assert proj_3.candidate_set_hash == cand_hash_1  # 候选快照哈希严格不变
    assert CognitiveProjection.compute_projection_hash(proj_3.model_dump()) != proj_hash_1  # 全文投影指纹改变

    # 4. 候选列表置换 -> 两个哈希均严格不变
    proj_4 = CognitiveProjection.project(mock_ctx, state_1, rep_1, [], [c2, c1], [], [])
    assert proj_4.candidate_set_hash == cand_hash_1
    assert CognitiveProjection.compute_projection_hash(proj_4.model_dump()) == proj_hash_1


# ============================================================================
# 任务 9 检验: 离线 Replay 确定性契约断言 (Replay Contract)
# ============================================================================
def test_replay_contract_determinism(mock_ctx):
    """验证：相同的 agent_id, tick, candidate_snapshot, raw LLM output 经由校验器重放，产出严格相同的 MindDecision"""
    c_a = CandidateAffordance(channel_id="AFF_REPLAY", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    expected_hash = CognitiveProjection.compute_candidate_snapshot_hash([c_a])
    raw_output = json.dumps({"status": "SELECTED", "candidate_id": "AFF_REPLAY", "reason": "Replay audit"})

    res_1 = LLMBoundaryValidator.validate_and_sanitize(raw_output, [c_a], expected_hash)
    res_2 = LLMBoundaryValidator.validate_and_sanitize(raw_output, [c_a], expected_hash)

    assert res_1.is_valid == res_2.is_valid == True
    assert res_1.decision.status == res_2.decision.status == MindDecisionStatus.SELECTED
    assert res_1.decision.candidate_id == res_2.decision.candidate_id == "AFF_REPLAY"
    assert res_1.decision.telemetry_reason == res_2.decision.telemetry_reason == "Replay audit"
