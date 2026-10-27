# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L15023-L15029 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #74  lines=6  compile=OK
# kind: fragment  ident: frag_L15023.py
# edits: none. Header comment is the only addition.
# ======================
if prior_intents:
    for p_intent in prior_intents:
        if not p_intent.is_fulfilled and p_intent.persistence_ticks > 1:
            if rep.situation_type != QualitativeSituation.HOMEOSTATIC_CRISIS:
                decayed = p_intent.model_copy(update={"persistence_ticks": p_intent.persistence_ticks - 1})
                generated_intents.append(decayed)
