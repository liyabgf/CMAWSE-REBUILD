# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L19409-L19511 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #95  lines=102  compile=FAIL:103:unterminated string literal (detected at line 10
# kind: test  ident: test_phase_3_1.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.1 - 认知边界强化与出处审计对抗测试
执行：pytest tests/test_phase3_1_abi_hardening.py
"""

import json
import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute
from cmawse.agent.cognitive_projection import CognitiveProjection, CognitiveMindContext
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.intent import SubjectiveIntent, ConcernDomain, QualitativeTransition, PhenomenologicalUrgency, IntendedScope
from cmawse.agent.ladder import FiveStageWorkLadder
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind, LLMCognitiveAdapter
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.provenance import DecisionProvenanceEnvelope
from cmawse.agent.representation import SubjectiveRepresentation


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_hardened",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []})
    )
    return SubjectContext.assemble("agent_hardened", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


@pytest.fixture
def feasible_candidates() -> list[CandidateAffordance]:
    return [
        CandidateAffordance(channel_id="AFF_01", action_type="ACT_1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, is_physically_feasible=True),
        CandidateAffordance(channel_id="AFF_02", action_type="ACT_2", actuator=ActuatorType.DUAL_LEGS, target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.SPATIAL_LOCOMOTION, is_physically_feasible=True),
    ]


# ============================================================================
# Task 1: 白名单 DTO 注入防护断言 (Whitelist DTO Hardening)
# ============================================================================
def test_task1_whitelist_dto_injection_defense(mock_ctx, feasible_candidates):
    """验证：向内部心智状态或表征注入未知扩展字段，绝对无法透传至 CognitiveMindContext，Schema 严格 extra='forbid'"""
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    projected = CognitiveProjection.project(mock_ctx, state, rep, [], feasible_candidates, [], [])
    projected_dict = projected.model_dump()

    # 尝试直接向 CognitiveMindContext 注入未授权的后门字段
    projected_dict["unauthorized_backdoor_field"] = "LEAK_SECRET"
    with pytest.raises(Exception):
        CognitiveMindContext.model_validate(projected_dict)


# ============================================================================
# Task 2: is_physically_feasible 字段隔离断言 (No Feasibility Leakage)
# ============================================================================
def test_task2_no_physical_feasibility_leakage(mock_ctx, feasible_candidates):
    """验证：投影至大模型的候选 DTO 中绝不包含 is_physically_feasible 内部物理真值字段"""
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    projected = CognitiveProjection.project(mock_ctx, state, rep, [], feasible_candidates, [], [])
    for cand_dto in projected.available_candidates:
        assert not hasattr(cand_dto, "is_physically_feasible")
        assert "is_physically_feasible" not in cand_dto.model_dump()


# ============================================================================
# Task 3: 候选规范化展示排序不变性 (Candidate Canonicalization)
# ============================================================================
def test_task3_candidate_canonicalization_order_invariance(mock_ctx):
    """验证：无论传入候选集如何乱序排列，规范化投影后的序列指纹与结构严格恒定"""
    c1 = CandidateAffordance(channel_id="AFF_B", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c2 = CandidateAffordance(channel_id="AFF_A", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c3 = CandidateAffordance(channel_id="AFF_C", action_type="C", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    proj_1 = CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2, c3], [], [])
    proj_2 = CognitiveProjection.project(mock_ctx, state, rep, [], [c3, c1, c2], [], [])

    # 规范化排序后 channel_id 必然为升序 [AFF_A, AFF_B, AFF_C]
    order_1 = [c.channel_id for c in proj_1.available_candidates]
    order_2 = [c.channel_id for c in proj_2.available_candidates]

    assert order_1 == order_2 == ["AFF_A", "AFF_B", "AFF_C"]
    assert proj_1.candidate_set_hash == proj_2.candidate_set_hash


# ============================================================================
# Task 4: 严格纯 JSON 边界防御断言 (Strict JSON Boundary)
# ============================================================================
def test_task4_strict_json_boundary_defense(feasible_candidates):
    """验证：Markdown 包裹、前后自然语言、重复键、JSON 数组/标量、未知字段全部被拒止为 SYSTEM_FAILURE_SILENT"""
    attacks = [
        # 1. Markdown 代码块包裹
        '