# -*- coding: utf-8 -*-
"""通用 Harness 孪生（REWRITTEN，P4 实验用）。

标记：REWRITTEN。这不是对任何真实 harness 框架的模拟，而是一个刻意最小化的
"通用执行循环"对照组：只做循环、调用、日志采集，不做任何领域机制（投影、
深拷贝隔离、异常守卫、字段校验）。世界组件仍复用 CMAWSE 引擎的
DiscretePhysicalWorld——本实验要区分的正是：哪些性质来自循环本身，哪些必须
来自显式机制。

与 CMAWSE run_session 的对照差异（逐条可测）：
- 观察：暴露完整内部状态（含 current_q、focal_obj、unobserved_latent），不做投影
- 历史：账本按引用传入 payload，不做 deepcopy
- 解析：agent 调用与返回值取字段不做 try/except 与类型守卫
- 评估：直接复用引擎评估器，无记录完整性保障
"""
import sys, os, copy
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
sys.path.insert(0, os.path.join(ROOT, 'rebuild', 'out'))
import CMAWSE_v1_0_3_EXPERIMENT_HARNESS as H


class GenericHarnessTwin:
    def __init__(self, master_seed=0x5A3F):
        self.master_seed = master_seed

    def run_session(self, condition, session_idx, agent_callable):
        session_seed = H.derive_session_seed(self.master_seed, session_idx)
        world = H.DiscretePhysicalWorld(condition, session_seed)
        ledger = []
        parsing_failures = 0

        for t in range(21):
            # 无投影：完整内部状态直接给 agent；无隔离：账本按引用传递
            full_state = {
                'tick': world.tick, 'state': world.current_q,
                'focal_object': world.focal_obj, 'context': world.current_ctx,
                'unobserved_latent': world.unobserved_latent,
                'available_actions': tuple(world.actions),
            }
            resp = agent_callable({'phase': 'INTERACTIVE', 'observation': full_state, 'history': ledger})
            act = resp.get('action')
            next_q, evt = world.step(act)
            ledger.append(evt)

        test_queries = []
        for tau in range(21, 30):
            q_in = world.states[tau % len(world.states)]
            x_in = world.objects[(tau * 2) % len(world.objects)]
            k_in = world.train_contexts[(tau * 3) % len(world.train_contexts)]
            act_in = world.actions[(tau * 5) % len(world.actions)]
            test_queries.append({'tau': tau, 'q': q_in, 'X': x_in, 'K': k_in, 'act': act_in,
                                 'true_label': H.ground_truth_transition(condition, q_in, x_in, k_in, act_in)})
        unseen_ctx = world.contexts[2]
        branch_q = {'tick': 10, 'state': ledger[10]['prev_state'], 'focal_object': ledger[10]['object'],
                    'context': ledger[10]['context'], 'action': world.actions[3]}
        payload = {'phase': 'BATCH_EVALUATION', 'context_history': ledger,
                   'd1_queries': [{k: v for k, v in q.items() if k != 'true_label'} for q in test_queries],
                   'd4_queries': [{'tau': f'd4_{i}', 'focal_object': world.objects[0], 'context': unseen_ctx, 'action': a}
                                  for i, a in enumerate(world.actions)],
                   'd5_query': branch_q}
        # 无解析守卫
        batch = agent_callable(payload)
        d1_preds = batch.get('d1_predictions', {})
        d2_matrix = batch.get('d2_matrix', {})
        d4_preds = batch.get('d4_predictions', {})
        d5_pred = batch.get('d5_prediction', 'INVALID')

        d1_delta, d1_pass = H.evaluate_d1(ledger, test_queries, d1_preds)
        d2_cr, d2_pass = H.evaluate_d2(d2_matrix, condition)
        d4_acc, d4_pass = H.evaluate_d4(unseen_ctx, condition, d4_preds)
        d5_acc, d5_pass = H.evaluate_d5(branch_q, d5_pred, condition)

        return {'session_idx': session_idx, 'condition': condition, 'session_seed': session_seed,
                'parsing_failures': parsing_failures, 'd1_delta': d1_delta, 'd1_pass': d1_pass,
                'd2_cr': d2_cr, 'd2_pass': d2_pass, 'd4_acc': d4_acc, 'd4_pass': d4_pass,
                'd5_acc': d5_acc, 'd5_pass': d5_pass, 'ledger': ledger}
