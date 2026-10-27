# rebuild/p7 —— P7 独立验证、LLM 接入与 Branch A 执行

环境：macOS / Python 3.13 / stdlib + pydantic 2.10.6 + pytest 9.2.0（本轮安装，环境级）。种子 0x5A3F；独立集 s11/s13；投机探针种子 4242/777/77。标记：全部 REWRITTEN；P3–P6 与 extracted/ 零改动。

文件映射：
- P7_PLAN.md（判据冻结于运行前）/ P7_REPORT.md / P7_DECISIONS.md / README.md
- A1：a_d6v3_validation.py + D6V3_RESULTS.csv + D6V3_INDEPENDENT_VALIDATION.md + logs/A1_d6v3.log
- A2：c_d1v2b_validation.py + D1V2B_RESULTS.csv + D1V2B_INDEPENDENT_VALIDATION.md + logs/A2_d1v2b.log
- B：LLM_CONTROLLED_EVALUATION.md（**NOT_RUN** + 冻结设计与可用性探测记录）
- C：b_branch_a.py + branch_a_copy/（__init__ 垫片，模块字节一致 sha256 记录于 CSV）+ BRANCH_A_RESULTS.csv + BRANCH_A_EXECUTION_REPORT.md + logs/C_branch_a.log

复现（仓库根）：
```bash
PYTHONPATH=. python3 rebuild/p7/a_d6v3_validation.py
PYTHONPATH=. python3 rebuild/p7/c_d1v2b_validation.py
python3 rebuild/p7/b_branch_a.py
```
（P7-B 无可运行脚本——模型接口不存在，见 NOT_RUN 记录。）
