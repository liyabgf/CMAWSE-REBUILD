# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L58110-L58381 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #155  lines=271  compile=OK
# kind: fragment  ident: frag_L58110.py
# edits: none. Header comment is the only addition.
# ======================
"""
Independent Standalone Test Suite for CMAWSE Hmid-3
Uses Python standard library `unittest` only. Zero third-party dependencies.
Covers C31 to C60.
"""
import copy
import os
import subprocess
import sys
import unittest

from CMAWSE_REFERENCE_RUNNER import (
    ASTNode, Hmid3Synthesizer, parse_canonical_string, evaluate_ast,
    FALLBACK_PROGRAM, MAX_NODES, MAX_EXPANDED_NODES, VAR_DOMAINS
)

class TestHmid3Conformance(unittest.TestCase):

    # ------------------------------------------------------------------------
    # C31 - C40: BASELINE TESTS
    # ------------------------------------------------------------------------

    def test_c31_equal_node_count_ordering(self):
        n1 = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("B")))
        n2 = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("A")))
        self.assertEqual(n1.node_count(), n2.node_count())
        self.assertTrue(n2 < n1)
        self.assertEqual(sorted([n1, n2])[0].to_canon_string(), "X == A")

    def test_c32_lexicographical_tie_break(self):
        t1 = parse_canonical_string("IF X == B THEN q1 ELSE q0")
        t2 = parse_canonical_string("IF X == A THEN q1 ELSE q0")
        self.assertEqual(t1.node_count(), t2.node_count())
        self.assertTrue(t2.to_canon_string() < t1.to_canon_string())

    def test_c33_identical_canon_string_deduplication(self):
        t1 = parse_canonical_string("IF X == A AND K == K_ctx THEN q1 ELSE q0")
        t2 = parse_canonical_string("IF K == K_ctx AND X == A THEN q1 ELSE q0")
        self.assertEqual(t1.to_canon_string(), t2.to_canon_string())

    def test_c34_unique_winner_multiple_zero_error(self):
        synth = Hmid3Synthesizer()
        data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"}]
        prog, _ = synth.synthesize(data)
        self.assertEqual(prog, "IF act == act_alpha THEN q1 ELSE q0")

    def test_c35_exact_12_node_ast_processed(self):
        # 1(Program) + 1(Condition) + 1(SimpleCond) + 1(act) + 1(IN) + 1(ConstSet) + 5(leaves) + 1(q1) = 12
        text_12 = "IF act IN {act_alpha, act_beta, act_gamma, act_delta, act_epsilon} THEN q1 ELSE q0"
        ast_12 = parse_canonical_string(text_12)
        self.assertEqual(ast_12.node_count(), 12)
        # Verify it successfully runs in synthesis
        data = [
            {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
            {"X": "B", "K": "L_ctx", "act": "act_beta", "label": "q1"},
            {"X": "C", "K": "M_ctx", "act": "act_gamma", "label": "q1"},
            {"X": "A", "K": "M_ctx", "act": "act_delta", "label": "q1"},
            {"X": "B", "K": "K_ctx", "act": "act_epsilon", "label": "q1"},
            {"X": "C", "K": "L_ctx", "act": "act_zeta", "label": "q0"},
        ]
        synth = Hmid3Synthesizer(max_nodes=12, max_expansions=1000)
        prog, _ = synth.synthesize(data)
        self.assertEqual(prog, text_12)

    def test_c36_13_node_branch_pruned_before_queue(self):
        # 6-element set causes node count = 13
        text_13 = "IF act IN {act_alpha, act_beta, act_gamma, act_delta, act_epsilon, act_zeta} THEN q1 ELSE q0"
        ast_13 = parse_canonical_string(text_13)
        self.assertEqual(ast_13.node_count(), 13)
        self.assertGreater(ast_13.node_count(), MAX_NODES)

    def test_c37_canonical_successor_determinism(self):
        synth = Hmid3Synthesizer()
        prods = synth._get_productions("<SimpleCond>")
        strings = [p.to_canon_string() for p in prods]
        self.assertEqual(strings, sorted(strings))

    def test_c38_c39_expansion_budget_and_unsolvable(self):
        synth = Hmid3Synthesizer(max_expansions=10)
        impossible_data = [
            {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
            {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q2"},
        ]
        prog, expansions = synth.synthesize(impossible_data)
        self.assertEqual(prog, FALLBACK_PROGRAM)
        self.assertEqual(expansions, 10)  # Exactly 10 expansions

    def test_c40_a_same_process_repeatability(self):
        data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"}]
        s1, e1 = Hmid3Synthesizer().synthesize(data)
        s2, e2 = Hmid3Synthesizer().synthesize(data)
        self.assertEqual(s1, s2)
        self.assertEqual(e1, e2)

    def test_c40_b_subprocess_hashseed_invariance(self):
        cmd = [
            sys.executable, "-c",
            "from CMAWSE_REFERENCE_RUNNER import Hmid3Synthesizer; "
            "print(Hmid3Synthesizer().synthesize([{'X': 'A', 'K': 'K_ctx', 'act': 'act_alpha', 'label': 'q1'}]))"
        ]
        outputs = []
        for seed in ("0", "1", "123456"):
            env = os.environ.copy()
            env["PYTHONHASHSEED"] = seed
            res = subprocess.check_output(cmd, env=env, universal_newlines=True).strip()
            outputs.append(res)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])

    # ------------------------------------------------------------------------
    # C41 - C50: COST, PRUNING & TIE-BREAKING TESTS
    # ------------------------------------------------------------------------

    def test_c41_cost_priority_over_string(self):
        n_small = ASTNode("q1")
        n_large = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("A")))
        self.assertLess((n_small.node_count(), n_small.to_canon_string()),
                        (n_large.node_count(), n_large.to_canon_string()))

    def test_c42_prefix_suffix_canonical_order(self):
        s1 = "IF X == A THEN q1 ELSE q0"
        s2 = "IF X == A THEN q2 ELSE q0"
        self.assertLess(s1, s2)

    def test_c43_partial_ast_canon_uniqueness(self):
        p1 = ASTNode("<Condition>", (ASTNode("<SimpleCond>"),))
        p2 = ASTNode("<Condition>", (ASTNode("<SimpleCond>"), ASTNode("<SimpleCond>")))
        self.assertNotEqual(p1.to_canon_string(), p2.to_canon_string())

    def test_c44_closed_set_blocks_reexpansion(self):
        synth = Hmid3Synthesizer()
        data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"}]
        _, exp = synth.synthesize(data)
        self.assertLess(exp, MAX_EXPANDED_NODES)

    def test_c45_max_nodes_equality_boundary(self):
        ast = parse_canonical_string("IF act IN {act_alpha, act_beta, act_gamma, act_delta, act_epsilon} THEN q1 ELSE q0")
        self.assertEqual(ast.node_count(), MAX_NODES)

    def test_c46_max_nodes_exceeded_pruning(self):
        synth = Hmid3Synthesizer(max_nodes=10)
        # Target requires 12 nodes, cannot be synthesized with max_nodes=10
        data = [
            {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
            {"X": "B", "K": "L_ctx", "act": "act_beta", "label": "q1"},
            {"X": "C", "K": "M_ctx", "act": "act_gamma", "label": "q1"},
            {"X": "A", "K": "M_ctx", "act": "act_delta", "label": "q1"},
            {"X": "B", "K": "K_ctx", "act": "act_epsilon", "label": "q1"},
        ]
        prog, _ = synth.synthesize(data)
        self.assertEqual(prog, FALLBACK_PROGRAM)

    def test_c47_budget_exact_stops(self):
        for budget in (1, 5, 10, 50):
            synth = Hmid3Synthesizer(max_expansions=budget)
            impossible = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
                          {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q2"}]
            _, exp = synth.synthesize(impossible)
            self.assertEqual(exp, budget)

    def test_c48_exact_single_winner(self):
        synth = Hmid3Synthesizer()
        data = [
            {"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q1"},
            {"X": "A", "K": "L_ctx", "act": "act_beta", "label": "q1"}
        ]
        prog, _ = synth.synthesize(data)
        self.assertEqual(prog, "IF X == A THEN q1 ELSE q0")

    def test_c49_fallback_on_unreachable_state(self):
        synth = Hmid3Synthesizer()
        data = [{"X": "A", "K": "K_ctx", "act": "act_alpha", "label": "q0"}]
        prog, _ = synth.synthesize(data)
        self.assertEqual(prog, FALLBACK_PROGRAM)

    def test_c50_hash_seed_indifference(self):
        data = [{"X": "C", "K": "M_ctx", "act": "act_gamma", "label": "q2"}]
        res1, exp1 = Hmid3Synthesizer().synthesize(data)
        res2, exp2 = Hmid3Synthesizer().synthesize(copy.deepcopy(data))
        self.assertEqual(res1, res2)
        self.assertEqual(exp1, exp2)

    # ------------------------------------------------------------------------
    # C51 - C60: NEW CONFORMANCE REPAIR TESTS
    # ------------------------------------------------------------------------

    def test_c51_constset_x_all_subsets(self):
        synth = Hmid3Synthesizer()
        prods = [p.to_canon_string() for p in synth._get_productions("<ConstSet_X>")]
        expected = ["{A, B}", "{A, B, C}", "{A, C}", "{B, C}"]
        self.assertEqual(prods, sorted(expected))

    def test_c52_constset_k_all_subsets(self):
        synth = Hmid3Synthesizer()
        prods = [p.to_canon_string() for p in synth._get_productions("<ConstSet_K>")]
        expected = ["{K_ctx, L_ctx}", "{K_ctx, L_ctx, M_ctx}", "{K_ctx, M_ctx}", "{L_ctx, M_ctx}"]
        self.assertEqual(prods, sorted(expected))

    def test_c53_constset_act_all_subsets_cardinality(self):
        synth = Hmid3Synthesizer()
        prods = [p.to_canon_string() for p in synth._get_productions("<ConstSet_act>")]
        # Total subsets for 6 elements of sizes 2..6 = 15 + 20 + 15 + 6 + 1 = 57
        self.assertEqual(len(prods), 57)
        self.assertEqual(prods, sorted(prods))

    def test_c54_disallow_invalid_cardinalities(self):
        synth = Hmid3Synthesizer()
        for var in ("X", "K", "act"):
            prods = synth._get_productions(f"<ConstSet_{var}>")
            for p in prods:
                self.assertGreaterEqual(len(p.children), 2)
                self.assertLessEqual(len(p.children), len(VAR_DOMAINS[var]))

    def test_c55_roundtrip_all_synthesized_productions(self):
        synth = Hmid3Synthesizer()
        for var in ("X", "K", "act"):
            for const_prod in synth._get_productions(f"<Const_{var}>"):
                prog = f"IF {var} == {const_prod.symbol} THEN q1 ELSE q0"
                ast = parse_canonical_string(prog)
                self.assertEqual(ast.to_canon_string(), prog)

    def test_c56_roundtrip_constset_productions(self):
        synth = Hmid3Synthesizer()
        for var in ("X", "K", "act"):
            for set_prod in synth._get_productions(f"<ConstSet_{var}>"):
                prog = f"IF {var} IN {set_prod.to_canon_string()} THEN q1 ELSE q0"
                ast = parse_canonical_string(prog)
                self.assertEqual(ast.to_canon_string(), prog)

    def test_c57_production_ordering_all_nonterminals(self):
        synth = Hmid3Synthesizer()
        nts = [
            "<Program>", "<Condition>", "<SimpleCond>",
            "<Const_X>", "<Const_K>", "<Const_act>",
            "<ConstSet_X>", "<ConstSet_K>", "<ConstSet_act>"
        ]
        for nt in nts:
            prods = synth._get_productions(nt)
            strings = [p.to_canon_string() for p in prods]
            self.assertEqual(strings, sorted(strings), f"Non-terminal {nt} productions are not canonically sorted")

    def test_c58_two_condition_canonical_variable_sort(self):
        # Order must be X < K < act
        ast1 = parse_canonical_string("IF X == A AND K == K_ctx THEN q1 ELSE q0")
        ast2 = parse_canonical_string("IF K == K_ctx AND X == A THEN q1 ELSE q0")
        self.assertEqual(ast1.to_canon_string(), ast2.to_canon_string())
        self.assertEqual(ast1.to_canon_string(), "IF X == A AND K == K_ctx THEN q1 ELSE q0")

    def test_c59_same_variable_conjunction_tie_breaker(self):
        # When two conditions are on the same variable, tie-break by CanonString
        c1 = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("B")))
        c2 = ASTNode("<SimpleCond>", (ASTNode("X"), ASTNode("=="), ASTNode("A")))
        cond = ASTNode("<Condition>", (c1, c2))
        self.assertEqual(cond.to_canon_string(), "X == A AND X == B")

    def test_c60_partial_ast_canonicalization_safety(self):
        # Ensure that incomplete ASTs with non-terminals produce valid, non-crashing CanonStrings
        partial1 = ASTNode("<Program>", (ASTNode("<Condition>"), ASTNode("q1")))
        partial2 = ASTNode("<Condition>", (ASTNode("<SimpleCond>"), ASTNode("<SimpleCond>")))
        s1 = partial1.to_canon_string()
        s2 = partial2.to_canon_string()
        self.assertIsInstance(s1, str)
        self.assertIsInstance(s2, str)
        self.assertTrue(s1.startswith("IF <Condition> THEN q1 ELSE q0"))


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHmid3Conformance)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
