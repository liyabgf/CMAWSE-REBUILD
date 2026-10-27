# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L14896-L14900 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #68  lines=4  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L14896.py
# edits: none. Header comment is the only addition.
# ======================
  if (ctx.recent_failure is not None
          and aff.target_id == ctx.recent_failure.target_id
          and aff.action_type == ctx.recent_failure.action_type):
      continue  # 直接从可行池中物理剔除！
  