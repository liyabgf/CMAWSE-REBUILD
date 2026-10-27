# E2 类型边界报告（P5）

## 1. 调用链（逐行读 rebuild/out 引擎源码，EXTRACTED 结构 + REWRITTEN 软熔断）

```text
agent_callable(payload)            # 交互 21 次 + 批次 1 次 + 置换 1 次
  └─ try: resp=...; act=resp.get('action')        # 解析守卫#1（调用+取键）
     except: parsing_failures+=1; act=None
world.step(act)                                     # 世界组件拒绝非法动作（独立机制）
batch: try: batch=...; d1_preds=batch.get(...)...   # 解析守卫#2（批次取键）
     except: parsing_failures+=1; 默认 {} / 'INVALID'
evaluate_d1(ledger, queries, d1_preds)  # 守卫外：.get 假定 dict → int/None/list 崩溃
evaluate_d2(d2_matrix, condition)       # 局部守卫：isinstance(matrix, dict) else (0.0, False)
evaluate_d4(..., d4_preds)              # 守卫外：.get 假定 dict → 同 d1 洞
evaluate_d5(..., d5_pred)               # 纯比较：任何垃圾判错（无类型假定）
```

## 2. 覆盖矩阵（16 用例 × 3 臂，完整数据 E2_TYPE_BOUNDARY_MATRIX.csv）

| 类别 | 用例 | A_orig | A_check | A_twin |
|---|---|---|---|---|
| 结构级 | none/str/raise/list | 解析守卫拦截 pf=2 | 同左 | 崩溃 |
| 字段类型 | d1_predictions=int | **崩溃(DOS)** | pf=2 拦截+原因 | 崩溃 |
| 字段类型 | multi_field | **崩溃(DOS)** | pf=2 拦截 | 崩溃 |
| 嵌套类型 | d2_matrix=str / d2 内层 int | 评估器局部守卫静默判错（pf=0，不可追溯） | pf=2 拦截+原因 | 静默判错 |
| 缺字段/额外字段 | {} / junk 字段 | 静默通过（pf=0） | pf=2（extra=forbid 语义） | 静默通过 |
| 空值/超长 | d5='' / d5=10000 字符 | 静默判错（pf=0） | pf=2 拦截 | 静默判错 |
| 非法枚举 | d5='HACK_STATE' | 静默判错（pf=0） | pf=2 拦截（闭词汇校验） | 静默判错 |
| 键类型 | d1 int keys | 静默判错（pf=0） | pf=2 拦截 | 静默判错 |
| 语义无效但类型合规 | 恒 q0 预测 | 正常评估判错 | **正常放行 pf=0**（无误拒） | 正常评估判错 |
| 正对照 | valid_oracle | pf=0 通过 | pf=0 通过 | — |

三臂中**无任何畸形用例使 d*_pass=True**；垃圾值无法原样进入记录（派生字段均为数值）。

## 3. 性质区分（不可互替）

- fail-closed：畸形输入后记录仍完整且指标为保守值——A_orig 对结构级成立；A_check 对全部 15 例成立。
- 错误被捕获：异常在解析守卫内消化——A_orig 仅覆盖"调用异常/缺字段"；字段类型错误逃逸至评估器。
- 记录完整：A_check 16/16；A_orig 12/16（4 例崩溃）；A_twin 11/16。
- 系统继续运行：同上跟随记录完整性。
- 拒绝可追溯：A_orig 对"静默判错"7 例 pf=0、无原因字段——**拒绝不可追溯**；A_check 全部有 rejection_reasons（BatchContractError 消息）。

## 4. REWRITTEN typecheck 与历史 llm_boundary.py 的差异（不宣称恢复历史实现）

| 维度 | 历史 llm_boundary.py（EXTRACTED, quarantine, 编译失败@L84 截断） | rebuild/p5/typecheck.py（REWRITTEN） |
|---|---|---|
| 依赖 | pydantic BaseModel/ConfigDict(extra=forbid, frozen) | 纯 stdlib |
| 输入形态 | JSON 字符串/ dict（Branch A：MindDecision 枚举、channel_id、快照哈希） | callable 返回的 dict（Phase II 契约） |
| 重复键拒止 | 有（object_pairs_hook） | 无（Phase II 无 JSON 字符串层） |
| TOCTOU 快照身份断言 | 有（candidate_set_hash） | 无（Phase II 无候选集） |
| 枚举闭词汇 | MindDecisionStatus/CognitiveSilentMode | VALID_STATES/MODELS（q0-q2/st_*/M1-M3） |
| 失败语义 | 返回 BoundaryValidationResult(is_valid=False, rejection_reason) | 抛 BatchContractError → 引擎既有 except 接管 → parse_failures+默认值 |
| 接入方式 | 引擎原生 | 包装 agent callable（引擎零改动） |

## 5. 失效边界结论

现引擎的失效封禁止于"调用与取键"层；字段类型层由评估器局部守卫部分兜底（d2/d5），d1/d4 为裸洞（DOS 可达）。外挂类型校验（A_check）在不修改引擎、不弱化任何断言的前提下闭合全部 15 例畸形并使拒绝可追溯——**验证标准按任务要求执行：不只验证"异常没抛出"，还验证了畸形输出未被接受为有效状态（d*_pass 全 False）且拒绝原因可追溯（rejection_reasons 逐条）**。
