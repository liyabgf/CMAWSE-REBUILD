# P4-D 后续实验：可证伪设计与实际运行结果

两项实验均已在仓库内**真实运行**（非设计稿），日志：`logs/E1_boundary.log`、`logs/E2_failclosed.log`、`E2_FAILCLOSED_MATRIX.csv`。选择标准：直接检验"LLM 不可靠时，显式系统约束能否限制错误后果"。

## E1 信息边界与变异封禁（已运行）

- **假设 H1**：CMAWSE 的投影+深拷贝机制使 (a) 潜变量对 agent 不可见、(b) agent 原位篡改账本不感染运行时；通用执行循环两者皆不成立。
- **实验组**：REWRITTEN 引擎（rebuild/out）。**对照组**：GenericHarnessTwin（rebuild/p4/generic_twin.py，REWRITTEN）——同一世界组件、同一 oracle 种子派生、同样的 21+1 调用结构，但无投影/无深拷贝/无解析守卫。
- **自变量**：harness 类型。**因变量**：潜变量暴露次数（探针 agent 计数）、账本感染条数（MUTATED_BY_AGENT）、非法动作提交数、评估字段完整性。**控制**：agent=v7 原版 AdversarialAgent 语义+键探针；CONDITION_C；seed 0x5A3F；session 0。
- **失败判据**：CMAWSE 组感染>0 或泄漏>0；或 twin 组两者皆 0。
- **可证伪预测**：CMAWSE (0/21, 0)，twin (21/21, ≥1)。
- **实际结果**：CMAWSE 暴露 0/21、感染 0、非法提交 0、字段齐全；twin 暴露 21/21、感染 1、非法提交 0、字段不齐（无 d6）。
- **解释**：H1 成立。非法动作拒绝两组同为 0 → 该性质来自**世界组件**（机制归属修正：不是循环的功劳，也不是 harness 层的独有机制）。
- **局限**：单种子单条件；twin 是刻意最小对照，真实通用框架可能自带隔离（届时性质仍成立，只是归属变为"框架已实现该显式机制"）；感染只测了 next_state 字段。

## E2 失效封禁（已运行）

- **假设 H2**：显式解析守卫使 CMAWSE 在 LLM 输出畸形时仍产出完整可审计记录；通用循环崩溃。
- **主体族**：oracle / dummy / adversarial / malformed_none / malformed_str / malformed_raise / malformed_type / partial_batch（8 类 × 2 harness = 16 组）。
- **因变量**：崩溃（异常类型）、账本感染、非法提交、记录完整性、parsing_failures。
- **失败判据**：CMAWSE 任一畸形主体崩溃或感染；或 twin 全部安然。
- **可证伪预测**：CMAWSE 8/8 无崩溃；twin ≥3 崩溃。
- **实际结果**：CMAWSE 7/8 无崩溃（None/str/raise 均 parse_fail=23、记录完整），**malformed_type 击穿**（AttributeError: 'int' object has no attribute 'get'——评估器在守卫之外假定 dict）；twin 4/8 崩溃（全部畸形类）。
- **解释**：H2 大体成立但有实测缺口——引擎的失效封禁止于"调用与取键"层，未覆盖"字段类型"层；档案中 llm_boundary.py 的严格类型边界（EXTRACTED，未执行）正是补此缺口的组件，Phase II 引擎未接入。twin 的崩溃面更大（连 partial_batch 之外的 None 都崩）。
- **局限**：畸形族为手工构造，未覆盖真实 LLM 故障分布；崩溃后的部分状态未检查（twin 崩溃即无记录）。

## 待实施（材料不足，不伪造）

- **E3 重放等价负对照**：篡改 1 bit 种子/1 条账本 → CLI 必须报错。缺项：无（可直接实施，本轮未排入）。
- **E4 D6 对抗主体**：构造记忆元标签的 agent → d6_divergence 必须 >0。缺项：无。
- **E5 D1 效度修复验证**：修复查询生成器（使 oracle 信息分支非死代码）+ 接入置换检验后，oracle/naive/random 应分离。缺项：**最终态查询生成器形态在档案中不存在（UNRESOLVED）**，只能按规格新设计并标 REWRITTEN。
