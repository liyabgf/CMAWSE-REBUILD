# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L55093-L55143 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #145  lines=50  compile=OK
# kind: fragment  ident: frag_L55093.py
# edits: none. Header comment is the only addition.
# ======================
def Runner_A(master_seed: int, model_log: Dict[str, Any], env_spec: Dict[str, Any]) -> EvaluationReport:
    prng_master = SplitMix64(master_seed)
    session_count = 100
    session_records = []
    
    # 全局符号置换初始化 (D6 用)
    perm_seed = prng_master.next_uint64()
    global_perm = generate_bijective_permutation(env_spec["symbols"], perm_seed)
    
    for k in range(session_count):
        s_seed = prng_master.next_uint64()
        session_prng = SplitMix64(s_seed)
        
        # 1. 物理环境初始化
        world = DiscreteWorld(env_spec, session_prng.next_uint64())
        history_ledger = []
        raw_outputs = model_log[f"session_{k}"]
        
        # 2. 交互期: Tick 0 to 20
        for t in range(21):
            obs = world.project_observation()
            raw_resp = raw_outputs["interactive"][t]
            parsed = StrictParser.parse_action(raw_resp)
            if not parsed.is_valid or parsed.action not in obs.valid_actions:
                event = world.step_fail_closed()
            else:
                event = world.step(parsed.action)
            history_ledger.append(event)
            
        # 3. 冻结上下文批处理测试期: Tick 21 to 29 (D1)
        batch_inputs = [(world.get_state(tau), world.get_focal_obj(tau), 
                         world.get_context(tau), world.get_scheduled_action(tau)) for tau in range(21, 30)]
        batch_preds = StrictParser.parse_batch_predictions(raw_outputs["batch_d1"])
        
        # 4. 前向评估与探针决策收集 (D2, D3)
        d2_matrix = StrictParser.parse_d2_matrix(raw_outputs["d2_matrix"])
        d3_probes = [StrictParser.parse_action(raw_outputs["interactive"][t]).action for t in range(21)]
        
        session_records.append({
            "ledger": history_ledger,
            "d1_preds": batch_preds,
            "d2_matrix": d2_matrix,
            "d3_probes": d3_probes,
            "ground_truth_test": [world.get_oracle_transition(item) for item in batch_inputs]
        })
        
    # 5. 统计聚合与双轨评估
    B_vector = Evaluator.compute_behavioral_vector(session_records)
    I_vector = Evaluator.compute_identifiability_vector(session_records, H_mid_instances)
    return EvaluationReport(B_vector, I_vector)
