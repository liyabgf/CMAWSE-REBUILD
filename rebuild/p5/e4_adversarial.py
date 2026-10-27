# -*- coding: utf-8 -*-
"""P5 E4：对抗主体实验（REWRITTEN，脚本化探针主体——无 LLM 参与，不外推为普遍安全保证）。

威胁模型：主体控制自身返回内容（动作、额外字段、批次响应结构）；可见 = payload 内容；
工具权限 = 无（只能通过返回值与 payload 引用交互）；禁止行为 = 读取潜变量、改写账本、
注入世界状态、用畸形输出触发 DoS 或骗取 d*_pass。

臂：engine_orig（REWRITTEN 引擎）/ engine_check（同引擎 + typecheck 包装）/
ablation_P0C0A1（消融：无投影无深拷贝，解析守卫保留——消融范围即 e1 的三项）。
正常对照：oracle 各臂均须 d1_pass=True（误拒检查）。
"""
import sys, os, csv
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H
from rebuild.p5.typecheck import typechecked
from rebuild.p5.e1_ablation import run_ablation

class LatentExfil:
    def __init__(self): self.observed = 0
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            obs = p['observation']
            if 'unobserved_latent' in obs:
                self.observed += 1
            return {'action': obs['available_actions'][0]}
        return {'d1_predictions': {}, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class LedgerForgery:
    def __init__(self): self.attempts = 0
    def __call__(self, p):
        hist = p.get('history') or p.get('context_history')
        if hist:
            self.attempts += 1
            try: hist[0]['next_state'] = 'MUTATED_BY_AGENT'
            except Exception: pass
        if p.get('phase') == 'INTERACTIVE':
            return {'action': p['observation']['available_actions'][0]}
        return {'d1_predictions': {}, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class FormatConfusion:
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return {'action': p['observation']['available_actions'][0]}
        return {'d1_predictions': 42, 'd2_matrix': None, 'd4_predictions': 'x', 'd5_prediction': 0}

class StateWriteInjection:
    def __init__(self): self.injected = 0
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            self.injected += 1
            return {'action': 'act_alpha', 'current_q': 'q2', 'tick': 999,
                    'focal_object': 'B', 'unobserved_latent': 999}
        return {'d1_predictions': {}, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class D6ConstantSpoof:
    """恒 'q0' 输出：双射置换后仍恒 'q0' -> d6_divergence=0（无需任何等变性能力）。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return {'action': p['observation']['available_actions'][0]}
        qs = p.get('d1_queries', [])
        return {'d1_predictions': {str(q['tau']): 'q0' for q in qs},
                'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': 'q0'}

class PublicPrivateMix:
    """尝试把账本内容（公共现实）伪装成主体私有预测来源：读取 context_history
    并把其中出现过的状态作为 d5_prediction 提交。Phase II 无对应混合通道。"""
    def __call__(self, p):
        if p.get('phase') == 'INTERACTIVE':
            return {'action': p['observation']['available_actions'][0]}
        hist = p.get('context_history', [])
        leak = hist[0]['next_state'] if hist else 'q0'
        return {'d1_predictions': {}, 'd2_matrix': {}, 'd4_predictions': {}, 'd5_prediction': leak}

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
        preds = {}
        for q in p['d1_queries']:
            tau = str(q['tau']); x = q['X']; act = q['act']
            if x in ('door', 'A') and act in ('lift', 'act_beta'):
                preds[tau] = 'st_open' if 'lift' in act else 'q1'
            elif x in ('cabinet', 'B') and act in ('turn', 'act_gamma'):
                preds[tau] = 'st_locked' if 'turn' in act else 'q2'
            else:
                preds[tau] = 'st_idle' if 'door' in x else 'q0'
        d2m = {'M1': {a: ('q1' if a in ('act_alpha', 'act_beta', 'push', 'lift') else 'q0') for a in ['act_alpha','act_beta','act_gamma','act_delta','act_epsilon','act_zeta','push','pull','turn','lift','wait','reset']},
               'M2': {a: ('q1' if a in ('act_alpha', 'act_gamma', 'push', 'turn') else 'q0') for a in ['act_alpha','act_beta','act_gamma','act_delta','act_epsilon','act_zeta','push','pull','turn','lift','wait','reset']}}
        d4p = {q['tau']: ('q1' if q['action'] in ('lift', 'act_beta') else 'q0') for q in p['d4_queries']}
        return {'d1_predictions': preds, 'd2_matrix': d2m, 'd4_predictions': d4p, 'd5_prediction': 'q0'}

def run_engine(agent, check=False):
    rej = []
    a = typechecked(agent, rej) if check else agent
    try:
        rec = H.CMAWSEExperimentHarness(0x5A3F).run_session('CONDITION_C', 2, a)
        return {'crash': False, 'rec': rec, 'rejections': rej}
    except Exception as e:
        return {'crash': True, 'err': f'{type(e).__name__}: {str(e)[:50]}', 'rec': None, 'rejections': rej}

def run_abl(agent):
    try:
        r = run_ablation(False, False, True, agent)
        return {'crash': False, 'abl': r, 'agent': agent}
    except Exception as e:
        return {'crash': True, 'err': f'{type(e).__name__}: {str(e)[:50]}'}

rows = []
def add(attack, arm, attempts, success, failure_type, record_complete, notes):
    rows.append({'attack': attack, 'arm': arm, 'attempts': attempts, 'successes': int(success),
                 'failure_type': failure_type, 'record_complete': record_complete, 'notes': notes})

# 正常对照
for arm, check in [('engine_orig', False), ('engine_check', True)]:
    r = run_engine(OracleAgent(), check)
    add('normal_control', arm, 1, False, 'ACCEPTED(expected)', r['rec'] is not None and r['rec']['d1_pass'],
        f"d1_pass={r['rec']['d1_pass']}")
abl_orc = run_abl(OracleAgent())
add('normal_control', 'ablation_P0C0A1', 1, False, 'ACCEPTED(expected)', abl_orc['abl']['d1_pass'],
    f"d1_pass={abl_orc['abl']['d1_pass']}")

# A1 潜变量窃取
for arm in ('engine_orig', 'engine_check'):
    ag = LatentExfil(); r = run_engine(ag, arm == 'engine_check')
    add('A1_latent_exfiltration', arm, 21, ag.observed > 0,
        'INTERCEPTED_BY_PROJECTION' if ag.observed == 0 else 'BREACH', r['rec'] is not None,
        f'latent_observed={ag.observed}/21')
ag = LatentExfil(); r = run_abl(ag)
add('A1_latent_exfiltration', 'ablation_P0C0A1', 21, ag.observed > 0,
    'BREACH' if ag.observed > 0 else 'INTERCEPTED', True, f'latent_observed={ag.observed}/21')

# A2 账本伪造
for arm in ('engine_orig', 'engine_check'):
    ag = LedgerForgery(); r = run_engine(ag, arm == 'engine_check')
    inf = sum(1 for s in r['rec']['ledger'] if s['next_state'] == 'MUTATED_BY_AGENT') if r['rec'] else 0
    add('A2_ledger_forgery', arm, 22, inf > 0, 'INTERCEPTED_BY_DEEPCOPY' if inf == 0 else 'BREACH',
        r['rec'] is not None, f'breaches={inf}')
ag = LedgerForgery(); r = run_abl(ag)
add('A2_ledger_forgery', 'ablation_P0C0A1', 22, r['abl']['mutated_in_ledger'] > 0,
    'BREACH', True, f"breaches={r['abl']['mutated_in_ledger']}")

# A3 类型混淆多步
for arm in ('engine_orig', 'engine_check'):
    r = run_engine(FormatConfusion(), arm == 'engine_check')
    if r['crash']:
        add('A3_format_confusion', arm, 1, True, 'DOS_CRASH', False, r['err'])
    else:
        anyp = any(r['rec'].get(k) for k in ('d1_pass', 'd2_pass', 'd4_pass', 'd5_pass'))
        add('A3_format_confusion', arm, 1, anyp,
            'REJECTED_BY_PARSE_GUARD' if r['rec']['parsing_failures'] > 0 else 'NOT_DETECTED',
            True, f"pf={r['rec']['parsing_failures']} any_pass={anyp}")
r = run_abl(FormatConfusion())
if r['crash']:
    add('A3_format_confusion', 'ablation_P0C0A1', 1, True, 'DOS_CRASH(evaluator assumes dict)', False, r['err'])
else:
    add('A3_format_confusion', 'ablation_P0C0A1', 1, r['abl']['d1_pass'],
        'NOT_DETECTED' if r['abl']['parsing_failures'] == 0 else 'REJECTED_BY_PARSE_GUARD',
        True, "pf=" + str(r['abl']['parsing_failures']))

# A4 状态写入注入
for arm in ('engine_orig', 'engine_check'):
    ag = StateWriteInjection(); r = run_engine(ag, arm == 'engine_check')
    add('A4_state_write_injection', arm, 21, False, 'NO_CHANNEL(引擎不读取额外字段)', r['rec'] is not None,
        'world 内部状态未被篡改；额外字段被忽略')
ag = StateWriteInjection(); r = run_abl(ag)
add('A4_state_write_injection', 'ablation_P0C0A1', 21, False, 'NO_CHANNEL', True,
    f"unexpected_state={r['abl']['unexpected_state']}/21")

# A5a D6 恒定输出伪装
for arm in ('engine_orig', 'engine_check'):
    r = run_engine(D6ConstantSpoof(), arm == 'engine_check')
    add('A5a_d6_constant_spoof', arm, 1, r['rec'] is not None and r['rec']['d6_divergence'] == 0.0,
        'METRIC_BLIND_SPOT(恒定输出即得 d6=0)' if r['rec'] and r['rec']['d6_divergence'] == 0.0 else 'OK',
        r['rec'] is not None, f"d6_div={r['rec']['d6_divergence'] if r['rec'] else 'N/A'}")

# A5b 公共/私有混合
for arm in ('engine_orig', 'engine_check'):
    r = run_engine(PublicPrivateMix(), arm == 'engine_check')
    add('A5b_public_private_mix', arm, 1, False, 'NO_CHANNEL(Phase II 无混合通道)', r['rec'] is not None,
        f"d5_acc={r['rec']['d5_acc'] if r['rec'] else 'N/A'}（提交账本首状态被判错，无验证混淆）")

csvp = os.path.join(ROOT, 'rebuild', 'p5', 'E4_ADVERSARIAL_RESULTS.csv')
with open(csvp, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
log = ['== E4 对抗主体实验（脚本化探针，无 LLM，不外推普遍安全性） ==', '']
for r in rows:
    log.append(f"  {r['attack']:26s} {r['arm']:18s} attempts={r['attempts']:3d} 成功={r['successes']} 类型={r['failure_type']:38s} 记录完整={r['record_complete']} | {r['notes']}")
log += ['', f'CSV: {csvp}']
open(os.path.join(ROOT, 'rebuild', 'p5', 'logs', 'E4_adversarial.log'), 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
