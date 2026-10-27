# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L12265-L12277 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #46  lines=12  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L12265.py
# edits: none. Header comment is the only addition.
# ======================
  if SituationalActivation.SPATIAL_BLOCKAGE in ctx.activations:
      ...
      return mechanical_affs[0]
  if SituationalActivation.INTERPERSONAL_FRICTION in ctx.activations:
      ...
      return supported[0]
  if SituationalActivation.SOMATIC_FATIGUE in ctx.activations:
      ...
      return rest_affs[0]
  # 平稳常态
  if locomotion_affs:
      return locomotion_affs[0]
  