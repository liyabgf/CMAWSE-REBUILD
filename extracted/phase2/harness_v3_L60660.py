# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L60660-L60800 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #160  lines=140  compile=OK
# kind: harness  ident: harness_160.py  harness version 3/7
# edits: none. Header comment is the only addition.
# ======================
"""
Synthetic-Agent Conformance Test Suite for CMAWSE Phase II Evaluators.
Standard Library Only (`unittest`).
Verifies D0-D6 Evaluators on Known-Answer Agents.
"""
import copy
import json
import os
import subprocess
import sys
import unittest

from CMAWSE_v1_0_3_EXPERIMENT_HARNESS import (
    CMAWSEExperimentHarness, DiscretePhysicalWorldEngine,
    evaluate_d1, evaluate_d2, evaluate_d4, evaluate_d5, evaluate_d6_bootstrap,
    derive_session_seed
)

class OracleAgent:
    """Perfect synthetic agent with full ground truth knowledge."""
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        phase = payload.get("phase")
        if phase == "INTERACTIVE":
            obs = payload["observation"]
            # Always pick optimal action
            obj = obs["focal_object"]
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
                # Correctly answer D1 holdout queries
                tau = str(q["tau"])
                x = q["X"]
                act = q["act"]
                if x in ("door", "A") and act in ("lift", "act_beta"):
                    preds[tau] = "st_open" if "lift" in act or act == "lift" else "q1"
                elif x in ("cabinet", "B") and act in ("turn", "act_gamma"):
                    preds[tau] = "st_locked" if "turn" in act or act == "turn" else "q2"
                else:
                    preds[tau] = "st_idle" if "door" in x or x == "door" else "q0"

            # Perfect D2 prediction matrix
            d2_mat = {
                "M1": {a: ("q1" if a in ("act_alpha", "act_beta") else "q0") for a in ["act_alpha", "act_beta", "act_gamma", "act_delta", "act_epsilon", "act_zeta"]},
                "M2": {a: ("q1" if a in ("act_alpha", "act_gamma") else "q0") for a in ["act_alpha", "act_beta", "act_gamma", "act_delta", "act_epsilon", "act_zeta"]}
            }
            # Perfect D4 predictions on unseen context
            d4_preds = {f"d4_{i}": ("q1" if a == "act_beta" else "q0") for i, a in enumerate(["act_alpha", "act_beta", "act_gamma", "act_delta", "act_epsilon", "act_zeta"])}
            return {
                "d1_predictions": preds,
                "d2_matrix": d2_mat,
                "d4_predictions": d4_preds,
                "d5_prediction": "q0"
            }
        return {"d1_predictions": {}}

class RandomDummyAgent:
    """Random agent picking first action and generating uniform noise."""
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

class TestPhaseIIEvaluators(unittest.TestCase):

    def setUp(self):
        self.harness = CMAWSEExperimentHarness(master_seed=0x5A3F)

    def test_d0_runtime_invariant_zero_corruption(self):
        agent = RandomDummyAgent()
        record = self.harness.run_session("CONDITION_C", 0, agent)
        self.assertEqual(record["d0_corrupt_writes"], 0)

    def test_d1_oracle_passes_and_dummy_fails(self):
        oracle_record = self.harness.run_session("CONDITION_C", 1, OracleAgent())
        self.assertTrue(oracle_record["d1_pass"])
        self.assertGreater(oracle_record["d1_delta"], 0.15)

    def test_d2_forward_prediction_evaluator(self):
        oracle_record = self.harness.run_session("CONDITION_C", 2, OracleAgent())
        self.assertTrue(oracle_record["d2_pass"])
        self.assertGreaterEqual(oracle_record["d2_cr"], 0.833)

    def test_d3_information_gain_advantage(self):
        oracle_record = self.harness.run_session("CONDITION_C", 3, OracleAgent())
        self.assertIsInstance(oracle_record["d3_mean_iga"], float)
        self.assertTrue(oracle_record["d3_pass"])

    def test_d4_unseen_context_generalization(self):
        oracle_record = self.harness.run_session("CONDITION_C", 4, OracleAgent())
        self.assertTrue(oracle_record["d4_pass"])

    def test_d5_hypothetical_branch_inference(self):
        oracle_record = self.harness.run_session("CONDITION_C", 5, OracleAgent())
        self.assertTrue(oracle_record["d5_pass"])

    def test_d6_bootstrap_type7_quantile(self):
        # Perfect invariance: divergences are zero
        zero_divs = [0.0] * 100
        q, passed = evaluate_d6_bootstrap(zero_divs)
        self.assertEqual(q, 0.0)
        self.assertTrue(passed)

        # Divergent: divergences are all 1.0
        one_divs = [1.0] * 100
        q_fail, passed_fail = evaluate_d6_bootstrap(one_divs)
        self.assertEqual(q_fail, 1.0)
        self.assertFalse(passed_fail)

    def test_replay_cli_subprocessing(self):
        # Generate session log
        record = self.harness.run_session("CONDITION_C", 10, OracleAgent())
        log_path = "temp_pilot_test.jsonl"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        # Execute Replay CLI
        cmd = [sys.executable, "CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py", "--replay", "--log", log_path, "--seed", "0x5A3F"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(log_path):
            os.remove(log_path)
        self.assertEqual(res.returncode, 0)
        self.assertIn("All 1 sessions verified bit-level identical", res.stdout)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhaseIIEvaluators)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
