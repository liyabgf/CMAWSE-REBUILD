# P7-A2：d1v2b 独立验证报告

## 独立性

新会话 s11/s13 + 新构造 holdout_v2c（N=30：6×(A,act_beta) + 6×(B,act_gamma) + 6×(A,act_alpha) + 6×(B,act_alpha) + 6×(C,act_alpha)；X 边际基线在 12 条中性查询上系统性错）——组合与 P6 的 N=36 不同，判据（acc≥0.5 ∧ delta≥0.15 ∧ p_raw<0.05）与基线（X 边际众数）原样冻结，未看结果调参。

## 结果（D1V2B_RESULTS.csv，156 行，logs/A2_d1v2b.log）

两独立会话结论逐项一致：

| 主体 | acc | delta | b/c | p_raw | pass |
|---|---|---|---|---|---|
| constant_q0 | 0.600 | 0.000 | 12/12 | 1.0 | False |
| majority_class | 0.200 | −0.400 | 0/12 | 0.00073 | False |
| random | 0.467 | −0.133 | 7/11 | 0.48 | False |
| simple_baseline_v2 | 0.600 | 0.000 | 0/0 | 1.0 | False |
| learned_agent | 0.600 | 0.000 | 0/0 | 1.0 | False |
| **rule_oracle** | 1.000 | +0.400 | 12/0 | 0.00073 | **True** |

- 平凡主体全败（constant 的 acc=0.60 > 0.5 但 delta/检验双重拦截——分布失衡威胁在此构造下被中和）。
- **oracle 泄漏审计：rule_oracle（世界转移函数现算，不读存储标签）与 label_oracle（读 y）预测逐条一致**——P6 oracle 的优势不来自读取测试标签；它来自**预编码的世界物理规则**，这正是"被测能力"的操作化定义，如实披露：oracle 是能力锚点而非普通被试。
- 语义保持变换：3 重命名 × 4 排列 × 6 主体 × 2 会话 = 144 格，**结论翻转 0**。
- 无关扰动：换 context 重算 y 全部不变（30/30，源码核实 CONDITION_C 转移不使用 q/ctx）。
- 阈值敏感性：δ* ∈ [0, 0.35] 通过集恒为 {rule_oracle}（本构造内稳定；不作普适阈值依据）。

## 边界

- 结论限于 CONDITION_C 物理（(X,act)→Y 可由账本充分学习）与 N=30 平衡构造；其他条件/分布需重验。
- p=0.00073 为本 holdout 上分离显著性（N=30、12 不一致对）；主体均为确定性函数，无抽样方差，不外推随机主体总体。
- 判定：**PARTIALLY_SUPPORTED → 升格为 SUPPORTED（限条件 C 构造内效度）**；普遍效度（跨条件、跨分布、LLM 主体）仍未验证。
