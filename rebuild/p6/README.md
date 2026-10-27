# rebuild/p6 —— P6 指标鉴别力、重放真实性与 D1 效度重设计

标记：脚本全部 REWRITTEN；被测引擎 rebuild/out（REWRITTEN，只读）；P6 原生副本 rebuild/p6/native/（REWRITTEN）。历史产物零改动。

环境：macOS / Python 3.13 / 仅标准库。种子：0x5A3F（引擎）、4242（random 主体）、777（顺序打乱）、77（账本洗牌）。调参集 session 1；留出集 session 5；全新验证集 session 7（d6v3）。

文件映射（对照任务要求的交付物）：
- P6_PLAN.md（预注册）/ P6_REPORT.md / P6_DECISIONS.md / README.md
- D6_DISCRIMINATION_REPORT.md + D6_RESULTS.csv（预注册 v2）+ D6_RESULTS_V3.csv（事后修订）+ a_d6.py + a_d6v3.py + logs/A_d6.log、A_d6v3.log
- REPLAY_CONTRACT.md + REPLAY_AUTHENTICITY_RESULTS.csv + b_replay.py + logs/B_replay.log
- D1_VALIDITY_REPORT.md + D1_RESULTS.csv + D1_PERMUTATION_RESULTS.csv + D1_THRESHOLD_SENSITIVITY.csv + c_d1.py + logs/C_d1.log
- TYPECHECK_NATIVEIZATION_REPORT.md + TYPECHECK_REGRESSION_RESULTS.csv + d_typecheck.py + native/ + logs/D_typecheck.log、D_v7_regression_native.log

复现（仓库根）：
```bash
PYTHONPATH=. python3 rebuild/p6/a_d6.py      # D6 v2（预注册）
PYTHONPATH=. python3 rebuild/p6/a_d6v3.py    # D6 v3（事后修订）
python3 rebuild/p6/b_replay.py               # 重放真实性
PYTHONPATH=. python3 rebuild/p6/c_d1.py      # D1 两阶段
PYTHONPATH=. python3 rebuild/p6/d_typecheck.py  # typecheck 四臂 + v7 回归
```
哈希清单：git 历史锚定（git log -1）；P0 档案 SHA256 在 manifests/SHA256SUMS.txt（未改动）。
