# -*- coding: utf-8 -*-
"""P5 E1 消融：分离信息边界(PROJECTION)/状态隔离(DEEPCOPY)/审计记录(AUDIT)的贡献。

标记：REWRITTEN（P5 实验代码）。被测机制的真实在码形态（对照 rebuild/out 引擎 run_session）：
- PROJECTION：obs = world.project_observation()，潜变量不进入 payload（结构性存在）
- DEEPCOPY：payload['history'] = copy.deepcopy(ledger)（两处：交互+批次）
- AUDIT：ledger.append(evt) + parsing_failures 计数
- 账本变异守卫：**Phase II 引擎中不存在独立机制**（事件由 world.step 产出后无条件入账），
  无法单独消融，仅在组合层面评估；非法动作拒绝属世界组件（P4-E1 已证）。

设计：全因子 2^3 = 8 配置 × {probe-adversarial, oracle 对照}。世界组件、种子、
调用结构、主体逻辑固定。指标分母：暴露 21 次调用；变异 21 次尝试；记录 13 键+21 条账本。
三态区分：拦截成功 / 机制未触发（无通道）/ 击穿。
"""
import sys, os, csv, copy, itertools, json
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H

OUT = os.path.join(ROOT, 'rebuild', 'p5')

class ProbeAdversarial:
    """EXTRACTED 语义（v7 AdversarialAgent）+ 探针扩展：逐调用变异 payload 历史、
    原位篡改 observation、注入额外字段、记录所见键。"""
    def __init__(self):
        self.latent_seen = 0
        self.calls = 0
        self.keys_seen = set()
        self.obs_tamper = 0
    def __call__(self, payload):
        self.calls += 1
        if 'history' in payload and payload['history']:
            try:
                payload['history'][0]['next_state'] = 'MUTATED_BY_AGENT'
            except Exception:
                pass
        ph = payload.get('phase')
        if ph == 'INTERACTIVE':
            obs = payload['observation']
            self.keys_seen.update(obs.keys())
            if 'unobserved_latent' in obs:
                self.latent_seen += 1
            try:
                obs['state'] = 'HACKED_OBS'
                self.obs_tamper += 1
            except Exception:
                pass
            return {'action': 'HACK_ACTION', 'current_q': 'HACKED', 'unobserved_latent': 999}
        return {'d1_predictions': {str(q['tau']): 'HACK_STATE' for q in payload.get('d1_queries', [])},
                'd2_matrix': 'INVALID_TYPE', 'd4_predictions': {}, 'd5_prediction': 'HACK_STATE'}

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

def run_ablation(projection, deepcopy, audit, agent):
    """REWRITTEN：参数化会话循环（结构与引擎 run_session 相同，机制可开关）。"""
    session_seed = H.derive_session_seed(0x5A3F, 1)
    world = H.DiscretePhysicalWorld('CONDITION_C', session_seed)
    ledger = []
    parsing_failures = 0
    unexpected_state = 0
    for t in range(21):
        if projection:
            obs = world.project_observation()
        else:
            obs = {'tick': world.tick, 'state': world.current_q, 'focal_object': world.focal_obj,
                   'context': world.current_ctx, 'unobserved_latent': world.unobserved_latent,
                   'available_actions': tuple(world.actions)}
        payload = {'phase': 'INTERACTIVE', 'observation': obs,
                   'history': copy.deepcopy(ledger) if deepcopy else ledger}
        try:
            resp = agent(payload)
            act = resp.get('action')
        except Exception:
            parsing_failures += 1
            act = None
        _, evt = world.step(act)
        if audit:
            ledger.append(evt)
        # 非预期状态变化检测：主体注入的字段不得改变世界内部状态
        if world.current_q == 'HACKED' or world.unobserved_latent == 999:
            unexpected_state += 1
    queries = []
    for tau in range(21, 30):
        q_in = world.states[tau % 3]; x_in = world.objects[(tau*2) % 3]
        k_in = world.train_contexts[(tau*3) % 2]; act_in = world.actions[(tau*5) % 6]
        queries.append({'tau': tau, 'X': x_in, 'K': k_in, 'act': act_in,
                        'true_label': H.ground_truth_transition('CONDITION_C', q_in, x_in, k_in, act_in)})
    unseen_ctx = world.contexts[2]
    batch_payload = {'phase': 'BATCH_EVALUATION',
                     'context_history': copy.deepcopy(ledger) if deepcopy else ledger,
                     'd1_queries': [{k: v for k, v in q.items() if k != 'true_label'} for q in queries],
                     'd4_queries': [{'tau': f'd4_{i}', 'focal_object': world.objects[0], 'context': unseen_ctx, 'action': a}
                                    for i, a in enumerate(world.actions)],
                     'd5_query': {'tick': 10}}
    try:
        batch = agent(batch_payload)
        d1_preds = batch.get('d1_predictions', {})
    except Exception:
        parsing_failures += 1
        d1_preds = {}
    d1_delta, d1_pass = H.evaluate_d1(ledger, queries, d1_preds)
    complete = all(k in ('d1_pass', 'd2_pass', 'd5_pass', 'd6_divergence', 'ledger') for k in ['d1_pass']) and len(ledger) == 21
    # 变异三态
    mutation_attempts = getattr(agent, 'calls', 0) if hasattr(agent, 'calls') else 0
    mutated_in_ledger = sum(1 for s in ledger if s['next_state'] == 'MUTATED_BY_AGENT')
    if mutated_in_ledger > 0:
        mutation_outcome = 'BREACH'
    elif deepcopy and mutation_attempts > 0:
        mutation_outcome = 'INTERCEPTED_BY_DEEPCOPY'
    elif not audit:
        mutation_outcome = 'NOT_TRIGGERED_NO_CHANNEL(ledger empty)'
    else:
        mutation_outcome = 'NOT_TRIGGERED'
    return {'latent_seen': getattr(agent, 'latent_seen', 0), 'calls': getattr(agent, 'calls', 0),
            'obs_tamper': getattr(agent, 'obs_tamper', 0),
            'mutated_in_ledger': mutated_in_ledger, 'mutation_outcome': mutation_outcome,
            'unexpected_state': unexpected_state, 'parsing_failures': parsing_failures,
            'd1_pass': d1_pass, 'record_complete': complete, 'ledger_len': len(ledger)}

def main():
    rows = []
    log = ['== E1 全因子消融 (2^3=8 配置 × 2 主体) ==', '']
    log.append('配置记法 P=projection C=deepcopy A=audit；主体 probe=对抗探针 oracle=正常对照')
    log.append('')
    for proj, dcpy, aud in itertools.product([True, False], repeat=3):
        tag = f'P{int(proj)}C{int(dcpy)}A{int(aud)}'
        probe = ProbeAdversarial()
        r1 = run_ablation(proj, dcpy, aud, probe)
        orc = OracleAgent()
        r2 = run_ablation(proj, dcpy, aud, orc)
        for who, r in [('probe', r1), ('oracle', r2)]:
            rows.append({'config': tag, 'projection': int(proj), 'deepcopy': int(dcpy), 'audit': int(aud),
                         'agent': who,
                         'latent_exposure': f"{r['latent_seen']}/21",
                         'latent_exposure_rate': round(r['latent_seen']/21, 4),
                         'mutation_attempts': r['calls'] if who == 'probe' else 0,
                         'mutation_breaches': r['mutated_in_ledger'] if who == 'probe' else 0,
                         'mutation_outcome': r['mutation_outcome'] if who == 'probe' else 'n/a',
                         'record_complete': r['record_complete'], 'ledger_len': r['ledger_len'],
                         'unexpected_state_changes': r['unexpected_state_changes'] if 'unexpected_state_changes' in r else r['unexpected_state'],
                         'd1_pass': r['d1_pass']})
        log.append(f"[{tag}] probe: latent={r1['latent_seen']}/21 变异={r1['mutated_in_ledger']}/{r1['calls']}({r1['mutation_outcome']}) 记录完整={r1['record_complete']} 非预期状态={r1['unexpected_state']}/21")
        log.append(f"[{tag}] oracle: d1_pass={r2['d1_pass']} 记录完整={r2['record_complete']} (误拒检查)")

    csvp = os.path.join(OUT, 'E1_ABLATION_MATRIX.csv')
    with open(csvp, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)
    log += ['', f'CSV: {csvp}  rows={len(rows)}']
    open(os.path.join(OUT, 'logs', 'E1_ablation.log'), 'w', encoding='utf-8').write(chr(10).join(log))
    print(chr(10).join(log))


if __name__ == "__main__":
    main()
