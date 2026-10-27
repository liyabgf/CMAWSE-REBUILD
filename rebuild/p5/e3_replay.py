# -*- coding: utf-8 -*-
"""P5 E3：重放负对照（REWRITTEN）。

重放契约来源（先读后测，不预设可交换性）：
- 代码契约（rebuild/out execute_replay_cli）：逐行 json.loads；校验
  session_seed == derive_session_seed(seed, session_idx)；重建世界并按记录 action
  逐步 step；账本 json 规范化逐字相等；任一不符 -> ValueError 退出非零。
- REPLAY_SPEC v0.3 prose（EXTRACTED，档案 L62600+）：确定性重放、账本对账、
  1e-9 浮点容差（CLI 实现为 json 字符串相等，比规格更严——差异记录）。
- 未定义项标 UNRESOLVED。顺序语义：账本按 tick 排序、事件次序编码于 tick/对象轮转，
  故重排预期"被检出"而非"应等价"。
"""
import sys, os, csv, json, subprocess, tempfile
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H

class OracleAgent:
    def __call__(self, p):
        ph = p.get('phase')
        if ph == 'INTERACTIVE':
            obs = p['observation']; obj = obs['focal_object']
            if obj in ('door', 'A'):
                act = 'lift' if 'lift' in obs['available_actions'] else 'act_beta'
            elif obj in ('cabinet', 'B'):
                act = 'turn' if 'turn' in obs['available_actions'] else 'act_gamma'
            else:
                act = obs['available_actions'][0]
            return {'action': act}
        return {'d1_predictions': {str(q['tau']): 'q0' for q in p['d1_queries']},
                'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

def make_record():
    rec = H.CMAWSEExperimentHarness(0x5A3F).run_session('CONDITION_C', 1, OracleAgent())
    return {k: v for k, v in rec.items() if k != 'ledger'} | {'ledger': rec['ledger']}

def write_log(path, records):
    with open(path, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r) + chr(10))

def run_cli(logpath, seed):
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'rebuild', 'out', 'CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py'),
                        '--replay', '--log', logpath, '--seed', hex(seed)],
                       capture_output=True, text=True, timeout=60)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ''

base = make_record()
tmp = tempfile.mkdtemp(prefix='p5e3_')
rows = []

def scenario(name, contract, expected, mutate, seed=0x5A3F):
    rec = json.loads(json.dumps(base))
    logp = os.path.join(tmp, name + '.jsonl')
    if mutate is not None:
        mutate(rec)
    write_log(logp, [rec])
    rc, msg = run_cli(logp, seed)
    verdict = 'MATCH' if msg.startswith('[SUCCESS]') == expected else 'UNEXPECTED'
    rows.append({'scenario': name, 'contract_source': contract, 'expected': 'SUCCESS' if expected else 'REJECTED',
                 'actual_exit': rc, 'actual_result': ('SUCCESS' if msg.startswith('[SUCCESS]') else 'REJECTED') + (': ' + msg[:70] if not msg.startswith('[SUCCESS]') else ''),
                 'verdict': verdict})
    return rows[-1]

# 1. 完全相同重复执行（契约：确定性重放 -> SUCCESS）
scenario('identical_rerun', 'code+REPLAY_SPEC', True, None)
# 2. 种子 1-bit 翻转（契约：种子派生校验 -> REJECTED）
scenario('seed_bitflip', 'code', False, None, seed=0x5A3E)
# 3. 篡改 next_state（契约：账本逐字对账 -> REJECTED）
def tamper_state(r):
    r['ledger'][5]['next_state'] = 'q2'
scenario('tamper_next_state', 'code', False, tamper_state)
# 4a. 篡改 action 为同结局动作（重放以账本为 action 唯一来源：只验一致性不验真实性 -> 预期不可检出）
def tamper_action_equiv(r):
    r['ledger'][5]['action'] = 'act_zeta'   # obj=C，任一合法动作结局均为 q0 -> 自洽
scenario('tamper_action_equivalent', 'code(一致性非真实性)', True, tamper_action_equiv)
# 4b. 篡改 action 为异结局动作（action 与记录结局矛盾 -> 检出）
def tamper_action_outcome(r):
    idx = next(i for i, s in enumerate(r['ledger']) if s['object'] == 'A' and s['action'] == 'act_beta')
    r['ledger'][idx]['action'] = 'act_alpha'  # A+act_beta->q1 改成 A+act_alpha->q0
scenario('tamper_action_outcome_changing', 'code', False, tamper_action_outcome)
# 5. 交换两个事件（顺序编码于 tick/对象轮转，语义有序 -> 预期检出）
def reorder(r):
    r['ledger'][3], r['ledger'][4] = r['ledger'][4], r['ledger'][3]
scenario('reorder_events', 'code(顺序语义在账本内)', False, reorder)
# 6. 重复提交事件（长度/推进偏离 -> REJECTED）
def dup(r):
    r['ledger'].insert(4, json.loads(json.dumps(r['ledger'][4])))
scenario('duplicate_event', 'code', False, dup)
# 7. 遗漏事件 -> REJECTED
def drop(r):
    del r['ledger'][4]
scenario('drop_event', 'code', False, drop)
# 8. JSON 行截断（规格未定义坏行处理 -> 记录实际行为，UNRESOLVED）
rec8 = json.loads(json.dumps(base))
logp8 = os.path.join(tmp, 'corrupt.jsonl')
open(logp8, 'w', encoding='utf-8').write(json.dumps(rec8)[:-30] + chr(10))
rc8, msg8 = run_cli(logp8, 0x5A3F)
rows.append({'scenario': 'corrupt_json_line', 'contract_source': 'UNRESOLVED(规格未定义)',
             'expected': 'UNDEFINED', 'actual_exit': rc8,
             'actual_result': ('SUCCESS' if msg8.startswith('[SUCCESS]') else 'REJECTED') + ': ' + msg8[:70],
             'verdict': 'DOCUMENTED'})
# 9. 会话重贴标签（session_idx 与 session_seed 同步改为一致的派生对）
def reindex(r):
    r['session_idx'] = 2
    r['session_seed'] = H.derive_session_seed(0x5A3F, 2)
scenario('session_relabel_consistent', 'UNRESOLVED(内容-会话绑定规格未定义)', True, reindex)
# 10. 记录级额外字段（重放只审计 seed+ledger -> SUCCESS；评估字段不受审计：范围发现）
def extra(r):
    r['d1_pass'] = True; r['d1_delta'] = 0.99; r['injected'] = 'x'
scenario('extra_record_fields', 'code(审计范围=seed+ledger)', True, extra)

csvp = os.path.join(ROOT, 'rebuild', 'p5', 'E3_REPLAY_RESULTS.csv')
with open(csvp, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
log = ['== E3 重放负对照 ==', '']
for r in rows:
    log.append(f"  {r['scenario']:28s} 契约={r['contract_source']:28s} 预期={r['expected']:9s} 实际exit={r['actual_exit']} {r['actual_result'][:60]} 判定={r['verdict']}")
log += ['', f'CSV: {csvp}', f'tmp logs: {tmp}']
open(os.path.join(ROOT, 'rebuild', 'p5', 'logs', 'E3_replay.log'), 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
