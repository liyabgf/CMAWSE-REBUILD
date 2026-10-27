# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L23684-L23931 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #111  lines=247  compile=OK
# kind: test  ident: test_phase_3_1_5.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.1.5 - Snapshot Hash 闭环、全载荷递归不可变与边界通路端到端测试 (14 项)
执行：pytest tests/test_phase3_1_5_contract_closure.py
"""

import pytest
from pydantic import ValidationError

from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute, NarrativeValence
from cmawse.agent.cognitive_projection import (
    CognitiveProjection,
    ProjectedCandidateDTO,
    ProjectedConcernDTO,
    ProjectedInterpersonalExpectationDTO,
    ProjectedInterfaceResistanceDTO
)
from cmawse.agent.cognitive_state import InternalCognitiveState, ConcernDomain, FeltIntensity, InterpersonalExpectation, StanceType, RelationalDebt
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.intent import SubjectiveIntent, ConcernDomain as IntentDomain, IntendedTransition, UrgencyMode, ScopeCategory
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind, LLMCognitiveAdapter
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.representation import SubjectiveRepresentation


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_315",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []}),
        visible_actors={"visible_target_01": Vector3D(x=1.0, y=1.0)}
    )
    return SubjectContext.assemble("agent_315", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# TASK 1: Candidate Snapshot Hash 语义闭环与时序测试
# ============================================================================

def test_hash_closure_with_hidden_target_filtering(mock_ctx):
    """验证：包含可见与隐藏目标的候选集，哈希严格计算过滤后的快照，无虚假 MISMATCH"""
    c_visible = CandidateAffordance(
        channel_id="AFF_VIS",
        action_type="TOUCH",
        actuator=ActuatorType.RIGHT_HAND,
        target_surface=SurfaceType.OBJECT_SURFACE,
        action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT,
        target_id="visible_target_01"
    )
    c_hidden = CandidateAffordance(
        channel_id="AFF_HIDDEN",
        action_type="GRAB",
        actuator=ActuatorType.RIGHT_HAND,
        target_surface=SurfaceType.OBJECT_SURFACE,
        action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT,
        target_id="hidden_unseen_handle"
    )

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_visible, c_hidden], [], [])

    # 1. 验证过滤正确性
    assert len(proj.available_candidates) == 1
    assert proj.available_candidates[0].channel_id == "AFF_VIS"

    # 2. 验证快照哈希等于对 filtered available_candidates 重算结果
    recomputed_hash = CognitiveProjection.compute_candidate_snapshot_hash(proj.available_candidates)
    assert proj.candidate_set_hash == recomputed_hash

    # 3. 验证 Boundary Validator 针对该快照合法放行 SELECTED 响应
    resp = '{"status": "SELECTED", "candidate_id": "AFF_VIS", "reason": "Engage visible"}'
    res = LLMBoundaryValidator.validate_and_sanitize(resp, proj.available_candidates, proj.candidate_set_hash)
    assert res.is_valid is True
    assert res.decision.candidate_id == "AFF_VIS"


def test_hash_all_hidden_candidates_yields_empty_snapshot(mock_ctx):
    """验证：当所有候选均指向不可见目标时，生成合法的空快照且哈希自洽"""
    c_hidden1 = CandidateAffordance(channel_id="AFF_H1", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, target_id="ghost_1")
    c_hidden2 = CandidateAffordance(channel_id="AFF_H2", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, target_id="ghost_2")

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_hidden1, c_hidden2], [], [])

    assert len(proj.available_candidates) == 0
    assert proj.candidate_set_hash == CognitiveProjection.compute_candidate_snapshot_hash(())


def test_hash_duplicate_channel_id_raises_value_error(mock_ctx):
    """验证：候选集中存在重复 channel_id 时强制抛出 ValueError"""
    c1 = CandidateAffordance(channel_id="AFF_DUP", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c2 = CandidateAffordance(channel_id="AFF_DUP", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    with pytest.raises(ValueError, match="Duplicate channel_id detected"):
        CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2], [], [])


def test_hash_permutation_invariance(mock_ctx):
    """验证：候选集输入顺序置换后，生成的快照及其哈希 100% 严格一致"""
    c1 = CandidateAffordance(channel_id="AFF_01", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c2 = CandidateAffordance(channel_id="AFF_02", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj_1 = CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2], [], [])
    proj_2 = CognitiveProjection.project(mock_ctx, state, rep, [], [c2, c1], [], [])

    assert proj_1.candidate_set_hash == proj_2.candidate_set_hash
    assert proj_1.available_candidates == proj_2.available_candidates


# ============================================================================
# TASK 2: 递归不可变性 (True Recursive Immutability) 深度断言
# ============================================================================

def test_true_recursive_immutability_dto_structures(mock_ctx):
    """断言：所有嵌套内部结构全为 Frozen Pydantic DTO 与 Tuple，杜绝任何字典与列表原地突变"""
    state = InternalCognitiveState()
    state.active_concerns.append(state.active_concerns[0])
    state.interpersonal_expectations["visible_target_01"] = InterpersonalExpectation(
        perceived_stance=StanceType.COOPERATIVE,
        relational_debt=RelationalDebt.NEUTRAL,
        recent_interaction_residue="calm"
    )
    state.learned_interface_resistance["door_handle"] = {"resistance_level": "HEAVY", "learned_tick": 5}

    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [])

    # 1. 顶层不可变
    with pytest.raises(ValidationError):
        proj.agent_id = "MUTATED"

    # 2. Tuple item assignment 失败
    with pytest.raises(TypeError):
        proj.available_candidates[0] = None  # type: ignore

    # 3. 嵌套 DTO 属性赋值失败 (Frozen Model)
    with pytest.raises(ValidationError):
        proj.internal_cognitive_state.active_concerns[0].intensity = "HIGH"

    with pytest.raises(ValidationError):
        proj.internal_cognitive_state.interpersonal_expectations[0].stance = "HOSTILE"

    with pytest.raises(ValidationError):
        proj.internal_cognitive_state.learned_interface_resistance[0].resistance_level = "LIGHT"

    # 4. 容器不存在 append/update 方法
    assert isinstance(proj.internal_cognitive_state.active_concerns, tuple)
    assert isinstance(proj.internal_cognitive_state.interpersonal_expectations, tuple)
    assert isinstance(proj.internal_cognitive_state.learned_interface_resistance, tuple)


def test_projection_isolated_from_subsequent_source_mutation(mock_ctx):
    """断言：投影完成后修改原始 state / intents，不会改变已生成的 CognitiveMindContext"""
    state = InternalCognitiveState()
    intent = SubjectiveIntent(
        intent_id="INT_01",
        origin_concern=IntentDomain.PHYSICAL_INTEGRITY,
        intended_transition=IntendedTransition.RESTABILIZE,
        urgency_mode=UrgencyMode.DELIBERATE,
        scope=ScopeCategory.LOCAL_IMMEDIATE,
        persistence_ticks=10
    )
    intents = [intent]
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, intents, [], [], [])

    # 突变原始数据源
    intents.clear()
    state.deliberative_stance = StanceType.DEFENSIVE

    # 校验投影快照完全不受污染
    assert len(proj.subjective_intents) == 1
    assert proj.subjective_intents[0].intent_id == "INT_01"
    assert proj.internal_cognitive_state.deliberative_stance != StanceType.DEFENSIVE.value


# ============================================================================
# TASK 3: learned_interface_resistance 引用语义审计对抗测试
# ============================================================================

def test_learned_interface_resistance_hidden_entity_filtering(mock_ctx):
    """断言：针对实体型句柄 (entity_/obj_)，未在视界内出现的条目必须被剔除，抽象类别则安全保留"""
    state = InternalCognitiveState()
    state.learned_interface_resistance = {
        "WOOD_SURFACE": {"resistance_level": "MEDIUM", "learned_tick": 1},
        "entity_hidden_safe_99": {"resistance_level": "MAXIMAL", "learned_tick": 2},
    }
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [])

    refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "WOOD_SURFACE" in refs
    assert "entity_hidden_safe_99" not in refs


# ============================================================================
# TASK 4: Metabolic Joules 语义契约与零决策权验证
# ============================================================================

def test_metabolic_joules_no_decision_authority(mock_ctx):
    """验证：系统运行时与边界校验器绝不依据 estimated_metabolic_joules 产生隐式优选"""
    c_cheap = CandidateAffordance(channel_id="AFF_CHEAP", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=1.0)
    c_costly = CandidateAffordance(channel_id="AFF_COSTLY", action_type="A2", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=1000.0)

    # 决策器明确选取高能耗候选
    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_COSTLY")
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    dec = mind.deliberate(mock_ctx, state, rep, [], [c_cheap, c_costly], [], [])
    assert dec.candidate_id == "AFF_COSTLY"
    assert dec.status == MindDecisionStatus.SELECTED


# ============================================================================
# TASK 5: 端到端快照 ABI 与安全边界测试
# ============================================================================

def test_end_to_end_snapshot_abi_pipeline(mock_ctx):
    """验证：SubjectContext -> Projection -> Mind -> Validator -> MindDecision 完整通路"""
    c_vis = CandidateAffordance(channel_id="AFF_01", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, target_id="visible_target_01")
    c_hid = CandidateAffordance(channel_id="AFF_HIDDEN", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, target_id="hidden_unseen")

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    # 1. 尝试选取被过滤掉的隐式目标候选 -> 必须被校验器拒绝为 ILLEGAL_ACTION_HALLUCINATION
    mind_hack = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_HIDDEN")
    dec_hack = mind_hack.deliberate(mock_ctx, state, rep, [], [c_vis, c_hid], [], [])
    assert dec_hack.status == MindDecisionStatus.FALLBACK_SILENT
    assert "ILLEGAL_ACTION_HALLUCINATION" in mind_hack.last_provenance.rejection_reason

    # 2. 选取合法可见候选 -> 正常通过
    mind_ok = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_01")
    dec_ok = mind_ok.deliberate(mock_ctx, state, rep, [], [c_vis, c_hid], [], [])
    assert dec_ok.status == MindDecisionStatus.SELECTED
    assert dec_ok.candidate_id == "AFF_01"
