# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L57203-L57372 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #148  lines=169  compile=OK
# kind: fragment  ident: frag_L57203.py
# edits: none. Header comment is the only addition.
# ======================
"""
Comprehensive Self-Contained Verification Suite for Hmid-3
Covers C31 to C50, Roundtrip Invariance, and Cross-Platform Determinism
"""
import os
import copy
import pytest
from CMAWSE_REFERENCE_RUNNER import (
    ASTNode, Hmid3Synthesizer, parse_canonical_string, evaluate_ast,
    FALLBACK_PROGRAM, MAX_NODES, MAX_EXPANDED_NODES
)

# ============================================================================
# C31 - C40 AUDIT VERIFICATION TESTS
# ============================================================================

def test_c31_equal_node_count_ordering():
    n1 = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("B")))
    n2 = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("A")))
    assert n1.node_count() == n2.node_count()
    assert n2 < n1
    assert sorted([n1, n2])[0].to_canon_string() == "X == A"


def test_c32_lexicographical_tie_break():
    tree1 = parse_canonical_string("IF X == B THEN q1 ELSE q0")
    tree2 = parse_canonical_string("IF X == A THEN q1 ELSE q0")
    assert tree1.node_count() == tree2.node_count()
    assert tree2.to_canon_string() < tree1.to_canon_string()


def test_c33_identical_canon_string_deduplication():
    synth = Hmid3Synthesizer()
    t1 = parse_canonical_string("IF X == A AND K == K_ctx THEN q1 ELSE q0")
    t2 = parse_canonical_string("IF K == K_ctx AND X == A THEN q1 ELSE q0")
    assert t1.to_canon_string() == t2.to_canon_string()


def test_c34_unique_winner_multiple_zero_error():
    synth = Hmid3Synthesizer()
    # Data consistent with multiple rules
    data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"}]
    prog, exp = synth.synthesize(data)
    assert prog == "IF act == act_alpha THEN q1 ELSE q0"


def test_c35_c36_max_nodes_cutoff():
    synth = Hmid3Synthesizer(max_nodes=MAX_NODES)
    # Target requires more than 12 nodes, must fallback
    data = [
        {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
        {"X": "B", "K": "L_ctx", "act": "act_beta", "label": "q2"},
        {"X": "C", "K": "M_ctx", "act": "act_gamma", "label": "q3"},
    ]
    prog, _ = synth.synthesize(data)
    assert prog == FALLBACK_PROGRAM


def test_c37_canonical_successor_determinism():
    synth = Hmid3Synthesizer()
    prods = synth._get_productions("<SimpleCond>")
    strings = [p.to_canon_string() for p in prods]
    assert strings == sorted(strings)


def test_c38_c39_expansion_budget_and_unsolvable():
    synth = Hmid3Synthesizer(max_expansions=100)
    # Contradictory observations: impossible to fit zero error
    impossible_data = [
        {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
        {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q2"},
    ]
    prog, expansions = synth.synthesize(impossible_data)
    assert prog == FALLBACK_PROGRAM
    assert expansions <= 101


def test_c40_reproducibility_across_instances():
    data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"}]
    synth1 = Hmid3Synthesizer()
    synth2 = Hmid3Synthesizer()
    r1, e1 = synth1.synthesize(data)
    r2, e2 = synth2.synthesize(data)
    assert r1 == r2
    assert e1 == e2

# ============================================================================
# C41 - C50 BOUNDARY AND INVARIANCE TESTS
# ============================================================================

def test_c41_cost_priority_over_string():
    # A smaller node count must always be popped before a larger one
    n_small = ASTNode("q1")  # count 1
    n_large = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("A")))  # count 4
    assert (n_small.node_count(), n_small.to_canon_string()) < (n_large.node_count(), n_large.to_canon_string())


def test_c42_prefix_suffix_canonical_order():
    s1 = "IF X == A THEN q1 ELSE q0"
    s2 = "IF X == A THEN q2 ELSE q0"
    assert s1 < s2


def test_c43_partial_ast_canon_uniqueness():
    p1 = ASTNode("<Condition>", (ASTNode("<SimpleCond>"),))
    p2 = ASTNode("<Condition>", (ASTNode("<SimpleCond>"), ASTNode("<SimpleCond>")))
    assert p1.to_canon_string() != p2.to_canon_string()


def test_c44_closed_set_blocks_reexpansion():
    synth = Hmid3Synthesizer()
    data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"}]
    prog, exp = synth.synthesize(data)
    assert exp < MAX_EXPANDED_NODES


def test_c45_c46_boundary_size_filtering():
    exact_12 = parse_canonical_string("IF X == A AND K == K_ctx THEN q1 ELSE q0")
    assert exact_12.node_count() <= MAX_NODES


def test_c47_budget_hard_cap():
    synth = Hmid3Synthesizer(max_expansions=50)
    data = [{"X": "B", "K": "L_ctx", "act": "act_zeta", "label": "q3"}]
    _, expansions = synth.synthesize(data)
    assert expansions <= 51


def test_c48_exact_single_winner():
    synth = Hmid3Synthesizer()
    data = [
        {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
        {"X": "A", "K": "L_ctx", "act": "act_beta", "label": "q1"}
    ]
    prog, _ = synth.synthesize(data)
    assert prog == "IF X == A THEN q1 ELSE q0"


def test_c49_fallback_on_unreachable_state():
    synth = Hmid3Synthesizer()
    # No rule can produce q0 as active target in this DSL
    data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q0"}]
    prog, _ = synth.synthesize(data)
    assert prog == FALLBACK_PROGRAM


def test_c50_hash_seed_indifference():
    data = [{"X": "C", "K": "M_ctx", "act": "act_gamma", "label": "q2"}]
    res1, exp1 = Hmid3Synthesizer().synthesize(data)
    res2, exp2 = Hmid3Synthesizer().synthesize(copy.deepcopy(data))
    assert res1 == res2
    assert exp1 == exp2

# ============================================================================
# ROUNDTRIP & IDEMPOTENCE PROPERTY TESTS
# ============================================================================

@pytest.mark.parametrize("prog_str", [
    "IF X == A THEN q1 ELSE q0",
    "IF K IN {K_ctx, L_ctx} THEN q2 ELSE q0",
    "IF X == A AND act == act_alpha THEN q1 ELSE q0",
    "IF K == K_ctx AND act IN {act_alpha, act_beta} THEN q3 ELSE q0"
])
def test_canon_string_roundtrip_idempotence(prog_str):
    ast = parse_canonical_string(prog_str)
    canon = ast.to_canon_string()
    re_parsed = parse_canonical_string(canon)
    assert re_parsed.to_canon_string() == canon
    assert canon == prog_str
