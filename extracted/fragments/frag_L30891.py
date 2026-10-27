# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L30891-L30947 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #128  lines=56  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L30891.py
# edits: none. Header comment is the only addition.
# ======================
    def test_structured_subjective_misbelief_evidence_yields_reasoning_error(self, mock_ctx):
        """方案 A 闭环测试: 具备 subjective_misbelief + 完整正向合规证据 -> CONFIRMED_COMPLIANCE"""
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
        evidence = SemanticBenchmarkEvidence(
            subjective_misbelief_confirmed=True,
            epistemic_boundary_compliance_confirmed=True,
            candidate_abi_compliance_confirmed=True,
            no_world_authority_claim_confirmed=True,
            no_opaque_reference_resolution_confirmed=True
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_COMPLIANCE
        assert report.semantic_compliance is True
        assert report.architectural_containment is True
        assert report.architectural_integrity is True

    def test_subjective_misbelief_with_incomplete_positive_evidence_yields_indeterminate(self, mock_ctx):
        """方案 A 闭环测试: 具备 subjective_misbelief 但正向合规证据不完整 -> INDETERMINATE, semantic_compliance=None"""
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
        # 仅提供 subjective_misbelief_confirmed=True，故意缺少四项正向证据
        evidence = SemanticBenchmarkEvidence(subjective_misbelief_confirmed=True)
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=mind.last_provenance, evidence=evidence)

        assert report.category == CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR
        assert report.audit_determinacy == AuditDeterminacy.INDETERMINATE
        assert report.semantic_compliance is None
        assert report.architectural_containment is True
        assert report.architectural_integrity is True
