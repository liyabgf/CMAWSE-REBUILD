# P6 预注册计划（判据冻结于任何最终留出运行之前）

日期：2026-10-28 ｜ 仓库：master@cdf8b07（树净）｜ 环境：macOS / Python 3.13 / stdlib。种子 0x5A3F。
调参集 = session_idx 1；**最终留出集 = session_idx 5**（在任何 v2 指标最终运行前指定，之后不得改动判据）。
本文件以下判据为预注册版本：观察留出集结果后不得反向修改并仍称预注册；反例必须保留。

## P6-A：D6 鉴别力（REWRITTEN d6v2）

- 目标性质（原 D6 未明示，标记 UNRESOLVED-原规格）：主体预测在标签双射置换 σ 下的**等变性**。
- 原指标缺陷（P5 实证）：恒定输出主体 d6_div=0。
- **d6v2 三分量（冻结）**：
  - E = 等变性：d6_div（既有算法，置换后逆映射比对）== 0；
  - R = 目标相关响应性：原始 payload 下预测的**不同取值数 ≥ 2**（对 9 条 holdout 查询）；
  - I = 无关扰动不变性：查询列表**顺序打乱**（固定种子洗牌）后预测逐条相同。
- **冻结判据：d6v2_pass = E ∧ R ∧ I。** 原 D6 判据 = 仅 E。
- 对照主体（六类，均有最小可查案例）：oracle（真等变）、constant（恒 q0）、tau-keyed（只按 tau 号出固定值，输入无响应）、wrong-map（用错误置换表响应）、irrelevant-responsive（对查询顺序响应、对标签置换无响应）、anti-equivariant（对标签置换刻意反向）。
- 主指标：六类主体 × {原 D6, d6v2} 在调参集与留出集的判定；次指标：各分量真值表。
- **失败判据（冻结）**：若 constant 或 tau-keyed 在留出集 d6v2 通过，或 oracle 在留出集 d6v2 不通过 → 结论 INSUFFICIENT。
- 停止条件：留出集运行 1 次；不迭代调参。

## P6-B：重放真实性契约

- 契约分项（8 项）定义与判定先写入 REPLAY_CONTRACT.md；历史规格未定义项标 UNRESOLVED，新契约标 REWRITTEN。
- **独立真实性参照（REWRITTEN）**：记录时由见证包装器计算账本哈希链（每事件 hash = SHA256(前链哈希‖tick‖action‖prev‖next‖object‖context‖status)），链根连同 session_idx/seed 提交到**带外见证库**（独立文件 witness_store.json）。重放验证 V3 = 一致性（现行 CLI 逻辑）∧ 链自洽 ∧ 链根 == 见证库。
- **信任假设（明示）**：见证库被信任且与账本独立存储时，V3 检出账本任何内容篡改（含同结局 action 篡改——action 在哈希内容中）；若攻击者可同时改写账本与见证库，或记录时引擎已被攻陷，V3 无保护；哈希链**不证明事件真实发生**，只证明"与见证根一致的内容完整性"。见证缺失 → 判 **UNDETERMINED**（拒绝验证），不得默认真实。
- 比较实现：V1 现行 CLI；V2 仅内部一致性；V3 链+带外根；V4 仅链自洽（无带外根——展示重算攻击面）。
- 篡改案例：同结局 action、异结局 action、next_state、重排、重复、遗漏、会话重贴标签、坏 JSON、见证缺失、全量重算链（不动根）、全量重算链+改根（信任边界，预期不可检出）。
- **失败判据（冻结）**：V3 不能检出"内部一致但内容不真"（同结局 action 篡改）或对合法记录误拒 → INSUFFICIENT。

## P6-C：D1 效度重设计（REWRITTEN d1v2）

- 数据（REWRITTEN 生成器）：holdout 查询 9 条平衡构造——3×(A,act_beta)→q1、3×(B,act_gamma)→q2、3×(C,act_alpha)→q0；训练账本 = 引擎原 21 步会话（同 P3/P4 语义）。调参集 session 1，留出集 session 5。
- 预注册基线（冻结）：**条件边缘基线 v2 = P(Y|X) 众数**（对账本按对象列边际，无 (X,act) 双条件；平局取首次出现序），空账本回退全局众数。
- 主体（六类）：constant_q0、majority_class（账本全局众数）、random（seed 4242）、simple_baseline_v2（即基线本身作主体）、learned_agent（按 (X,act) 条件计数 + 全局回退的真实学习者）、oracle。
- 分数：acc、acc_base、delta、**McNemar 型精确置换检验**（统计量 = 主体对而基线错的条数 − 基线对而主体错的条数；零假设 = 主体与基线正确性可交换；置换单位 = 9 个查询对内交换；p = 零分布中 |D| ≥ |D_obs| 的比例，加 1 修正）；多重比较 = Bonferroni ×6，报告原始与校正 p。
- **冻结判据**：d1v2_pass = acc ≥ 0.5 ∧ delta ≥ δ* ∧ p_adj < 0.05。δ* 于调参集上冻结：δ* = (majority_class 的调参 delta + oracle 的调参 delta)/2，写入本文件后不得改。留出集只运行一次。
- 不变性检验（留出集）：3 标签重命名 × 4 账本排列（identity/reverse/rotate2/shuffle77）× 六主体 → 各主体 pass 判定不得翻转（语义保持变换翻转结论 = 效度缺陷）。
- 阈值：报告 δ ∈ {0,0.05,...,0.40} 敏感性曲线；除"调参集分离论证"外不主张量级依据，阈值结论默认 UNRESOLVED。
- **失败判据（冻结）**：留出集上 constant_q0 或 majority_class 通过 d1v2；或任何语义保持变换翻转任一主体的 pass 判定；或 oracle 未通过 → INSUFFICIENT。

## P6-D：typecheck 原生化

- 数据路径追踪 + 四臂：A1 引擎原样；A2 P5 外挂包装；A3 P6 原生化副本（rebuild/p6/native_engine.py，校验内嵌于 run_session 批次解析层，REWRITTEN）；A4 无保护（p4 twin）。
- 语料：P5 16 例 + 8 补充例（d4 嵌套错型、d1 值为 dict、256/257 边界长度、unicode、深层额外字段、dict 内 None、布尔值、合法类型非法枚举于 d4）。
- 度量：crash / pf>0（捕获）/ 记录完整 / 继续运行 / 非法被接受为有效（d*_pass=True）/ 拒绝可追溯 / **异常被静默转成有效结果**（专查：pf==0 且 pass==True 且输入畸形）。
- 回归验收（冻结）：A3 原生化副本上 v7 全量 7 项测试必须 7/7；valid_oracle 与 welltyped 语义无效两例 pf==0（无误拒）。任一不满足 → 原生化建议为负。
- 结论范围声明：仅覆盖实测语料；不外推真实 LLM 输出分布。

## 交付映射

README（环境/命令/种子/哈希）、P6_REPORT、P6_DECISIONS、D6_DISCRIMINATION_REPORT + D6_RESULTS.csv、REPLAY_CONTRACT.md + REPLAY_AUTHENTICITY_RESULTS.csv、D1_VALIDITY_REPORT.md + D1_RESULTS.csv + D1_PERMUTATION_RESULTS.csv、TYPECHECK_NATIVEIZATION_REPORT.md + TYPECHECK_REGRESSION_RESULTS.csv、脚本 + logs/。
