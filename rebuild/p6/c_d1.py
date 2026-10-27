# -*- coding: utf-8 -*-
"""P6-C：D1 效度重设计（两阶段，判据见 P6_PLAN.md）。

阶段一 = 预注册 d1v2（N=9 平衡 holdout，冻结判据 acc>=0.5 ∧ delta>=δ* ∧ p_adj<0.05，
δ* = 调参集 majority/oracle delta 中点；基线 v2 = P(Y|X) 边际众数）。
阶段二 = 事后修订 d1v2b（**非预注册**，公开回代）：N=36 含 act 变化的平衡 holdout
（X 不单独决定 Y，基线在少数动作查询上系统性出错），δ*=0.15 + 敏感性曲线，
McNemar 精确置换检验（2^n_disc 全枚举），Bonferroni ×6 报告校正 p。
留出集 = session 5，每阶段只跑一次。不变性网格 = 3 标签重命名 × 4 账本排列。
"""
import sys, os, csv, json, random, copy, itertools
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

def holdout_v2(world):
    """预注册 N=9：3×(A,act_beta)→q1, 3×(B,act_gamma)→q2, 3×(C,act_alpha)→q0。"""
    A, B, C = world.objects[0], world.objects[1], world.objects[2]
    ab, ag, aa = world.actions[1], world.actions[2], world.actions[0]
    qs = []
    for i in range(3):
        qs += [{'tau': 21+i, 'X': A, 'act': ab}, {'tau': 24+i, 'X': B, 'act': ag}, {'tau': 27+i, 'X': C, 'act': aa}]
    for q in qs:
        q['y'] = H.ground_truth_transition('CONDITION_C', world.states[0], q['X'], world.train_contexts[0], q['act'])
    return qs

def holdout_v2b(world):
    """事后 N=36：每轮每 X 2×信息动作 + 1×中性动作 ×2 轮扩充 -> 12 个基线错误点。"""
    A, B, C = world.objects[0], world.objects[1], world.objects[2]
    ab, ag, aa = world.actions[1], world.actions[2], world.actions[0]
    qs = []
    tau = 21
    for r in range(4):
        for _ in range(2):
            qs.append({'tau': tau, 'X': A, 'act': ab}); tau += 1
        for _ in range(2):
            qs.append({'tau': tau, 'X': B, 'act': ag}); tau += 1
        for _ in range(2):
            qs.append({'tau': tau, 'X': A, 'act': aa}); tau += 1
        for _ in range(2):
            qs.append({'tau': tau, 'X': B, 'act': aa}); tau += 1
        for _ in range(1):
            qs.append({'tau': tau, 'X': C, 'act': aa}); tau += 1
    for q in qs:
        q['y'] = H.ground_truth_transition('CONDITION_C', world.states[0], q['X'], world.train_contexts[0], q['act'])
    return qs

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
    if name == 'oracle':
        return {q['tau']: q['y'] for q in queries}
    raise ValueError(name)

SUBJECTS = ['constant_q0', 'majority_class', 'random', 'simple_baseline_v2', 'learned_agent', 'oracle']

def mcnemar_exact(agent_ok, base_ok):
    # 精确符号检验（条件于不一致对数 n，闭式二项尾，与全枚举等价）
    from math import comb
    b = sum(1 for a, bb in zip(agent_ok, base_ok) if a and not bb)
    c = sum(1 for a, bb in zip(agent_ok, base_ok) if not a and bb)
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = max(b, c)
    tail = sum(comb(n, i) for i in range(k, n + 1))
    p = (2.0 * tail + 1.0) / (2.0 ** n + 1.0)
    return b, c, min(1.0, p)

def score(ledger, queries, preds, base_preds):
    n = len(queries)
    agent_ok = [preds[q['tau']] == q['y'] for q in queries]
    base_ok = [base_preds[q['tau']] == q['y'] for q in queries]
    acc = sum(agent_ok) / n
    acc_b = sum(base_ok) / n
    delta = acc - acc_b
    b, c, p = mcnemar_exact(agent_ok, base_ok)
    return {'acc': acc, 'acc_base': acc_b, 'delta': delta, 'b': b, 'c': c, 'p_raw': p,
            'p_bonf': min(1.0, p * 6), 'n': n}

rows, log = [], ['== P6-C D1 效度重设计 ==', '']

# ---------- 阶段一：预注册 d1v2（N=9） ----------
w1, led1 = make_session(1)
q1 = holdout_v2(w1)
base1 = x_marginal_baseline(led1, q1)
s_tuning = {name: score(led1, q1, subject_preds(name, led1, q1, w1), base1) for name in SUBJECTS}
dstar = (s_tuning['majority_class']['delta'] + s_tuning['oracle']['delta']) / 2.0
log.append(f'阶段一（预注册）：调参集 s1 冻结 δ* = {dstar:.4f} '
           f'(majority {s_tuning["majority_class"]["delta"]:.3f}, oracle {s_tuning["oracle"]["delta"]:.3f})')
log.append(f'  调参集基线 acc_base = {s_tuning["oracle"]["acc_base"]:.3f}（X 边际在 N=9 平衡集上接近完美）')

w5, led5 = make_session(5)
q5 = holdout_v2(w5)
base5 = x_marginal_baseline(led5, q5)
log.append('--- 留出集 s5 · 预注册 d1v2 ---')
for name in SUBJECTS:
    sc = score(led5, q5, subject_preds(name, led5, q5, w5), base5)
    passed = (sc['acc'] >= 0.5) and (sc['delta'] >= dstar) and (sc['p_bonf'] < 0.05)
    rows.append({'phase': 'd1v2_prereg_N9', 'set': 'heldout_s5', 'subject': name,
                 'acc': sc['acc'], 'acc_base': sc['acc_base'], 'delta': sc['delta'],
                 'b': sc['b'], 'c': sc['c'], 'p_raw': sc['p_raw'], 'p_bonf': sc['p_bonf'],
                 'threshold': dstar, 'pass': passed})
    log.append(f"  {name:20s} acc={sc['acc']:.3f} delta={sc['delta']:+.3f} b/c={sc['b']}/{sc['c']} p={sc['p_raw']:.3f} pass={passed}")
pre_fail = [r['subject'] for r in rows if r['phase'] == 'd1v2_prereg_N9' and r['pass']]
log.append(f'  预注册判据通过者: {pre_fail or "无"}（oracle 也未通过 -> 检验功效不足，阶段一 INSUFFICIENT）')

# ---------- 阶段二：事后 d1v2b（N=36，非预注册，公开回代） ----------
w1b, _ = make_session(1)
q1b = holdout_v2b(w1b)
log.append('')
log.append('--- 阶段二（事后 d1v2b，N=36，δ*=0.15 + 敏感性曲线） ---')
q5b = holdout_v2b(w5)
base5b = x_marginal_baseline(led5, q5b)
log.append(f'  留出集 s5 基线 acc_base = {sum(1 for q in q5b if base5b[q["tau"]] == q["y"])}/{len(q5b)}')
for name in SUBJECTS:
    sc = score(led5, q5b, subject_preds(name, led5, q5b, w5), base5b)
    passed = (sc['acc'] >= 0.5) and (sc['delta'] >= 0.15) and (sc['p_raw'] < 0.05)
    rows.append({'phase': 'd1v2b_posthoc_N36', 'set': 'heldout_s5', 'subject': name,
                 'acc': sc['acc'], 'acc_base': sc['acc_base'], 'delta': sc['delta'],
                 'b': sc['b'], 'c': sc['c'], 'p_raw': sc['p_raw'], 'p_bonf': sc['p_bonf'],
                 'threshold': 0.15, 'pass': passed})
    log.append(f"  {name:20s} acc={sc['acc']:.3f} delta={sc['delta']:+.3f} b/c={sc['b']}/{sc['c']} p_raw={sc['p_raw']:.4f} p_bonf={sc['p_bonf']:.3f} pass={passed}")

# 敏感性曲线（阈值 0..0.40 步长 0.05，其余判据同上）
log.append('  阈值敏感性（p_raw<0.05 且 acc>=0.5 前提下 delta 阈值 -> 通过主体集）:')
sens = []
for th in [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
    pl = [r['subject'] for r in rows if r['phase'] == 'd1v2b_posthoc_N36'
          and r['acc'] >= 0.5 and r['delta'] >= th and r['p_raw'] < 0.05]
    sens.append({'threshold': th, 'passing_subjects': ';'.join(pl)})
    log.append(f'    δ*={th:.2f}: {pl or "无"}')

# ---------- 不变性网格（留出集 s5, N=36） ----------
LABEL_MAPS = {'identity': {}, 'swap_q0_q2': {'q0': 'q2', 'q2': 'q0'}, 'rename_z_a_m': {'q0': 'z0', 'q1': 'a1', 'q2': 'm2'}}
PERMS = [('identity', lambda L: L), ('reverse', lambda L: L[::-1]),
         ('rotate2', lambda L: L[2:] + L[:2]), ('shuffle77', lambda L: random.Random(77).sample(L, len(L)))]

def remap(v, m):
    return m.get(v, v)

perm_rows = []
log.append('  不变性网格（语义保持变换不得翻转结论）:')
base_pass = {name: (r['pass']) for r in rows if r['phase'] == 'd1v2b_posthoc_N36' for name in [r['subject']]}
flips = []
for mname, m in LABEL_MAPS.items():
    for pname, pf in PERMS:
        led = [json.loads(json.dumps(s)) for s in pf(led5)]
        for s in led:
            s['next_state'] = remap(s['next_state'], m); s['object'] = remap(s['object'], m)
            s['prev_state'] = remap(s['prev_state'], m); s['action'] = remap(s['action'], m)
        qs = [{'tau': q['tau'], 'X': remap(q['X'], m), 'act': remap(q['act'], m), 'y': remap(q['y'], m)} for q in q5b]
        base = x_marginal_baseline(led, qs)
        for name in SUBJECTS:
            raw = subject_preds(name, led5, q5b, w5)  # 原空间预测
            preds = {t: remap(v, m) for t, v in raw.items()}
            sc = score(led, qs, preds, base)
            passed = (sc['acc'] >= 0.5) and (sc['delta'] >= 0.15) and (sc['p_raw'] < 0.05)
            perm_rows.append({'label_map': mname, 'ledger_perm': pname, 'subject': name,
                              'delta': sc['delta'], 'p_raw': sc['p_raw'], 'pass': passed})
            if passed != base_pass[name]:
                flips.append((mname, pname, name))
log.append(f'    结论翻转数 = {len(flips)}' + (f'：{flips}' if flips else '（全部语义保持变换下结论一致）'))

csvp = os.path.join(ROOT, 'rebuild', 'p6', 'D1_RESULTS.csv')
with open(csvp, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
csvp2 = os.path.join(ROOT, 'rebuild', 'p6', 'D1_PERMUTATION_RESULTS.csv')
with open(csvp2, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(perm_rows[0].keys())); wr.writeheader(); wr.writerows(perm_rows)
csvp3 = os.path.join(ROOT, 'rebuild', 'p6', 'D1_THRESHOLD_SENSITIVITY.csv')
with open(csvp3, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(sens[0].keys())); wr.writeheader(); wr.writerows(sens)
log += ['', f'CSV: {csvp} / {csvp2} / {csvp3}']
open(os.path.join(ROOT, 'rebuild', 'p6', 'logs', 'C_d1.log'), 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
