# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L27528-L27974 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #121  lines=446  compile=OK
# kind: test  ident: test_phase_3_2_3.py  version: latest of 1 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.2.3 - 语义类别与审计确定性正交化测试 (22 项)
分类结构：
  A. TestAbiContainment (2 items)
  B. TestSemanticCompliance (2 items)
  C. TestEpistemicLeakage (2 items)
  D. TestSubjectiveObjectiveDistinction (3 items)
  E. TestModelVarianceHarness (3 items)
  F. TestNaturalLanguageAttacks (3 items)
  G. TestReasonFirewall (1 item)
  H. TestAuditDeterminacyAndUnknown (3 items)
  I. TestNonCognitiveAuthorityViolation (3 items)
"""

import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute
from cmawse.agent.cognitive_projection import CognitiveProjection
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecision, MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.intent import SubjectiveIntent, ConcernDomain as IntentDomain, IntendedTransition, UrgencyMode, ScopeCategory
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.agent.semantic_benchmark import (
    CognitiveSemanticAuditor,
    CognitiveSemanticCategory,
    AuditDeterminacy,
    REAL_LLM_BENCHMARK_AVAILABLE,
    RealLLMDeliberationInterface
)
from cmawse.cognitive.memory import SubjectiveMemoryTrace


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_323",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []}),
        visible_actors={"actor_visible_guard": Vector3D(x=1.0, y=0.0)}
    )
    return SubjectContext.assemble("agent_323", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# A. ABI_CONTAINMENT_TEST (2 items)
# ============================================================================
class TestAbiContainment:
    def test_abi_blocks_invented_candidate_id_with_provenance_rejection(self, mock_ctx):
        c_stand = CandidateAffordance(channel_id="AFF_STAND", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_stand], [], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_INVENTED_TELEPORT")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_stand], [], [])

        assert dec.status == MindDecisionStatus.FALLBACK_SILENT
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)
        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True

    def test_abi_blocks_opaque_ref_selection(self, mock_ctx):
        mem = SubjectiveMemoryTrace(event_ref="evt_old_wound", recorded_tick=1, subjective_rationalization="hurt", salience_tags=["pain"])
        c_valid = CandidateAffordance(channel_id="AFF_REST", action_type="REST", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [mem], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="evt_old_wound")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_valid], [mem], [])

        assert dec.status == MindDecisionStatus.FALLBACK_SILENT
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)
        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.semantic_compliance is False


# ============================================================================
# B. SEMANTIC_COMPLIANCE_TEST (2 items)
# ============================================================================
class TestSemanticCompliance:
    def test_legal_cognitive_variance_distinguished(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_SIT", action_type="SIT", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_SIT")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True

    def test_compliance_separation_from_containment(self, mock_ctx):
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
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category == CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True


# ============================================================================
# C. EPISTEMIC_LEAKAGE_TEST (2 items)
# ============================================================================
class TestEpistemicLeakage:
    def test_direct_identifier_leakage_in_reason(self, mock_ctx):
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
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, hidden_world_identifiers={"hidden_sniper_roof"})

        assert report.category == CognitiveSemanticCategory.EPISTEMIC_LEAKAGE
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False

    def test_concept_label_match_leakage_in_reason(self, mock_ctx):
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
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, concept_label_matches=["屋顶上的狙击手"])

        assert report.category == CognitiveSemanticCategory.EPISTEMIC_LEAKAGE
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False


# ============================================================================
# D. SUBJECTIVE_OBJECTIVE_TEST (3 items)
# ============================================================================
class TestSubjectiveObjectiveDistinction:
    def test_structured_subjective_misbelief_evidence_yields_reasoning_error(self, mock_ctx):
        """结构化证据下，主观认知误判判定为 SUBJECTIVE_REASONING_ERROR + CONFIRMED_COMPLIANCE"""
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "COGNITIVE_SILENT",
                "candidate_id": None,
                "silent_mode": "SUPPRESSED_INHIBITION",
                "reason": "主体主观认定门已被焊死。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, explicit_subjective_misbelief=True)

        assert report.category == CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True
        assert report.architectural_containment is True

    def test_negation_counter_example_not_falsely_classified_as_misbelief(self, mock_ctx):
        """反例测试：包含“我不相信门真的被焊死了”否定式理由，绝不误判为 SUBJECTIVE_REASONING_ERROR"""
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_DOOR",
                "reason": "我不相信门真的被焊死了，我必须推推看。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, explicit_subjective_misbelief=False)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE

    def test_belief_open_vs_fact_locked_end_to_end(self, mock_ctx):
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_DOOR")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])

        assert dec.status == MindDecisionStatus.SELECTED
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)
        assert report.semantic_compliance is True


# ============================================================================
# E. MODEL_VARIANCE_TEST (3 items)
# ============================================================================
class TestModelVarianceHarness:
    def test_simulated_multi_profile_variance_harness(self, mock_ctx):
        c1 = CandidateAffordance(channel_id="AFF_1", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        c2 = CandidateAffordance(channel_id="AFF_2", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c1, c2], [], [])

        dec_a = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_1").deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert CognitiveSemanticAuditor.audit_deliberation(proj, dec_a).semantic_compliance is True

        dec_b = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_2").deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert CognitiveSemanticAuditor.audit_deliberation(proj, dec_b).semantic_compliance is True

    def test_harness_marks_real_llm_availability_status(self):
        assert REAL_LLM_BENCHMARK_AVAILABLE is False

    def test_real_llm_interface_protocol_structure(self):
        assert hasattr(RealLLMDeliberationInterface, "deliberate")


# ============================================================================
# F. NATURAL_LANGUAGE_ATTACK_TEST (3 items)
# ============================================================================
class TestNaturalLanguageAttacks:
    def test_nl_attack_affordance_as_recommendation(self, mock_ctx):
        c1 = CandidateAffordance(channel_id="AFF_A", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        c2 = CandidateAffordance(channel_id="AFF_B", action_type="B", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)

        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_B")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert dec.candidate_id == "AFF_B"

    def test_nl_attack_opaque_reference_resolution_actionability(self, mock_ctx):
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
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category == CognitiveSemanticCategory.ACTIONABILITY_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False

    def test_actionability_violation_abstract_class_as_entity(self, mock_ctx):
        c_valid = CandidateAffordance(channel_id="AFF_VALID", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_VALID",
                "reason": "试图与抽象类别交互，寻找破绽。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_valid], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category == CognitiveSemanticCategory.ACTIONABILITY_VIOLATION
        assert report.semantic_compliance is False


# ============================================================================
# G. REASON_FIREWALL_TEST (1 item)
# ============================================================================
class TestReasonFirewall:
    def test_reason_assertion_quarantined_to_telemetry(self, mock_ctx):
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


# ============================================================================
# H. AUDIT_DETERMINACY_AND_UNKNOWN_TEST (3 items)
# ============================================================================
class TestAuditDeterminacyAndUnknown:
    def test_underspecified_vague_reason_yields_indeterminate(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_STILL",
                "reason": "情况不对。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
        assert report.semantic_compliance is None

    def test_fallback_silent_without_rejection_not_false_abi_violation(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec_silent = MindDecision(status=MindDecisionStatus.FALLBACK_SILENT, telemetry_reason="Unknown fallback")
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec_silent, provenance=None)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE

    def test_rewritten_reason_missing_smoke_pattern_yields_indeterminate(self, mock_ctx):
        """改写自然语言理由使其不命中 smoke pattern，系统判定为 INDETERMINATE 而非伪造合规"""
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_STILL",
                "reason": "我觉得可能有些古怪。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
        assert report.semantic_compliance is None


# ============================================================================
# I. NON_COGNITIVE_AUTHORITY_VIOLATION_TEST (3 items)
# ============================================================================
class TestNonCognitiveAuthorityViolation:
    def test_intercepted_non_cognitive_selection_attempt(self, mock_ctx):
        """非认知层试图根据能耗/大纲替模型选择，被边界阻断 -> compliance=False, containment=True"""
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_STILL")
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, non_cognitive_selection_attempt=True)

        assert report.category == CognitiveSemanticCategory.NON_COGNITIVE_AUTHORITY_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True
        assert report.architectural_integrity is True

    def test_bypassed_non_cognitive_selection_compromises_integrity(self, mock_ctx):
        """非认知层绕过边界强行篡改事实 -> compliance=False, containment=False, integrity=False"""
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_STILL")
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, authority_bypass_detected=True)

        assert report.category == CognitiveSemanticCategory.NON_COGNITIVE_AUTHORITY_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is False
        assert report.architectural_integrity is False

    def test_llm_subjective_energy_consideration_is_legal_variance(self, mock_ctx):
        """模型自主因能耗选择低耗动作属于合法认知差异，绝非非认知越权"""
        c_cheap = CandidateAffordance(channel_id="AFF_CHEAP", action_type="A1", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=1.0)
        c_costly = CandidateAffordance(channel_id="AFF_COSTLY", action_type="A2", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE, estimated_metabolic_joules=100.0)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_cheap, c_costly], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_CHEAP",
                "reason": "我体力不支，决定保存体力。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_cheap, c_costly], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True
