# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L12285-L12293 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #47  lines=8  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L12285.py
# edits: none. Header comment is the only addition.
# ======================
  core_belief = ctx.self_narrative.constants.get("core_belief", "")
  if "寸步不让" in core_belief or "体面" in core_belief or "绝不示弱" in core_belief:
      if aff.action_attribute == ActionAttribute.INTERPERSONAL_DE_ESCALATION:
          valence = NarrativeValence.VIOLATING
      elif aff.action_attribute == ActionAttribute.INTERPERSONAL_ASSERTION:
          valence = NarrativeValence.SUPPORTED
  elif "好汉不吃眼前亏" in core_belief or "生存第一" in core_belief or "自保" in core_belief:
      ...
  