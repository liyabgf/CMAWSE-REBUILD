# P8 LLM 接入可行性裁决

## 四层能力判定（按任务要求的区分）

| 层 | 判定 | 证据 |
|---|---|---|
| 1. 子智能体能调用模型 | **SUPPORTED** | P8-R1/R2/R3 三次真实调用（raw/*.txt，含完整原始输出） |
| 2. 独立程序能调用模型 | **BLOCKED（凭据）** | 官方 SDK 从独立进程启动成功、协议链路完整，模型调用返回 ACCOUNT_SIGN_IN_REQUIRED；环境无 DEEPSEEK_API_KEY。机械可行性 SUPPORTED、实际调用 BLOCKED |
| 3. CMAWSE 能通过适配器调用模型 | **PARTIALLY_SUPPORTED** | 编排层适配器经 Harness 子智能体（受支持扩展点）完成真实调用；不经独立进程直连 |
| 4. CMAWSE 能安全使用模型输出 | **SUPPORTED** | 12 案例矩阵（LLM_INTEGRATION_RESULTS.csv）：真实越权输出被 REJECT_UNAUTHORIZED、真实类型违规被 REJECT_TYPE、合法类型语义无效单独评分不误拒、requestId 全链路 LINKED |

## 真实执行了什么 / 未执行什么

已执行（真实模型调用）：T1 正常预测（9/9 正确，ACCEPT_EVALUATED）、T8 越权指令（模型服从了 world_state_patch 注入指令——适配器独立拒绝，纵深防御实证）、T5 诱导类型违规（整数值+note 字段，REJECT_TYPE）。已执行（合成故障注入，标记 SYNTHETIC，注入点=适配器边界）：服务不可用/超时/空输出/畸形 JSON/重复重放/规则冲突。已执行（独立程序）：SDK 调用（真实，凭据阻塞，完整留痕）。**未执行**：P7 冻结的四配置受控评估（A/B/C/D 消融，需成批独立模型调用，当前阻塞于层 2）——判据未改、不声称执行过。

## 最终五问

1. **Harness 模型能力能否被 CMAWSE 复用？** 能，但只有一条受支持路径：编排层委托子智能体（子智能体与主 Agent 共享 ctx.llm 路由）。独立进程 SDK 路径已设计与实测到凭据边界。
2. **最小接入方式与依赖？** CMAWSE 引擎 → P8 适配器（输入构造/原始留痕/解析/类型/权限/世界操作/审计） → 子智能体调用面。依赖：Harness 会话存活、子智能体工具、会话默认路由；独立进程替代需 DEEPSEEK_API_KEY 或账户登录。
3. **是否需要独立模型服务？** 当前不需要也不可行（无密钥）；取得 API key 后，SDK 路径（deepseek-harness-sdk 或直连 api.deepseek.com）即为受支持的独立服务方式，适配器 model_call 步骤可直接替换。
4. **可审计/可追踪/失败安全？** 是：requestId 贯穿（T10 LINKED）、原始输出落盘、LlmError 结构化（code/message/status）、失败分类计数、拒绝均在校验链有因可查；模型无法触及校验代码。
5. **真实测试与未执行项？** 见上节。P7 冻结受控评估维持 NOT_RUN（层 2 阻塞）。
6. **是否接入 Branch A 认知链？** 暂不（UNRESOLVED→待定）：Branch A agent 层认知链模块仍缺失（P7 结论），先补模块再谈 LLM 接入；适配器本身已达可集成状态。下一步优先级：获得凭据 → 层 2 直连 → P7 冻结评估原样执行 → Branch A 模块回溯后集成。

## 脱敏与环境

- 原始日志（raw/、logs/）不含任何凭据值；凭据仅记录来源名（DEEPSEEK_API_KEY / ~/.dsh 凭据文件 / 账户令牌头）。
- 环境：macOS，Python 3.13.2，pydantic 2.10.6，pytest 9.2.0，deepseek-harness-sdk（pip 安装于本机 site-packages）；DSH checkout /Users/liyang/deepseek-harness（58 包）；会话路由 deepseek-account 体系。
