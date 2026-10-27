# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L30951-L31009 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #129  lines=58  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L30951.py
# edits: none. Header comment is the only addition.
# ======================
    def test_scenario_a_contained_illegal_candidate(self, mock_ctx):
        """场景 A: illegal candidate 被 validator 拦截 -> containment=True, integrity=True"""
        c_real = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_real], [], [])

        # 模拟被 Boundary Validator 拦截并降阶为 FALLBACK_SILENT 的决策包
        dec = MindDecision(status=MindDecisionStatus.FALLBACK_SILENT, candidate_id="AFF_INVENTED", telemetry_reason="Fallback")
        prov = DecisionProvenanceEnvelope(
            agent_id="agent_325",
            tick=1,
            rejection_reason="ILLEGAL_ACTION_HALLUCINATION: candidate_id not in available candidates",
            source_candidates_snapshot_hash="hash_mock"
        )
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec, provenance=prov)
        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is True
        assert report.architectural_integrity is True

    def test_scenario_b_bypassed_illegal_candidate(self, mock_ctx):
        """场景 B: illegal candidate 真正 bypass boundary -> containment=False, integrity=False"""
        c_real = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_real], [], [])

        # 模拟未经拦截、直接输出非法 candidate_id 的违规决策
        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_GHOST_BYPASS", telemetry_reason="Direct bypass attempt")
        report = CognitiveSemanticAuditor.audit_deliberation(proj, dec)
        assert report.category == CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION
        assert report.audit_determinacy == AuditDeterminacy.CONFIRMED_VIOLATION
        assert report.semantic_compliance is False
        assert report.architectural_containment is False
        assert report.architectural_integrity is False

    def test_scenario_c_legal_candidate_normal_pass(self, mock_ctx):
        """场景 C: legal candidate 正常通过 -> compliance=True, containment=True, integrity=True"""
        c_real = CandidateAffordance(channel_id="AFF_REAL", action_type="A", actuator=ActuatorType.TORSO, target_surface=SurfaceType.UNOBSTRUCTED_SPACE, action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE)
        state = InternalCognitiveState()
        rep = SubjectiveRepresentation.from_context(mock_ctx)
        proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_real], [], [])

        dec = MindDecision(status=MindDecisionStatus.SELECTED, candidate_id="AFF_REAL", telemetry_reason="Legal action")
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
        assert report.architectural_containment is True
        assert report.architectural_integrity is True
