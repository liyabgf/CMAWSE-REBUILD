# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3176-L3178 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #17  lines=2  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L03176.py
# edits: none. Header comment is the only addition.
# ======================
  self._ledger.append(verified_event)  # 先持久化
  updated_state = StateCommitter.apply_transaction(...)  # 后原子提交
  