# rebuild/p8/llm_integration —— P8 LLM 接入专项（REWRITTEN）

文件映射：
- HARNESS_MODEL_PATH_AUDIT.md（子任务 A：子智能体审计 + 主 Agent 复核）
- CMAWSE_ADAPTER_DESIGN.md（子任务 B：最小适配接口 9 步流水线与边界）
- LLM_INTEGRATION_FEASIBILITY.md（最终裁决：四层能力 + 五问）
- LLM_INTEGRATION_RESULTS.csv（12 案例矩阵，含真实/合成/SDK 阻塞标记）
- adapter.py（适配器 + 故障注入测试矩阵，可复现）
- sdk_smoke.py（独立程序 SDK 调用最小验证，真实执行，凭据阻塞留痕）
- smoke_payload.json（s5 会话冻结载荷）；raw/（R1/R2/R3 原始模型输出 + SDK 调用记录）
- logs/adapter_pipeline.log（全链路 requestId 日志）

复现（仓库根）：
```bash
PYTHONPATH=. python3 rebuild/p8/llm_integration/adapter.py   # 12 案例矩阵
python3 rebuild/p8/llm_integration/sdk_smoke.py               # 独立 SDK 调用（需 ~/.dsh；当前凭据阻塞）
```
P3–P7 与 extracted/ 零改动；凭据值未读取未落盘。
