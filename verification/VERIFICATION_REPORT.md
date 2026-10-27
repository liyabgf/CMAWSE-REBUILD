# CMAWSE 现有资产独立核验报告

日期：2026-10-28 ｜ 核验人：重建会话（独立于资产整理会话）
原则：**不将此前会话的自我报告当作验证证据**。一切结论以 `manifests/SHA256SUMS.txt` 哈希锚定的只读副本为基线，由 `verification/scripts/` 下新写的脚本独立复跑得出，日志落盘于 `verification/logs/`。

## 逐项核验结果

| # | 核验项 | 方法 | 结论 | 证据 |
|---|--------|------|------|------|
| V1 | 11 份资产 PDF 无损渲染 | pdfminer 反向提取 + 字符多重集亏空对账 | **11/11 PASS**（8 份零亏空；3 份亏空 24 字符全部属于构建端附录留档替换表） | logs/V1_pdf_lossless.log |
| V2 | 对话导出 python 代码块形态 | fence 解析 + compile() 门禁 + 省略检测 | **93 块 / 8,458 行 / 64 可编译 / 29 语法残段 / 14 显式省略** | logs/V2_code_compile.log |
| V3 | F1：两份 Schema v0.1 词汇互斥 | 枚举标记逐一定位 | **成立**：schema#1（DERIVED_REPORT@ER.md L3978/L4116、GENERAL_SCIENTIFIC_CLAIM 等）与 schema#2（AMBIGUOUS_PROVENANCE、EMPIRICAL_FACTOR、BENCHMARK_MANIFEST 等）同文件并存且值域互斥 | logs/V3toV7_forensic.log |
| V4 | F4：Phase 3.8 出处唯一 | 全语料 grep | **成立**："Phase 3.8"/"REGISTRY_V0.1_CLOSURE" 仅出现于闭环归档.md（各 3 次），其余全部文本 0 次 | 同上 |
| V5 | F6：碰真实数据前存档.pdf 独有内容 | 60 个 24 字符内容探针 + 标识符对账 | **成立（VERIFIED）**：内容探针仅 4/60 命中语料；标识符 9/17 命中为名称级回响（如 fixture_pass_01 在 conv 2 讨论中被提及），非内容重复。孤本关键类名 ContainerShapeMismatchError 不在任何文本档案 | 同上 |
| V6 | Registry 实现代码在档率 | 类定义/import 标记全语料搜索 | **成立（0 在档）**：class EvidenceRecord / ClaimRecord / StatisticalRecord / SummaryRecord、def _check_granularity 全部 0 命中。models.py 被提及 34+25 次但无实现体 | 同上 |
| V7 | 对话边界与 token 声明 | "Skip to main content" 边界 + token 行提取 | **header 数字 VERIFIED**（8 段对话边界、合计 3,850,626 tokens 与导出头一致）；**md==完整对话 UNVERIFIED** | 同上 |
| V8 | .pages 无独有内容 | Snappy 字面量段扫描 + 语料/孪生交叉比对 | **PARTIALLY_VERIFIED**：11/11 有 PDF 孪生提取、mtime 配对一致；未发现语料之外的实质内容。初扫异常样本（"审计基线…"、"1_ENGINEERING…"）经定向 grep 定性为**格式差异近匹配**（语料与孪生中均在），非独有内容 | logs/V8_pages_fragment.log |

## 对此前口头报告的纠错（本次独立复核发现）

1. **"Registry 代码 0 在档"需要收窄表述**：Registry 数据类实现 0 在档成立；但 `from pydantic`(49 次)、`ConfigDict`(183 次) 命中并非 Registry——它们是 **Branch A 核心模块**（schema.py / core/schema.py / core/arbiter.py / world/bus.py / agent/* / cognitive/* / runtime/orchestrator.py 等，块首带"模块：路径"docstring 的完整清单）。此前评估把 Branch A 提取前景说得偏悲观，实际模块头齐全、可直接归属提取。
2. **.pages 初扫"未覆盖样本"**为核验脚本匹配粒度问题（精确子串 vs 格式差异），已逐条定向复核排除。结论回到片段级：未发现独有内容，但全文级一致性仍不可证。

## UNVERIFIED 清单（不可从现有文件复核）

- **U1** md/PDF 导出 == 完整对话：不可证。反证已存在（孤本案例：导出跳过报告正文）。
- **U2** .pages 全文级一致性：IWA/Snappy 全文解压未成功（自实现解包器在主块失步），仅有字面量段级核验。
- **U3** token 头数（3,850,626）为导出工具自报值，无法从文件侧复算。
- **U4** 原始 PDF 的图像内容：仅做过 XObject 计数（0–1/份），未做视觉级检查。
- **U5** `.DS_Store` 无实质内容：未单独取证（常规 macOS 元数据，风险极低）。

## 结论

资产层（11 份 PDF + 哈希锚定 + 核验日志）**可复核、可复现、可入 git**。代码层的真实形态比此前评估更乐观：Branch A 有模块头完整清单，Phase II 骨架三版本完整可编译，Registry 实现类 0 在档（只能重写）。
