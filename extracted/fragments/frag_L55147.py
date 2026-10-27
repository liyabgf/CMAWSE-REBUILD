# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L55147-L55186 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #146  lines=39  compile=OK
# kind: fragment  ident: frag_L55147.py
# edits: none. Header comment is the only addition.
# ======================
def Runner_B(master_seed: int, model_log: Dict[str, Any], env_spec: Dict[str, Any]) -> EvaluationReport:
    # 独立实现的 PRNG 流
    rng = SeedTree(master_seed)
    all_sessions_data = []
    
    # 建立会话循环
    for s_idx in range(100):
        s_rng = rng.spawn_child(f"session_{s_idx}")
        env = IsolatedEnvironment(env_spec, seed=s_rng.get_int())
        
        # 逐步执行交互
        step_log = []
        for step in range(21):
            o_t = env.get_observation()
            response_str = model_log[f"session_{s_idx}"]["interactive"][step]
            act_obj = SafeJsonReader.extract(response_str)
            
            # 状态机约束校验
            if act_obj.action in o_t.allowed_set:
                evt = env.apply_transition(act_obj.action)
            else:
                evt = env.abort_to_silent()
            step_log.append(evt)
            
        # 离线批量推断提取 (D1)
        test_queries = env.get_frozen_test_queries(start=21, end=29)
        test_predictions = SafeJsonReader.extract_d1_block(model_log[f"session_{s_idx}"]["batch_d1"])
        
        all_sessions_data.append({
            "history": step_log,
            "predictions": test_predictions,
            "test_truth": [env.evaluate_offline(q) for q in test_queries],
            "d2_response": SafeJsonReader.extract_d2_block(model_log[f"session_{s_idx}"]["d2_matrix"])
        })
        
    # 最终打分调用
    b_out = MetricPipeline.run_behavior_tests(all_sessions_data)
    i_out = MetricPipeline.run_hmid_comparisons(all_sessions_data)
    return EvaluationReport(b_out, i_out)
