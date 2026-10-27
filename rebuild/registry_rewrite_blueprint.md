# Registry (models/validator/tests) 重写蓝图（REWRITTEN 目标，前置 F1 裁决）

## 在档率
实现代码 0（V6：EvidenceRecord/ClaimRecord/StatisticalRecord/SummaryRecord/_check_granularity 全部 0 命中）。只能重写。

## 蓝图素材（全部在档，带行号锚点）
- 枚举闭式：Phase 3.1 审计基线 8 枚举 28 值（schema#2 词汇）。
- 字段规范：`Evidence Registry.md` L3941–4188 Schema v0.1 文本（schema#1 词汇）。
- 修复语义：Phase 3.1–3.7 全链审计的每项修复描述（ER.md conv 2 + 整理执行一.txt）。
- 测试蓝图：孤本 PDF 的 31 fixtures/12 攻击类/24 violations Fail-Closed/`fixture_pass_01~06`（assets/08 PDF + verification/artifacts/pdf_text/）。
- 验收基线：66 项测试（60/66 历史通过）+ 三元等式断言形态（Phase 3.7）。

## 纪律
- 产物打 REWRITTEN；数字不混入 REG-01~10。
- 重写后的 validator 与 Phase 2 孤本报告的 "无冲突" 声明之间的关系必须按 F1 裁决结果定性，不得回避。
