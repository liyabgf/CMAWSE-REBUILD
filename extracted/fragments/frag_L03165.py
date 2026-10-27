# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3165-L3169 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #16  lines=4  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L03165.py
# edits: none. Header comment is the only addition.
# ======================
  involved_actors = list(self._agents.keys())
  self._memory.settle_event(verified_event, involved_actors)
  for aid in involved_actors:
      self._rumor.inject_witness_event(aid, verified_event)
  