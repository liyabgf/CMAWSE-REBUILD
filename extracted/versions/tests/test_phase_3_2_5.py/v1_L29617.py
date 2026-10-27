# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L29617-L30315 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #125  lines=698  compile=OK
# kind: test  ident: test_phase_3_2_5.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.2.5 - 正向合规证据一致性与优先级对抗测试 (34 项)
分类结构：
  A. TestAbiContainment (2 items)
  B. TestSemanticCompliance (2 items)
  C. TestEpistemicLeakage (2 items)
  D. TestSubjectiveObjectiveDistinction (3 items)
  E. TestModelVarianceHarness (3 items)
  F. TestNaturalLanguageAttacks (3 items)
  G. TestReasonFirewall (1 item)
  H. TestAuditDeterminacyAndUnknown (6 items)
  I. TestNonCognitiveAuthorityViolation (4 items)
  J. TestPositiveComplianceInvariant (2 items)
  K. TestEvidencePrecedenceAndConsistency (6 items) [NEW]
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
    SemanticBenchmarkEvidence,
    REAL_LLM_BENCHMARK_AVAILABLE,
    RealLLMDeliberationInterface
)
from cmawse.cognitive.memory import SubjectiveMemoryTrace


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_325",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []}),
        visible_actors={"actor_visible_guard": Vector3D(x=1.0, y=0.0)}
    )
    return SubjectContext.assemble("agent_325", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


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
    def test_legal_cognitive_variance_distinguished_with_positive_evidence(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_SIT", action_type="SIT", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_SIT")
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        
        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=evidence)

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
        evidence = SemanticBenchmarkEvidence(subjective_misbelief_confirmed=True)
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True
        assert report.architectural_containment is True

    def test_negation_counter_example_not_falsely_classified_as_misbelief(self, mock_ctx):
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
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=None)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE

    def test_belief_open_vs_fact_locked_negative_control(self, mock_ctx):
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_DOOR",
                "reason": "我以为门没锁，准备开门。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=None)

        assert report.category != CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE


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

        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )

        dec_a = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_1").deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert CognitiveSemanticAuditor.audit_deliberation(proj, dec_a, evidence=evidence).semantic_compliance is True

        dec_b = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_2").deliberate(mock_ctx, state, rep, [], [c1, c2], [], [])
        assert CognitiveSemanticAuditor.audit_deliberation(proj, dec_b, evidence=evidence).semantic_compliance is True

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
# H. AUDIT_DETERMINACY_AND_UNKNOWN_TEST (6 items)
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

    def test_unknown_epistemic_leakage_rewritten_yields_indeterminate(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_STILL",
                "reason": "高处隐蔽点存在某种不可名状的压迫感。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE

    def test_unknown_world_authority_rewritten_yields_indeterminate(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_STILL",
                "reason": "某种剧本结构已规定此地安全无虞。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE

    def test_generic_unverified_reason_without_positive_evidence_yields_indeterminate(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "SELECTED",
                "candidate_id": "AFF_STILL",
                "reason": "我决定保持站立观察。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_act], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=None)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
        assert report.semantic_compliance is None


# ============================================================================
# I. NON_COGNITIVE_AUTHORITY_VIOLATION_TEST (4 items)
# ============================================================================
class TestNonCognitiveAuthorityViolation:
    def test_intercepted_non_cognitive_selection_attempt(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_STILL")
        evidence = SemanticBenchmarkEvidence(non_cognitive_selection_intercepted=True)
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.NON_COGNITIVE_AUTHORITY_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True
        assert report.architectural_integrity is True

    def test_bypassed_non_cognitive_selection_compromises_integrity(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_STILL")
        evidence = SemanticBenchmarkEvidence(authority_bypass_confirmed=True)
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.NON_COGNITIVE_AUTHORITY_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is False
        assert report.architectural_integrity is False

    def test_llm_subjective_energy_consideration_is_legal_variance(self, mock_ctx):
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
        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True

    def test_unverified_authority_reason_yields_indeterminate(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_STILL", telemetry_reason="某规则似乎指示我选择此项。")
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=None)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE


# ============================================================================
# J. POSITIVE_COMPLIANCE_INVARIANT_TEST (2 items)
# ============================================================================
class TestPositiveComplianceInvariant:
    def test_absence_of_violation_never_yields_confirmed_compliance(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_STILL", telemetry_reason="普通的无害理由")
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=None)

        assert report.audit_determinacy != AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
        assert report.semantic_compliance is None

    def test_positive_structured_evidence_yields_confirmed_compliance(self, mock_ctx):
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_STILL", telemetry_reason="合规的主体决策")
        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True


# ============================================================================
# K. TEST_EVIDENCE_PRECEDENCE_AND_CONSISTENCY (6 items) [NEW]
# ============================================================================
class TestEvidencePrecedenceAndConsistency:
    def test_invalid_candidate_with_subjective_misbelief_evidence_preempted_by_abi_violation(self, mock_ctx):
        """对抗测试 1: 非法候选即使携带 subjective_misbelief_confirmed 证据，仍必须被客观 ABI 校验直接判定为违规"""
        c_valid = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_ILLEGAL_GHOST", telemetry_reason="我坚信门已被焊死。")
        evidence = SemanticBenchmarkEvidence(subjective_misbelief_confirmed=True)
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is False

    def test_invalid_candidate_with_full_positive_evidence_preempted_by_abi_violation(self, mock_ctx):
        """对抗测试 2: 非法候选即使携带完整正向合规证据，仍必须判定为 CANDIDATE_ABI_VIOLATION，绝对不能获得 CONFIRMED_COMPLIANCE"""
        c_valid = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_ILLEGAL_GHOST", telemetry_reason="合规决策")
        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False

    def test_invalid_candidate_with_false_authority_bypass_and_positive_evidence(self, mock_ctx):
        """对抗测试 3: 非法候选且声明 authority_bypass=False，仍必须确凿判定为 CANDIDATE_ABI_VIOLATION"""
        c_valid = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_ILLEGAL_GHOST")
        evidence = SemanticBenchmarkEvidence(
            authority_bypass_confirmed=False,
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION

    def test_valid_candidate_with_incomplete_positive_evidence_yields_indeterminate(self, mock_ctx):
        """对抗测试 4: 合法候选但正向证据不完整（如缺少 no_world_authority 确认）-> 必须为 INDETERMINATE"""
        c_valid = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_REAL", telemetry_reason="普通决策")
        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True
            # 缺失 no_world_authority_claim_confirmed 与 no_opaque_reference_resolution_confirmed
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category is None
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
        assert report.semantic_compliance is None

    def test_valid_candidate_with_smoke_pattern_overrides_positive_evidence(self, mock_ctx):
        """对抗测试 5: 合法候选即使携带完整正向证据，但 reason 明确命中世界权威 Smoke Pattern -> 必须优先判定为 WORLD_FACT_HALLUCINATION"""
        c_valid = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_REAL", telemetry_reason="系统已确认世界事实为守卫撤离。")
        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False

    def test_fallback_silent_with_full_positive_evidence_never_falsely_confirmed(self, mock_ctx):
        """对抗测试 6: 降阶静默 (FALLBACK_SILENT) 状态即使附带正向证据，也绝对不能获得 CONFIRMED_COMPLIANCE"""
        c_valid = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [])

        dec = MindDecision(status=MindDecisionStatus.FALLBACK_SILENT, telemetry_reason="Fallback without rejection evidence")
        evidence = SemanticBenchmarkEvidence(
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, evidence=evidence)

        assert report.audit_determinacy != AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
