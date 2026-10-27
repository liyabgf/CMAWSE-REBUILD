# Phase II 最终引擎重写蓝图（REWRITTEN 目标）

## 目标
产出一个引擎文件 `rebuild/out/CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py`，通过 `extracted/phase2/harness_v7_L62449.py`（最终一致性测试）7/7，并满足 v1.0.3 规范。

## 素材
- 基体：v6 (L61914, Closed Reconciled, RESTORED) —— 全部评估器 d1/d2/d4/d5/d6、SplitMix64、wilcoxon_pratt 已在档且实跑通过。
- 缺口（P2 门禁定性）：v7 期望的 record 接口（键 `d1_pass`、`d2_pass`、`d5_pass`、`d6_divergence`…）。档案内 L60447/L61433 给出该接口的历史形态（v2/v4 代）；L59670 给出 v1 代的 `d1_passed` 形态。最终键集以 v7 测试的读取处为准（逐处枚举）。
- D3 缺席是**档案合法状态**（BLOCKED-BY-SPEC，Phase II 记录），不是缺口，重写不得凭空补 D3。

## 步骤
1. 枚举 v7 全部 7 个用例对引擎返回结构的读取键 → 接口契约表。
2. 以 v6 为基体，仅改 run/record 装配层满足契约（评估器逻辑不动 → 保持 RESTORED 语义的内核 + REWRITTEN 的装配层，两层分别标注）。
3. 跑 v7 → 7/7；再跑档案声明对照：L62686 "Ran 7 tests in 0.489s OK"。
4. 产出 REWRITTEN 清单：逐行列出改动点与依据行号。
