# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L62892-L62899 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #165  lines=7  compile=OK
# kind: fragment  ident: frag_L62892.py
# edits: none. Header comment is the only addition.
# ======================
def ground_truth_transition(condition: str, q: str, obj: str, ctx: str, act: str) -> str:
    ...
    if obj == door_obj and act == lift_act:
        return target_q
    elif obj == cab_obj and act == turn_act:
        return second_q
    return idle_q
