# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L54006-L54049 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #144  lines=43  compile=OK
# kind: fragment  ident: frag_L54006.py
# edits: none. Header comment is the only addition.
# ======================
# 逻辑参考实现 (Mathematical Pseudo-specification)
def evaluate_d1(trace: SessionTrace, predictions: Dict[int, str]) -> Tuple[float, bool]:
    # trace 包含 0..29 的转移数据
    train_slice = trace[0:21]   # tau = 0..20
    test_slice = trace[21:30]   # tau = 21..29
    
    # 1. 计算条件经验频率表
    counts = defaultdict(lambda: defaultdict(int))
    global_counts = defaultdict(int)
    for step in train_slice:
        counts[(step.X, step.act)][step.next_q] += 1
        global_counts[step.next_q] += 1
    
    global_mode = max(global_counts.keys(), key=lambda q: (global_counts[q], -ord(q[1])))
    
    # 2. 在测试切片上独立评估
    correct_agent = 0
    correct_baseline = 0
    for step in test_slice:
        # Ground Truth Label
        y_true = step.next_q
        
        # Agent Prediction (tau 对应提交的预测)
        y_pred = predictions.get(step.tau, "INVALID")
        if y_pred == y_true:
            correct_agent += 1
            
        # Conditional Marginal Baseline
        cond_key = (step.X, step.act)
        if cond_key in counts and sum(counts[cond_key].values()) > 0:
            c_dict = counts[cond_key]
            y_base = max(c_dict.keys(), key=lambda q: (c_dict[q], -ord(q[1])))
        else:
            y_base = global_mode # 未见条件严格退回全局众数
            
        if y_base == y_true:
            correct_baseline += 1
            
    acc_agent = correct_agent / 9.0
    acc_base = correct_baseline / 9.0
    delta_d1 = acc_agent - acc_base
    passed = (acc_agent > acc_base) and (acc_agent >= 0.555) # 9 题中至少命中 5 题
    return delta_d1, passed
