# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L18298-L18446 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #90  lines=148  compile=OK
# kind: test  ident: test_phase_3_0_1.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.0.1 - 主权补丁与边界防御专门测试 (Test 1 - Test 6)
执行：pytest tests/test_phase3_01_sovereignty_patch.py
"""

import random
import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.cognitive_projection import CognitiveProjection
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import CognitiveSilentMode, MindDecisionStatus
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.representation import SubjectiveRepresentation


@pytest.fixture
def mock_context() -> SubjectContext:
    horizon = PrivateHorizon(agent_id="test_agent", tick=1, self_position=Vector3D(x=0.0, y=0.0), local_environment=PhysicalEnvironmentSnapshot())
    return SubjectContext.assemble("test_agent", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


@pytest.fixture
def sample_candidates() -> list[CandidateAffordance]:
    return [
        CandidateAffordance(channel_id="AFF_A", action_type="ACT_A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, is_physically_feasible=True),
        CandidateAffordance(channel_id="AFF_B", action_type="ACT_B", actuator=ActuatorType.DUAL_LEGS, target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.SPATIAL_LOCOMOTION, is_physically_feasible=True),
        CandidateAffordance(channel_id="AFF_C", action_type="ACT_C", actuator=ActuatorType.DUAL_HANDS, target_surface=SurfaceType.MANIPULABLE_HARDWARE, action_attribute=ActionAttribute.ENVIRONMENTAL_MANIPULATION, is_physically_feasible=True),
    ]


# ============================================================================
# Test 1: Mock 零首项选择攻击断言 (Mock First Candidate Attack)
# ============================================================================
def test_1_mock_never_selects_first_candidate(mock_context, sample_candidates):
    """验证：随机打乱候选集 20 次，未指定 fixed_candidate_id 的 Mock 必然返回 UNRESOLVED_COGNITION，绝不选择 [0]"""
    mock_mind = DeterministicMockCognitiveMind()
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_context)

    rng = random.Random(42)
    for _ in range(20):
        shuffled = list(sample_candidates)
        rng.shuffle(shuffled)
        decision = mock_mind.deliberate(mock_context, state, rep, [], shuffled, [], [])

        # 核心断言：绝对不因排在首位而产生 SELECTED
        assert decision.status == MindDecisionStatus.UNRESOLVED_COGNITION
        assert decision.candidate_id is None


# ============================================================================
# Test 2: 显式注入候选置换不变性断言 (Mock Explicit Candidate)
# ============================================================================
def test_2_mock_explicit_candidate_permutation(mock_context, sample_candidates):
    """验证：显式指定 fixed_candidate_id='AFF_B' 时，无论列表如何乱序，严格返回 SELECTED('AFF_B')"""
    mock_mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_B")
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_context)

    rng = random.Random(123)
    for _ in range(20):
        shuffled = list(sample_candidates)
        rng.shuffle(shuffled)
        decision = mock_mind.deliberate(mock_context, state, rep, [], shuffled, [], [])

        assert decision.status == MindDecisionStatus.SELECTED
        assert decision.candidate_id == "AFF_B"


# ============================================================================
# Test 3: Projection 零候选裁剪权断言 (Projection Does Not Filter)
# ============================================================================
def test_3_projection_does_not_filter_infeasible_candidates(mock_context):
    """验证：输入包含可行与不可行候选，Projection 完整序列化全部候选，绝不在投影层静默删除"""
    cands = [
        CandidateAffordance(channel_id="AFF_FEASIBLE", action_type="ACT_1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, is_physically_feasible=True),
        CandidateAffordance(channel_id="AFF_INFEASIBLE", action_type="ACT_2", actuator=ActuatorType.DUAL_LEGS, target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.SPATIAL_LOCOMOTION, is_physically_feasible=False),
    ]
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_context)

    projected = CognitiveProjection.project(mock_context, state, rep, [], cands, [], [])

    # 核心断言：投影后的数量必须严格等于 2，不可行候选保留但标记 is_physically_feasible=False
    assert len(projected.available_candidates) == 2
    proj_infeasible = next(c for c in projected.available_candidates if c.channel_id == "AFF_INFEASIBLE")
    assert proj_infeasible.is_physically_feasible is False


# ============================================================================
# Test 4: 静默模式缺失严格拒止断言 (Silent Mode Missing Fail-Closed)
# ============================================================================
def test_4_silent_mode_missing_fails_closed(sample_candidates):
    """验证：LLM 返回 COGNITIVE_SILENT 且 silent_mode=null 时，严禁自动补充默认值，必须拒止为 SYSTEM_FAILURE_SILENT"""
    raw_response = {
        "status": "COGNITIVE_SILENT",
        "candidate_id": None,
        "silent_mode": None,
        "reason": "Missing explicit mode"
    }
    result = LLMBoundaryValidator.validate_and_sanitize(raw_response, sample_candidates)

    assert result.is_valid is False
    assert result.decision.status == MindDecisionStatus.SYSTEM_FAILURE_SILENT
    assert "MISSING_SILENT_MODE_ON_COGNITIVE_SILENT" in result.rejection_reason


# ============================================================================
# Test 5: 显式指定静默模式合法放行断言 (Silent Mode Explicit Pass)
# ============================================================================
def test_5_silent_mode_explicit_passes(sample_candidates):
    """验证：LLM 显式指定 OBSERVATIONAL_STANCE 时，合规放行为 COGNITIVE_SILENT"""
    raw_response = {
        "status": "COGNITIVE_SILENT",
        "candidate_id": None,
        "silent_mode": "OBSERVATIONAL_STANCE",
        "reason": "Observing the field"
    }
    result = LLMBoundaryValidator.validate_and_sanitize(raw_response, sample_candidates)

    assert result.is_valid is True
    assert result.decision.status == MindDecisionStatus.COGNITIVE_SILENT
    assert result.decision.silent_mode == CognitiveSilentMode.OBSERVATIONAL_STANCE


# ============================================================================
# Test 6: 校验器零选择权断言 (Validator Never Selects)
# ============================================================================
def test_6_validator_never_selects_substitute_candidate(sample_candidates):
    """验证：面对各类非法输入，Validator 只能 VALIDATE 或 REJECT，绝不自行补选其他候选"""
    illegal_inputs = [
        {"status": "SELECTED", "candidate_id": None},                                  # 缺失 ID
        {"status": "SELECTED", "candidate_id": "AFF_NON_EXISTENT"},                   # 幻觉 ID
        {"status": "SELECTED", "candidate_id": "AFF_A", "silent_mode": "PASSIVE_CONSERVATION"}, # 冲突
        {"status": "UNKNOWN_STATUS", "candidate_id": None},                            # 未知状态
        "{malformed_json",                                                             # 损坏 JSON
    ]

    for raw in illegal_inputs:
        res = LLMBoundaryValidator.validate_and_sanitize(raw, sample_candidates)
        assert res.is_valid is False
        assert res.decision.status == MindDecisionStatus.SYSTEM_FAILURE_SILENT
        # 绝不替模型擅自选择合法列表中的 AFF_A / AFF_B
        assert res.decision.candidate_id is None
