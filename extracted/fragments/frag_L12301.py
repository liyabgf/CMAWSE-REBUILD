# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L12301-L12305 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #48  lines=4  compile=FAIL:2:unexpected indent
# kind: fragment  ident: frag_L12301.py
# edits: none. Header comment is the only addition.
# ======================
  # 情境 D: 平稳常态（NORMATIVE EQUILIBRIUM）
  locomotion_affs = [a for a in feasible_pool if a.action_attribute == ActionAttribute.LOCOMOTION]
  if locomotion_affs:
      return locomotion_affs[0]  # 只要腿没断，平稳状态下必须行走！
  