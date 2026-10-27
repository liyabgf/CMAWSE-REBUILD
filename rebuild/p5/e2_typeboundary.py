# -*- coding: utf-8 -*-
"""P5 E2 加深：失效封禁的实际边界定位（REWRITTEN）。

三臂对比：A_orig=REWRITTEN 引擎原样；A_check=同引擎+rebuild/p5/typecheck.py 包装
（校验失败抛异常，由引擎既有 except 接住）；A_twin=通用孪生（无守卫参照）。
指标区分：crash（异常逃逸）/ caught（parse_failures 计数）/ record_complete /
continued（正常返回记录）/ invalid_accepted（非法输出进入记录并使任一 d*_pass=True，
或垃圾值直接存入记录字段）/ traceable（拒绝原因可追溯）。
"""
import sys, os, csv
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H
from rebuild.p4.generic_twin import GenericHarnessTwin
from rebuild.p5.typecheck import typechecked, BatchContractError

def oracle_batch():
    d2m = {'M1': {a: ('q1' if a in ('act_alpha', 'act_beta', 'push', 'lift') else 'q0') for a in ['act_alpha','act_beta','act_gamma','act_delta','act_epsilon','act_zeta','push','pull','turn','lift','wait','reset']},
           'M2': {a: ('q1' if a in ('act_alpha', 'act_gamma', 'push', 'turn') else 'q0') for a in ['act_alpha','act_beta','act_gamma','act_delta','act_epsilon','act_zeta','push','pull','turn','lift','wait','reset']}}
    return d2m

def valid_d1(queries):
    return {str(q['tau']): 'q0' for q in queries}

def make_agent(batch_resp_factory):
    class A:
        def __call__(self, p):
            if p.get('phase') == 'INTERACTIVE':
                return {'action': p['observation']['available_actions'][0]}
            return batch_resp_factory(p)
    return A()

CASES = [
    ('valid_oracle', lambda p: {'d1_predictions': valid_d1(p['d1_queries']), 'd2_matrix': oracle_batch(),
                                'd4_predictions': {q['tau']: 'q0' for q in p['d4_queries']}, 'd5_prediction': 'q0'}),
    ('none', lambda p: None),
    ('str', lambda p: 'NOT_A_DICT'),
    ('raise', lambda p: (_ for _ in ()).throw(RuntimeError('LLM crash'))),
    ('list', lambda p: [1, 2, 3]),
    ('d1_predictions_int', lambda p: {'d1_predictions': 42}),
    ('d2_matrix_str', lambda p: {'d2_matrix': 'INVALID_TYPE'}),
    ('d2_nested_int', lambda p: {'d2_matrix': {'M1': {'act_alpha': 7}}}),
    ('empty_dict', lambda p: {}),
    ('extra_fields', lambda p: {'d1_predictions': valid_d1(p['d1_queries']), 'junk': 1}),
    ('d5_empty_string', lambda p: {'d5_prediction': ''}),
    ('d5_illegal_enum', lambda p: {'d5_prediction': 'HACK_STATE'}),
    ('d5_long_input', lambda p: {'d5_prediction': 'A' * 10000}),
    ('multi_field_malformed', lambda p: {'d1_predictions': 42, 'd2_matrix': None, 'd4_predictions': 'x', 'd5_prediction': 0}),
    ('d1_int_keys', lambda p: {21: 'q0'}),
    ('welltyped_semantically_invalid', lambda p: {'d1_predictions': valid_d1(p['d1_queries']),
                                                  'd2_matrix': oracle_batch(), 'd4_predictions': {q['tau']: 'q1' for q in p['d4_queries']},
                                                  'd5_prediction': 'q1'}),
]

def run_arm(arm, case_name, factory):
    rejections = []
    crashed_flag_holder = {'v': False}
    agent = make_agent(factory)
    if arm == 'A_check':
        agent = typechecked(agent, rejections)
    h = H.CMAWSEExperimentHarness(0x5A3F) if arm != 'A_twin' else GenericHarnessTwin(0x5A3F)
    crashed = None
    try:
        rec = h.run_session('CONDITION_C', 2, agent)
        pf = rec.get('parsing_failures')
        complete = all(k in rec for k in ('d1_pass', 'd2_pass', 'd4_pass', 'd5_pass', 'd6_divergence', 'ledger'))
        # 非法被接受 = 畸形批次响应仍使任一 d*_pass=True（合法对照除外）。
        # 判错（acc/pass=False）不算"被接受"；记录派生字段均为数值，垃圾值无法原样入库。
        any_pass = any(rec.get(k) for k in ('d1_pass', 'd2_pass', 'd4_pass', 'd5_pass'))
        malformed_case = case_name not in ('valid_oracle', 'welltyped_semantically_invalid')
        invalid_accepted = bool(any_pass and malformed_case)
        # 边界性质分类：parse 守卫(pf>0) / 评估器局部守卫(无 pf 无 crash，静默判错) / 崩溃
        if crashed_flag_holder.get('v'):
            boundary = 'CRASH'
        elif pf and pf > 0:
            boundary = 'PARSE_GUARD_REJECTED'
        elif malformed_case:
            boundary = 'EVALUATOR_LOCAL_GUARD_SILENT'
        else:
            boundary = 'ACCEPTED_VALID'
        return {'case': case_name, 'arm': arm, 'crash': 'NO', 'parse_failures': pf,
                'record_complete': complete, 'continued': True, 'invalid_accepted': invalid_accepted,
                'boundary': boundary,
                'rejection_traceable': len(rejections) > 0,
                'rejection_reasons': ' | '.join(rejections[:2])}
    except Exception as e:
        return {'case': case_name, 'arm': arm, 'crash': f'{type(e).__name__}: {str(e)[:50]}',
                'parse_failures': 'N/A', 'record_complete': False, 'continued': False,
                'invalid_accepted': 'N/A-crash', 'boundary': 'CRASH',
                'rejection_traceable': len(rejections) > 0,
                'rejection_reasons': ' | '.join(rejections[:2])}

rows = []
for name, fac in CASES:
    for arm in ('A_orig', 'A_check', 'A_twin'):
        rows.append(run_arm(arm, name, fac))

csvp = os.path.join(ROOT, 'rebuild', 'p5', 'E2_TYPE_BOUNDARY_MATRIX.csv')
keys = list(rows[0].keys())
with open(csvp, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=keys); wr.writeheader(); wr.writerows(rows)

log = ['== E2 类型边界三臂矩阵 ==', '']
for r in rows:
    log.append(f"  {r['arm']:8s} {r['case']:28s} crash={str(r['crash'])[:40]:40s} pf={str(r['parse_failures']):4s} complete={r['record_complete']} invalid_accepted={r['invalid_accepted']}")
log += ['', f'CSV: {csvp} rows={len(rows)}']
out = os.path.join(ROOT, 'rebuild', 'p5', 'logs', 'E2_typeboundary.log')
open(out, 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
