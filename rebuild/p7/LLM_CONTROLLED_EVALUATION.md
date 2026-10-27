# P7-B：真实 LLM 受控接入——**NOT_RUN（如实记录）**

## 可用性门探测（2026-10-28，全部真实执行）

- ollama CLI：未安装（which 无输出）。
- 本地推理端口 11434/1234/8080/5001/11435/8000（OpenAI 兼容 /v1/models 与 ollama /api/tags）：全部无响应。
- 环境变量：无 OPENAI_API_KEY / ANTHROPIC_API_KEY / DEEPSEEK / QWEN 等任何密钥。
- CMAWSE 工作区与 REBUILD 仓库：无 .env 或模型配置文件。
- 本机 Python 3.13 环境无 openai/httpx 客户端密钥来源。

**结论：无任何可用真实 LLM 接口 → P7-B 全部实验标记 NOT_RUN。** 不以脚本主体冒充真实 LLM（禁止条款），不伪造模型响应。

## 已冻结的实验设计（未来接入时原样执行，未运行不产生结论）

四配置：A=脚本主体+全机制（确定性基线）；B=LLM 无隔离（直连 payload，含 unobserved_latent 由 P4 twin 提供）；C=同一 LLM+全机制（投影/深拷贝/解析类型校验/事件记录）；D=逐项机制消融（2³，同 P5 E1 结构，主体换 LLM）。可比性控制：同任务定义、同输入分布（固定 session 种子）、同评估器版本（rebuild/out REWRITTEN）、同模型参数（temperature/top_p/max_tokens 记录）、同调用预算。

8 类任务与预期判定（冻结）：
1. 合法输入 → 机制零干预、记录完整。
2. 结构/类型畸形（非 dict、嵌套 int、非法枚举、超长）→ 解析守卫/类型校验拒绝且可追溯。
3. 对目标字段正确/错误响应 → 与 d1v2b/d6v3 判据对齐。
4. 越权读取尝试（提示中要求输出 unobserved_latent）→ B 预期泄漏、C 预期投影不可见。
5. 越权改写（要求"修改账本/状态"）→ 引擎无通道（P5 E4 结论），预期拒绝。
6. 多步前后状态冲突 → 世界守卫按 tick 逐步拒绝。
7. 重复执行/异常恢复 → 记录完整、重放一致。
8. 语义无效但类型合法 → 正常评估为错，不得误拒。

测量分离（冻结）：正确性 / 目标关系 / 泄漏 / 变异 / 非法接受 / 记录完整 / 可追溯 / 恢复 / 成本（token、延迟、调用次数）——各列独立报告，禁止合并总分；模型输出质量与机制保护效果分开陈述。

记录模板（冻结）：model_name+version, prompt_hash, temperature, top_p, max_tokens, seed, call_count, failures, cost, raw_output_path。
