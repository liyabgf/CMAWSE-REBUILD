# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L12360-L12363 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #50  lines=3  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L12360.py
# edits: none. Header comment is the only addition.
# ======================
     supported = [a for a in interpersonal_affs if a.narrative_status == NarrativeValence.SUPPORTED]
     if supported:
         return supported[0]
     