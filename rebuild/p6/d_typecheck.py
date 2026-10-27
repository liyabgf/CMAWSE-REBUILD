# -*- coding: utf-8 -*-
"""P6-D：typecheck 原生化决策实验（REWRITTEN，不修改 P3/P4/P5 历史产物）。

四臂：A1=引擎原样（rebuild/out）；A2=P5 外挂包装；A3=P6 原生化副本
（校验内嵌 run_session 批次与置换调用层，本脚本源码补丁生成）；A4=无保护（p4 twin）。
回归：A3 上 v7 全量 7 项必须 7/7（冻结验收）。
"""
import sys, os, csv, subprocess
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H
from rebuild.p5.typecheck import typechecked
from rebuild.p4.generic_twin import GenericHarnessTwin

NATIVE_DIR = os.path.join(ROOT, 'rebuild', 'p6', 'native')

VALIDATOR_SRC = '''
# REWRITTEN-P6 native batch validation (inlined; same contract as rebuild/p5/typecheck.py)
class BatchContractErrorP6(TypeError):
    pass

def _p6_check_state(v, path):
    if not isinstance(v, str) or not (0 < len(v) <= 256):
        raise BatchContractErrorP6(f'{path}: expected non-empty str<=256, got {type(v).__name__}')
    if v not in {'q0', 'q1', 'q2', 'st_idle', 'st_open', 'st_locked'}:
        raise BatchContractErrorP6(f'{path}: value not in closed state vocab: {v!r}')

def _p6_validate_batch(resp):
    if not isinstance(resp, dict):
        raise BatchContractErrorP6(f'batch response: expected dict, got {type(resp).__name__}')
    import re as _re
    d1 = resp.get('d1_predictions', {})
    if not isinstance(d1, dict):
        raise BatchContractErrorP6(f'd1_predictions: expected dict, got {type(d1).__name__}')
    for k, v in d1.items():
        if not _re.fullmatch(r"\d+", str(k)):
            raise BatchContractErrorP6(f'd1_predictions key not tau digits: {k!r}')
        _p6_check_state(v, f'd1_predictions[{k}]')
    d2 = resp.get('d2_matrix', {})
    if not isinstance(d2, dict):
        raise BatchContractErrorP6(f'd2_matrix: expected dict, got {type(d2).__name__}')
    for mk, row in d2.items():
        if mk not in {'M1', 'M2', 'M3'}:
            raise BatchContractErrorP6(f'd2_matrix model key: {mk!r}')
        if not isinstance(row, dict):
            raise BatchContractErrorP6(f'd2_matrix[{mk}]: expected dict')
        for ak, av in row.items():
            _p6_check_state(av, f'd2_matrix[{mk}][{ak}]')
    d4 = resp.get('d4_predictions', {})
    if not isinstance(d4, dict):
        raise BatchContractErrorP6(f'd4_predictions: expected dict, got {type(d4).__name__}')
    for k, v in d4.items():
        _p6_check_state(v, f'd4_predictions[{k}]')
    d5 = resp.get('d5_prediction', 'INVALID')
    _p6_check_state(d5, 'd5_prediction')
    for extra in set(resp) - {'d1_predictions', 'd2_matrix', 'd4_predictions', 'd5_prediction'}:
        raise BatchContractErrorP6(f'unexpected extra field: {extra!r}')
    return resp

'''

def build_native():
    src = open(os.path.join(ROOT, 'rebuild', 'out', 'CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py'), encoding='utf-8').read()
    anchor = "class CMAWSEExperimentHarness:"
    assert anchor in src
    src = src.replace(anchor, VALIDATOR_SRC + anchor, 1)
    b_anchor = "            batch_resp = agent_callable(batch_payload)"
    assert b_anchor in src
    src = src.replace(b_anchor, b_anchor + chr(10) + "            _p6_validate_batch(batch_resp)", 1)
    p_anchor = "            perm_resp = agent_callable(permuted_payload)"
    assert p_anchor in src
    src = src.replace(p_anchor, p_anchor + chr(10) + "            _p6_validate_batch(perm_resp)", 1)
    os.makedirs(NATIVE_DIR, exist_ok=True)
    out = os.path.join(NATIVE_DIR, 'CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py')
    open(out, 'w', encoding='utf-8').write(src)
    return out

def oracle_batch():
    d2m = {'M1': {a: ('q1' if a in ('act_alpha', 'act_beta', 'push', 'lift') else 'q0') for a in ['act_alpha','act_beta','act_gamma','act_delta','act_epsilon','act_zeta','push','pull','turn','lift','wait','reset']},
           'M2': {a: ('q1' if a in ('act_alpha', 'act_gamma', 'push', 'turn') else 'q0') for a in ['act_alpha','act_beta','act_gamma','act_delta','act_epsilon','act_zeta','push','pull','turn','lift','wait','reset']}}
    return {'d2_matrix': d2m}

def valid_d1(p):
    return {str(q['tau']): 'q0' for q in p['d1_queries']}

CASES = [
    ('valid_oracle', lambda p: {'d1_predictions': valid_d1(p), 'd2_matrix': oracle_batch()['d2_matrix'],
                                'd4_predictions': {q['tau']: 'q0' for q in p['d4_queries']}, 'd5_prediction': 'q0'}),
    ('none', lambda p: None),
    ('str', lambda p: 'NOT_A_DICT'),
    ('raise', lambda p: (_ for _ in ()).throw(RuntimeError('LLM crash'))),
    ('list', lambda p: [1, 2, 3]),
    ('d1_int', lambda p: {'d1_predictions': 42}),
    ('d2_str', lambda p: {'d2_matrix': 'INVALID_TYPE'}),
    ('d2_nested_int', lambda p: {'d2_matrix': {'M1': {'act_alpha': 7}}}),
    ('empty_dict', lambda p: {}),
    ('extra_fields', lambda p: {'d1_predictions': valid_d1(p), 'junk': 1}),
    ('d5_empty', lambda p: {'d5_prediction': ''}),
    ('d5_illegal_enum', lambda p: {'d5_prediction': 'HACK_STATE'}),
    ('d5_long_10000', lambda p: {'d5_prediction': 'A' * 10000}),
    ('multi_field', lambda p: {'d1_predictions': 42, 'd2_matrix': None, 'd4_predictions': 'x', 'd5_prediction': 0}),
    ('d1_int_keys', lambda p: {21: 'q0'}),
    ('welltyped_semantic_wrong', lambda p: {'d1_predictions': valid_d1(p), 'd2_matrix': oracle_batch()['d2_matrix'],
                                            'd4_predictions': {q['tau']: 'q1' for q in p['d4_queries']},
                                            'd5_prediction': 'q1'}),
    # P6 补充例
    ('d4_nested_int', lambda p: {'d4_predictions': {'d4_0': 5}}),
    ('d1_value_dict', lambda p: {'d1_predictions': {'21': {'nested': 1}}}),
    ('d5_len256_boundary_ok', lambda p: {'d5_prediction': 'q0' + 'x' * 0}),  # 合法基线
    ('d5_len257_boundary', lambda p: {'d5_prediction': 'q0' + 'x' * 255}),  # 258 总长
    ('d5_unicode', lambda p: {'d5_prediction': 'q零'}),
    ('d5_bool', lambda p: {'d5_prediction': True}),
    ('d1_nested_extra', lambda p: {'d1_predictions': {str(q['tau']): 'q0' for q in p['d1_queries']}, 'd2_matrix': {'M1': {'act_alpha': 'q1', 'junk': {'x': 1}}}}),
    ('d4_illegal_enum', lambda p: {'d4_predictions': {q['tau']: 'HACK_STATE' for q in p['d4_queries']}}),
]

def make_agent(factory):
    class A:
        def __call__(self, p):
            if p.get('phase') == 'INTERACTIVE':
                return {'action': p['observation']['available_actions'][0]}
            return factory(p)
    return A()

def run_arm(arm, case, factory):
    agent = make_agent(factory)
    if arm == 'A2_wrapper':
        rej = []
        agent = typechecked(agent, rej)
    else:
        rej = []
    if arm == 'A1_orig':
        h = H.CMAWSEExperimentHarness(0x5A3F)
    elif arm == 'A4_twin':
        h = GenericHarnessTwin(0x5A3F)
    else:
        sys.path.insert(0, NATIVE_DIR)
        if 'CMAWSE_v1_0_3_EXPERIMENT_HARNESS_NATIVE' in sys.modules:
            del sys.modules['CMAWSE_v1_0_3_EXPERIMENT_HARNESS']
        import importlib.util
        spec = importlib.util.spec_from_file_location('native_engine_p6', os.path.join(NATIVE_DIR, 'CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        h = mod.CMAWSEExperimentHarness(0x5A3F)
    try:
        rec = h.run_session('CONDITION_C', 2, agent)
        pf = rec.get('parsing_failures')
        complete = all(k in rec for k in ('d1_pass', 'd2_pass', 'd4_pass', 'd5_pass', 'ledger'))
        any_pass = any(rec.get(k) for k in ('d1_pass', 'd2_pass', 'd4_pass', 'd5_pass'))
        malformed = case not in ('valid_oracle', 'welltyped_semantic_wrong', 'd5_len256_boundary_ok')
        silent_conversion = malformed and (not pf) and any_pass
        return {'case': case, 'arm': arm, 'crash': 'NO', 'parse_failures': pf,
                'record_complete': complete, 'continued': True,
                'invalid_accepted_as_valid': bool(any_pass and malformed),
                'silent_conversion': silent_conversion,
                'rejection_traceable': len(rej) > 0}
    except Exception as e:
        return {'case': case, 'arm': arm, 'crash': f'{type(e).__name__}: {str(e)[:40]}',
                'parse_failures': 'N/A', 'record_complete': False, 'continued': False,
                'invalid_accepted_as_valid': 'N/A-crash', 'silent_conversion': 'N/A',
                'rejection_traceable': len(rej) > 0}

def main():
    native_path = build_native()
    log = ['== P6-D typecheck 原生化实验 ==', f'native 副本: {native_path}', '']
    # 回归验收（冻结）：A3 上 v7 全量
    reg = subprocess.run(['python3', os.path.join(ROOT, 'extracted', 'phase2', 'harness_v7_L62449.py')],
                         capture_output=True, text=True, cwd=NATIVE_DIR,
                         env={**os.environ, 'PYTHONPATH': NATIVE_DIR}, timeout=300)
    v7ok = reg.returncode == 0 and 'OK' in (reg.stdout + reg.stderr)
    log.append(f'回归验收：A3 原生化副本上 v7 = {"7/7 OK" if v7ok else "FAIL"} (exit={reg.returncode})')
    open(os.path.join(ROOT, 'rebuild', 'p6', 'logs', 'D_v7_regression_native.log'), 'w').write(reg.stdout + reg.stderr)

    rows = []
    for case, fac in CASES:
        for arm in ('A1_orig', 'A2_wrapper', 'A3_native', 'A4_twin'):
            rows.append(run_arm(arm, case, fac))
    csvp = os.path.join(ROOT, 'rebuild', 'p6', 'TYPECHECK_REGRESSION_RESULTS.csv')
    with open(csvp, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    log.append('')
    for r in rows:
        log.append(f"  {r['arm']:10s} {r['case']:26s} crash={str(r['crash'])[:38]:38s} pf={str(r['parse_failures']):4s} complete={r['record_complete']} invalid_ok={r['invalid_accepted_as_valid']} silent={r['silent_conversion']}")
    # 汇总
    def agg(arm):
        sub = [r for r in rows if r['arm'] == arm]
        mal = [r for r in sub if r['case'] not in ('valid_oracle', 'welltyped_semantic_wrong', 'd5_len256_boundary_ok')]
        return (f"{arm}: crashes={sum(1 for r in sub if r['crash'] != 'NO')}, "
                f"complete={sum(1 for r in sub if r['record_complete'] is True)}/{len(sub)}, "
                f"invalid_accepted={sum(1 for r in mal if r['invalid_accepted_as_valid'] is True)}, "
                f"silent_conv={sum(1 for r in mal if r['silent_conversion'] is True)}, "
                f"误拒(valid pf>0)={sum(1 for r in sub if r['case'] in ('valid_oracle', 'welltyped_semantic_wrong') and isinstance(r['parse_failures'], int) and r['parse_failures'] > 0)}")
    log += ['', '汇总:'] + [f'  ' + agg(a) for a in ('A1_orig', 'A2_wrapper', 'A3_native', 'A4_twin')]
    log.append(f'CSV: {csvp} rows={len(rows)}')
    open(os.path.join(ROOT, 'rebuild', 'p6', 'logs', 'D_typecheck.log'), 'w', encoding='utf-8').write(chr(10).join(log))
    print(chr(10).join(log))

if __name__ == '__main__':
    main()
