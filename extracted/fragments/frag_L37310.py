# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L37310-L37320 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #137  lines=10  compile=FAIL:10:positional argument follows keyword argument
# kind: fragment  ident: frag_L37310.py
# edits: none. Header comment is the only addition.
# ======================
# 摘录自 benchmarks/phase4_runner.py 的实际审议逻辑
if "焊死" in str(context.projected_memories) or "焊死" in context.self_narrative.core_belief:
    return MindDecision(status=MindDecisionStatus.COGNITIVE_SILENT, silent_mode="SUPPRESSED_INHIBITION")

if context.somatic.fatigue >= 80:
    # 强制选择低能耗或静默
    return MindDecision(status=MindDecisionStatus.COGNITIVE_SILENT, silent_mode="INHIBITED_STASIS")

if any("殴打" in m.subjective_rationalization for m in context.projected_memories):
    return MindDecision(status=MindDecisionStatus.COGNITIVE_SILENT, ...)
