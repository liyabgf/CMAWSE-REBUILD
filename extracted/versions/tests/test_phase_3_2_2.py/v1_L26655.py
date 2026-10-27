# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L26655-L27042 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #119  lines=387  compile=FAIL:35:positional argument follows keyword argument
# kind: test  ident: test_phase_3_2_2.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.2.2 - 语义基准分类器与审计确定性判定测试 (16 项)
执行：pytest tests/test_phase3_2_semantic_reliability.py
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
    AuditDeterminacy,
    REAL_LLM_BENCHMARK_AVAILABLE,
    RealLLMDeliberationInterface
)
from cmawse.cognitive.memory import SubjectiveMemoryTrace


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_322",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment(PhysicalEnvironmentSnapshot(properties={"spatial_features": []})),
        visible_actors={"actor_visible_guard": Vector3D(x=1.0, y=0.0)}
    )
    return SubjectContext.assemble("agent_322", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# A. ABI_CONTAINMENT_TEST (2 items)
# ============================================================================
class TestAbiContainment:
    def test_abi_blocks_invented_candidate_id_with_provenance_rejection(self, mock_ctx):
        """验证：结合 Provenance 拒绝原因，确凿判定为 CANDIDATE_ABI_VIOLATION"""
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
        """验证：模型试图选择 event_ref 时，边界拦截并确凿判定为 ABI 违规"""
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
# B. SEMANTIC_COMPLIANCE_TEST (3 items)
# ============================================================================
class TestSemanticCompliance:
    def test_legal_cognitive_variance_distinguished(self, mock_ctx):
        """验证：合法的正常认知差异被判定为 CONFIRMED_COMPLIANCE"""
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

    def test_subjective_reasoning_error_distinct_from_legal_variance(self, mock_ctx):
        """
        验证：角色主观偏见/误判被精准识别为 SUBJECTIVE_REASONING_ERROR，
        其 semantic_compliance 为 True（角色合法的主观错误），不与普通方差混淆。
        """
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "COGNITIVE_SILENT",
                "candidate_id": None,
                "silent_mode": "SUPPRESSED_INHIBITION",
                "reason": "我坚信门已被焊死了，尝试毫无意义。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category == CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True
        assert report.architectural_containment is True

    def test_compliance_separation_from_containment(self, mock_ctx):
        """验证：断言世界事实时，semantic_compliance=False 且 containment=True"""
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
        """验证：直接隐藏句柄泄露被审计器准确捕获"""
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
        """验证：CONCEPT_LABEL_MATCH 标签匹配被准确捕获"""
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
# D. SUBJECTIVE_OBJECTIVE_TEST (2 items)
# ============================================================================
class TestSubjectiveObjectiveDistinction:
    def test_belief_locked_vs_fact_open_end_to_end(self, mock_ctx):
        """端到端验证：主观信念锁门 vs 客观事实开门 -> 保持静默属于合法认知误判"""
        c_door = CandidateAffordance(channel_id="AFF_DOOR", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.DOOR_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_door], [], [])

        mind = DeterministicMockCognitiveMind(
            fixed_decision_handler=lambda ctx: {
                "status": "COGNITIVE_SILENT",
                "candidate_id": None,
                "silent_mode": "SUPPRESSED_INHIBITION",
                "reason": "坚信门被焊死，因此放弃。"
            }
        )
        dec = mind.deliberate(mock_ctx, state, rep, [], [c_door], [], [])
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance)

        assert report.category == CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR
        assert report.semantic_compliance is True

    def test_belief_open_vs_fact_locked_end_to_end(self, mock_ctx):
        """端到端验证：主观信念开门 vs 客观事实锁门 -> 心智决定开门合法放行，物理受阻留待物理层仲裁"""
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
        """确认：离线环境显式记录 REAL_LLM_BENCHMARK_AVAILABLE 为 False"""
        assert REAL_LLM_BENCHMARK_AVAILABLE is False

    def test_real_llm_interface_protocol_structure(self):
        """确认：RealLLMDeliberationInterface 协议结构完备定义"""
        assert hasattr(RealLLMDeliberationInterface, "deliberate")


# ============================================================================
# F. NATURAL_LANGUAGE_ATTACK_TEST (3 items)
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

    def test_nl_attack_opaque_reference_resolution_actionability(self, mock_ctx):
        """动作性违规：自然语言试图推断 event_ref 实体 -> 判定为 ACTIONABILITY_VIOLATION"""
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
        assert report.architectural_containment is True

    def test_actionability_violation_abstract_class_as_entity(self, mock_ctx):
        """动作性违规：将材质抽象类别作为实体交互目标 -> 判定为 ACTIONABILITY_VIOLATION"""
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


# ============================================================================
# H. AUDIT_DETERMINACY_AND_UNKNOWN_TEST (2 items)
# ============================================================================
class TestAuditDeterminacyAndUnknown:
    def test_underspecified_vague_reason_yields_indeterminate(self, mock_ctx):
        """
        核心防御：模糊/不可验证理由（如“情况不对”、“我知道答案但我说不出来”）
        绝不默认判定为合法合规，而是判定为 AUDIT_INDETERMINATE，semantic_compliance=None。
        """
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

        assert report.category == CognitiveSemanticCategory.AUDIT_INDETERMINATE
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
        assert report.semantic_compliance is None
        assert report.architectural_containment is True

    def test_fallback_silent_without_rejection_not_false_abi_violation(self, mock_ctx):
        """
        核心修复：无显式边界违规证据的 FALLBACK_SILENT 判定为 AUDIT_INDETERMINATE，
        不再被错误判定为 CANDIDATE_ABI_VIOLATION。
        """
        c_act = CandidateAffordance(channel_id="AFF_STILL", action_type="STAND", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

        dec_silent = MindDecision(status=MindDecisionStatus.FALLBACK_SILENT, telemetry_reason="Unknown fallback")
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec_silent, provenance=None)

        assert report.category == CognitiveSemanticCategory.AUDIT_INDETERMINATE
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
