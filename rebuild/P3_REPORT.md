# P3 执行报告：Phase II 最终引擎装配层重建

日期：2026-10-28 ｜ 环境：macOS / Python 3.13 ｜ 基线：本仓库 master@6e6e7b5
产物：`rebuild/out/CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py`（**REWRITTEN**），验收测试为未修改的 RESTORED 块 `extracted/phase2/harness_v7_L62449.py`（档案 L62449-L62600）。

## 1. 实际修改的文件与提交

| 文件 | 操作 | 内容 |
|---|---|---|
| `rebuild/out/CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py` | 新增 | REWRITTEN 最终引擎（v6 基体 + 5 处补丁，见 §3） |
| `rebuild/out/engine_v6.diff` | 新增 | 与 v6 基体的逐行 diff（40 行） |
| `extracted/phase2/CMAWSE_v1_0_3_EXPERIMENT_HARNESS.py` | git rm | P2 门禁期的装配伪件，提取树恢复为纯提取物（历史在 git 中可追溯） |
| `verification/logs/P3_v7_final.log` | 新增 | 终验两次全量运行（7/7 OK ×2） |
| `verification/logs/P3_matrix/` | 新增 | 权威配对矩阵 + 15 份逐对完整日志 |
| `verification/VERIFICATION_REPORT.md`、`P2_GATE_SUMMARY.md` | 未修改 | 历史结论保留原文；本报告对 P2 期矩阵计数误差的纠正见 §4 注 |

## 2. 基线与 6/7 失败的根因（全部实证，非推测）

基线复跑（turn 起始）：v6 装配模块（sha256 与 v6 完全一致）+ v7 → **1/7 通过，2 失败 + 4 错误**，与 P2 门禁记录一致。

**根因 R1（4 个 ERROR 的共同根因）——零似然异常熔断误实现为致命退出。**
v6 把 v2/v4 的 `update_reference_prior` 改名为 `_strict` 并把 `total <= 0` 分支从"保持先验"改为 `raise ValueError`；`run_session` 捕获后直接返回 `{"status": "INVALID_REFERENCE_OUTCOME", "session_idx": ...}`，全部评估字段缺失 → v7 读 `d1_pass/d2_pass/d5_pass/d6_divergence` 时 KeyError。
触发点（插桩实测）：CONDITION_C session 1 的 t=8，obj=C ctx=K act=act_gamma obs=q0；彼时先验已收敛为点质量（M1 权重 0），三模型似然全为 0。
证据：v2/v4 同函数 docstring 明写设计语义 "If real world produces observation outside all 3 reference models, hold prior"；档案产物六（L62608+）Gate D 声明"引入严格的零似然异常熔断"且 CLOSED——熔断指记录异常，不指丢弃整会话。
**注意：`d1_passed` vs `d1_pass` 拼写差异仅为 v1 代（L59670）的线索，非根因**——v2/v4/v6/v7 全部使用 `d1_pass`，KeyError 由 R1 的早退造成。

**根因 R2（test_d1 断言失败）——D1 基线在字母序平局折断下退化为完美预测器。**
实测分量：oracle session 1 训练账本全局计数 {q0:7, q1:7, q2:7}（结构性三方平局：世界类 `focal_obj = objects[tick % 3]` 均匀轮转 × 21 步 × oracle 确定性策略 A→q1/B→q2/C→q0）；9 条 holdout 查询真值全为 q0 且 (X,act) 键全部不在条件计数中 → 基线全部落到 global_mode；`max(sorted(keys), key=count)` 在平局时取字母序首个 q0 → 基线 9/9 全对，oracle 也 9/9 → delta=0 → `delta>=0.15` 结构性不可满足。
关键事实：**v2/v4/v6 的 `evaluate_d1` 逐字相同，且 v4 实测同一平局同一 delta=0**——即没有任何在档引擎能通过 v7 的 d1。oracle 与 dummy 在该 holdout 上预测向量完全相同（全 q0），二者可区分的唯一渠道是各自会话账本诱导的基线差异。

**根因 R3（test_canonical_replay_cli，仅 v4 配对）**——v4 的 CLI 输出 "Replay verified bit-level identical"，v7 断言 "Canonical deterministic replay verified"。消息字符串漂移。v6 起已一致，本报告不处理（v6 基体已含正确文案）。

**根因 R4（test_d3，v4 配对的 ERROR）**——v4 缺 `evaluate_study_d3` 接口（v6 起才有）。v6 基体已含。

## 3. 最终版本与 v6 的差异（完整 diff 见 engine_v6.diff）

| 补丁 | 位置 | 旧契约 | 新契约 | 理由 |
|---|---|---|---|---|
| F1 | `update_reference_prior_strict` | total≤0 → raise → 会话早退，记录无评估字段 | total≤0 → 保持先验 + `ZERO_LIKELIHOOD_EVENTS` 计数（会话级重置） | 回归在档 v2/v4 语义与 Gate D"熔断=记录"的描述；会话必须完整产出评估记录 |
| F1c/F1d | `run_session` | — | 记录新增可加性字段 `zero_likelihood_events` | 熔断可审计（不改变既有字段） |
| F2 | `evaluate_d1` global_mode | 平局按字母序（q0 优先） | 平局按首次出现序（dict 插入序） | 字母序使朴素基线在全 q0 holdout 上 9/9 全对，D1 的 delta≥0.15 对任何主体（含完美 oracle）不可满足，评估器缺陷；首次出现序是经验众数标准约定 |

评估器其余全部逐字保留；世界类、六评估器、Wilcoxon-Pratt、CLI 重放逻辑、种子派生零改动。测试未删、断言未减、预期未放宽；oracle/dummy/adversarial 全部使用 v7 原定义。

**被否决的备选方案**（均有更大语义冲击或更弱证据，记录备查）：交互循环 21→22 步（破坏 23-call 结构与 parsing_failure_rate 分母）；基线改为对象条件边缘分布（会使 dummy 同样过 d1，实测否决）；focal_obj 改 PRNG 驱动（破坏 CLI 重放的 PRNG 流一致性，需引入第二 RNG）。

## 4. 版本配对验证矩阵（权威重测，逐对完整日志在 P3_matrix/）

| 引擎 | v3 测试 | v5 测试 | v7 测试（最终） |
|---|---|---|---|
| v1 (L59440) | 不可运行 | 不可运行 | 不可运行 |
| v2 (L59942) | 不可运行 | 不可运行 | 不可运行 |
| v4 (Rev2) | 不可运行 | 不可运行 | FAIL 4/7（d1、d3、CLI） |
| v6 (Closed Reconciled) | 不可运行 | 不可运行 | FAIL 1/7（仅 d0 过） |
| **REWRITTEN** | 不可运行 | 不可运行 | **PASS 7/7** |

v3/v5 不可运行属**测试侧缺陷**（v3 导入 `DiscretePhysicalWorldEngine`——该类名在全部在档引擎中无定义，被后续版本更名 `DiscretePhysicalWorld`，v3 为被取代的历史测试；v5 自身 `NameError: Dict`，typing 导入缺失）。
注：P2 期矩阵（`P2_pairing_matrix.log`）把 v4 误计为 6/7 失败——其计数正则按 7 项套算；逐项重跑实证 v4 为 3 项失败（2F+1E）。P2 结论"无配对可复现 7/7"不受影响，反而加强。

## 5. 7/7 完整测试的真实运行记录与复现命令

`verification/logs/P3_v7_final.log`（两次连跑，均 `Ran 7 tests ... OK`，耗时 ~0.06s）：
```text
Ran 7 tests in 0.064s  OK
Ran 7 tests in 0.062s  OK
```
复现命令（仓库根起）：
```bash
cd rebuild/out
PYTHONPATH=. python3 ../../extracted/phase2/harness_v7_L62449.py
```
CLI 重放单独复现：引擎文件支持 `--replay --log <file> --seed 0x5A3F`，实测 exit 0，输出含 "Canonical deterministic replay verified"。测试写临时文件 `temp_audit_session.jsonl` 于运行目录并自清理。

## 6. 与历史 L62686/L62782 的对照结论

档案两处记录（`Ran 7 tests ... OK`，一次标注为工作区物理执行）在**任何在档引擎配对下均不可复现**（§4 矩阵）。本 REWRITTEN 版本通过同一测试集 7/7——这构成**测试结果复现**，**不构成"历史实现已恢复"**：产出历史 OK 的引擎最终状态不在档案中（本报告给出两种可能：当时工作区存在未归档的最终编辑；或该输出未在归档代码上实际执行）。历史日志仅作为"期望行为规格"使用。

## 7. 未解决问题与限制

- **U-P3-1**：历史 7/7 的真实来源不可判定（档案内证据不足以裁决"未归档编辑" vs "输出未经实际执行"）。结论限定为：REWRITTEN 复现了 v7 全部断言，且 F1/F2 均有在档语义依据，但不等于逐行恢复历史最终态。
- **U-P3-2**：F2 是装配层语义决定（平局折断约定）。已记录旧/新契约与被否决备选；若未来档案出现最终引擎本体，应以原件为准重新裁决。
- **U-P3-3**：v3/v5 测试侧缺陷未修（超出本轮范围：只处理引擎装配层）。它们是历史演化的死枝，保留原样。
- **U-P3-4**：测试通过 ≠ 因果机制正确（档案 L62786 原话）。7/7 仅为装配层一致性；Gate F/G（D4 上下文机制、Hmid 模型族）仍为 BLOCKED-BY-SPEC，与本轮无关。
- `zero_likelihood_events` 为新增可加性字段，CLI 重放对账本比对不受影响。
