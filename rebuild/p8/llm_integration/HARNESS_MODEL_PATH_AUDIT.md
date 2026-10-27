# DSH 模型调用路径审计（P8 子任务 A，子智能体执行 + 主 Agent 复核）

分工记录：本审计由子智能体（Audit harness model call path, id 456da75d）独立执行并交付证据表，主 Agent 另行在 checkout 做旁证核验（列于文末）并合并。子智能体与主 Agent 是否复用同一模型服务：**是**（见下）。

## 结论（已确认事实 / 代码推断 / 未知 分级）

**已确认（文件:行 证据，由子智能体提供、主 Agent 抽查一致）**
- 路由核心：packages/llm/llm 的 LlmRuntime 适配器注册表（registerAdapter，index.ts:204,394）。内置 provider：deepseek-official（API-key，llm-deepseek-api-key/src/index.ts:39）、deepseek-account（账号令牌，llm-deepseek-account/src/index.ts:111）；通用 llm-pi-ai 按配置注册 openai/anthropic/google 等（provider-data.generated.ts:12-45）。
- 默认目录模型：deepseek-flash、deepseek-v4-pro（llm-deepseek/src/models.ts:8,16）。
- 调用执行：agent 循环 packages/core/agent-loop/src/agent.ts:453（llm.stream）。机制 = HTTP fetch + SSE（sse.ts、transport.ts），默认端点 https://api.deepseek.com（可被 DEEPSEEK_BASE_URL 覆盖，config.ts:118）。
- 子智能体共享：subagent-spawn-in-process 在同一 cordis Context 创建子 Agent，共享 ctx.llm 注册表（src/index.ts:2-5）；子路由受 AllowedModelRoute 限制（tool-subagent/src/model-selection.ts:16-19）。
- 外部调用面：(a) **Python SDK deepseek-harness-sdk**（python/sdk，stdio 换行 JSON-RPC 驱动捆绑 dsh --profile sdk，需显式 dsh_home/DSH_HOME）；(b) Web GUI 127.0.0.1:3080 的 JSON-RPC 控制器（非 OpenAI-compatible 聊天端点）。
- 结果/异常/用量：流式 StreamChunk（text-delta/usage/finish 等，types.ts:470-481）、TokenUsage（input/output/cache/reasoning，types.ts:175-188）、LlmError（code: AUTH/RATE_LIMIT/QUOTA/CONTEXT_WINDOW_EXCEEDED/SERVER…含 status/requestId，index.ts:100-127）、AbortSignal 取消、300s 流空闲超时、llm-retry 重试、token-meter 计量。
- 凭据来源（仅名称）：DEEPSEEK_API_KEY 环境变量 / credentials 服务文件 $DSH_HOME 或 ~/.dsh/.credentials.yaml（600 权限）/ deepseek-account 的 x-dsh-auth-token。**未读取、未复制、未输出任何凭据值。**

**主 Agent 运行时复核（本会话实证）**
- list_subagent_models()：单 provider "a12334"，无广播模型；显式路由 "a12334/a12334" 被拒（"not allowed for this Session"）→ 子智能体实际运行于会话默认路由，路由选择受 Host 限制。
- 三次子智能体真实调用（P8-R1/R2/R3）成功返回——子智能体路径**实际可用**。
- 独立 Python 进程经官方 SDK：启动、JSON-RPC、事件流（request/header 含 provider/model/maxTokens/reasoningEffort、request/context 含 contextWindow=1,000,000、turn 生命周期）全部正常，模型调用止步于 LlmError(code=ACCOUNT_SIGN_IN_REQUIRED)（raw/sdk_call_result.json 有完整记录）。SDK 机械链路可用、真实凭据阻塞。

**未知/不存在证据**
- 未发现面向外部的 OpenAI-compatible /v1/chat/completions 端点（不能证明完全不存在）。
- pi-ai 完整可配模型列表取决于用户 settings（动态）。
