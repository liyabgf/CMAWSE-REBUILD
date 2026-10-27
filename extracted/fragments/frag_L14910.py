# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L14910-L14921 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #69  lines=11  compile=OK
# kind: fragment  ident: frag_L14910.py
# edits: none. Header comment is the only addition.
# ======================
# 1. 痛苦直接生成止痛意向 (line 72)
if rep.somatic_appraisal.dominant_strain in (StrainCategory.ACUTE_PAIN, StrainCategory.MECHANICAL_IMMOBILITY):
    generated_intents.append(SubjectiveIntent(..., intended_transition=QualitativeTransition.MITIGATE_PAIN))

# 2. 空间受限直接生成拓扑疏通意向 (line 86)
if rep.spatial_appraisal.confinement_mode in (ConfinementLevel.STRICT_DEAD_END, ConfinementLevel.PARTIAL_OBSTRUCTION):
    generated_intents.append(SubjectiveIntent(..., intended_transition=QualitativeTransition.EXPAND_SPACE))

# 3. 对抗人格直接生成防线确立意向 (line 100)
if rep.relational_appraisal.interpersonal_climate in (...) and posture == "DEFIANT":
    generated_intents.append(SubjectiveIntent(..., intended_transition=QualitativeTransition.REESTABLISH_BOUNDARY))
