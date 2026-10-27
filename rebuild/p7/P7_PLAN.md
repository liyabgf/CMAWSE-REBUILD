# P7 预注册计划（判据冻结于任何 P7 最终运行之前）

日期：2026-10-28 ｜ 基线：master@f53511e（P3–P6 完整，树净，P6 报告↔CSV↔日志抽查一致）。

## 数据隔离策略（冻结）

- P6 已用会话：s1（调参）、s5（留出）、s7（d6v3 全新验证）——**全部视为已参与开发决策，P7 不再作为独立测试集**。
- **P7 独立集：session 11 与 session 13**（grep 全仓确认从未出现；冻结后不得更换）。
- P7 主体类、标签组合、判定规则均先于运行写入本文件/脚本；运行后不回改。

## P7-A1：d6v3 独立验证（冻结判据）

- 判据（与 P6 相同，不改）：d6v3 = E(双射等变) ∧ R2(标签交换响应：交换前预测必须不同 + 交换后预测随之交换) ∧ I(顺序不变)。
- 新主体类（未参与 P6 开发，五类 + 投机探针）：partial_target_responder（部分表+硬编码标签）、seen_correct_unseen_fail（表学习+不敏感回退）、order_sensitive_equivariant（等变但对顺序敏感——I 分量必要性探针）、range_limited_degrade（仅 A 组正确越界退化）、tau_hash_rich（输出丰富与目标无关）、memoizer_gaming（首调缓存投机）。
- 分量必要性消融：E-only / E∧R2 / E∧I / R2∧I / 全量，逐配置记录误通过主体。
- 判定规则（冻结）：在 s11 与 s13 上，六类 P6 主体 + 六类 P7 新主体的判定必须与设计预期一致；若任一新主体被 d6v3 通过而其定义明确不含目标等变能力（memoizer、tau_hash_rich、range_limited、order_sensitive 除外——它们按定义应分别失败于 R2/R2/R2/I），记为失效反例。
- 已知范围声明（冻结）：seen_correct_unseen_fail 可能通过 d6v3——d6v3 测等变响应性不测正确性，若发生按"范围澄清"记录而非缺陷；正确性属 D1 职责。
- 停止条件：每会话每主体运行一次，不迭代。

## P7-A2：d1v2b 独立验证（冻结判据）

- 判据（同 P6 d1v2b）：pass = acc≥0.5 ∧ delta≥0.15 ∧ p_raw<0.05（McNemar 闭式，Bonferroni×6 报告）；基线 = P(Y|X) 边际众数。
- 新数据（冻结）：新 holdout_v2c N=30（12 信息 + 12 中性-同对象异动作 + 6 中性-C），会话 s11/s13；K 字段变化作无关扰动（条件 C 物理忽略 K——先核实 ground_truth_transition 源码后再用）。
- oracle 信息泄漏审计（冻结）：rule_oracle（由世界转移函数现算，不读存储标签）与 label_oracle（读 q['y']，P6 实现）预测必须逐条一致；若一致则 P6 oracle 优势=世界物理知识（被测能力的定义锚点），非存储标签泄漏；同时披露"oracle 优势来自预编码物理规则"这一定义性事实。
- 判定规则（冻结）：s11/s13 上 trivial 主体（constant/majority/random）不得通过；oracle 必须通过；语义保持变换（3 重命名 × 4 排列）零翻转。任一不满足 → d1v2b 降级。
- 阈值：[0,0.40] 敏感性只作本构造记录，不作普适依据。

## P7-B：真实 LLM 受控接入（冻结设计与可用性门）

- 设计（冻结）：四配置 A=脚本主体+全机制（确定性基线）、B=LLM 无隔离、C=LLM+全机制、D=逐项消融；8 类任务（合法/畸形/正确错误响应/越权读取/越权改写/多步冲突/重复与恢复/语义无效格式合法）；测量分离：正确性、目标关系、泄漏、变异、非法接受、记录完整、可追溯、恢复、成本。
- **可用性门（已探测，冻结记录）**：本机无 ollama、无 LM Studio（1234/8080/5001/11435/8000 端口探测无响应）、环境无 OPENAI/ANTHROPIC/DEEPSEEK/QWEN 密钥、CMAWSE 工作区无 .env。**若门不开 → NOT_RUN，如实记录，不以脚本主体冒充。**
- 已冻结的提示与案例模板随 LLM_CONTROLLED_EVALUATION.md 交付，供未来接入时原样执行。

## P7-C：Branch A 执行验证（冻结）

- 已核断裂面（冻结记录）：extracted/src/cmawse 无任何 __init__.py（包结构缺失）；测试导入的 cmawse.agent.cognitive_state / deliberation / representation 不在提取树（grep 全仓无类定义）；agent/llm_boundary.py 仅存在于 quarantine 且 compile=FAIL@L84（截断）；extracted 测试均需 pytest（已装 9.2.0）。
- 可自洽子集（冻结）：cmawse/world/bus.py + cmawse/core/schema.py（PrivateHorizon / PublicRealityBus / DefaultSpatialPolicy / DefaultWitnessPolicy）。
- P7 副本（REWRITTEN 包装，模块字节不变）：rebuild/p7/branch_a_copy/ —— 仅添加 __init__.py；副本模块与 extracted 的 sha256 逐一比对并记录。
- 认知隔离操作化定义（冻结）：私有 = 各主体 PrivateHorizon 内容（视野外主体坐标、衰减后不可闻声学、感官剥夺者的全部感知）；公共 = VerifiedEventEntry 经 witness 资格过滤后的账本；允许 = 只读消费自身 horizon、经仲裁提交动作；禁止 = 读取他人 horizon、越权写公共现实。
- 最小执行案例（冻结）：(1) 视距外主体不得进入 visible_actors；(2) horizon 冻结（变异被 pydantic 拒绝）；(3) 声学衰减阈值正确；(4) 感官剥夺者空视界；(5) 目击资格按视界过滤（非参与者+非视听范围 → 不合格；直接参与者 → 合格）；(6) generate_horizons 确定性重放。
- 判定规则（冻结）：6 案例中任一与定义不符 → Branch A 认知隔离主张记 INSUFFICIENT；全部通过也仅覆盖 bus/schema 子集，agent/cognitive 链维持 UNVERIFIED（缺模块，不得以子集结果外推）。

## 交付映射
README / P7_PLAN / P7_REPORT / P7_DECISIONS / D6V3_INDEPENDENT_VALIDATION.md + D6V3_RESULTS.csv / D1V2B_INDEPENDENT_VALIDATION.md + D1V2B_RESULTS.csv / LLM_CONTROLLED_EVALUATION.md（NOT_RUN 记录 + 冻结设计）/ BRANCH_A_EXECUTION_REPORT.md + BRANCH_A_RESULTS.csv / 脚本 + logs/。
