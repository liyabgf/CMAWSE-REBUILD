# -*- coding: utf-8 -*-
"""E1: 信息边界与变异封禁实验（REWRITTEN）。

假设：CMAWSE 的投影+深拷贝机制使得（a）不可观测潜变量对 agent 不可见、
（b）agent 对历史账本的原位变异不会感染运行时；通用执行循环不具备这两性质。
对照：generic_twin（同一世界组件，无投影/无隔离/无守卫）。
探针 agent：记录所见 payload 键并执行 v7 原版 AdversarialAgent 的变异与注入。
失败判据：若 CMAWSE 组感染计数>0 或泄漏计数>0，或 twin 组两者均为 0，则假设证伪。
"""
import sys, os
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H
from rebuild.p4.generic_twin import GenericHarnessTwin

log = []

def make_probe_adversarial():
    """v7 原版 AdversarialAgent（EXTRACTED 语义）+ 键探针。"""
    seen = {'keys': set(), 'latent_seen': 0, 'calls': 0}
    class ProbeAdversarial:
        def __call__(self, payload):
            seen['calls'] += 1
            if 'history' in payload and payload['history']:
                try:
                    payload['history'][0]['next_state'] = 'MUTATED_BY_AGENT'
                except Exception:
                    pass
            ph = payload.get('phase')
            if ph == 'INTERACTIVE':
                obs = payload['observation']
                seen['keys'].update(obs.keys())
                if 'unobserved_latent' in obs:
                    seen['latent_seen'] += 1
                return {'action': 'HACK_ACTION', 'unobserved_latent': 999}
            return {'d1_predictions': {str(q['tau']): 'HACK_STATE' for q in payload.get('d1_queries', [])},
                    'd2_matrix': 'INVALID_TYPE', 'd4_predictions': {}, 'd5_prediction': 'HACK_STATE'}
    return ProbeAdversarial(), seen

def measure(name, harness_cls):
    agent, seen = make_probe_adversarial()
    harness = harness_cls(master_seed=0x5A3F) if harness_cls is H.CMAWSEExperimentHarness else harness_cls(0x5A3F)
    rec = harness.run_session('CONDITION_C', 0, agent)
    infected = sum(1 for s in rec['ledger'] if s['next_state'] == 'MUTATED_BY_AGENT')
    invalid_committed = sum(1 for s in rec['ledger']
                            if s['status'] == 'COMMITTED' and s['action'] not in H.DiscretePhysicalWorld('CONDITION_C', 0).actions)
    eval_keys = {'d1_pass', 'd2_pass', 'd5_pass', 'd6_divergence'}
    complete = eval_keys.issubset(rec.keys()) or ('d6_divergence' not in eval_keys and {'d1_pass','d2_pass','d5_pass'}.issubset(rec.keys()))
    row = (name, len(seen['keys']), sorted(seen['keys']), seen['latent_seen'], infected,
           invalid_committed, complete, sorted(k for k in eval_keys if k in rec.keys()))
    log.append(f'[{name}] payload键数={row[1]} 键={row[2]}')
    log.append(f'[{name}] latent 暴露次数={row[3]}/21 | 账本感染={row[4]} | 非法动作被提交={row[5]} | 评估字段齐全={row[6]}')
    return row

log.append('== E1: 信息边界与变异封禁 ==')
try:
    r_cm = measure('CMAWSE-engine', H.CMAWSEExperimentHarness)
except Exception as e:
    log.append(f'[CMAWSE-engine] CRASH: {type(e).__name__}: {e}')
try:
    r_tw = measure('GenericTwin', GenericHarnessTwin)
except Exception as e:
    log.append(f'[GenericTwin] CRASH: {type(e).__name__}: {e}')

out = os.path.join(ROOT, 'rebuild', 'p4', 'logs', 'E1_boundary.log')
open(out, 'w', encoding='utf-8').write(chr(10).join(log))
print(chr(10).join(log))
print('LOG:', out)
