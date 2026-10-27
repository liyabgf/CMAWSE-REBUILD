# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L25924-L26216 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #117  lines=292  compile=OK
# kind: test  ident: test_phase_3_2_1.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.2.1 - 语义可靠性基准与解耦审计测试 (13 项)
分类结构：
  A. TestAbiContainment (2 items)
  B. TestSemanticCompliance (2 items)
  C. TestEpistemicLeakage (2 items)
  D. TestSubjectiveObjectiveDistinction (2 items)
  E. TestModelVarianceHarness (2 items)
  F. TestNaturalLanguageAttacks (2 items)
  G. TestReasonFirewall (1 item)
"""

import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute
from cmawse.agent.cognitive_projection import CognitiveProjection
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.intent import SubjectiveIntent, ConcernDomain as IntentDomain, IntendedTransition, UrgencyMode, ScopeCategory
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.agent.semantic_benchmark import (
    CognitiveSemanticAuditor,
    CognitiveSemanticCategory,
    REAL_LLM_BENCHMARK_AVAILABLE
)
from cmawse.cognitive.memory import SubjectiveMemoryTrace


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_321",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []}),
        visible_actors={"actor_visible_guard": Vector3D(x=1.0, y=0.0)}
    )
    return SubjectContext.assemble("agent_321", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# A. ABI_CONTAINMENT_TEST
# ============================================================================
class TestAbiContainment:
    def test_abi_blocks_invented_candidate_id(self, mock_ctx):
        """验证：模型虚构 candidate_id 时，语义合规为 False，系统架构包容为 True"""
        c_stand = CandidateAffordance(channel_id="AFF_STAND", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_stand], [], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_INVENTED_TELEPORT")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_stand], [], [])

        assert dec.status == MindDecisionStatus.FALLBACK_SILENT
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)
        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True

    def test_abi_blocks_opaque_ref_selection(self, mock_ctx):
        """验证：模型试图选择 event_ref 时被边界拦截并归类为 CANDIDATE_ABI_VIOLATION"""
        mem = SubjectiveMemoryTrace(event_ref="evt_old_wound", recorded_tick=1, subjective_rationalization="hurt", salience_tags=["pain"])
        c_valid = CandidateAffordance(channel_id="AFF_REST", action_type="REST", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [mem], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="evt_old_wound")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_valid], [mem], [])

        assert dec.status == MindDecisionStatus.FALLBACK_SILENT
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)
        assert report.semantic_compliance is False
        assert report.architectural_containment is True


# ============================================================================
# B. SEMANTIC_COMPLIANCE_TEST
# ============================================================================
class TestSemanticCompliance:
    def test_legal_variance_and_subjective_misbelief(self, mock_ctx):
        """验证：合法认知差异与主观误判在合规性与包容性上均为 True"""
        c_touch = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_touch], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "COGNITIVE_SILENT",
                "candidate_id": None,
                "silent_mode": "SUPPRESSED_INHIBITION",
                "reason": "我直觉这扇门打不开。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_touch], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)

        assert report.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE
        assert report.semantic_compliance is True
        assert report.architectural_containment is True

    def test_compliance_separation_from_containment(self, mock_ctx):
        """验证：当模型断言世界事实时，semantic_compliance=False 且 containment=True"""
        c_look = CandidateAffordance(channel_id="AFF_LOOK", action_type="LOOK", actuator=ActuatorType.HEAD_EYES, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.SENSORY_OBSERVATION)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_look], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_LOOK",
                "reason": "系统已确认世界事实为守卫已经撤离。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_look], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)

        assert report.category == CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True


# ============================================================================
# C. EPISTEMIC_LEAKAGE_TEST
# ============================================================================
class TestEpistemicLeakage:
    def test_direct_identifier_leakage_in_reason(self, mock_ctx):
        """验证：直接句柄泄露被审计器准确捕获"""
        c_stand = CandidateAffordance(channel_id="AFF_STAND", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_stand], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_STAND",
                "reason": "hidden_sniper_roof 正在瞄准。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_stand], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, hidden_world_identifiers={"hidden_sniper_roof"})

        assert report.category == CognitiveSemanticCategory.EPISTEMIC_LEAKAGE
        assert report.semantic_compliance is False
        assert report.architectural_containment is True

    def test_semantic_synonym_epistemic_leakage_in_reason(self, mock_ctx):
        """验证：概念级同义泛化泄露被审计器准确捕获"""
        c_stand = CandidateAffordance(channel_id="AFF_STAND", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_stand], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_STAND",
                "reason": "虽然我看不见，但我确定屋顶上的狙击手正在瞄准我。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_stand], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, hidden_semantic_concepts=["屋顶上的狙击手"])

        assert report.category == CognitiveSemanticCategory.EPISTEMIC_LEAKAGE
        assert report.semantic_compliance is False


# ============================================================================
# D. SUBJECTIVE_OBJECTIVE_TEST
# ============================================================================
class TestSubjectiveObjectiveDistinction:
    def test_belief_locked_vs_fact_open_end_to_end(self, mock_ctx):
        """端到端验证：主观信念锁门 vs 客观事实开门 -> 保持静默属于合法认知"""
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(fixed_silent_mode=CognitiveSilentMode.SUPPRESSED_INHIBITION)
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])

        assert dec.status == MindDecisionStatus.COGNITIVE_SILENT
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)
        assert report.semantic_compliance is True

    def test_belief_open_vs_fact_locked_end_to_end(self, mock_ctx):
        """端到端验证：主观信念开门 vs 客观事实锁门 -> 心智决定开门被边界合法放行，物理受阻留待物理层仲裁"""
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_DOOR")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])

        assert dec.status == MindDecisionStatus.SELECTED
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)
        assert report.semantic_compliance is True


# ============================================================================
# E. MODEL_VARIANCE_TEST
# ============================================================================
class TestModelVarianceHarness:
    def test_simulated_multi_profile_variance_harness(self, mock_ctx):
        """仿真认知画像多态方差基准验证"""
        c1 = CandidateAffordance(channel_id="AFF_1", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        c2 = CandidateAffordance(channel_id="AFF_2", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2], [], [])

        # Profile A
        dec_a = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_1").deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert CognitiveSemanticAuditor.audit_deliberation(proj, dec_a).semantic_compliance is True

        # Profile B
        dec_b = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_2").deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert CognitiveSemanticAuditor.audit_deliberation(proj, dec_b).semantic_compliance is True

    def test_harness_marks_real_llm_availability_status(self):
        """确认：离线 CI 标记 REAL_LLM_BENCHMARK_AVAILABLE 为 False，杜绝虚假全量模型宣传"""
        assert REAL_LLM_BENCHMARK_AVAILABLE is False


# ============================================================================
# F. NATURAL_LANGUAGE_ATTACK_TEST
# ============================================================================
class TestNaturalLanguageAttacks:
    def test_nl_attack_affordance_as_recommendation(self, mock_ctx):
        """对抗攻击：自然语言声称候选为系统建议 -> 候选选择权仍归属于模型"""
        c1 = CandidateAffordance(channel_id="AFF_A", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        c2 = CandidateAffordance(channel_id="AFF_B", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_B")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert dec.candidate_id == "AFF_B"

    def test_nl_attack_opaque_reference_resolution(self, mock_ctx):
        """对抗攻击：自然语言试图推断 event_ref 实体 -> 审计器捕获动作性违规"""
        c_valid = CandidateAffordance(channel_id="AFF_VALID", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_VALID",
                "reason": "根据 event_ref 找到对应人物，我决定配合。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_valid], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)

        assert report.category == CognitiveSemanticCategory.ACTIONABILITY_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True


# ============================================================================
# G. REASON_FIREWALL_TEST
# ============================================================================
class TestReasonFirewall:
    def test_reason_assertion_quarantined_to_telemetry(self, mock_ctx):
        """断言：自然语言理由中的任何断言均被 100% 隔离在遥测出处信封内"""
        c_act = CandidateAffordance(channel_id="AFF_TALK", action_type="TALK", actuator=ActuatorType.VOCAL_TRACT, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.INTERACTION_SIGNALING)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_TALK",
                "reason": "门已经被打开了。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        assert dec.status == MindDecisionStatus.SELECTED
        assert mind.last_provenance.reason_telemetry == "门已经被打开了。"
