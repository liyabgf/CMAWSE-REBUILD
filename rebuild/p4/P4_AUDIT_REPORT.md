# P4 审计报告：P3 独立复核 + D1 评估器效度

日期：2026-10-28 ｜ 环境：macOS / Python 3.13（仓库内复现命令见 §5）｜ 标记约定：EXTRACTED / REWRITTEN / UNRESOLVED

## 1. P3 独立复核（P4-A）

- Git 历史核实：`ac6911b`（REWRITTEN 引擎 + 提取树去伪件）与 `cbc52c4`（审计证据）内容与 P3 报告一致；P3 前工作树干净，既有日志未覆盖。
- 代码差异核实：对 v6 基体与 P3 产物做去注释 diff，语义差异**恰为报告所述两处**——F1 零似然软熔断（hold prior + 计数器 + 记录字段，5 行）与 F2 全局众数平局折断（1 行）。无其他语义改动。
- 独立重跑：v7 全量 7/7 OK（`logs/P4_v7_rerun.log`），CLI 重放 exit 0 且输出 "Canonical deterministic replay verified"（`logs/P4_cli_rerun.log`）。
- **与 P3 报告的不一致处：无。** P3 报告中唯一需要修正的细节由 P4-B 补充：holdout (X,act) 键在条件计数中的覆盖是 **2/9**（P3 报告写"9/9 未见"是措辞不精确；delta=0.7778 的算式与 2/9 覆盖一致）。

## 2. D1 效度审计（P4-B）——现象独立重建，非复述

`d1_audit.py`（REWRITTEN）不调用 run_session，直接驱动世界组件重演 Phase-1/2，与引擎记录做 json 规范化比对：**一致（True）**。实测：
- 训练账本全局计数 {q1:7, q2:7, q0:7}（结构性三方平局：`objects[tick%3]` 均匀轮转 × 21 步 × oracle 确定性策略）；首次出现序 [q1,q2,q0]。
- holdout 9 条查询真值全为 q0；(X,act) 键在条件计数中覆盖 2/9，未覆盖 7/9 全部落全局众数。
- alpha 规则：gm=q0 → acc_base=9/9 → oracle delta=0 → fail（档案版行为，与 P2 门禁一致）。first 规则：gm=q1 → acc_base=2/9 → oracle delta=0.7778 → pass（P3 行为）。

## 3. 敏感性与效度威胁（核心结论）

`D1_SENSITIVITY_MATRIX.csv`（1008 行：4 场景 × 7 排列 × 3 标签映射 × 3 平局规则 × 4 主体）实测：

- **三种平局规则（alpha/first/last）在 real 场景下 d1_pass 都随语义无关的排列/命名在 {0,1} 间翻转。** alpha 在"标签重命名 z0/a1/m2"下 oracle 变 pass；first 在"账本反转/洗牌"下 oracle 变 fail；last 同样敏感。确定性 ≠ 无偏：**D1 的判定依赖账本顺序与标签命名这两个与预测任务语义无关的自由度**，此为已证实的效度威胁（对档案版与 P3 版同样成立）。
- **holdout 退化**：9 条查询真值全 q0 ⇒ 任何"恒答 q0"的主体 acc=9/9。在 first 规则 + 原始顺序下，naive_q0 的 delta=0.7778、random 的 delta=0.3333——**与 oracle 同过**。v7 协议里 dummy 之所以 fail，是因为 dummy 跑自己的会话、其账本 q0 占绝对多数 → 自身基线=完美预测器 → delta=0。即：**oracle/dummy 的区分来自各自账本的统计形态，而非 D1 对预测能力本身的辨别力**。
- **oracle 的信息分支为死代码**：v7 oracle 为 (A,act_beta)→q1、(B,act_gamma)→q2 准备的分支在现 holdout 上永不触发（查询生成器不产此键）——强烈暗示最终态的查询生成器与在档版本不同，但档案内无证据可裁决：**UNRESOLVED**。
- **规格-实现落差**：档案 L54312 的正式判据为 PASSED ⟺ p_perm < α_prereg(0.01) ∧ Δ̄_D1 ≥ δ(0.15)——含置换检验；提取出的 evaluate_d1 只实现 delta/acc 两项，**无置换 p 值**：UNRESOLVED（规格要求的统计检验缺失于所有在档实现）。
- **阈值 0.15**：有档案依据——L54316 参数预注册（"比条件边际基线多命中至少 1.35 个样本点"），属预注册效应量门限；1.35 点这一量级本身的推导依据未给出：**部分 UNRESOLVED**。
- **数据泄漏检查**：d1_queries 构造时显式剔除 true_label（引擎与孪生均验证）；未发现标签泄漏。基线选择偏差存在（条件众数基线在覆盖键上=完美预测器，见 §3 第 2 条）。

## 4. 效度判定（与"能否通过测试"分开陈述）

- **代码能否通过测试**：能。P3 REWRITTEN 引擎对 v7 原断言 7/7（三次运行一致），此为一致性事实。
- **D1 是否有效测量"优于基线的预测能力"**：**不充分（INSUFFICIENT）**。三条已证实缺陷：判定对账本排列/标签命名敏感；holdout 标签分布退化使平凡主体不可区分；规格要求的置换检验未实现。P3 的 F2 修复恢复了"测试通过"，但**没有恢复 D1 的效度**——两者是不同命题，本报告分开判定。
- 结论限定：以上针对 Phase II 微型环境下的 D1；不外推到 Branch A 的 D1 相关审计（未在本轮执行，UNVERIFIED）。

## 5. 复现

```bash
cd /Users/liyang/Documents/CMAWSE-REBUILD
python3 rebuild/p4/d1_audit.py            # §2-3 全部数字与 CSV
python3 rebuild/p4/exp_boundary.py        # E1
python3 rebuild/p4/exp_failclosed.py      # E2
cd rebuild/out && PYTHONPATH=. python3 ../../extracted/phase2/harness_v7_L62449.py   # 7/7
```

## 6. 事实/观察/推断/未决 分层

- 已证实事实：§1 全部；§2 全部（脚本实测）；§3 敏感性翻转（矩阵实测）；阈值预注册存在（L54316 原文）。
- 实验观察：E1/E2 数字（见 P4_EXPERIMENT_DESIGNS.md）。
- 解释性推断：最终态查询生成器与在档不同（由 oracle 死代码分支推断，UNRESOLVED）；v7 协议中 oracle/dummy 分离依赖各自账本统计（由矩阵与 dummy 会话实测推断）。
- 未解决：置换检验缺失、1.35 点量级依据、查询生成器历史形态、P3-U 系列（继承）。
