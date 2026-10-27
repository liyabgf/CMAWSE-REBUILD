# -*- coding: utf-8 -*-
"""P7-A1：d6v3 独立验证（REWRITTEN）。

独立集 s11/s13（grep 核实从未用于任何开发决策）；新主体类 6 个（未参与 P6 开发）；
分量必要性消融（E-only / E∧R2 / E∧I / R2∧I / full）；新目标变换 σ2（非 D6 映射）。
冻结判据见 P7_PLAN.md。
"""
import sys, os, csv, copy, random, json
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H
from rebuild.p6.a_d6 import LearnTable, Constant, TauKeyed, WrongMap, IrrelevantResponsive, AntiEquivariant, Explorer
from rebuild.p6.a_d6 import make_payload

PAIRS = [(0, 1), (1, 2), (0, 2)]  # 与 P6 a_d6v3 冻结定义一致（本地化实现，不 import 避免重跑历史实验）
def exchange_payloads(payload):
    out = []
    for i, j in PAIRS:
        pp = copy.deepcopy(payload)
        for k in ('X', 'act'):
            pp['d1_queries'][i][k], pp['d1_queries'][j][k] = pp['d1_queries'][j][k], pp['d1_queries'][i][k]
        out.append((pp, i, j))
    return out

# ---------- 新主体类（P7，未参与开发） ----------

class PartialTargetResponder:
    """对部分目标标签正确响应（硬编码原空间表），无全局等变结构。"""
    def __call__(self, p):
        preds = {}
        for q in p.get('d1_queries', []):
            if q['X'] == 'A' and q['act'] == 'act_beta':
                preds[str(q['tau'])] = 'q1'
            elif q['X'] == 'B' and q['act'] == 'act_gamma':
                preds[str(q['tau'])] = 'q2'
            else:
                preds[str(q['tau'])] = 'q1'
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class SeenCorrectUnseenFail:
    """已见组合正确（表学习），未见组合退化为固定 q0（对标签不敏感）。"""
    def __call__(self, p):
        table = {}
        for s in p.get('context_history', []):
            table[(s['object'], s['action'])] = s['next_state']
        preds = {str(q['tau']): table.get((q['X'], q['act']), 'q0') for q in p.get('d1_queries', [])}
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class OrderSensitiveEquivariant:
    """I 分量必要性探针（重设计）：标签空间无关（表学习 -> E=0、R2 应过），
    但当列表位置与 tau 规范秩不一致时翻转 q1/q2 -> 顺序打乱下失败（I=0）。
    若 E_R2 配置（去掉 I）放行此类主体，则证明 I 分量必要。"""
    def __call__(self, p):
        hist = p.get('context_history', [])
        table = {}
        x_counts = {}
        for s2 in hist:
            table[(s2['object'], s2['action'])] = s2['next_state']
            x_counts.setdefault(s2['object'], []).append(s2['next_state'])
        x_mode = {x: max(set(ys), key=ys.count) for x, ys in x_counts.items()}
        # 翻转对（取历史值集前两个，标签空间无关 -> 与任意全局双射交换）
        vals = sorted(set(s2['next_state'] for s2 in hist))
        fa, fb = (vals[0], vals[1]) if len(vals) >= 2 else (None, None)
        # 顺序条件（结构性，tau 在双射下不变 -> E=0；交换探针保序 -> R2=1；乱序破坏 -> I=0）
        qsl = p.get('d1_queries', [])
        do_flip = bool(qsl) and qsl[0]['tau'] == min(q['tau'] for q in qsl)
        preds = {}
        for q in qsl:
            v = table.get((q['X'], q['act']), x_mode.get(q['X'], 'q0'))
            if do_flip:
                if v == fa:
                    v = fb
                elif v == fb:
                    v = fa
            preds[str(q['tau'])] = v
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class RangeLimitedDegrade:
    """仅 A 组正确（等变于 A），B/C 越界退化为 q0。R2 在 B/C 对上失败。"""
    def __call__(self, p):
        preds = {}
        for q in p.get('d1_queries', []):
            if q['X'] == 'A':
                v = 'q1' if q['act'] == 'act_beta' else 'q0'
            else:
                v = 'q0'
            preds[str(q['tau'])] = H.D6_INVERSE_MAP.get(v, v)
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class TauHashRich:
    """输出变化丰富（tau 哈希）但与目标字段无关。E=0(直通), I=1, R2=0。"""
    def __call__(self, p):
        labels = ['q0', 'q1', 'q2']
        preds = {}
        for q in p.get('d1_queries', []):
            preds[str(q['tau'])] = labels[hash(q['tau']) % 3]
        return {'d1_predictions': preds, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class MemoizerGaming:
    """投机：首次调用缓存预测，后续调用一律返回缓存（试图骗过 E/I，必被 R2 击穿）。"""
    def __init__(self):
        self._cache = None
    def __call__(self, p):
        if self._cache is None:
            table = {}
            for s in p.get('context_history', []):
                table[(s['object'], s['action'])] = s['next_state']
            self._cache = {str(q['tau']): table.get((q['X'], q['act']), 'q0') for q in p.get('d1_queries', [])}
        return {'d1_predictions': dict(self._cache), 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

# ---------- 组件度量 ----------

def equivariance(agent, payload, perm_fn):
    p0 = copy.deepcopy(payload)
    p1 = perm_fn(payload)
    r0 = agent(copy.deepcopy(p0))['d1_predictions']
    r1 = agent(copy.deepcopy(p1))['d1_predictions']
    inv = H.D6_INVERSE_MAP
    total = len(r0)
    bad = 0
    for k, v in r0.items():
        v1 = r1.get(k, v)
        if inv.get(v1, v1) != v:
            bad += 1
    return bad / total if total else 0.0

def permute_with_d6(payload):
    return H.CMAWSEExperimentHarness(0x5A3F)._apply_bijective_permutation(payload)

# σ2：另一套目标变换（对象循环置换 + 动作反置；状态原样——验证 E 对任意双射的泛化）
SIGMA2_OBJ = {'A': 'C', 'B': 'A', 'C': 'B'}
SIGMA2_ACT = {'act_alpha': 'act_zeta', 'act_beta': 'act_epsilon', 'act_gamma': 'act_delta',
              'act_delta': 'act_gamma', 'act_epsilon': 'act_beta', 'act_zeta': 'act_alpha'}

def _perm2(v):
    if isinstance(v, dict):
        return {SIGMA2_OBJ.get(k, SIGMA2_ACT.get(k, k)): _perm2(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_perm2(x) for x in v]
    return SIGMA2_OBJ.get(v, SIGMA2_ACT.get(v, v))

def permute_with_sigma2(payload):
    return _perm2(payload)

def inverse2(v):
    for d in (SIGMA2_OBJ, SIGMA2_ACT):
        for a, b in d.items():
            if b == v:
                return a
    return v

def equivariance_sigma2(agent, payload):
    p0 = copy.deepcopy(payload)
    p1 = permute_with_sigma2(payload)
    r0 = agent(copy.deepcopy(p0))['d1_predictions']
    r1 = agent(copy.deepcopy(p1))['d1_predictions']
    total = len(r0); bad = 0
    for k, v in r0.items():
        if inverse2(r1.get(k, v)) != v:
            bad += 1
    return bad / total if total else 0.0

def exchange_response(agent, payload):
    p0 = copy.deepcopy(payload)
    preds0 = agent(copy.deepcopy(p0))['d1_predictions']
    def qi(i): return str(payload['d1_queries'][i]['tau'])
    ok = True
    for pe, i, j in exchange_payloads(payload):
        pe_preds = agent(copy.deepcopy(pe))['d1_predictions']
        if preds0.get(qi(i)) == preds0.get(qi(j)):
            ok = False; continue
        if pe_preds.get(qi(i)) != preds0.get(qi(j)) or pe_preds.get(qi(j)) != preds0.get(qi(i)):
            ok = False
    return 1 if ok else 0

def order_invariance(agent, payload):
    p0 = copy.deepcopy(payload)
    p1 = copy.deepcopy(payload)
    random.Random(777).shuffle(p1['d1_queries'])
    r0 = agent(copy.deepcopy(p0))['d1_predictions']
    r1 = agent(copy.deepcopy(p1))['d1_predictions']
    return 1 if r0 == r1 else 0

def accuracy(agent, payload):
    r = agent(copy.deepcopy(payload))['d1_predictions']
    qs = payload['d1_queries']
    return sum(1 for q in qs if r.get(str(q['tau'])) == q.get('true_label')) / len(qs)

VARIANTS = ['E_only', 'E_R2', 'E_I', 'R2_I', 'full']

def verdict(E, R2, I, variant):
    if variant == 'E_only':
        return 1 if E == 0 else 0
    if variant == 'E_R2':
        return 1 if (E == 0 and R2) else 0
    if variant == 'E_I':
        return 1 if (E == 0 and I) else 0
    if variant == 'R2_I':
        return 1 if (R2 and I) else 0
    return 1 if (E == 0 and R2 and I) else 0

SUBJECTS = [
    ('learn_table(P6)', LearnTable), ('constant_q0(P6)', Constant), ('tau_keyed(P6)', TauKeyed),
    ('wrong_map(P6)', WrongMap), ('irrelevant_position(P6)', IrrelevantResponsive), ('anti_equivariant(P6)', AntiEquivariant),
    ('partial_target_responder(P7)', PartialTargetResponder), ('seen_correct_unseen_fail(P7)', SeenCorrectUnseenFail),
    ('order_sensitive_equivariant(P7)', OrderSensitiveEquivariant), ('range_limited_degrade(P7)', RangeLimitedDegrade),
    ('tau_hash_rich(P7)', TauHashRich), ('memoizer_gaming(P7)', MemoizerGaming),
]

rows, log = [], ['== P7-A1 d6v3 独立验证（s11/s13，冻结） ==', '']
for sid in (11, 13):
    payload, _qs = make_payload(sid)
    log.append(f'--- session {sid} ---')
    for name, cls in SUBJECTS:
        ag = cls()
        E = equivariance(ag, payload, permute_with_d6)
        E2 = equivariance_sigma2(ag, payload)
        R2 = exchange_response(ag, payload)
        I = order_invariance(ag, payload)
        acc = accuracy(ag, payload)
        rec = {'set': f's{sid}', 'subject': name, 'E_d6': round(E, 3), 'E_sigma2': round(E2, 3),
               'R2': R2, 'I': I, 'acc': round(acc, 3)}
        for v in VARIANTS:
            rec['verdict_' + v] = verdict(E, R2, I, v)
        rows.append(rec)
        log.append(f"  {name:32s} E={E:.2f} E2={E2:.2f} R2={R2} I={I} acc={acc:.2f} full={rec['verdict_full']}")
    log.append('')

csvp = os.path.join(ROOT, 'rebuild', 'p7', 'D6V3_RESULTS.csv')
with open(csvp, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)

# 分量必要性汇总
log.append('分量消融（每配置误通过主体：定义上不应通过者通过）:')
expect_fail = {'constant_q0(P6)', 'tau_keyed(P6)', 'wrong_map(P6)', 'irrelevant_position(P6)', 'anti_equivariant(P6)',
               'partial_target_responder(P7)', 'order_sensitive_equivariant(P7)', 'range_limited_degrade(P7)',
               'tau_hash_rich(P7)', 'memoizer_gaming(P7)'}
for v in VARIANTS:
    fps = sorted(set(r['subject'] for r in rows if r['verdict_' + v] == 1 and r['subject'] in expect_fail))
    log.append(f'  {v:8s}: 误通过 {len(fps)} 类 -> {fps}')
log.append('')
log.append('CSV: ' + csvp)
open(os.path.join(ROOT, 'rebuild', 'p7', 'logs', 'A1_d6v3.log'), 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
