# P1 提取报告（extract.py）

源：archive/CMAWSE第一阶段.md（哈希锚定）；python 块总数 166

入库统计: {"module": 22, "test": 14, "harness": 7, "fragment": 0, "quarantine": 4}

模块/测试版本层（src|tests = 最新版；versions/ = 全部历史层）：

| kind | ident | versions | latest@L | destination |
|---|---|---|---|---|
| module | agent/affordance.py | 1 | L10363 | src|tests (latest) |
| module | agent/base.py | 4 | L10953 | src|tests (latest) |
| module | agent/cognitive_projection.py | 7 | L23310 | src|tests (latest) |
| module | agent/context.py | 2 | L13406 | src|tests (latest) |
| module | agent/generator.py | 2 | L13532 | src|tests (latest) |
| module | agent/ladder.py | 2 | L13834 | src|tests (latest) |
| module | agent/llm_adapter.py | 6 | L22493 | src|tests (latest) |
| module | agent/llm_boundary.py | 5 | L21193 | quarantine(compile-fail) |
| module | agent/nl_adapter.py | 1 | L31183 | src|tests (latest) |
| module | agent/nl_contract.py | 3 | L33128 | src|tests (latest) |
| module | agent/provenance.py | 4 | L22402 | src|tests (latest) |
| module | agent/selector.py | 2 | L13734 | src|tests (latest) |
| module | agent/semantic_benchmark.py | 7 | L30528 | src|tests (latest) |
| module | cognitive/memory.py | 3 | L5337 | src|tests (latest) |
| module | cognitive/rumor.py | 2 | L3614 | src|tests (latest) |
| module | committer.py | 1 | L475 | src|tests (latest) |
| module | core/arbiter.py | 2 | L1726 | src|tests (latest) |
| module | core/committer.py | 1 | L1534 | src|tests (latest) |
| module | core/ledger.py | 1 | L1452 | src|tests (latest) |
| module | core/schema.py | 2 | L1254 | src|tests (latest) |
| module | ledger.py | 1 | L385 | src|tests (latest) |
| module | runtime/orchestrator.py | 4 | L5477 | src|tests (latest) |
| module | world/bus.py | 3 | L4176 | src|tests (latest) |
| test | test_phase_3_0.py | 1 | L17392 | quarantine(compile-fail) |
| test | test_phase_3_0_1.py | 1 | L18298 | src|tests (latest) |
| test | test_phase_3_1.py | 1 | L19409 | quarantine(compile-fail) |
| test | test_phase_3_1_1.py | 1 | L20557 | src|tests (latest) |
| test | test_phase_3_1_2.py | 1 | L21757 | src|tests (latest) |
| test | test_phase_3_1_3.py | 1 | L22773 | src|tests (latest) |
| test | test_phase_3_1_5.py | 1 | L23684 | src|tests (latest) |
| test | test_phase_3_1_6.py | 2 | L24574 | src|tests (latest) |
| test | test_phase_3_2.py | 1 | L25267 | src|tests (latest) |
| test | test_phase_3_2_1.py | 1 | L25924 | src|tests (latest) |
| test | test_phase_3_2_2.py | 1 | L26655 | quarantine(compile-fail) |
| test | test_phase_3_2_3.py | 1 | L27528 | src|tests (latest) |
| test | test_phase_3_2_4.py | 1 | L28506 | src|tests (latest) |
| test | test_phase_3_2_5.py | 1 | L29617 | src|tests (latest) |
| test | test_suite_027.py | 1 | L4789 | src|tests (latest) |
| test | test_suite_044.py | 1 | L11089 | src|tests (latest) |
| test | test_suite_057.py | 1 | L13968 | src|tests (latest) |

归一化说明：裸 schema.py/arbiter.py 映射为 core/schema.py、core/arbiter.py（同一契约模块的历史命名）。
fragments/ 为对话内无模块头的 python 块（含语法残段），保留供追溯，不构成可构建代码。
quarantine/ 为最新版编译失败者，防止拼装出"看似完整"的伪文件。
