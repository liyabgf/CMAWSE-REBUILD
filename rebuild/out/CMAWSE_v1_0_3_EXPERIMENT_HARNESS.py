# ===== PROVENANCE =====
# status: REWRITTEN (P3 assembly-layer rebuild)
# base: extracted/phase2/harness_v6_L61914.py (RESTORED, CMAWSE第一阶段.md @ L61914)
# changes: F1 zero-likelihood soft fuse (hold prior + audit counter, reconciled
#          to in-archive v2/v4 semantics); F2 D1 baseline global-mode
#          tie-break by first-observed order (was alphabetical).
# rationale & full diff: rebuild/P3_REPORT.md, rebuild/out/engine_v6.diff
# acceptance: extracted/phase2/harness_v7_L62449.py (RESTORED, unmodified) 7/7
# date: 2026-10-28
# ======================
# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L61914-L62442 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #163  lines=528  compile=OK
# kind: harness  ident: harness_163.py  harness version 6/7
# edits: none. Header comment is the only addition.
# ======================
"""
CMAWSE Phase II Executable Experiment Harness & Evaluator (v1.0.3 Closed Reconciled Engine)
Standard Library Only. Zero External Dependencies.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# ============================================================================
# 1. DETERMINISTIC PRNG: SplitMix64
# ============================================================================

class SplitMix64:
    __slots__ = ("_state",)

    def __init__(self, seed: int):
        self._state: int = seed & 0xFFFFFFFFFFFFFFFF

    def next_uint64(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self._state
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

def derive_session_seed(master_seed: int, session_idx: int) -> int:
    combiner = (master_seed ^ (session_idx * 0x9E3779B97F4A7C15)) & 0xFFFFFFFFFFFFFFFF
    return SplitMix64(combiner).next_uint64()

# ============================================================================
# 2. IMMUTABLE WORLD DEFINITION
# ============================================================================

COND_A_VOCAB = {
    "states": ("st_idle", "st_open", "st_locked", "st_error"),
    "objects": ("door", "cabinet", "safe"),
    "contexts": ("hall", "office", "vault"),
    "actions": ("push", "pull", "turn", "lift", "wait", "reset")
}

COND_BC_VOCAB = {
    "states": ("q0", "q1", "q2", "q3"),
    "objects": ("A", "B", "C"),
    "contexts": ("K", "L", "M"),
    "actions": ("act_alpha", "act_beta", "act_gamma", "act_delta", "act_epsilon", "act_zeta")
}

D6_BIJECTION_MAP = {
    "q0": "s0", "q1": "s1", "q2": "s2", "q3": "s3",
    "A": "obj_X", "B": "obj_Y", "C": "obj_Z",
    "K": "env_U", "L": "env_V", "M": "env_W",
    "act_alpha": "op_1", "act_beta": "op_2", "act_gamma": "op_3",
    "act_delta": "op_4", "act_epsilon": "op_5", "act_zeta": "op_6"
}
D6_INVERSE_MAP = {v: k for k, v in D6_BIJECTION_MAP.items()}

def ground_truth_transition(condition: str, q: str, obj: str, ctx: str, act: str) -> str:
    if condition == "CONDITION_A":
        if obj == "door" and act == "push":
            return "st_open"
        elif obj == "cabinet" and act in ("pull", "turn"):
            return "st_locked"
        return "st_idle"
    else:  # CONDITION_B & CONDITION_C
        target_q = "st_open" if condition == "CONDITION_B" else "q1"
        second_q = "st_locked" if condition == "CONDITION_B" else "q2"
        idle_q = "st_idle" if condition == "CONDITION_B" else "q0"

        door_obj = "door" if condition == "CONDITION_B" else "A"
        lift_act = "lift" if condition == "CONDITION_B" else "act_beta"
        cab_obj = "cabinet" if condition == "CONDITION_B" else "B"
        turn_act = "turn" if condition == "CONDITION_B" else "act_gamma"

        if obj == door_obj and act == lift_act:
            return target_q
        elif obj == cab_obj and act == turn_act:
            return second_q
        return idle_q

# ============================================================================
# 3. D3 MATHEMATICAL ENGINE & REFERENCE BAYESIAN FILTER
# ============================================================================

def ref_model_transition(model_idx: int, obj: str, ctx: str, act: str) -> str:
    if model_idx == 0:  # M1
        if obj in ("A", "door") and act in ("act_alpha", "act_beta", "push", "lift"):
            return "q1" if act in ("act_beta", "lift") else "q2"
        return "q0"
    elif model_idx == 1:  # M2
        if ctx in ("K", "hall") and act in ("act_alpha", "act_gamma", "push", "turn"):
            return "q1"
        return "q0"
    else:  # M3
        if act in ("act_beta", "lift"):
            return "q1"
        elif act in ("act_gamma", "turn"):
            return "q2"
        return "q0"

def calculate_shannon_entropy(p_dist: List[float]) -> float:
    return sum(-p * math.log2(p) for p in p_dist if p > 0.0)

def compute_step_iga(obj: str, ctx: str, chosen_act: Optional[str],
                     actions: Tuple[str, ...], prior: List[float]) -> Tuple[float, List[float]]:
    h_prior = calculate_shannon_entropy(prior)
    ig_per_action: Dict[str, float] = {}

    for a in actions:
        outcomes: Dict[str, float] = {}
        for m_idx in range(3):
            if prior[m_idx] > 0.0:
                y = ref_model_transition(m_idx, obj, ctx, a)
                outcomes[y] = outcomes.get(y, 0.0) + prior[m_idx]

        exp_cond_ent = 0.0
        for y, p_y in outcomes.items():
            if p_y > 0.0:
                post_y = [
                    (prior[m_idx] * (1.0 if ref_model_transition(m_idx, obj, ctx, a) == y else 0.0)) / p_y
                    for m_idx in range(3)
                ]
                exp_cond_ent += p_y * calculate_shannon_entropy(post_y)

        ig_per_action[a] = max(0.0, h_prior - exp_cond_ent)

    mean_ig = sum(ig_per_action.values()) / float(len(actions)) if actions else 0.0
    d_t = (ig_per_action[chosen_act] - mean_ig) if chosen_act in ig_per_action else (0.0 - mean_ig)
    return d_t, prior

ZERO_LIKELIHOOD_EVENTS = 0


def update_reference_prior_strict(prior: List[float], obj: str, ctx: str,
                                  act: str, obs_y: str) -> List[float]:
    numerators = []
    for m_idx in range(3):
        pred_y = ref_model_transition(m_idx, obj, ctx, act)
        lik = 1.0 if pred_y == obs_y else 0.0
        numerators.append(prior[m_idx] * lik)

    total = sum(numerators)
    if total <= 0.0:
        # REWRITTEN-F1 (assembly fix): soft zero-likelihood fuse.
        # v6 raised ValueError -> run_session aborted -> conformance records lost
        # all evaluation fields (P2 gate KeyError d1_pass...). Reconciled to the
        # in-archive v2/v4 semantics ("hold prior") plus an audit counter.
        global ZERO_LIKELIHOOD_EVENTS
        ZERO_LIKELIHOOD_EVENTS += 1
        return prior
    return [n / total for n in numerators]

def wilcoxon_signed_rank_pratt(diffs: List[float]) -> Tuple[float, float]:
    n = len(diffs)
    if n == 0:
        return 0.0, 1.0

    abs_diffs = [abs(d) for d in diffs]
    indexed = sorted(range(n), key=lambda i: abs_diffs[i])
    ranks = [0.0] * n

    i = 0
    while i < n:
        j = i
        while j < n - 1 and abs_diffs[indexed[j]] == abs_diffs[indexed[j + 1]]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1

    w_pos = sum(ranks[idx] for idx in range(n) if diffs[idx] > 0.0)
    w_zeros = sum(ranks[idx] for idx in range(n) if diffs[idx] == 0.0)
    total_rank_sum = sum(ranks)

    mean_w = (total_rank_sum - w_zeros) / 2.0
    var_w = sum(r * r for r in ranks) / 4.0

    if var_w <= 0.0:
        return float(w_pos), 1.0

    z = (w_pos - mean_w) / math.sqrt(var_w)
    p_value = 0.5 * math.erfc(z / math.sqrt(2))
    return float(w_pos), float(p_value)

# ============================================================================
# 4. DISCRETE WORLD ENGINE
# ============================================================================

class DiscretePhysicalWorld:
    def __init__(self, condition: str, session_seed: int):
        self.condition: str = condition
        self.tick: int = 0
        self.prng = SplitMix64(session_seed)
        vocab = COND_A_VOCAB if condition == "CONDITION_A" else COND_BC_VOCAB

        self.states: Tuple[str, ...] = vocab["states"]
        self.objects: Tuple[str, ...] = vocab["objects"]
        self.contexts: Tuple[str, ...] = vocab["contexts"]
        self.actions: Tuple[str, ...] = vocab["actions"]

        self.current_q: str = self.states[0]
        self.focal_obj: str = self.objects[0]
        self.train_contexts: Tuple[str, ...] = (self.contexts[0], self.contexts[1])
        self.current_ctx: str = self.train_contexts[0]
        self.unobserved_latent: int = self.prng.next_uint64() % 2

    def project_observation(self) -> Dict[str, Any]:
        avail = list(self.actions)
        n = len(avail)
        for i in range(n - 1, 0, -1):
            j = self.prng.next_uint64() % (i + 1)
            avail[i], avail[j] = avail[j], avail[i]

        return {
            "tick": self.tick,
            "state": self.current_q,
            "focal_object": self.focal_obj,
            "context": self.current_ctx,
            "available_actions": tuple(avail)
        }

    def step(self, action: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        prev_q = self.current_q
        if action is None or action not in self.actions:
            status = "REJECTED_INVALID_ACTION"
            next_q = prev_q
        else:
            next_q = ground_truth_transition(self.condition, prev_q, self.focal_obj, self.current_ctx, action)
            status = "COMMITTED"

        self.current_q = next_q
        self.tick += 1

        event = {
            "tick": self.tick - 1,
            "action": action,
            "prev_state": prev_q,
            "next_state": next_q,
            "object": self.focal_obj,
            "context": self.current_ctx,
            "status": status
        }
        self.focal_obj = self.objects[self.tick % len(self.objects)]
        self.current_ctx = self.train_contexts[self.tick % len(self.train_contexts)]
        return next_q, event

# ============================================================================
# 5. D0 - D6 EVALUATORS
# ============================================================================

def evaluate_d1(train_ledger: List[Dict[str, Any]], test_queries: List[Dict[str, Any]],
                predictions: Dict[Any, str]) -> Tuple[float, bool]:
    cond_counts: Dict[Tuple[str, str], Dict[str, int]] = {}
    global_counts: Dict[str, int] = {}

    for step in train_ledger:
        if step["status"] == "COMMITTED":
            key = (step["object"], step["action"])
            nxt = step["next_state"]
            cond_counts.setdefault(key, {})[nxt] = cond_counts.setdefault(key, {}).get(nxt, 0) + 1
            global_counts[nxt] = global_counts.get(nxt, 0) + 1

    # REWRITTEN-F2 (assembly fix): tie-break by first-observed order (dict
    # insertion order) instead of alphabetical sort. The alphabetical tie-break
    # let the naive baseline degenerate into a perfect predictor on the
    # all-q0 holdout (structural 7/7/7 ledger tie), making D1's
    # delta>=0.15 criterion unsatisfiable for ANY agent incl. a perfect
    # oracle. First-occurrence order is the standard empirical-mode convention.
    global_mode = max(global_counts.keys(), key=lambda k: global_counts[k]) if global_counts else "q0"
    correct_agent = 0
    correct_base = 0

    for query in test_queries:
        tau = query["tau"]
        y_true = query["true_label"]
        y_pred = predictions.get(str(tau), predictions.get(tau, "INVALID"))
        if y_pred == y_true:
            correct_agent += 1

        cond_key = (query["X"], query["act"])
        if cond_key in cond_counts and cond_counts[cond_key]:
            c_dict = cond_counts[cond_key]
            y_base = max(sorted(c_dict.keys()), key=lambda k: (c_dict[k], -ord(k[-1])))
        else:
            y_base = global_mode

        if y_base == y_true:
            correct_base += 1

    n = float(len(test_queries))
    acc_agent = correct_agent / n
    acc_base = correct_base / n
    delta = acc_agent - acc_base
    passed = (delta >= 0.15) and (acc_agent >= 0.50)
    return delta, passed

def evaluate_d2(matrix: Dict[str, Dict[str, str]], condition: str) -> Tuple[float, bool]:
    if not isinstance(matrix, dict):
        return 0.0, False
    vocab = COND_A_VOCAB if condition == "CONDITION_A" else COND_BC_VOCAB
    actions = vocab["actions"]
    correct = 0

    for m_idx, m_name in enumerate(["M1", "M2"]):
        model_preds = matrix.get(m_name, {})
        for a in actions:
            y_pred = model_preds.get(a, "INVALID")
            y_ref = ref_model_transition(m_idx, vocab["objects"][0], vocab["contexts"][0], a)
            if y_pred == y_ref:
                correct += 1

    cr = correct / 12.0
    return cr, (cr >= 0.833)

def evaluate_d4(unseen_context: str, condition: str, agent_preds: Dict[str, str]) -> Tuple[float, bool]:
    vocab = COND_A_VOCAB if condition == "CONDITION_A" else COND_BC_VOCAB
    test_queries = [
        {"tau": f"d4_{i}", "X": vocab["objects"][0], "K": unseen_context, "act": a}
        for i, a in enumerate(vocab["actions"])
    ]
    correct = sum(
        1 for q in test_queries
        if agent_preds.get(q["tau"]) == ground_truth_transition(condition, vocab["states"][0], q["X"], q["K"], q["act"])
    )
    acc = correct / float(len(test_queries))
    return acc, (acc >= 0.66)

def evaluate_d5(branch_query: Dict[str, Any], agent_pred: str, condition: str) -> Tuple[float, bool]:
    y_true = ground_truth_transition(
        condition, branch_query["state"], branch_query["focal_object"],
        branch_query["context"], branch_query["action"]
    )
    passed = (agent_pred == y_true)
    return (1.0 if passed else 0.0), passed

def evaluate_d6_bootstrap(session_divergences: List[float], seed: int = 0x5A3F) -> Tuple[float, bool]:
    if not session_divergences:
        return 1.0, False
    b_prng = SplitMix64(seed)
    n = len(session_divergences)
    b_reps = 10000
    boot_means = []

    for _ in range(b_reps):
        s = sum(session_divergences[b_prng.next_uint64() % n] for _ in range(n))
        boot_means.append(s / float(n))

    boot_means.sort()
    h = 1.0 + (float(b_reps) - 1.0) * 0.99
    j = int(math.floor(h))
    g = h - float(j)
    q_099 = boot_means[-1] if j >= b_reps else boot_means[j - 1] + g * (boot_means[j] - boot_means[j - 1])
    return q_099, bool(q_099 < 0.10)

# ============================================================================
# 6. HARNESS CONTROLLER & STUDY-LEVEL AGGREGATOR
# ============================================================================

class CMAWSEExperimentHarness:
    def __init__(self, master_seed: int = 0x5A3F):
        self.master_seed: int = master_seed

    def run_session(self, condition: str, session_idx: int,
                    agent_callable: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        session_seed = derive_session_seed(self.master_seed, session_idx)
        world = DiscretePhysicalWorld(condition, session_seed)
        ledger: List[Dict[str, Any]] = []
        parsing_failures = 0
        global ZERO_LIKELIHOOD_EVENTS
        ZERO_LIKELIHOOD_EVENTS = 0
        prior = [1/3, 1/3, 1/3]
        iga_trajectory: List[float] = []

        # --------------------------------------------------------------------
        # Phase 1: Interactive Exploration (Calls 1..21)
        # --------------------------------------------------------------------
        for t in range(21):
            obs = world.project_observation()
            payload = {
                "phase": "INTERACTIVE",
                "observation": obs,
                "history": copy.deepcopy(ledger)
            }
            try:
                resp = agent_callable(payload)
                act = resp.get("action")
            except Exception:
                parsing_failures += 1
                act = None

            d_t, prior = compute_step_iga(obs["focal_object"], obs["context"], act, obs["available_actions"], prior)
            iga_trajectory.append(d_t)

            next_q, evt = world.step(act)
            ledger.append(evt)
            try:
                prior = update_reference_prior_strict(prior, evt["object"], evt["context"], act or "NONE", next_q)
            except ValueError:
                return {"status": "INVALID_REFERENCE_OUTCOME", "session_idx": session_idx}

        # --------------------------------------------------------------------
        # Phase 2: Frozen Batch Holdout (Call 22)
        # --------------------------------------------------------------------
        test_queries = []
        for tau in range(21, 30):
            q_in = world.states[tau % len(world.states)]
            x_in = world.objects[(tau * 2) % len(world.objects)]
            k_in = world.train_contexts[(tau * 3) % len(world.train_contexts)]
            act_in = world.actions[(tau * 5) % len(world.actions)]
            test_queries.append({
                "tau": tau, "q": q_in, "X": x_in, "K": k_in, "act": act_in,
                "true_label": ground_truth_transition(condition, q_in, x_in, k_in, act_in)
            })

        unseen_ctx = world.contexts[2]
        branch_q = {
            "tick": 10,
            "state": ledger[10]["prev_state"],
            "focal_object": ledger[10]["object"],
            "context": ledger[10]["context"],
            "action": world.actions[3]
        }

        batch_payload = {
            "phase": "BATCH_EVALUATION",
            "context_history": copy.deepcopy(ledger),
            "d1_queries": [{k: v for k, v in q.items() if k != "true_label"} for q in test_queries],
            "d4_queries": [
                {"tau": f"d4_{i}", "focal_object": world.objects[0], "context": unseen_ctx, "action": a}
                for i, a in enumerate(world.actions)
            ],
            "d5_query": branch_q
        }

        try:
            batch_resp = agent_callable(batch_payload)
            d1_preds = batch_resp.get("d1_predictions", {})
            d2_matrix = batch_resp.get("d2_matrix", {})
            d4_preds = batch_resp.get("d4_predictions", {})
            d5_pred = batch_resp.get("d5_prediction", "INVALID")
        except Exception:
            parsing_failures += 1
            d1_preds, d2_matrix, d4_preds, d5_pred = {}, {}, {}, "INVALID"

        # --------------------------------------------------------------------
        # Phase 3: True Permutation Evaluation (Call 23)
        # --------------------------------------------------------------------
        permuted_payload = self._apply_bijective_permutation(batch_payload)
        try:
            perm_resp = agent_callable(permuted_payload)
            raw_perm_d1 = perm_resp.get("d1_predictions", {})
            perm_d1_preds = {k: D6_INVERSE_MAP.get(v, v) for k, v in raw_perm_d1.items()}
        except Exception:
            parsing_failures += 1
            perm_d1_preds = {}

        d1_delta, d1_pass = evaluate_d1(ledger, test_queries, d1_preds)
        d2_cr, d2_pass = evaluate_d2(d2_matrix, condition)
        d3_mean_iga = sum(iga_trajectory) / float(len(iga_trajectory))
        d4_acc, d4_pass = evaluate_d4(unseen_ctx, condition, d4_preds)
        d5_acc, d5_pass = evaluate_d5(branch_q, d5_pred, condition)

        diffs = sum(1 for q_item in test_queries if d1_preds.get(str(q_item["tau"])) != perm_d1_preds.get(str(q_item["tau"])))
        d6_div = diffs / float(len(test_queries))

        return {
            "session_idx": session_idx,
            "condition": condition,
            "session_seed": session_seed,
            "parsing_failures": parsing_failures,
            "parsing_failure_rate": parsing_failures / 23.0,
            "d1_delta": d1_delta, "d1_pass": d1_pass,
            "d2_cr": d2_cr, "d2_pass": d2_pass,
            "d3_mean_iga": d3_mean_iga,
            "d4_acc": d4_acc, "d4_pass": d4_pass,
            "d5_acc": d5_acc, "d5_pass": d5_pass,
            "d6_divergence": d6_div,
            "zero_likelihood_events": ZERO_LIKELIHOOD_EVENTS,
            "ledger": ledger
        }

    def _apply_bijective_permutation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        def permute(val: Any) -> Any:
            if isinstance(val, str):
                return D6_BIJECTION_MAP.get(val, val)
            elif isinstance(val, list):
                return [permute(x) for x in val]
            elif isinstance(val, tuple):
                return tuple(permute(x) for x in val)
            elif isinstance(val, dict):
                return {D6_BIJECTION_MAP.get(k, k): permute(v) for k, v in val.items()}
            return val
        return permute(copy.deepcopy(payload))

    def evaluate_study_d3(self, session_records: List[Dict[str, Any]]) -> Tuple[float, float, bool]:
        """Aggregate statistical evaluation of D3 across N=100 sessions."""
        valid_records = [r for r in session_records if "d3_mean_iga" in r]
        diffs = [r["d3_mean_iga"] for r in valid_records]
        if not diffs:
            return 0.0, 1.0, False

        mean_delta = sum(diffs) / float(len(diffs))
        w_stat, p_val = wilcoxon_signed_rank_pratt(diffs)
        passed = (p_val < 0.01) and (mean_delta >= 0.05)
        return mean_delta, p_val, passed

# ============================================================================
# 7. CANONICAL REPLAY VERIFIER CLI
# ============================================================================

def execute_replay_cli():
    parser = argparse.ArgumentParser(description="CMAWSE v1.0.3 Deterministic Replay Verifier CLI")
    parser.add_argument("--replay", action="store_true", required=True)
    parser.add_argument("--log", type=str, required=True)
    parser.add_argument("--seed", type=lambda x: int(x, 0), required=True)
    args = parser.parse_args()

    with open(args.log, "r", encoding="utf-8") as f:
        sessions = [json.loads(line) for line in f if line.strip()]

    for s in sessions:
        s_idx = s["session_idx"]
        cond = s["condition"]
        exp_seed = derive_session_seed(args.seed, s_idx)
        if s["session_seed"] != exp_seed:
            raise ValueError(f"Session {s_idx} seed mismatch! Expected {exp_seed}, got {s['session_seed']}")

        replayed_world = DiscretePhysicalWorld(cond, exp_seed)
        replayed_ledger = []
        for step in s["ledger"]:
            _, evt = replayed_world.step(step["action"])
            replayed_ledger.append(evt)

        if json.dumps(s["ledger"], sort_keys=True) != json.dumps(replayed_ledger, sort_keys=True):
            raise ValueError(f"Ledger mismatch in Session {s_idx}!")

    print(f"[SUCCESS] Canonical deterministic replay verified across {len(sessions)} sessions. 0 discrepancies.")
    sys.exit(0)

if __name__ == "__main__":
    if "--replay" in sys.argv:
        execute_replay_cli()
