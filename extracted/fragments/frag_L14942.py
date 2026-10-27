# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L14942-L14949 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #70  lines=7  compile=OK
# kind: fragment  ident: frag_L14942.py
# edits: none. Header comment is the only addition.
# ======================
resonance_refs = [m.event_ref for m in ctx.recalled_memories if m.emotional_scar > 20.0]

if ctx.horizon.visible_actors:
    if resonance_refs:
        climate = ClimateMode.HOSTILE_PRESSURE
    else:
        climate = ClimateMode.UNCERTAIN_SCRUTINY
