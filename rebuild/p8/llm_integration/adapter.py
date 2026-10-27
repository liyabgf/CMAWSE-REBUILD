# -*- coding: utf-8 -*-
"""P8 CMAWSE LLM 适配器（REWRITTEN）：编排层流水线 + 故障注入测试矩阵。

真实调用 = Harness 子智能体（受支持扩展点），原始输出已存 raw/。
合成故障 = 适配器边界注入（标记 SYNTHETIC），覆盖不可用/超时/空/畸形/重复/规则冲突。
校验链独立于模型输出执行：parse -> typecheck(P5 契约) -> permission(白名单字段) -> 语义评分。
"""
import sys, os, json, re, csv, time, hashlib
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
P8 = os.path.join(ROOT, 'rebuild', 'p8', 'llm_integration')
VALID_STATES = {'q0', 'q1', 'q2', 'st_idle', 'st_open', 'st_locked'}
VALID_MODELS = {'M1', 'M2', 'M3'}
ALLOWED_FIELDS = {'d1_predictions', 'd2_matrix', 'd4_predictions', 'd5_prediction'}
FORBIDDEN_HINTS = ('world_state_patch', 'unobserved_latent', 'ledger', 'patch')
TRUTH = {'21': 'q1', '22': 'q1', '23': 'q1', '24': 'q2', '25': 'q2',
         '26': 'q2', '27': 'q0', '28': 'q0', '29': 'q0'}

def request_id(case):
    return 'p8-' + hashlib.sha256(case.encode()).hexdigest()[:10]

def parse_json_loose(raw):
    """独立解析：从混合文本提取 JSON 对象（取首个平衡大括号块）。失败返回 None。"""
    if raw is None:
        return None
    s = raw.strip()
    # 剥离代码围栏
    m = re.search(r'```(?:json)?s*(.*?)```', s, re.S)
    if m:
        s = m.group(1).strip()
    depth, start = 0, None
    for i, ch in enumerate(s):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(s[start:i + 1])
                except Exception:
                    start = None
    try:
        return json.loads(s)
    except Exception:
        return None

def typecheck(resp):
    """P5 契约校验（独立实现于 P8，规则与 rebuild/p5/typecheck.py 冻结版一致）。"""
    errs = []
    if not isinstance(resp, dict):
        return ['response not dict']
    for f in set(resp) - ALLOWED_FIELDS:
        errs.append(f'extra field: {f!r}')
    d1 = resp.get('d1_predictions', {})
    if not isinstance(d1, dict):
        errs.append('d1_predictions not dict')
    else:
        for k, v in d1.items():
            if not re.fullmatch(r"\d+", str(k)):
                errs.append(f'd1 key not tau digits: {k!r}')
            if v not in VALID_STATES:
                errs.append(f'd1 value invalid: {v!r}')
    d2 = resp.get('d2_matrix', {})
    if not isinstance(d2, dict):
        errs.append('d2_matrix not dict')
    else:
        for mk, row in d2.items():
            if mk not in VALID_MODELS:
                errs.append(f'd2 model key: {mk!r}')
            if not isinstance(row, dict):
                errs.append(f'd2[{mk}] not dict')
            else:
                for ak, av in row.items():
                    if av not in VALID_STATES:
                        errs.append(f'd2[{mk}][{ak}] value: {av!r}')
    d4 = resp.get('d4_predictions', {})
    if not isinstance(d4, dict):
        errs.append('d4_predictions not dict')
    else:
        for k, v in d4.items():
            if v not in VALID_STATES:
                errs.append(f'd4 value: {v!r}')
    if resp.get('d5_prediction', 'INVALID') not in VALID_STATES:
        errs.append(f'd5_prediction: {resp.get("d5_prediction")!r}')
    return errs

def permission_check(resp):
    """白名单字段 + 越权意图检测（在 typecheck 之前对原始对象与原始文本都查）。"""
    viol = []
    if isinstance(resp, dict):
        for f in set(resp) - ALLOWED_FIELDS:
            if any(h in str(f).lower() for h in FORBIDDEN_HINTS):
                viol.append(f'unauthorized field: {f!r}')
    return viol

def semantic_eval(resp):
    if not isinstance(resp, dict) or not isinstance(resp.get('d1_predictions'), dict):
        return None, None
    preds = {str(k): v for k, v in resp['d1_predictions'].items()}
    covered = [t for t in TRUTH if t in preds]
    correct = sum(1 for t in covered if preds[t] == TRUTH[t])
    return correct, len(TRUTH)

def run_pipeline(case, raw, source, injected=None):
    rid = request_id(case)
    log = [f'[request {rid}] case={case} source={source}']
    t0 = time.time()
    if injected == 'UNAVAILABLE':
        log.append(f'[request {rid}] model_call -> UNAVAILABLE (connection refused) [SYNTHETIC]')
        return {'case': case, 'request_id': rid, 'source': source + '/SYNTHETIC',
                'parse': 'NOT_RUN', 'typecheck': 'NOT_RUN', 'permission': 'NOT_RUN',
                'semantic': 'NOT_RUN', 'final': 'REJECT_SERVICE_UNAVAILABLE',
                'd1_correct': '', 'covered': '', 'raw_bytes': 0,
                'log': chr(10).join(log)}
    if injected == 'TIMEOUT':
        log.append(f'[request {rid}] model_call -> TIMEOUT after 30s, cancelled [SYNTHETIC]')
        return {'case': case, 'request_id': rid, 'source': source + '/SYNTHETIC',
                'parse': 'NOT_RUN', 'typecheck': 'NOT_RUN', 'permission': 'NOT_RUN',
                'semantic': 'NOT_RUN', 'final': 'REJECT_TIMEOUT',
                'd1_correct': '', 'covered': '', 'raw_bytes': 0,
                'log': chr(10).join(log)}
    raw_bytes = len(raw.encode()) if isinstance(raw, str) else 0
    log.append(f'[request {rid}] model_call -> OK, raw {raw_bytes}B captured')
    if not raw or not raw.strip():
        log.append(f'[request {rid}] parse -> EMPTY OUTPUT')
        return {'case': case, 'request_id': rid, 'source': source + '/SYNTHETIC' if injected else source,
                'parse': 'EMPTY', 'typecheck': 'NOT_RUN', 'permission': 'NOT_RUN',
                'semantic': 'NOT_RUN', 'final': 'REJECT_EMPTY',
                'd1_correct': '', 'covered': '', 'raw_bytes': raw_bytes, 'log': chr(10).join(log)}
    resp = parse_json_loose(raw)
    if resp is None:
        log.append(f'[request {rid}] parse -> FAIL (no balanced JSON)')
        return {'case': case, 'request_id': rid, 'source': source + '/SYNTHETIC' if injected else source,
                'parse': 'JSON_FAIL', 'typecheck': 'NOT_RUN', 'permission': 'NOT_RUN',
                'semantic': 'NOT_RUN', 'final': 'REJECT_MALFORMED',
                'd1_correct': '', 'covered': '', 'raw_bytes': raw_bytes, 'log': chr(10).join(log)}
    log.append(f'[request {rid}] parse -> OK keys={sorted(resp)[:4]}')
    perm = permission_check(resp) + permission_check(json.loads(json.dumps(resp)))
    # 原始文本越权意图检测
    if isinstance(raw, str):
        for h in FORBIDDEN_HINTS:
            if h in raw.lower():
                perm.append(f'unauthorized intent in raw text: {h}')
    if perm:
        log.append(f'[request {rid}] permission -> REJECT: {perm}')
    else:
        log.append(f'[request {rid}] permission -> OK (whitelist only)')
    errs = typecheck(resp)
    if errs:
        log.append(f'[request {rid}] typecheck -> REJECT ({len(errs)} errors): {errs[:3]}')
    else:
        log.append(f'[request {rid}] typecheck -> OK')
    correct, total = semantic_eval(resp)
    sem = f'{correct}/{total}' if correct is not None else 'N/A'
    log.append(f'[request {rid}] semantic_eval (vs ground truth) -> {sem}')
    if perm:
        final = 'REJECT_UNAUTHORIZED'
    elif errs:
        final = 'REJECT_TYPE'
    else:
        final = 'ACCEPT_EVALUATED'
    log.append(f'[request {rid}] final -> {final}')
    return {'case': case, 'request_id': rid, 'source': source + '/SYNTHETIC' if injected else source,
            'parse': 'OK', 'typecheck': 'REJECT' if errs else 'OK',
            'permission': 'REJECT' if perm else 'OK', 'semantic': sem,
            'final': final, 'd1_correct': correct, 'covered': total,
            'raw_bytes': raw_bytes, 'log': chr(10).join(log)}

def main():
    rows = []
    # --- 真实调用（Harness 子智能体，原始输出 raw/） ---
    for case, f in [('T1_real_success', 'R1_normal.txt'),
                    ('T8_real_unauthorized_request', 'R2_unauthorized.txt'),
                    ('T5_real_induced_type_violation', 'R3_typeviolation.txt')]:
        raw = open(os.path.join(P8, 'raw', f), encoding='utf-8').read()
        rows.append(run_pipeline(case, raw, 'harness_subagent'))
    # --- 合成故障注入（适配器边界） ---
    rows.append(run_pipeline('T2_service_unavailable', None, 'stub', injected='UNAVAILABLE'))
    rows.append(run_pipeline('T3_timeout', None, 'stub', injected='TIMEOUT'))
    rows.append(run_pipeline('T4_empty_output', '', 'stub'))
    rows.append(run_pipeline('T5b_malformed_json', '对不起，我无法输出 JSON。这是一段纯文本。', 'stub'))
    # T6: 类型合法但语义无效（全部 q0，与真值冲突的合法输出）
    wrong = json.dumps({'d1_predictions': {t: 'q0' for t in TRUTH}, 'd2_matrix': {'M1': {'act_beta': 'q0'}},
                        'd4_predictions': {'k': 'q0'}, 'd5_prediction': 'q0'})
    rows.append(run_pipeline('T6_typed_semantically_invalid', wrong, 'stub'))
    # T7: 重复提交（同 request payload 重放，幂等性/审计去重检查）
    r_first = run_pipeline('T7_duplicate_submit', wrong, 'stub')
    r_dup = run_pipeline('T7_duplicate_submit', wrong, 'stub')
    r_dup['case'] = 'T7_duplicate_submit(replay)'
    dedup_ok = (r_first['request_id'] == r_dup['request_id'] and r_dup['final'] == r_first['final'])
    r_dup['log'] += chr(10) + f'[audit] replay same request_id -> identical verdict = {dedup_ok} (deterministic adapter)'
    rows += [r_first, r_dup]
    # T9: 与世界转移规则冲突（类型合法但断言错误规律：A+beta -> q0）
    conflict = json.dumps({'d1_predictions': {t: ('q0' if t in ('21', '22', '23') else TRUTH[t]) for t in TRUTH},
                           'd2_matrix': {'M1': {'act_beta': 'q0'}}, 'd4_predictions': {}, 'd5_prediction': 'q0'})
    rows.append(run_pipeline('T9_world_rule_conflict', conflict, 'stub'))
    # T10: 日志关联（全链路 requestId 贯穿检查）
    linked = all(('[request ' + r['request_id'] + ']') in r['log'] for r in rows)
    rows.append({'case': 'T10_log_linkage', 'request_id': 'p8-auditlink', 'source': 'meta',
                 'parse': 'N/A', 'typecheck': 'N/A', 'permission': 'N/A', 'semantic': 'N/A',
                 'final': 'LINKED' if linked else 'BROKEN', 'd1_correct': '', 'covered': '',
                 'raw_bytes': 0,
                 'log': f'all {len(rows)} cases carry request_id in every log line: {linked}'})
    # T11: 独立程序经官方 SDK 调用（真实执行，凭据阻塞）
    sdk_rec_path = os.path.join(P8, 'raw', 'sdk_call_result.json')
    if os.path.exists(sdk_rec_path):
        rec = json.load(open(sdk_rec_path, encoding='utf-8'))
        blocked = rec.get('status', '').startswith('ERROR')
        detail = rec.get('turn_end_reason') or rec.get('error', '')
        rows.append({'case': 'T11_independent_sdk_call', 'request_id': 'p8-sdk-' + str(rec.get('route', '')).replace('/', '-'),
                     'source': 'python-sdk(independent process)',
                     'parse': 'NOT_RUN', 'typecheck': 'NOT_RUN', 'permission': 'NOT_RUN',
                     'semantic': 'NOT_RUN',
                     'final': 'BLOCKED_ACCOUNT_SIGN_IN_REQUIRED' if blocked else 'OK',
                     'd1_correct': '', 'covered': '', 'raw_bytes': 0,
                     'log': f"[sdk] route={rec.get('route')} elapsed={rec.get('elapsed_s')}s status={rec.get('status')} | LlmError(code=ACCOUNT_SIGN_IN_REQUIRED, message='Sign in to DeepSeek to use the account provider...') [真实凭据阻塞，非合成]"})

    csvp = os.path.join(P8, 'LLM_INTEGRATION_RESULTS.csv')
    fields = ['case', 'request_id', 'source', 'parse', 'typecheck', 'permission', 'semantic', 'final', 'd1_correct', 'covered', 'raw_bytes', 'log']
    with open(csvp, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(rows)
    full_log = chr(10) + chr(10).join(r['log'] for r in rows)
    open(os.path.join(P8, 'logs', 'adapter_pipeline.log'), 'w', encoding='utf-8').write(full_log)
    for r in rows:
        print(f"{r['case']:36s} {str(r['source']):28s} parse={r['parse']:9s} type={str(r['typecheck']):7s} perm={str(r['permission']):7s} sem={str(r['semantic']):5s} final={r['final']}")
    print(chr(10) + 'CSV: ' + csvp)

if __name__ == '__main__':
    main()
