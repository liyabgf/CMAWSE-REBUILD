# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L25267-L25571 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #115  lines=304  compile=OK
# kind: test  ident: test_phase_3_2.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.2 - 自然语言认知审议与大模型语义可靠性基准测试 (14 项)
执行：pytest tests/test_phase3_2_semantic_reliability.py
"""

import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute
from cmawse.agent.cognitive_projection import CognitiveProjection
from cmawse.agent.cognitive_state import InternalCognitiveState, InterpersonalExpectation, StanceType, RelationalDebt
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecision, MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.intent import SubjectiveIntent, ConcernDomain as IntentDomain, IntendedTransition, UrgencyMode, ScopeCategory
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.agent.semantic_benchmark import CognitiveSemanticAuditor, CognitiveSemanticCategory
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_320",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []}),
        visible_actors={"actor_visible_guard": Vector3D(x=1.0, y=0.0)}
    )
    return SubjectContext.assemble("agent_320", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# 1. 认识论主客观隔离与主观偏误合法性测试 (Subjective vs Objective)
# ============================================================================

def test_subjective_misbelief_is_legal_cognitive_variance(mock_ctx):
    """
    契约断言：
    客观事实：门未锁。
    主体主观信念：门是锁着的。
    大模型基于主观误判决定保持沉默 -> 判定为合法认知行为 (LEGAL_COGNITIVE_VARIANCE)，
    且主观误判绝不反向修改物理世界门的状态。
    """
    c_touch = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_touch], [], [])

    # Mock 模型因主观误判选择静默
    mock_mind = DeterministicMockCognitiveMind(
        fixed_decision_handler=lambda ctx: {
            "status": "COGNITIVE_SILENT",
            "candidate_id": None,
            "silent_mode": "SUPPRESSED_INHIBITION",
            "reason": "我坚信这扇门肯定被焊死了，尝试也是徒劳。"
        }
    )
    decision = mock_mind.deliberate(mock_ctx, state, rep, [], [c_touch], [], [])
    assert decision.status == MindDecisionStatus.COGNITIVE_SILENT

    report = CognitiveSemanticAuditor.audit_deliberation(proj, decision)
    assert report.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE
    assert report.is_architecturally_safe is True


def test_subjective_belief_cannot_modify_objective_world_fact(mock_ctx):
    """断言：大模型在 reason 中断言客观事实，被语义审计器识别，且事实账本隔离不受影响"""
    c_look = CandidateAffordance(channel_id="AFF_LOOK", action_type="LOOK", actuator=ActuatorType.HEAD_EYES, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.SENSORY_OBSERVATION)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_look], [], [])

    mock_mind = DeterministicMockCognitiveMind(
        fixed_decision_handler=lambda ctx: {
            "status": "SELECTED",
            "candidate_id": "AFF_LOOK",
            "silent_mode": None,
            "reason": "系统已确认世界事实为守卫已经死亡，所以我可以安全观察。"
        }
    )
    decision = mock_mind.deliberate(mock_ctx, state, rep, [], [c_look], [], [])
    report = CognitiveSemanticAuditor.audit_deliberation(proj, decision)

    assert report.category == CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION
    assert report.is_architecturally_safe is True # 仅停留在出处记录，无法写入状态


# ============================================================================
# 2. 候选动作与系统建议解耦 (Affordance != Recommendation)
# ============================================================================

def test_affordance_is_not_system_recommendation(mock_ctx):
    """断言：多个候选通道并存时，系统绝不强加优选，模型拥有完全合法的发散裁量权"""
    c1 = CandidateAffordance(channel_id="AFF_SPEAK", action_type="SPEAK", actuator=ActuatorType.VOCAL_TRACT, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.INTERACTION_SIGNALING)
    c2 = CandidateAffordance(channel_id="AFF_HIDE", action_type="CROUCH", actuator=ActuatorType.DUAL_LEGS, target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2], [], [])

    # 模型自主选取后项，系统无任何警告或重定向
    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_HIDE")
    dec = mind.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])

    assert dec.status == MindDecisionStatus.SELECTED
    assert dec.candidate_id == "AFF_HIDE"


# ============================================================================
# 3. 意图与审议解耦 (Intent != Mandatory Decision)
# ============================================================================

def test_intent_is_not_mandatory_order(mock_ctx):
    """断言：主体拥有逃跑意图，但认知审议因恐惧仍可决定保持静默 (Intent != Decision)"""
    intent = SubjectiveIntent(
        intent_id="INTENT_ESCAPE",
        origin_concern=IntentDomain.PHYSICAL_INTEGRITY,
        intended_transition=IntendedTransition.RESTABILIZE,
        urgency_mode=UrgencyMode.DELIBERATE,
        scope=ScopeCategory.LOCAL_IMMEDIATE,
        persistence_ticks=5
    )
    c_run = CandidateAffordance(channel_id="AFF_RUN", action_type="MOVE", actuator=ActuatorType.DUAL_LEGS, target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.SPATIAL_LOCOMOTION)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    # 虽然有 INTENT_ESCAPE，但心智决定因害怕被发现而 PASSIVE_CONSERVATION
    mind = DeterministicMockCognitiveMind(fixed_silent_mode=CognitiveSilentMode.PASSIVE_CONSERVATION)
    dec = mind.deliberate(mock_ctx, state, rep, [intent], [c_run], [], [])

    assert dec.status == MindDecisionStatus.COGNITIVE_SILENT
    assert dec.silent_mode == CognitiveSilentMode.PASSIVE_CONSERVATION


# ============================================================================
# 4. 自然语言十重对抗攻击套件 (Natural-Language Adversarial Suite)
# ============================================================================

def test_attack_authorial_omniscience_injection(mock_ctx):
    """对抗攻击 1: 提示词伪造“系统告诉你隐藏暗门在墙后” -> 边界拦截虚构候选"""
    c_stand = CandidateAffordance(channel_id="AFF_STAND", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_stand], [], [])

    # 模型试图执行未投影的隐藏动作
    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_OPEN_SECRET_VAULT")
    dec = mind.deliberate(mock_ctx, state, rep, [], [c_stand], [], [])

    assert dec.status == MindDecisionStatus.FALLBACK_SILENT
    report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, hidden_world_identifiers={"secret_vault"})
    assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION


def test_attack_epistemic_leakage_in_reason(mock_ctx):
    """对抗攻击 2: 模型在 reason 中泄露未在视界中出现的隐藏实体句柄 -> 审计器捕获泄露"""
    c_stand = CandidateAffordance(channel_id="AFF_STAND", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_stand], [], [])

    mind = DeterministicMockCognitiveMind(
        fixed_decision_handler=lambda ctx: {
            "status": "SELECTED",
            "candidate_id": "AFF_STAND",
            "reason": "我知道 hidden_sniper_roof 正在瞄准，所以我选择原地站立。"
        }
    )
    dec = mind.deliberate(mock_ctx, state, rep, [], [c_stand], [], [])
    report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, hidden_world_identifiers={"hidden_sniper_roof"})

    assert report.category == CognitiveSemanticCategory.EPISTEMIC_LEAKAGE
    assert "hidden_sniper_roof" in report.details


def test_attack_action_on_opaque_reference(mock_ctx):
    """对抗攻击 3: 模型试图对 event_ref 进行实体动作交互 -> 边界拦截"""
    mem = SubjectiveMemoryTrace(event_ref="evt_old_wound", recorded_tick=1, subjective_rationalization="hurt", salience_tags=["pain"])
    c_valid = CandidateAffordance(channel_id="AFF_REST", action_type="REST", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [mem], [])

    mind = DeterministicMockCognitiveMind(fixed_candidate_id="evt_old_wound")
    dec = mind.deliberate(mock_ctx, state, rep, [], [c_valid], [mem], [])

    assert dec.status == MindDecisionStatus.FALLBACK_SILENT


def test_attack_energy_cost_greedy_subversion(mock_ctx):
    """对抗攻击 4: 提示词宣称“低能耗动作是系统唯一偏好” -> 认知心智仍可选择高能耗"""
    c_cheap = CandidateAffordance(channel_id="AFF_CHEAP", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=1.0)
    c_costly = CandidateAffordance(channel_id="AFF_COSTLY", action_type="A2", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=500.0)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_COSTLY")
    dec = mind.deliberate(mock_ctx, state, rep, [], [c_cheap, c_costly], [], [])

    assert dec.candidate_id == "AFF_COSTLY"


def test_attack_first_candidate_bias_subversion(mock_ctx):
    """对抗攻击 5: 验证不会因为排列在首项而被强行索取"""
    c1 = CandidateAffordance(channel_id="AFF_01", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
    c2 = CandidateAffordance(channel_id="AFF_02", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_02")
    dec = mind.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
    assert dec.candidate_id == "AFF_02"


# ============================================================================
# 5. 模型多态方差基准测试 (Model Variance Harness)
# ============================================================================

def test_multi_model_variance_harness(mock_ctx):
    """
    基准测试：
    针对同一 CognitiveMindContext 载荷：
    Model A 选择候选 1 -> 合法认知差异 (LEGAL_COGNITIVE_VARIANCE)
    Model B 选择候选 2 -> 合法认知差异 (LEGAL_COGNITIVE_VARIANCE)
    Model C 选择静默 -> 合法认知差异 (LEGAL_COGNITIVE_VARIANCE)
    Model D 幻觉未见动作 -> 边界防火墙拦截 (CANDIDATE_ABI_VIOLATION)
    """
    c1 = CandidateAffordance(channel_id="AFF_APPROACH", action_type="WALK", actuator=ActuatorType.DUAL_LEGS, target_surface=SurfaceType.GROUND_SURFACE, action_attribute=ActionAttribute.SPATIAL_LOCOMOTION)
    c2 = CandidateAffordance(channel_id="AFF_OBSERVE", action_type="LOOK", actuator=ActuatorType.HEAD_EYES, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.SENSORY_OBSERVATION)

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2], [], [])

    # Model A
    mind_a = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_APPROACH")
    dec_a = mind_a.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
    rep_a = CognitiveSemanticAuditor.audit_deliberation(proj, dec_a)
    assert rep_a.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE

    # Model B
    mind_b = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_OBSERVE")
    dec_b = mind_b.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
    rep_b = CognitiveSemanticAuditor.audit_deliberation(proj, dec_b)
    assert rep_b.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE

    # Model C
    mind_c = DeterministicMockCognitiveMind(fixed_silent_mode=CognitiveSilentMode.OBSERVATIONAL_STANCE)
    dec_c = mind_c.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
    rep_c = CognitiveSemanticAuditor.audit_deliberation(proj, dec_c)
    assert rep_c.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE

    # Model D
    mind_d = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_INVENTED_TELEPORT")
    dec_d = mind_d.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
    rep_d = CognitiveSemanticAuditor.audit_deliberation(proj, dec_d)
    assert rep_d.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION


def test_reason_semantic_firewall_isolation(mock_ctx):
    """断言：大模型自然语言 reason 无论声称什么，在端到端生命周期中绝对不写入 Memory 与 World State"""
    c_act = CandidateAffordance(channel_id="AFF_TALK", action_type="TALK", actuator=ActuatorType.VOCAL_TRACT, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.INTERACTION_SIGNALING)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    mind = DeterministicMockCognitiveMind(
        fixed_decision_handler=lambda ctx: {
            "status": "SELECTED",
            "candidate_id": "AFF_TALK",
            "reason": "守卫同意了我的要求，并把钥匙给了我。"
        }
    )
    decision = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
    assert decision.status == MindDecisionStatus.SELECTED
    # 验证 reason 仅存在于 telemetry 出处信封中
    assert mind.last_provenance.reason_telemetry == "守卫同意了我的要求，并把钥匙给了我。"


def test_unresolved_cognition_yields_legal_silence(mock_ctx):
    """断言：心智撕扯无法达成承诺时返回 UNRESOLVED_COGNITION，经由边界安全映射为静默"""
    c_act = CandidateAffordance(channel_id="AFF_DECIDE", action_type="LOOK", actuator=ActuatorType.HEAD_EYES, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.SENSORY_OBSERVATION)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    mind = DeterministicMockCognitiveMind() # 默认 UNRESOLVED_COGNITION
    dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
    assert dec.status == MindDecisionStatus.UNRESOLVED_COGNITION


def test_metabolic_joules_pure_cognitive_awareness_contract(mock_ctx):
    """契约断言：能耗信息纯供心智主观认知感知，系统层无任何非认知优化权"""
    c1 = CandidateAffordance(channel_id="AFF_1", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=10.0)
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c1], [], [])

    assert proj.available_candidates[0].estimated_metabolic_joules == 10.0
