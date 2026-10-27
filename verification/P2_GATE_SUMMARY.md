# P2 验证门禁结论（Phase II 提取物实跑）

## 实验设计
- 对象：`extracted/phase2/` 全部 7 个提取块（4 引擎版本 + 3 测试版本，均 RESTORED，无省略号）。
- 装配：测试块以模块名 `CMAWSE_v1_0_3_EXPERIMENT_HARNESS` 导入引擎，引擎文件按版本逐一装配为该模块名，形成引擎×测试全配对矩阵。
- 基线：档案内验收声明（CMAWSE第一阶段.md L62686-62688 与 L62782-62784："Ran 7 tests / OK"，且声明为工作区物理执行结果）。

## 结果
| 引擎 | v3 测试 | v5 测试 | v7 测试（最终） |
|---|---|---|---|
| v1 (L59440) | ERROR | ERROR | ERROR |
| v2 (L59942) | ERROR | ERROR | ERROR |
| v4 (L60907, Rev2) | ERROR | ERROR | FAIL(7 tests: 2F+4E) |
| v6 (L61914, Closed Reconciled) | ERROR | ERROR | **FAIL(7 tests: 2F+4E)** |

引擎单独实跑（exit code）：v1/v2/v4/v6 全部 0。

## 失败定性
- v7 对 v6/v4：`KeyError: 'd1_pass'/'d2_pass'/'d5_pass'/'d6_divergence'` + 2 个断言失败。接口漂移：档案内 L59670（v1 代）用 `d1_passed`，L60447/L61433（v2/v4 代）用 `d1_pass`，而 v6 最终引擎的返回结构不满足 v7 期望的 record 形态。
- v3：要求 `class DiscretePhysicalWorldEngine`——该类名在档案中被引用 7 次但**从未以完整类定义出现**（后续版本更名为 `DiscretePhysicalWorld`），v3 为被取代的历史测试。
- v5：自身 `NameError: Dict`（typing 导入缺失），独立缺陷。

## 门禁判定
**FAIL —— 档案声称的最终态 "Ran 7 tests / OK" 无法由任何提取出的引擎版本复现。**

法医结论（与 F6 同构，代码层版本）：导出保留了通过的测试与 OK 声明，但未保留产出该 OK 的引擎最终状态（极可能存在于当时真实工作区的文件编辑中，仅以 prose 差异描述留痕）。

**重建指令**：Phase II 最终引擎必须按 v1.0.3 规范重写（蓝图见 rebuild/phase2_rewrite_blueprint.md），产物打 **REWRITTEN** 标签，验收目标 = v7 测试 7/7 通过 + 档案内数字对照（REG 登记表）。禁止把 v6 冒充最终引擎。
