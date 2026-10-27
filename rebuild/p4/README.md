# rebuild/p4 —— P4 评估器效度审计与机制边界识别

来源标记：本目录全部脚本为 REWRITTEN（审计/实验代码）；引用的档案行号指向 archive/（EXTRACTED 证据）；引擎被测对象为 rebuild/out（REWRITTEN）与 extracted/phase2（EXTRACTED）。

- P4_AUDIT_REPORT.md —— P3 独立复核 + D1 效度结论
- D1_SENSITIVITY_MATRIX.csv —— 1008 行敏感性矩阵（排列×标签×规则×主体）
- MECHANISM_BOUNDARY_MATRIX.md —— 机制边界四分类矩阵
- P4_EXPERIMENT_DESIGNS.md —— E1/E2 设计与实际结果、E3-E5 待实施
- E2_FAILCLOSED_MATRIX.csv —— 失效封禁 16 组矩阵
- d1_audit.py / exp_boundary.py / exp_failclosed.py / generic_twin.py —— 审计与实验脚本
- logs/ —— P4_v7_rerun.log、P4_cli_rerun.log、d1_audit.log、E1_boundary.log、E2_failclosed.log

环境：macOS / Python 3.13（标准库即可；引擎零外部依赖）。复现命令见 P4_AUDIT_REPORT.md §5。
