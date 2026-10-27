# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L62449-L62600 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #164  lines=151  compile=OK
# kind: harness  ident: harness_164.py  harness version 7/7
# edits: none. Header comment is the only addition.
# ======================
"""
CMAWSE Phase II Synthetic Conformance Suite (Rev3)
Explicitly imports all types. Covers:
1. OracleAgent
2. RandomDummyAgent
3. AdversarialAgent (Exploiting metadata, injection, in-place mutation)
4. Full Wilcoxon-Pratt study-level integration test
5. Canonical Replay CLI subprocess test
"""
from __future__ import annotations
import copy
import json
import os
import subprocess
import sys
import unittest
from typing import Any, Dict, List, Optional, Tuple

from CMAWSE_v1_0_3_EXPERIMENT_HARNESS import (
    CMAWSEExperimentHarness, DiscretePhysicalWorld,
    wilcoxon_signed_rank_pratt, evaluate_d6_bootstrap,
    derive_session_seed
)

class OracleAgent:
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        phase = payload.get("phase")
        if phase == "INTERACTIVE":
            obs = payload["observation"]
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
    """Agent deliberately attempting in-place history mutation and illegal injection."""
    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "history" in payload and payload["history"]:
            try:
                payload["history"][0]["next_state"] = "MUTATED_BY_AGENT"
            except Exception:
                pass
        phase = payload.get("phase")
        if phase == "INTERACTIVE":
            return {"action": "HACK_ACTION", "unobserved_latent": 999}
        return {
            "d1_predictions": {str(q["tau"]): "HACK_STATE" for q in payload.get("d1_queries", [])},
            "d2_matrix": "INVALID_TYPE",
            "d4_predictions": {},
            "d5_prediction": "HACK_STATE"
        }

class TestPhaseIIConformance(unittest.TestCase):

    def setUp(self):
        self.harness = CMAWSEExperimentHarness(master_seed=0x5A3F)

    def test_d0_architectural_isolation_and_interception(self):
        """Verifies that in-place mutations do not infect runtime and illegal actions are rejected."""
        rec = self.harness.run_session("CONDITION_C", 0, AdversarialAgent())
        for step in rec["ledger"]:
            self.assertEqual(step["status"], "REJECTED_INVALID_ACTION")
            self.assertNotEqual(step["next_state"], "MUTATED_BY_AGENT")

    def test_d1_oracle_passes_and_dummy_fails(self):
        rec_oracle = self.harness.run_session("CONDITION_C", 1, OracleAgent())
        rec_dummy = self.harness.run_session("CONDITION_C", 2, RandomDummyAgent())
        self.assertTrue(rec_oracle["d1_pass"])
        self.assertFalse(rec_dummy["d1_pass"])

    def test_d2_evaluator_strictness(self):
        rec_oracle = self.harness.run_session("CONDITION_C", 3, OracleAgent())
        rec_adv = self.harness.run_session("CONDITION_C", 4, AdversarialAgent())
        self.assertTrue(rec_oracle["d2_pass"])
        self.assertFalse(rec_adv["d2_pass"])

    def test_d3_study_level_aggregate_wilcoxon(self):
        """Generates multi-session data and verifies D3 study-level Wilcoxon-Pratt."""
        records = [self.harness.run_session("CONDITION_C", i, OracleAgent()) for i in range(10, 25)]
        mean_delta, p_val, passed = self.harness.evaluate_study_d3(records)
        self.assertIsInstance(mean_delta, float)
        self.assertIsInstance(p_val, float)
        self.assertLess(p_val, 0.05)

    def test_d5_hypothetical_branch(self):
        rec = self.harness.run_session("CONDITION_C", 5, OracleAgent())
        self.assertTrue(rec["d5_pass"])

    def test_d6_bijective_permutation_evaluator(self):
        rec_oracle = self.harness.run_session("CONDITION_C", 6, OracleAgent())
        self.assertEqual(rec_oracle["d6_divergence"], 0.0)

    def test_canonical_replay_cli(self):
        rec = self.harness.run_session("CONDITION_C", 7, OracleAgent())
        log_file = "temp_audit_session.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

        cmd = [sys.executable, "CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py", "--replay", "--log", log_file, "--seed", "0x5A3F"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(log_file):
            os.remove(log_file)

        self.assertEqual(res.returncode, 0)
        self.assertIn("Canonical deterministic replay verified", res.stdout)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhaseIIConformance)
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)
