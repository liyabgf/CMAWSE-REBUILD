# P3 权威版本配对矩阵（2026-10-28，逐对完整日志见 P3_matrix/）

引擎：v1(L59440)/v2(L59942)/v4(L60907)/v6(L61914)/REWRITTEN(rebuild/out)
测试：v3(L60660)/v5(L61509)/v7(L62449)

| 引擎 | v3 测试 | v5 测试 | v7 测试（最终） |
|---|---|---|---|
| v1 | NOT-RUNNABLE | NOT-RUNNABLE | NOT-RUNNABLE |
| v2 | NOT-RUNNABLE | NOT-RUNNABLE | NOT-RUNNABLE |
| v4 | NOT-RUNNABLE | NOT-RUNNABLE | FAIL 4/7 |
| v6 | NOT-RUNNABLE | NOT-RUNNABLE | FAIL 1/7 |
| rewritten | NOT-RUNNABLE | NOT-RUNNABLE | PASS 7/7 |

逐行明细（含失败原因）：

  v1 x v3: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v1 x v5: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v1 x v7: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v2 x v3: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v2 x v5: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v2 x v7: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v4 x v3: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v4 x v5: NOT-RUNNABLE  exit=1 test-defect: NameError Dict (typing import missing in test)
  v4 x v7: FAIL 4/7 exit=1 
  v6 x v3: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  v6 x v5: NOT-RUNNABLE  exit=1 test-defect: NameError Dict (typing import missing in test)
  v6 x v7: FAIL 1/7 exit=1 
  rewritten x v3: NOT-RUNNABLE  exit=1 IMPORT/RUNTIME ERROR
  rewritten x v5: NOT-RUNNABLE  exit=1 test-defect: NameError Dict (typing import missing in test)
  rewritten x v7: PASS 7/7 exit=0 
