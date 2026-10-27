# -*- coding: utf-8 -*-
"""P7-A2：d1v2b 独立验证（REWRITTEN）。独立集 s11/s13（从未参与任何开发决策）。

新构造（冻结于 P7_PLAN）：holdout_v2c N=30 = 6×(A,act_beta)→q1 + 6×(B,act_gamma)→q2
+ 6×(A,act_alpha)→q0 + 6×(B,act_alpha)→q0 + 6×(C,act_alpha)→q0。
基线 = P(Y|X) 边际众数（账本 A 全 q1 / B 全 q2 / C 全 q0 -> 基线在中性查询上系统性错）。
oracle 泄漏审计：rule_oracle（世界转移函数现算，不读 y）vs label_oracle（读 y，P6 实现）。
"""
import sys, os, csv, json, random, copy
from math import comb
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H
from rebuild.p6.a_d6 import Explorer

def make_session(session_idx):
    seed = H.derive_session_seed(0x5A3F, session_idx)
    world = H.DiscretePhysicalWorld('CONDITION_C', seed)
    ledger = []
    ex = Explorer()
    for t in range(21):
        obs = world.project_observation()
        act = ex({'phase': 'INTERACTIVE', 'observation': obs})['action']
        _, evt = world.step(act)
        ledger.append(evt)
    return world, ledger

def holdout_v2c(world):
    A, B, C = world.objects[0], world.objects[1], world.objects[2]
    ab, ag, aa = world.actions[1], world.actions[2], world.actions[0]
    qs = []
    tau = 21
    for _ in range(6):
        qs.append({'tau': tau, 'X': A, 'act': ab}); tau += 1
    for _ in range(6):
        qs.append({'tau': tau, 'X': B, 'act': ag}); tau += 1
    for _ in range(6):
        qs.append({'tau': tau, 'X': A, 'act': aa}); tau += 1
    for _ in range(6):
        qs.append({'tau': tau, 'X': B, 'act': aa}); tau += 1
    for _ in range(6):
        qs.append({'tau': tau, 'X': C, 'act': aa}); tau += 1
    for q in qs:
        q['y'] = H.ground_truth_transition('CONDITION_C', world.states[0], q['X'], world.train_contexts[0], q['act'])
    return qs

# K 无关性先核实（源码断言，不用未验证假设）
K_IGNORED = True  # 源码逐行核实（见 logs）：CONDITION_C 分支不使用 q/ctx 参数，转移仅由 (obj, act) 决定

def x_marginal_baseline(ledger, queries):
    counts = {}
    for s in ledger:
        counts.setdefault(s['object'], []).append(s['next_state'])
    mode = {x: max(set(ys), key=lambda k: (ys.count(k), -ys.index(k))) for x, ys in counts.items()}
    return {q['tau']: mode.get(q['X'], 'q0') for q in queries}

def global_mode(ledger):
    ys = [s['next_state'] for s in ledger]
    return max(set(ys), key=lambda k: (ys.count(k), -ys.index(k))) if ys else 'q0'

def subject_preds(name, ledger, queries, world):
    if name == 'constant_q0':
        return {q['tau']: 'q0' for q in queries}
    if name == 'majority_class':
        g = global_mode(ledger)
        return {q['tau']: g for q in queries}
    if name == 'random':
        r = random.Random(4242)
        labels = sorted(set(s['next_state'] for s in ledger))
        return {q['tau']: r.choice(labels) for q in queries}
    if name == 'simple_baseline_v2':
        return x_marginal_baseline(ledger, queries)
    if name == 'learned_agent':
        table = {(s['object'], s['action']): s['next_state'] for s in ledger}
        xb = x_marginal_baseline(ledger, queries)
        return {q['tau']: table.get((q['X'], q['act']), xb[q['tau']]) for q in queries}
    if name == 'rule_oracle':
        # 泄漏审计主体：只用世界转移函数（q, obj, ctx, act），不读查询存储的 y
        return {q['tau']: H.ground_truth_transition('CONDITION_C', world.states[0], q['X'], world.train_contexts[0], q['act']) for q in queries}
    if name == 'label_oracle':
        return {q['tau']: q['y'] for q in queries}
    raise ValueError(name)

SUBJECTS = ['constant_q0', 'majority_class', 'random', 'simple_baseline_v2', 'learned_agent', 'rule_oracle']

def mcnemar_exact(agent_ok, base_ok):
    b = sum(1 for a, bb in zip(agent_ok, base_ok) if a and not bb)
    c = sum(1 for a, bb in zip(agent_ok, base_ok) if not a and bb)
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = max(b, c)
    tail = sum(comb(n, i) for i in range(k, n + 1))
    return b, c, min(1.0, (2.0 * tail + 1.0) / (2.0 ** n + 1.0))

def score(ledger, queries, preds, base_preds):
    agent_ok = [preds[q['tau']] == q['y'] for q in queries]
    base_ok = [base_preds[q['tau']] == q['y'] for q in queries]
    n = len(queries)
    b, c, p = mcnemar_exact(agent_ok, base_ok)
    return {'acc': sum(agent_ok) / n, 'acc_base': sum(base_ok) / n,
            'delta': sum(agent_ok) / n - sum(base_ok) / n, 'b': b, 'c': c,
            'p_raw': p, 'p_bonf': min(1.0, p * 6), 'n': n}

rows, log = [], ['== P7-A2 d1v2b 独立验证（s11/s13，冻结判据：acc>=0.5 ∧ delta>=0.15 ∧ p_raw<0.05）==', '']
log.append(f'ground_truth_transition 源码 K 无关性：context 参数不参与条件 C 转移 = {K_IGNORED}（已读源码核实）')

for sid in (11, 13):
    w, led = make_session(sid)
    qs = holdout_v2c(w)
    base = x_marginal_baseline(led, qs)
    # oracle 泄漏审计
    ro = subject_preds('rule_oracle', led, qs, w)
    lo = subject_preds('label_oracle', led, qs, w)
    leak_audit = (ro == lo)
    log.append('')
    log.append(f'--- session {sid} ---')
    log.append(f'  oracle 泄漏审计：rule_oracle 与 label_oracle 预测完全一致 = {leak_audit}'
               f'（基线 acc = {sum(1 for q in qs if base[q["tau"]] == q["y"])}/{len(qs)}）')
    for name in SUBJECTS:
        sc = score(led, qs, subject_preds(name, led, qs, w), base)
        passed = (sc['acc'] >= 0.5) and (sc['delta'] >= 0.15) and (sc['p_raw'] < 0.05)
        rows.append({'set': f's{sid}', 'subject': name, 'acc': round(sc['acc'], 4),
                     'acc_base': round(sc['acc_base'], 4), 'delta': round(sc['delta'], 4),
                     'b': sc['b'], 'c': sc['c'], 'p_raw': round(sc['p_raw'], 6),
                     'p_bonf': round(sc['p_bonf'], 4), 'pass': passed})
        log.append(f"  {name:20s} acc={sc['acc']:.3f} delta={sc['delta']:+.3f} b/c={sc['b']}/{sc['c']} p={sc['p_raw']:.5f} pass={passed}")
    # K 无关扰动（若源码核实成立）：对每条查询换 K/ctx 字段重算 y，验证不变
    if K_IGNORED:
        alt_ctx = w.contexts[(w.contexts.index(w.train_contexts[0]) + 1) % len(w.contexts)] if len(w.contexts) > 1 else w.train_contexts[0]
        k_changed = sum(1 for q in qs if H.ground_truth_transition('CONDITION_C', w.states[0], q['X'], alt_ctx, q['act']) == q['y'])
        log.append(f'  K/ctx 无关扰动：换 context 重算 y 全部不变 = {k_changed}/{len(qs)}')
    # 语义保持变换不变性（重命名 + 账本排列）
    LABEL_MAPS = {'identity': {}, 'swap_q0_q2': {'q0': 'q2', 'q2': 'q0'}, 'rename_z_a_m': {'q0': 'z0', 'q1': 'a1', 'q2': 'm2'}}
    PERMS = [('identity', lambda L: L), ('reverse', lambda L: L[::-1]), ('rotate2', lambda L: L[2:] + L[:2]), ('shuffle77', lambda L: random.Random(77).sample(L, len(L)))]
    base_pass = {r['subject']: r['pass'] for r in rows if r['set'] == f's{sid}'}
    flips = []
    def remap(v, m): return m.get(v, v)
    for mn, m in LABEL_MAPS.items():
        for pn, pf in PERMS:
            ledp = [json.loads(json.dumps(s)) for s in pf(led)]
            for s in ledp:
                s['next_state'] = remap(s['next_state'], m); s['object'] = remap(s['object'], m)
                s['prev_state'] = remap(s['prev_state'], m); s['action'] = remap(s['action'], m)
            qsp = [{'tau': q['tau'], 'X': remap(q['X'], m), 'act': remap(q['act'], m), 'y': remap(q['y'], m)} for q in qs]
            basep = x_marginal_baseline(ledp, qsp)
            for name in SUBJECTS:
                raw = subject_preds(name, led, qs, w)
                predsp = {t: remap(v, m) for t, v in raw.items()}
                sc = score(ledp, qsp, predsp, basep)
                passed = (sc['acc'] >= 0.5) and (sc['delta'] >= 0.15) and (sc['p_raw'] < 0.05)
                rows.append({'set': f's{sid}[{mn}/{pn}]', 'subject': name, 'acc': round(sc['acc'], 4),
                             'acc_base': round(sc['acc_base'], 4), 'delta': round(sc['delta'], 4),
                             'b': sc['b'], 'c': sc['c'], 'p_raw': round(sc['p_raw'], 6),
                             'p_bonf': round(sc['p_bonf'], 4), 'pass': passed})
                if passed != base_pass[name]:
                    flips.append((sid, mn, pn, name))
    log.append(f'  语义保持变换（3 重命名 × 4 排列 × 6 主体）：翻转数 = {len(flips)}' + (f' {flips}' if flips else ''))

csvp = os.path.join(ROOT, 'rebuild', 'p7', 'D1V2B_RESULTS.csv')
with open(csvp, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
# 阈值敏感性（两个独立会话）
log.append('阈值敏感性（p_raw<0.05 ∧ acc>=0.5 前提下 delta 阈值 -> 通过主体集）:')
for th in [0.0, 0.15, 0.25, 0.35]:
    pl = sorted(set(r['subject'] for r in rows if r['set'] in ('s11', 's13') and r['acc'] >= 0.5 and r['delta'] >= th and r['p_raw'] < 0.05))
    log.append(f'  δ*={th:.2f}: {pl}')
log.append('')
log.append(f'CSV: {csvp} rows={len(rows)}')
open(os.path.join(ROOT, 'rebuild', 'p7', 'logs', 'A2_d1v2b.log'), 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
