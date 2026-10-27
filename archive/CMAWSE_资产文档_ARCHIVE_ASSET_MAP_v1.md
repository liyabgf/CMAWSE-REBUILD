# CMAWSE 工作区资产文档（ARCHIVE ASSET MAP — FINAL）

**文号**：CMAWSE-ASSET-DOC-2026-v1.1（v1.1：补全全量读取覆盖核验，新增 F6/F7 发现）
**性质**：档案梳理成果固化（本文档为新增文件，未改动任何既有文件）
**梳理范围**：/Users/liyang/Documents/CMAWSE 全部 20 个实体文件（4 个 Markdown/TXT 导出 + 16 个 PDF + 11 个 .pages 快照）
**信息来源**：3 个对话导出文本 + PDF 内容提取交叉核验；关键结论均标注物理文件与行号。

---

## 一、物理结构总判

**本工作区不包含任何代码。** 无 src/、tests/、specs/、reports/、benchmarks/ 目录；对话中引用的全部 .py、规范、报告文件均只存在于对话文本内部。历史上 PASS 1.5 审计所统计的"58 个物理文件"指向的是另一个工作区状态，当前目录是其文档化存档，而非项目本体。因此档案中所有 "60/66 passed"、"135 tests"、"C31–C65" 均为对话内文本声称，在本工作区不可执行复验。

**实体构成**：8 段独立对话导出，合计 3,850,626 tokens；外加若干单篇报告 PDF 快照与最终闭环归档。文件 mtime 集中于 2026-09-08 至 09-10 05:12（约两天内落盘），而文档内部自述时间线为 2024-03～2024-07；物理时间仅反映"归档动作"的顺序，不反映项目时序。

---

## 二、对话与文件对照表（文件 → 对话身份）

| 物理文件 | 内容（对话标题 / tokens） | 备注 |
| :--- | :--- | :--- |
| CMAWSE启动.md | 「CMAWSE 复杂叙事仿真引擎架构」120,377 | 白皮书原型 + 因果仲裁代码讨论 + Dify/本地模型可行性问答 |
| CMAWSE第一阶段.md | **5 段拼接** | 总 2,244,673 tokens |
| ├ L1–23242 | 「CMAWSE v1.2 系统构建规范」544,605 | 白皮书→Phase 1 核心→Phase 2 全程 |
| ├ L23243–30446 | 「CMAWSE 3.1.5 契约一致性修复」173,687 | Phase 3.2.3 起 |
| ├ L30447–49030 | 「CMAWSE 审计一致性最终闭环」344,962 | Phase 3.2.6 终局（containment 语义冲突闭环） |
| ├ L49031–50133 | 「CMAWSE 系统架构深度评析」497,232 | 无对应 PDF |
| └ L50134–63032 | 「CMAWSE 系统独立重建研究」684,187 | Reconstruct-v2 + Micro-World 0.3~1.0 + v1.0.x + Phase II 全程 |
| Evidence Registry.md | **2 段拼接** | 总 1,485,576 tokens |
| ├ L1–4203 | 「CMAWSE 档案考古索引构建」756,606 | PASS 1 / 1.5 / 2 → 证据账本 → 二阶/三阶审计 → SPEC v0.1 + SCHEMA v0.1 |
| └ L4204–5428 | 「CMAWSE Schema 粒度加固」728,970 | Registry Validator Phase 1/2 → Phase 3.1–3.7 |
| 整理执行一.txt | 同上一段对话的纯文本导出 | 与 Evidence Registry.md L4204+ 内容同源 |
| CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md | 编译版闭环归档 | **全工作区唯一含 Phase 3.8 的文件**；最后写入（09-10 05:12） |

**PDF / .pages 快照映射**（均为上述对话或其中单篇报告的导出）：

| PDF | 对应内容 |
| :--- | :--- |
| CMAWSE（1.2存档）.pdf | v1.2 白皮书（CMAWSE-ARCH-2024-REV3, IP 注册版）；字体子集无 ToUnicode，机器提取乱码，可用文本版在 CMAWSE第一阶段.md L7–330 |
| 执行阶段一.pdf | 「v1.2 系统构建规范」快照（543,782 tokens，略早于 md 版 544,605） |
| 执行阶段二.pdf | 「CMAWSE 3.1.5 契约一致性修复」快照 |
| 实现和实验数据.pdf | 「审计一致性最终闭环」快照（Phase 3.2.5 矛盾修复全程） |
| CMAWSE Phase II阶段存档.pdf | 「系统独立重建研究」快照（Reconstruct-v2 全文 + Micro-World 数据） |
| CMAWSE_v1.0.2_Implementation_Frozen_Spec.md.pdf | BLOCK-14 终审 + Hmid-3 UCS 形式化契约 |
| CMAWSE v1.0.3 Freeze Candidate 规范与实现修订报告.pdf | v1.0.3 候选规范 + RUNNER/TEST_SUITE/NOTES/CHANGELOG 产物 |
| Phase II Pre-Pilot Forensic Audit：…领先于实际 evaluator 实现。.pdf | Phase II Forensic Audit v2（DEF-01~04 修复） |
| CMAWSE Phase II: 规范完备性与可实现性法医审计报告 (v0.1).pdf | BLOCKED-BY-SPEC 终审报告 |
| 当前阶段.pdf | 「档案考古索引构建」快照（PASS 1 起点时刻） |
| Evidence Registry碰真实数据前存档.pdf | Registry Validator Phase 2：31 个对抗 fixture 实施报告 | ⚠ 全工作区唯一含独有内容的 PDF（详见 F6） |
| 当规范存在于自然语言文档，….pdf | Phase 3.2 规范漂移法医取证（含 ARCHIVE MARKERS） |
| CMAWSE_Evidence_Registry_Schema_Drift_Conformance_Repair_Phase3.1-3.3.md.pdf | Phase 3.3 最小符合性修复 |
| Registry Structural Validity ≠ …（Phase 3.6）.pdf | 语义/数值完整性审计（7 攻击面） |
| CMAWSE Evidence Registry Phase 3.7.pdf | 样本单元去重与三元等式修复 |

---

## 三、项目演进脉络（六阶段主线）

**阶段 0｜史前（档案缺位）**：角色卡 → 漫品铺子 → 动态社会模拟。仅被 PASS 2 的 [ASSET-10] 引用（docs/explorations/*），本工作区无实体。

**阶段 1｜v1.2 白皮书与 Branch A（计算叙事学运行时）**：六大公理（状态从属、因果隔离、做功阶梯 ΔE₁–ΔE₄、零事件轮、主体间性、大纲自愈）+ 五平面拓扑（Narrative/World/Agent/Causal/Event Ledger/Rendering）。Phase 1 落地 schema/ledger/committer(RFC 6902)/arbiter 四件套；Phase 2 经历 NO-GO → 8 条红线 → GO 的语义加固；三次 500-Tick 与青州 200-Tick 实验。

**阶段 2｜同构定罪（范式断裂点）**：现实青州 vs 赛博青州因果图 8 阶段 1:1 双射同构，RETRACTED CLAIM 01「自发文学涌现」被推翻。其后 Field ≠ Environment 认识论重构（Field 升级为 Causal Modifier 的审计与缺口分析）。

**阶段 3｜Branch A 认知层收尾**：Phase 3.2.3–3.2.6 四维正交审计（语义性质×审计确定性×架构拦截×主权完整性，135 tests）；Phase 3.3.0 非自愈严格解析器与供应商契约（20 类攻击全拦截）。核心工程教训：architectical_containment 的「拦截/穿透」语义冲突必须显式解耦。

**阶段 4｜Branch B（因果基准）与 Phase II 阻断**：Reconstruct-v2 宣告与文学修辞决裂，剔除 Layer D（不可操作化的内部表征假设），建立 L0–L3 匿名微世界。核心负结果：53.3%（16/30, p=0.856）、51.6%（33/64, p=0.859）、D=0.367（分母 60→30 修正后）、+20%（动作词语言先验主效应）。规范演进：v1.0.1 → v1.0.2（BLOCK-11~14，Hmid-3 由 A* 改为确定性 UCS）→ v1.0.3 FREEZE-CANDIDATE（C40 跨平台 = UNVERIFIED）。Phase II D0–D6 harness 三轮法医修复（DEF-01 NameError、DEF-02 伪双射置换、DEF-03 Wilcoxon-Pratt、DEF-04 字段泄露）后，工程门禁 EXECUTION-READY，但规范完备性审计终审 **BLOCKED-BY-SPEC**（D4 端点 ctx 旁路无效；Hmid-1/4/5/6 无闭式）。

**阶段 5｜方法论清算（档案考古与三阶审计）**：PASS 1（36 条目，覆盖不可靠）→ PASS 1.5（实测 58 文件、18 缺口；确立 CANDIDATE ≠ FROZEN、Branch A/B 断裂、10 个转折点、5 条 RETRACTED/SUPERSEDED 声明）→ PASS 2（10 个 ASSET、5 个最小研究对象、11 个开放问题、8 条 Do-Not-Publish）→ 证据账本 v0.1 → 二阶审计判 SUBSTANTIVE_EVIDENCE_INFLATION（十项修辞越界）→ 三阶审计判 SUBSTANTIVE_PROVENANCE_FAILURE（数字拼接/分母混淆/总结通胀），产出唯一合法数字登记表 REG-01~10 与严格定界科学立场。

**阶段 6｜Evidence Registry 闭环**：SPEC v0.1（14 原则、DAG 拓扑、ScopeDTO 范围防火墙、总结反通胀、语言黑名单）+ SCHEMA v0.1 → Validator Phase 1 → Phase 2（31 fixture / 12 攻击类）→ Phase 3.0 原型登记（6 PASS / 4 FAIL）→ 3.1 SCHEMA_DRIFT_FOUND → 3.2 CONFIRMED → 3.3 CONFORMANCE_RESTORED（删 11 漂移枚举，60 tests）→ 3.4 真实复核（3 PASS / 7 FAIL，REG-06/07/08 假通过揭穿）→ 3.5 推翻「规范局限」叙事（REG-09=OUT_OF_SCOPE、REG-10=CATEGORY_ERROR）→ 3.6 定界 STRUCTURAL_PLUS_PROVENANCE（数值重算/载荷验签/科学真值 = ABSENT）→ 3.7 三元等式封堵重复 ID（66 tests）→ 3.8 REGISTRY_V0.1_CLOSURE = CLOSED。

---

## 四、本次独立核验发现（档案内未被记录的结构性事实）

**F1｜两个互不相容的「Schema v0.1」。** 对话一内嵌的 CMAWSE_EVIDENCE_REGISTRY_SCHEMA_v0.1.md（Evidence Registry.md L3941–4188）与 Phase 3.1 审计作为基线引用的「Schema v0.1」（L4339 起 / 整理执行一.txt L164–174）枚举值集大面积互斥：前者合法定义 DERIVED_REPORT（且有 RULE-DAG-03 专门管辖）与 GENERAL_SCIENTIFIC_CLAIM；后者将二者判为漂移并在 Phase 3.3 删除。前者 EvidenceRecord 为单数 sample_unit_id、无 granularity、control_type 三元组为 {TREATMENT, NEGATIVE_CONTROL, SHAM_CONTROL}；后者为 sample_unit_ids + EvidenceGranularity + ConditionType {CONTROL, TREATMENT, COUNTERFACTUAL} + SampleUnitType。即：Phase 3.3「未修改 Schema v0.1」只对第二份文档成立；两份同号文档之间的 v0.1→v0.1 词汇置换本身从未被任何审计覆盖。

**F2｜REG-01~10 原型发生词汇迁移。** SPEC v0.1 登记时使用 schema#1 词汇（STATUS: ACTIVE，L3611–3635）；Phase 3.4 复核时 REG-01 被表述为 schema#2 词汇（AGGREGATE, REPORT, EMPIRICAL_FACTOR, VERIFIED，L4826）。Phase 3.5/3.8 的「Schema v0.1 边界自洽、严禁推进 v0.2」结论建立在第二套词汇之上；第一套词汇下的原型合法性从未被复核。

**F3｜符合性基线文档缺位。** 第二份「Schema v0.1」的正文在本工作区不存在，仅以 Phase 3.1 审计报告中的引用形式出现。漂移判定、删除清单、60 项测试全部针对一份无法在档核验原文的基线。

**F4｜Phase 3.8 无对话出处。** 全工作区仅闭环归档 md 含 Phase 3.8 / REGISTRY_V0.1_CLOSURE 文本；对应对话导出止于 Phase 3.7。CLOSED 终审裁决缺少逐字 transcript 溯源，与该档案自身「审计报告闭合状态不得领先于实现」的纪律（见 Phase II Pre-Pilot Forensic Audit 标题）构成同型风险。

**F5｜快照与导出存在版本差。** 执行阶段一.pdf 为 543,782 tokens 的较早快照，md 为 544,605 tokens 的较晚导出；PDF 族整体是归档过程中按阶段逐段导出的产物，写盘顺序与项目阶段一致（Phase II PDF → Registry PDF → 大 md → 闭环归档，最终文件为闭环归档 md，09-10 05:12）。

**F6｜工作区唯一含独有内容的文件：Evidence Registry碰真实数据前存档.pdf/.pages。** 经全文探针比对（28 字符归一化采样 + 标识符检索），其余 15 份 PDF 的信息全部被 MD/TXT 语料覆盖（低分者均为提取失真，标识符核验零缺失）；唯独此文件（Registry Validator Phase 2：Adversarial Fixtures 报告全文，3,052 字符）的内容——31 个 fixture、12 大攻击类别、24 项越界全部拦截（Fail-Closed）、fixture_pass_01~06、ContainerShapeMismatchError 健壮性建议、"当前是否可以进入真实 Registry prototype validation：可以进入"的裁决——不存在于任何文本文件。原因：Evidence Registry.md 第二段对话（Schema 粒度加固）的导出只保留了 Phase 2 的模型思考摘要，跳过了报告正文。该报告因此成为 Schema v0.1 词汇争议（F1）的关键物证：它声明"Schema/Validator 无冲突"，且以 schema#1 词汇合法使用 DERIVED_REPORT / GENERAL_SCIENTIFIC_CLAIM / DIRECTLY_TRACEABLE / ACTIVE，并引用 16/30、33/64、11/30 分母规范——即 Phase 3.1 判定"漂移"之前，实现层曾与 schema#1 完全对称。此物证在 Phase 3.1–3.8 全链审计中从未被引用。

**F7｜PDF 无截图内容，.pages 无独有内容。** 全部 16 份 PDF 仅含 0–1 个图片 XObject（对话导出型 PDF 中的那 1 个为 1.6KB 级小附件，非信息性截图），此前 FlateDecode 高计数均为文本内容流。11 个 .pages（IWA/Snappy 包）经字面量段字符串提取 + 与 PDF 孪生/语料库交叉比对（可疑片段逐条复核，均在 CMAWSE第一阶段.md 对应段落命中），确认无任何独有内容；.pages 与 PDF 孪生的 mtime 配对（相差 0–1 分钟）证明为同源导出。.pages 正文未做逐字节全文解压（自实现 Snappy 解包器在 Document.iwa 主块上失步），此结论基于字面量片段级核验，非全文比对。

---

## 五、当前合法科学立场（承自三阶审计，禁止外推）

1. **工程事实**：纯标准库的 StateCommitter + EventLedger + 边界校验架构，在既有测试集内对非法指令/格式畸变实现 100% 拦截、快照零污染。
2. **受限负结果**：特定轻量模型画像在 30 对全匿名离散轨迹中，预测 53.3%（p=0.856）、分歧率 0.367（NC1=0.300, p=0.584），未显著高于随机基线；+20% 增益由动作词语言先验驱动（p<10⁻⁴）。
3. **案例级负结果**：12 主体固定几何封闭仿真中，题材文本替换不改变因果图（8 阶段双射同构），仅证伪该特定配置的叙事分歧能力。
4. **阻断状态**：D4 伪端点、Hmid-1/4/5/6 无闭式、C40 跨平台未验证 → 系统保持 BLOCKED-BY-SPEC；v1.0.3 仅为 FREEZE-CANDIDATE，严禁以 FROZEN 名义引用任何全称结论。
5. **Registry 职责边界**：验证器只做结构 + 溯源校验（类型/封闭枚举/DAG/三元等式/认识论门禁）；数值重算、载荷验签、语义真值、科学有效性判定 = ABSENT。

**唯一合法数字登记表（REG-01~10）**：53.3%（MW-0.3.1, 16/30, p=0.856）；51.6%（MW-0.7, 33/64, p=0.859）；D=0.367（MW-0.4.1, 11/30, p=0.584，禁引旧值 0.183）；NC1=0.300；+20%（MW-0.3.1 Group C, p<10⁻⁴）；35 项 Hmid-3 测试；135 项语义审计；20 类攻击；8 阶段同构；N≥120（功效门限 85.4%）。

---

## 六、开放问题与资产分级（承自 PASS 1.5 / PASS 2，经本档核认）

**开放问题**：Branch B 成果是否反哺 Branch A；D4 真实上下文算子重塑；Phase 3.3.0 语言先验的定位（妥协 vs 接地探索）；Hmid-1/4 停止形式化的原因；THEORY-01~03（上下文因果算子、语义接地梯度、涌现充要条件）；SPEC-01~03（Hmid 闭式、跨平台比特级核验、INDETERMINATE 收敛边界）；ENG-01~02（API 事务保证、刚体网格）。

**可发表性（PASS 2 分级）**：A级 = ASSET-07（匿名反先验微世界，需跨模型矩阵盲测）、ASSET-01（受控状态机运行时）、ASSET-09（法医审计方法学）；B级 = ASSET-08（Hmid-3 UCS）、ASSET-05（四维正交审计）、ASSET-04（同构证伪案例）、ASSET-02（视界防火墙）；C级 = ASSET-06（严格解析器）、ASSET-03（四阶解耦）；D级 = ASSET-10（史前档案）。

**Do-Not-Publish（8 条）**：不得宣称 v1.0.3=FROZEN；不得宣称 D4 证明因果迁移；不得宣称 Hmid 全闭合；不得混淆引用 53.3% 的实验归属；不得全称证伪 LLM 因果能力；不得全称证伪多 Agent 生成能力；不得混拼两分支范式发表；不得将 CMAWSE 单一等同于小说引擎或因果基准。

---

## 七、处置建议（供下一步决策）

本档案的最终状态是「文档闭环、代码缺位」。若要恢复可执行性，最小路径是：以对话文本内的 v1.0.3 参考实现（CMAWSE第一阶段.md L58599–59263）与 Registry Phase 3.7 修复后的 validator 语义为蓝本重建代码库，重建时首先解决 F1（两份 Schema v0.1 的身份裁决：择一为准或正式升版），再补 Phase 3.8 的独立 transcript，使 CLOSED 状态与实物实现对齐。

---

## 八、全量读取覆盖核验表

| 类别 | 数量 | 读取方式 | 结论 |
| :--- | :--- | :--- | :--- |
| Markdown（对话导出） | 3 个文件 / 8 段对话 / 3,850,626 tokens | 全文作为归一化语料库参与包含性检验；关键区段逐行精读；标题/边界行全量索引 | 全部读取，结构完整映射 |
| TXT（对话导出） | 1 | 同上 | 与 Evidence Registry.md 第二段同源 |
| 闭环归档 MD | 1 | 全文逐行精读 | 全部读取 |
| PDF | 16 | 16/16 全文文本提取（zlib + ToUnicode CMap 解码，合计约 70 万字符），逐份内容分类 + 包含性/标识符双重比对 | 15 份为重复内容；1 份独有（F6）；对话导出型 PDF 存在字符丢失型提取失真（如 "Skip to min cntent"），已按文件注明 |
| PDF 内嵌图片 | 0–1 个/份 | XObject 对象统计 | 无信息性截图，无内容遗漏 |
| .pages | 11 | 包结构解析 + IWA/Snappy 字面量段字符串提取 + 与 PDF 孪生及语料库交叉比对 + mtime 配对验证 | 无独有内容；正文为非全文级核验（F7） |
| .DS_Store | 1 | 字符串读取 | 仅图标位置元数据，无历史文件名 |

覆盖盲区仅两处，均已在 F6/F7 中定界：碰真实数据前存档的 .pages 孪生正文未逐字节解压；.pages 正文核验为片段级而非全文级。两者均不影响内容结论。

---
*本文档基于全工作区只读梳理生成。除本文件外未创建、修改或删除任何文件。*
