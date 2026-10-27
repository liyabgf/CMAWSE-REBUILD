# rebuild/p5 —— P5 机制消融、重放负对照与对抗主体实验

来源标记：脚本全部 REWRITTEN；被测引擎 rebuild/out（REWRITTEN）；对照 generic_twin（REWRITTEN, p4）；引用档案行号指向 archive/（EXTRACTED）。

文件：
- P5_REPORT.md —— 事实/观察/推断/未决 四层分离总报告
- E1_ABLATION_MATRIX.csv + logs/E1_ablation.log —— 2^3 全因子消融（16 行）
- E2_TYPE_BOUNDARY_REPORT.md + E2_TYPE_BOUNDARY_MATRIX.csv + logs/E2_typeboundary.log —— 三臂 48 行
- E3_REPLAY_RESULTS.csv + logs/E3_replay.log —— 11 场景
- E4_ADVERSARIAL_RESULTS.csv + logs/E4_adversarial.log —— 18 行（5 攻击类 × 3 臂 + 正常对照）
- E1_ABLATION/E2/E3/E4 脚本：e1_ablation.py、e2_typeboundary.py、e3_replay.py、e4_adversarial.py、typecheck.py
- logs/E1_baseline.log、logs/E2_baseline.log —— P4 基线复跑（数值与 P4 一致，历史日志未覆盖）

环境：macOS / Python 3.13 / 仅标准库；种子 0x5A3F；会话 idx 1(E1/E3)/2(E2/E4)；CONDITION_C。

复现：
```bash
cd /Users/liyang/Documents/CMAWSE-REBUILD
python3 rebuild/p5/e1_ablation.py      # E1（CSV+log 重生成）
python3 rebuild/p5/e2_typeboundary.py  # E2
python3 rebuild/p5/e3_replay.py        # E3（CLI 子进程 exit 码）
python3 rebuild/p5/e4_adversarial.py   # E4
python3 rebuild/p4/exp_boundary.py     # 基线 E1（写 p4 日志）
python3 rebuild/p4/exp_failclosed.py   # 基线 E2
```
