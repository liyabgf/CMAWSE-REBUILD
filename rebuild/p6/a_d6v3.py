# -*- coding: utf-8 -*-
"""P6-A 续：d6v3 事后修订版（**非预注册**——因预注册 d6v2 在留出集被 tau_keyed 反例击穿，
按 P6_PLAN 冻结判据 d6v2=INSUFFICIENT；本文件为公开的事后修订，并在从未使用过的
全新会话 s7 上验证，避免用设计集冒充留出集）。

d6v3 分量：
- E：全局双射置换下的等变性（既有算法；注意 INVERSE 只译 s 空间值，输出恒为
  原空间标签的主体 E 恒 0 —— 这是 v2 失效根因，也是原 D6 盲区的结构解释）。
- R2（标签交换响应性）：取两条 (X,act) 与真标签均不同的查询，交换其 (X,act) 标签
  （tau 位置不动），等变主体的预测必须随之交换。逐组配对检验。
- I：查询顺序不变性（同 v2）。
d6v3_pass = E ∧ R2 ∧ I。
"""
import sys, os, csv, random, copy
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
from rebuild.p6.a_d6 import (Explorer, balanced_queries, LearnTable, Constant, TauKeyed,
                             WrongMap, IrrelevantResponsive, AntiEquivariant, AGENTS, make_payload)
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H

PAIRS = [(0, 1), (1, 2), (0, 2)]  # 交错序：索引 0/1/2 = q1/q2/q0 组首条，组间对比

def exchange_payloads(payload):
    """每对独立构造交换 (X,act) 标签的 payload（避免重叠复合交换）。"""
    out = []
    for i, j in PAIRS:
        p = copy.deepcopy(payload)
        for k in ('X', 'act'):
            p['d1_queries'][i][k], p['d1_queries'][j][k] = p['d1_queries'][j][k], p['d1_queries'][i][k]
        out.append((p, i, j))
    return out

def evaluate3(agent_cls, payload):
    agent = agent_cls()
    p0 = copy.deepcopy(payload)
    p1 = H.CMAWSEExperimentHarness(0x5A3F)._apply_bijective_permutation(copy.deepcopy(payload))
    exchanges = exchange_payloads(payload)
    p2 = copy.deepcopy(payload)
    random.Random(777).shuffle(p2['d1_queries'])
    preds0 = agent(copy.deepcopy(p0))['d1_predictions']
    raw1 = agent(copy.deepcopy(p1))['d1_predictions']
    inv1 = {k: H.D6_INVERSE_MAP.get(v, v) for k, v in raw1.items()}
    preds_by_pair = {(i, j): agent(copy.deepcopy(pe))['d1_predictions'] for pe, i, j in exchanges}
    preds2 = agent(copy.deepcopy(p2))['d1_predictions']
    n = len(p0['d1_queries'])
    E = sum(1 for q in p0['d1_queries'] if preds0.get(str(q['tau'])) != inv1.get(str(q['tau']))) / n
    # v3b（第二轮事后修订）：交换前预测必须不同，否则交换检验对恒定主体空洞成立
    def qi(i):
        return str(p0['d1_queries'][i]['tau'])
    R2 = all(preds0.get(qi(i)) != preds0.get(qi(j))
             and preds_by_pair[(i, j)].get(qi(i)) == preds0.get(qi(j))
             and preds_by_pair[(i, j)].get(qi(j)) == preds0.get(qi(i))
             for i, j in PAIRS)
    I = all(preds0.get(str(q['tau'])) == preds2.get(str(q['tau'])) for q in p0['d1_queries'])
    acc = sum(1 for q in p0['d1_queries'] if preds0.get(str(q['tau'])) == q['true_label']) / n
    return {'E': E, 'R2': R2, 'I': I, 'acc': acc,
            'd6v3_pass': (E == 0.0) and R2 and I}

rows, log = [], ['== P6-A d6v3（事后修订，非预注册；含全新会话 s7 验证） ==', '']
for setname, idx in [('tuning_s1', 1), ('heldout_s5', 5), ('fresh_s7(never used before)', 7)]:
    payload, _ = make_payload(idx)
    log.append(f'--- {setname} ---')
    for name, cls in AGENTS:
        r = evaluate3(cls, payload)
        rows.append({'set': setname, 'agent': name, 'E_equivariance': r['E'],
                     'R2_label_exchange': r['R2'], 'I_order_invariant': r['I'],
                     'accuracy': r['acc'], 'd6v3_pass': r['d6v3_pass']})
        log.append(f"  {name:28s} E={r['E']:.2f} R2={int(r['R2'])} I={int(r['I'])} acc={r['acc']:.2f} d6v3={int(r['d6v3_pass'])}")

csvp = os.path.join(ROOT, 'rebuild', 'p6', 'D6_RESULTS_V3.csv')
with open(csvp, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
log += ['', f'CSV: {csvp}']
open(os.path.join(ROOT, 'rebuild', 'p6', 'logs', 'A_d6v3.log'), 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
