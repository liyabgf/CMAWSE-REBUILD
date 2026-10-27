# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L61509-L61703 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #162  lines=194  compile=OK
# kind: harness  ident: harness_162.py  harness version 5/7
# edits: none. Header comment is the only addition.
# ======================
"""
CMAWSE Phase II Conformance Test Suite (Rev2)
Features:
1. OracleAgent (Passes valid endpoints)
2. RandomDummyAgent (Fails baseline thresholds)
3. AdversarialAgent (Attempts JSON corruption, metadata exploitation, and state tampering)
4. Full Wilcoxon Signed-Rank with Pratt Zero-Handling Verification
5. Subprocess CLI Replay Verification
"""
import copy
import json
import os
import subprocess
import sys
import unittest

from CMAWSE_v1_0_3_EXPERIMENT_HARNESS import (
    CMAWSEExperimentHarness, DiscretePhysicalWorld,
    wilcoxon_signed_rank_pratt, evaluate_d6_bootstrap,
    D6_BIJECTION_MAP
)

# ============================================================================
# SYNTHETIC AGENT FIXTURES
# ============================================================================

class OracleAgent:
    """Perfect synthetic agent adhering to canonical rules."""
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        phase = payload.get("phase")
        if phase == "INTERACTIVE":
            obs = payload["observation"]
            obj = obs["focal_object"]
            # Oracle optimal probe selection
            if obj in ("door", "A"):
                act = "lift" if "lift" in obs["available_actions"] else "act_beta"
            elif obj in ("cabinet", "B"):
                act = "turn" if "turn" in obs["available_actions"] else "act_gamma"
            else:
                act = obs["available_actions"][0]
            return {"action": act}
        elif phase == "BATCH_EVALUATION":
            preds = {}
            for q in payload["d1_queries"]:
                tau = str(q["tau"])
                x = q["X"]
                act = q["act"]
                if x in ("door", "A") and act in ("lift", "act_beta"):
                    preds[tau] = "st_open" if "lift" in act else "q1"
                elif x in ("cabinet", "B") and act in ("turn", "act_gamma"):
                    preds[tau] = "st_locked" if "turn" in act else "q2"
                else:
                    preds[tau] = "st_idle" if "door" in x else "q0"

            d2_mat = {
                "M1": {a: ("q1" if a in ("act_alpha", "act_beta", "push", "lift") else "q0") for a in ["act_alpha", "act_beta", "act_gamma", "act_delta", "act_epsilon", "act_zeta", "push", "pull", "turn", "lift", "wait", "reset"]},
                "M2": {a: ("q1" if a in ("act_alpha", "act_gamma", "push", "turn") else "q0") for a in ["act_alpha", "act_beta", "act_gamma", "act_delta", "act_epsilon", "act_zeta", "push", "pull", "turn", "lift", "wait", "reset"]}
            }
            d4_preds = {q["tau"]: ("q1" if q["action"] in ("lift", "act_beta") else "q0") for q in payload["d4_queries"]}
            return {
                "d1_predictions": preds,
                "d2_matrix": d2_mat,
                "d4_predictions": d4_preds,
                "d5_prediction": "q0"
            }
        return {}

class RandomDummyAgent:
    """Random noise agent."""
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        phase = payload.get("phase")
        if phase == "INTERACTIVE":
            return {"action": payload["observation"]["available_actions"][0]}
        return {
            "d1_predictions": {str(q["tau"]): "q0" for q in payload.get("d1_queries", [])},
            "d2_matrix": {},
            "d4_predictions": {},
            "d5_prediction": "INVALID"
        }

class AdversarialAgent:
    """Malicious agent attempting injection, tampering, and heuristic exploitation."""
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Attempt 1: Mutate passed history in-place
        if "history" in payload and payload["history"]:
            try:
                payload["history"][0]["next_state"] = "CORRUPTED_BY_AGENT"
            except Exception:
                pass

        # Attempt 2: Inject extra fields & illegal action ID
        phase = payload.get("phase")
        if phase == "INTERACTIVE":
            return {
                "action": "HACK_INVENTED_ACTION",
                "unobserved_latent": 999,
                "raw_world_write": True
            }
        return {
            "d1_predictions": {str(q["tau"]): "CORRUPT_STATE" for q in payload.get("d1_queries", [])},
            "malformed_injection": "DROP TABLE ledger;"
        }

# ============================================================================
# CONFORMANCE TEST CASES
# ============================================================================

class TestPhaseIIHarnessConformance(unittest.TestCase):

    def setUp(self):
        self.harness = CMAWSEExperimentHarness(master_seed=0x5A3F)

    def test_d0_runtime_invariant_adversarial_tampering(self):
        """Verify that malicious agent cannot corrupt world state."""
        agent = AdversarialAgent()
        record = self.harness.run_session("CONDITION_C", 0, agent)
        # Invariant: corrupt writes must be strictly zero
        self.assertEqual(record["d0_corrupt_writes"], 0)
        # All invalid actions must be intercepted as REJECTED_INVALID_ACTION
        for step in record["ledger"]:
            self.assertEqual(step["status"], "REJECTED_INVALID_ACTION")

    def test_d1_oracle_passes_and_dummy_fails(self):
        rec_oracle = self.harness.run_session("CONDITION_C", 1, OracleAgent())
        rec_dummy = self.harness.run_session("CONDITION_C", 2, RandomDummyAgent())
        self.assertTrue(rec_oracle["d1_pass"])
        self.assertFalse(rec_dummy["d1_pass"])

    def test_d2_multi_hypothesis_forward_eval(self):
        rec = self.harness.run_session("CONDITION_C", 3, OracleAgent())
        self.assertTrue(rec["d2_pass"])
        self.assertGreaterEqual(rec["d2_cr"], 0.833)

    def test_d3_wilcoxon_pratt_exact_math(self):
        """Verifies Pratt zero-handling Wilcoxon signed-rank algorithm."""
        # Case 1: Strictly positive gains
        pos_diffs = [0.1] * 50 + [0.2] * 50
        w, p = wilcoxon_signed_rank_pratt(pos_diffs)
        self.assertLess(p, 1e-4)

        # Case 2: Symmetric around zero (Null holds)
        null_diffs = [-0.1] * 50 + [0.1] * 50
        w_null, p_null = wilcoxon_signed_rank_pratt(null_diffs)
        self.assertGreater(p_null, 0.4)

        # Case 3: Many zeros (Pratt handling active)
        zero_diffs = [0.0] * 80 + [0.1] * 20
        w_z, p_z = wilcoxon_signed_rank_pratt(zero_diffs)
        self.assertIsInstance(p_z, float)

    def test_d4_context_generalization_no_unseen_label(self):
        rec = self.harness.run_session("CONDITION_C", 4, OracleAgent())
        self.assertTrue(rec["d4_pass"])

    def test_d5_hypothetical_branch_inference(self):
        rec = self.harness.run_session("CONDITION_C", 5, OracleAgent())
        self.assertTrue(rec["d5_pass"])

    def test_d6_true_bijective_permutation_robustness(self):
        """Verifies true symbol permutation mapping."""
        rec = self.harness.run_session("CONDITION_C", 6, OracleAgent())
        # Oracle un-permuted prediction matches unpermuted run perfectly -> div = 0
        self.assertEqual(rec["d6_divergence"], 0.0)

    def test_d6_bootstrap_type7_quantile_exactness(self):
        divs_zero = [0.0] * 100
        q0, pass0 = evaluate_d6_bootstrap(divs_zero)
        self.assertEqual(q0, 0.0)
        self.assertTrue(pass0)

        divs_large = [0.20] * 100
        q1, pass1 = evaluate_d6_bootstrap(divs_large)
        self.assertEqual(q1, 0.20)
        self.assertFalse(pass1)

    def test_canonical_replay_cli_subprocess(self):
        """Verifies --replay CLI in an isolated Python process."""
        record = self.harness.run_session("CONDITION_C", 10, OracleAgent())
        log_file = "temp_replay_audit.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        cmd = [sys.executable, "CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py", "--replay", "--log", log_file, "--seed", "0x5A3F"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(log_file):
            os.remove(log_file)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("Replay verified bit-level identical across 1 sessions", proc.stdout)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhaseIIHarnessConformance)
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)
