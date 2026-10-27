# -*- coding: utf-8 -*-
"""P6-A：D6 鉴别力实验（REWRITTEN d6v2，判据见 P6_PLAN.md，已冻结）。

关键设计事实（先核实后使用）：引擎 _apply_bijective_permutation 对整个 payload
（含 context_history）递归施加标签双射 σ；因此"从 payload 自带历史学表"的主体天然
等变，而"按字面规则查标签"的主体（如 v7 oracle 的 A/B 死分支）不具备等变性——
v7 测试中 oracle d6=0 来自 holdout 退化下的恒定输出（P4/P5 已证），非真实等变。
"""
import sys, os, csv, random, copy
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H

class Explorer:
    """交互阶段用 v7 oracle 探索策略，产生含 (A,act_beta)/(B,act_gamma)/(C,*) 键的账本。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            obs = p['observation']; obj = obs['focal_object']
            if obj in ('door', 'A'):
                act = 'lift' if 'lift' in obs['available_actions'] else 'act_beta'
            elif obj in ('cabinet', 'B'):
                act = 'turn' if 'turn' in obs['available_actions'] else 'act_gamma'
            else:
                act = obs['available_actions'][0]
            return {'action': act}
        return {}

def balanced_queries(world):
    """REWRITTEN 平衡 holdout：3×(A,act_beta)→q1, 3×(B,act_gamma)→q2, 3×(C,act_alpha)→q0。"""
    A, B, C = world.objects[0], world.objects[1], world.objects[2]
    ab, ag, aa = world.actions[1], world.actions[2], world.actions[0]
    qs = []
    for i in range(3):
        qs.append({'tau': 21 + i, 'q': world.states[0], 'X': A, 'K': world.train_contexts[0], 'act': ab})
        qs.append({'tau': 24 + i, 'q': world.states[0], 'X': B, 'K': world.train_contexts[0], 'act': ag})
        qs.append({'tau': 27 + i, 'q': world.states[0], 'X': C, 'K': world.train_contexts[0], 'act': aa})
    for q in qs:
        q['true_label'] = H.ground_truth_transition('CONDITION_C', q['q'], q['X'], q['K'], q['act'])
    return qs

# ---------------- 六类对照主体 ----------------
class LearnTable:
    """1 正确等变：从 payload 自带 context_history 学 (object,action)->y 表 + 首现序全局回退。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return Explorer()(p)
        hist = p.get('context_history', [])
        table, counts, order = {}, {}, []
        for s in hist:
            y = s['next_state']
            if y not in counts:
                order.append(y)
            counts[y] = counts.get(y, 0) + 1
            table[(s['object'], s['action'])] = y
        gm = max(order, key=lambda k: counts[k]) if order else 'q0'
        # v2 subject (post-hoc agent fix, disclosed): fallback = X-marginal mode (label-sensitive),
        # so predictions always depend on the query labels -> fully equivariant subject.
        x_counts = {}
        for s2 in hist:
            x_counts.setdefault(s2['object'], []).append(s2['next_state'])
        x_mode = {x: max(set(ys), key=ys.count) for x, ys in x_counts.items()}
        preds = {}
        for q in p.get('d1_queries', []):
            preds[str(q['tau'])] = table.get((q['X'], q['act']), x_mode.get(q['X'], gm))
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class Constant:
    """2 恒定输出。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return Explorer()(p)
        return {'d1_predictions': {str(q['tau']): 'q0' for q in p.get('d1_queries', [])},
                'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class TauKeyed:
    """3 输入无响应：只按 tau 奇偶输出，与 X/act 无关。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return Explorer()(p)
        preds = {str(q['tau']): ('q0' if q['tau'] % 2 == 0 else 'q1') for q in p.get('d1_queries', [])}
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class WrongMap:
    """4 错误方向响应：对正确答案施加错误置换 τ（q1<->q2）。"""
    TAU = {'q1': 'q2', 'q2': 'q1', 'q0': 'q0'}
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return Explorer()(p)
        base = LearnTable()(p)['d1_predictions']
        preds = {k: self.TAU.get(v, v) for k, v in base.items()}
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class IrrelevantResponsive:
    """5 无关扰动响应：答案正确，但对查询列表位置敏感（前半正确、后半给错标签）。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return Explorer()(p)
        base = LearnTable()(p)['d1_predictions']
        qs = p.get('d1_queries', [])
        preds = {}
        for i, q in enumerate(qs):
            v = base[str(q['tau'])]
            preds[str(q['tau'])] = v if i < len(qs) // 2 else ('q2' if v != 'q2' else 'q1')
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class AntiEquivariant:
    """6 对抗：检测到置换 payload（历史首条 object != 'A'）即返回原始空间恒定值。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return Explorer()(p)
        hist = p.get('context_history', [])
        if hist and hist[0]['object'] != 'A':
            preds = {str(q['tau']): 'q0' for q in p.get('d1_queries', [])}
        else:
            preds = LearnTable()(p)['d1_predictions']
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

AGENTS = [('learn_table_equivariant', LearnTable), ('constant_q0', Constant), ('tau_keyed_unresponsive', TauKeyed),
          ('wrong_map_response', WrongMap), ('irrelevant_position_response', IrrelevantResponsive),
          ('anti_equivariant', AntiEquivariant)]

def make_payload(session_idx):
    seed = H.derive_session_seed(0x5A3F, session_idx)
    world = H.DiscretePhysicalWorld('CONDITION_C', seed)
    ledger = []
    ex = Explorer()
    for t in range(21):
        obs = world.project_observation()
        act = ex({'phase': 'INTERACTIVE', 'observation': obs})['action']
        _, evt = world.step(act)
        ledger.append(evt)
    queries = balanced_queries(world)
    return {'phase': 'BATCH_EVALUATION', 'context_history': ledger, 'd1_queries': queries}, queries

def shuffled_payload(payload, seed=777):
    p2 = copy.deepcopy(payload)
    r = random.Random(seed)
    r.shuffle(p2['d1_queries'])
    return p2

def evaluate(agent_cls, payload):
    agent = agent_cls()
    p0 = copy.deepcopy(payload)
    p1 = H.CMAWSEExperimentHarness(0x5A3F)._apply_bijective_permutation(copy.deepcopy(payload))
    p2 = shuffled_payload(payload)
    preds0 = agent(copy.deepcopy(p0))['d1_predictions']
    raw1 = agent(copy.deepcopy(p1))['d1_predictions']
    inv1 = {k: H.D6_INVERSE_MAP.get(v, v) for k, v in raw1.items()}
    preds2 = agent(copy.deepcopy(p2))['d1_predictions']
    n = len(p0['d1_queries'])
    E = sum(1 for q in p0['d1_queries'] if preds0.get(str(q['tau'])) != inv1.get(str(q['tau']))) / n
    R = len(set(preds0.values())) >= 2
    I = all(preds0.get(str(q['tau'])) == preds2.get(str(q['tau'])) for q in p0['d1_queries'])
    acc = sum(1 for q in p0['d1_queries'] if preds0.get(str(q['tau'])) == q['true_label']) / n
    return {'E_div': E, 'R': R, 'I': I, 'acc': acc,
            'orig_d6_pass': E == 0.0, 'd6v2_pass': (E == 0.0) and R and I,
            'preds0': preds0, 'inv1': inv1}

def main():
    rows, log = [], ['== P6-A D6 鉴别力（判据已预注册冻结） ==', '']
    log.append(f"D6_BIJECTION_MAP 键数={len(H.D6_BIJECTION_MAP)}（用于置换 payload 的双射）")
    for setname, idx in [('tuning_s1', 1), ('heldout_s5', 5)]:
        payload, queries = make_payload(idx)
        log.append(f'--- {setname}: 账本 {len(payload["context_history"])} 条, holdout 真值分布 '
                   f'{ {y: sum(1 for q in queries if q["true_label"] == y) for y in ("q0","q1","q2")} } ---')
        for name, cls in AGENTS:
            r = evaluate(cls, payload)
            rows.append({'set': setname, 'agent': name,
                         'E_equivariance_div': r['E_div'], 'R_responsive': r['R'], 'I_order_invariant': r['I'],
                         'accuracy': r['acc'], 'orig_d6_pass': r['orig_d6_pass'], 'd6v2_pass': r['d6v2_pass']})
            log.append(f"  {name:28s} E={r['E_div']:.2f} R={int(r['R'])} I={int(r['I'])} acc={r['acc']:.2f} 原D6通过={int(r['orig_d6_pass'])} d6v2通过={int(r['d6v2_pass'])}")

    csvp = os.path.join(ROOT, 'rebuild', 'p6', 'D6_RESULTS.csv')
    with open(csvp, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k not in ('preds0', 'inv1')]); wr.writeheader(); wr.writerows(rows)
    log += ['', f'CSV: {csvp}', '',
            '冻结失败判据核对（留出集）：',
            f"  constant 通过 d6v2？ {[r['d6v2_pass'] for r in rows if r['set']=='heldout_s5' and r['agent']=='constant_q0'][0]} (必须 False)",
            f"  tau_keyed 通过 d6v2？ {[r['d6v2_pass'] for r in rows if r['set']=='heldout_s5' and r['agent']=='tau_keyed_unresponsive'][0]} (必须 False)",
            f"  learn_table 通过 d6v2？ {[r['d6v2_pass'] for r in rows if r['set']=='heldout_s5' and r['agent']=='learn_table_equivariant'][0]} (必须 True)"]
    open(os.path.join(ROOT, 'rebuild', 'p6', 'logs', 'A_d6.log'), 'w', encoding='utf-8').write(chr(10).join(log))
    print(chr(10).join(log))


if __name__ == "__main__":
    main()
