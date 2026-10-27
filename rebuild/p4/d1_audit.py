# -*- coding: utf-8 -*-
"""P4-B: D1 评估器效度审计（REWRITTEN 审计脚本，只读使用 rebuild/out 引擎）。

标记：REWRITTEN（审计代码，非档案材料）。被审对象：
- extracted/phase2/harness_v6_L61914.py 的 evaluate_d1（EXTRACTED，字母序平局）
- rebuild/out 引擎的 evaluate_d1（REWRITTEN，首次出现序平局）

实验维度：
- ledger 顺序置换（恒等/反转/旋转/固定种子洗牌）——不改变计数，只改变顺序
- 标签重命名/置换——不改变语义，只改变名字的字母序
- 平局状态对照（真实 7/7/7、构造 8/7/6、构造三方平局异序、构造两方平局）
- 主体策略：oracle（全对）、naive_q0（恒 q0）、adversarial（恒错）、random(seeded)
- 基线规则：alpha（v6 档案版）、first（P3 版）、last（末次出现序，对照用）

核心问题：D1 的判定是否依赖与任务语义无关的排列/命名？
"""
import sys, os, csv, json, copy

ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H

OUT = os.path.join(ROOT, 'rebuild', 'p4')
LOG = os.path.join(OUT, 'logs', 'd1_audit.log')


# ---------- 独立重建：不调用 run_session，直接驱动世界 ----------
class OracleAgent:
    """v7 测试原版 oracle 策略（EXTRACTED 语义）。"""
    def __call__(self, payload):
        ph = payload.get('phase')
        if ph == 'INTERACTIVE':
            obs = payload['observation']; obj = obs['focal_object']
            if obj in ('door', 'A'):
                act = 'lift' if 'lift' in obs['available_actions'] else 'act_beta'
            elif obj in ('cabinet', 'B'):
                act = 'turn' if 'turn' in obs['available_actions'] else 'act_gamma'
            else:
                act = obs['available_actions'][0]
            return {'action': act}
        return {}


def build_ledger_and_holdout(master_seed, session_idx, condition='CONDITION_C'):
    """独立重演 Phase-1 交互与 Phase-2 holdout 构造（与 run_session 相同的确定公式）。"""
    seed = H.derive_session_seed(master_seed, session_idx)
    world = H.DiscretePhysicalWorld(condition, seed)
    ledger = []
    for t in range(21):
        obs = world.project_observation()
        act = OracleAgent()({'phase': 'INTERACTIVE', 'observation': obs})['action']
        next_q, evt = world.step(act)
        ledger.append(evt)
    queries = []
    for tau in range(21, 30):
        q_in = world.states[tau % len(world.states)]
        x_in = world.objects[(tau * 2) % len(world.objects)]
        k_in = world.train_contexts[(tau * 3) % len(world.train_contexts)]
        act_in = world.actions[(tau * 5) % len(world.actions)]
        queries.append({'tau': tau, 'q': q_in, 'X': x_in, 'K': k_in, 'act': act_in,
                        'true_label': H.ground_truth_transition(condition, q_in, x_in, k_in, act_in)})
    return ledger, queries


def relabel(x, mapping):
    return mapping.get(x, x) if isinstance(x, str) else x


def global_mode(ledger, rule, mapping):
    counts, order = {}, []
    for s in ledger:
        if s['status'] != 'COMMITTED':
            continue
        y = relabel(s['next_state'], mapping)
        if y not in counts:
            order.append(y)
        counts[y] = counts.get(y, 0) + 1
    if not counts:
        return relabel('q0', mapping), counts
    if rule == 'alpha':
        return max(sorted(counts.keys()), key=lambda k: counts[k]), counts
    if rule == 'first':
        return max(order, key=lambda k: counts[k]), counts
    if rule == 'last':
        return max(reversed(order), key=lambda k: counts[k]), counts
    raise ValueError(rule)


def baseline_predictions(ledger, queries, rule, mapping):
    cond_counts = {}
    for s in ledger:
        if s['status'] != 'COMMITTED':
            continue
        key = (s['object'], s['action'])
        y = relabel(s['next_state'], mapping)
        cond_counts.setdefault(key, {})[y] = cond_counts.setdefault(key, {}).get(y, 0) + 1
    gm, _ = global_mode(ledger, rule, mapping)
    preds = {}
    for q in queries:
        ck = (q['X'], q['act'])
        if ck in cond_counts:
            c = cond_counts[ck]
            if rule == 'alpha':
                preds[q['tau']] = max(sorted(c.keys()), key=lambda k: c[k])
            elif rule == 'first':
                preds[q['tau']] = max(c.keys(), key=lambda k: c[k])   # dict 插入序
            else:
                preds[q['tau']] = max(reversed(list(c.keys())), key=lambda k: c[k])
        else:
            preds[q['tau']] = gm
    return preds, gm


def agent_predictions(strategy, queries, mapping, rng):
    preds = {}
    for q in queries:
        y = relabel(q['true_label'], mapping)
        if strategy == 'oracle':
            p = y
        elif strategy == 'naive_q0':
            p = relabel('q0', mapping)
        elif strategy == 'adversarial':
            p = 'MUTATED' if y != 'MUTATED' else 'OTHER'
        elif strategy == 'random':
            p = relabel(rng.choice(['q0', 'q1', 'q2']), mapping)
        preds[q['tau']] = p
    return preds


def permute(lst, kind, k=0, seed=0):
    import random
    c = list(lst)
    if kind == 'identity':
        return c
    if kind == 'reverse':
        return c[::-1]
    if kind == 'rotate':
        return c[k % len(c):] + c[:k % len(c)]
    if kind == 'shuffle':
        r = random.Random(seed)
        r.shuffle(c)
        return c
    raise ValueError(kind)


def main():
    log = []
    ledger_real, queries_real = build_ledger_and_holdout(0x5A3F, 1)
    # 交叉核对：与引擎 run_session 的记录一致性
    rec = H.CMAWSEExperimentHarness(0x5A3F).run_session('CONDITION_C', 1, OracleAgent())
    same = json.dumps(ledger_real, sort_keys=True) == json.dumps(rec['ledger'], sort_keys=True)
    gc = {}
    for s in ledger_real:
        if s['status'] == 'COMMITTED':
            gc[s['next_state']] = gc.get(s['next_state'], 0) + 1
    labels = sorted(set(q['true_label'] for q in queries_real))
    log.append('== 独立重建核对 ==')
    log.append(f'独立账本 == 引擎账本 (json 规范化): {same}')
    log.append(f'全局计数: {gc}')
    log.append(f'首次出现序: {[y for y in dict.fromkeys(s["next_state"] for s in ledger_real if s["status"]=="COMMITTED")]}')
    log.append(f'holdout 真值集合: {labels}  (全 q0: {labels == ["q0"]})')
    log.append(f'holdout (X,act) 键在条件计数中的覆盖: '
               f'{sum(1 for q in queries_real if (q["X"], q["act"]) in {(s["object"], s["action"]) for s in ledger_real})}/9')

    # 构造对照账本（同样的 (object,action) 键结构，不同的结果分布）
    def synth_ledger(dist):
        base = [s for s in ledger_real if s['status'] == 'COMMITTED']
        out = []
        for i, s in enumerate(base):
            t = copy.deepcopy(s)
            t['next_state'] = dist[i % len(dist)]
            out.append(t)
        return out
    ledger_notie = synth_ledger(['q1', 'q1', 'q1', 'q1', 'q1', 'q1', 'q1', 'q1', 'q2', 'q2', 'q2', 'q2', 'q2', 'q2', 'q2', 'q0', 'q0', 'q0', 'q0', 'q0', 'q0'])  # 8/7/6
    ledger_tie_q2first = synth_ledger(['q2', 'q1', 'q0'] * 7)  # 三方平局，q2 首现
    ledger_2tie = synth_ledger(['q1', 'q0', 'q1', 'q0', 'q1', 'q0', 'q1', 'q0', 'q1', 'q0', 'q1', 'q0', 'q1', 'q0', 'q0', 'q0', 'q0', 'q0', 'q0', 'q0', 'q0'])  # q1:7 q0:14 无平局? -> 调整
    ledger_2tie = synth_ledger(['q1'] * 7 + ['q0'] * 7 + ['q2'] * 7)[:14] + synth_ledger(['q0'] * 7)  # q1:7 q0:14 -> 2候选

    import random
    rng = random.Random(1234)

    label_maps = {
        'identity': {},
        'swap_q0_q2': {'q0': 'q2', 'q2': 'q0'},
        'rename_z_a_m': {'q0': 'z0', 'q1': 'a1', 'q2': 'm2'},
    }
    perms = [('identity', 0, 0), ('reverse', 0, 0), ('rotate', 1, 0), ('rotate', 3, 0),
             ('rotate', 5, 0), ('shuffle', 0, 11), ('shuffle', 0, 77)]
    scenarios = [('real_7_7_7', ledger_real), ('control_no_tie_8_7_6', ledger_notie),
                 ('control_3tie_q2first', ledger_tie_q2first), ('control_2cand', ledger_2tie)]
    strategies = ['oracle', 'naive_q0', 'adversarial', 'random']

    rows = []
    for sname, led in scenarios:
        for pname, k, seed in perms:
            pled = permute(led, pname, k, seed)
            for mname, mapping in label_maps.items():
                for rule in ['alpha', 'first', 'last']:
                    bp, gm = baseline_predictions(pled, queries_real, rule, mapping)
                    for st in strategies:
                        ap = agent_predictions(st, queries_real, mapping, rng)
                        acc_b = sum(1 for q in queries_real if bp[q['tau']] == relabel(q['true_label'], mapping)) / 9.0
                        acc_a = sum(1 for q in queries_real if ap[q['tau']] == relabel(q['true_label'], mapping)) / 9.0
                        delta = acc_a - acc_b
                        rows.append({
                            'scenario': sname, 'ledger_perm': f'{pname}' + (f'k{k}' if k else (f's{seed}' if pname == 'shuffle' else '')),
                            'label_map': mname, 'baseline_rule': rule, 'strategy': st,
                            'global_mode': gm, 'acc_agent': round(acc_a, 4), 'acc_base': round(acc_b, 4),
                            'delta': round(delta, 4), 'd1_pass': int(delta >= 0.15 and acc_a >= 0.5),
                        })
    csv_path = os.path.join(OUT, 'D1_SENSITIVITY_MATRIX.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    # 敏感性统计
    def verdict_set(st, rule, filt):
        return {r['d1_pass'] for r in rows if r['strategy'] == st and r['baseline_rule'] == rule and filt(r)}

    log.append('')
    log.append('== 敏感性分析 ==')
    real = lambda r: r['scenario'] == 'real_7_7_7'
    for st in strategies:
        for rule in ['alpha', 'first', 'last']:
            vs = verdict_set(st, rule, real)
            log.append(f'real 场景 strategy={st:12s} rule={rule:5s} -> d1_pass 取值集合 {sorted(vs)}'
                       f'{"  [排列/命名敏感]" if len(vs) > 1 else ""}')
    log.append('')
    log.append('关键对比（oracle, real 场景）: alpha 规则 d1_pass='
               f'{sorted(verdict_set("oracle", "alpha", real))}, first 规则 d1_pass={sorted(verdict_set("oracle", "first", real))}')
    log.append('naive_q0（恒 q0 主体）在 first 规则下 real 场景 d1_pass='
               f'{sorted(verdict_set("naive_q0", "first", real))} —— 若含 1 则 P3 修复未恢复区分度')

    log.append('')
    log.append(f'CSV: {csv_path}  rows={len(rows)}')
    open(LOG, 'w', encoding='utf-8').write(chr(10).join(log))
    print(chr(10).join(log))


if __name__ == '__main__':
    main()
