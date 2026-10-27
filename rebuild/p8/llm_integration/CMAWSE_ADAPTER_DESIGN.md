# CMAWSE LLM 适配器最小设计（REWRITTEN，P8）

## 前提事实（P7-B 探测 + P8 审计，见 HARNESS_MODEL_PATH_AUDIT.md）

- 本机无独立 LLM API（无密钥、无本地推理端点）。
- 唯一实际可用的模型调用能力 = Harness 的受支持扩展点：**子智能体执行**（subagent 工具，模型路由由 Harness 会话配置决定；本会话中 provider 路由选择被拒绝，仅默认路由可用）。
- 外部独立 Python 程序**不能**直接 import/调起 Harness 内部模型服务（审计确认无导出 SDK/HTTP 端点）。

## 架构：编排层适配器（mediated adapter）

CMAWSE 引擎（rebuild/out，P3 REWRITTEN，只读）不接触任何模型细节。适配器位于两者之间：

```
[CMAWSE 引擎] --batch payload--> [P8 适配器]
  1. input_build:      payload 规范化 + 冻结提示模板渲染（prompt 指纹 = sha256）
  2. model_call:       受支持调用面（本环境 = 子智能体委托；未来 = 任意 SDK/HTTP）
  3. raw_capture:      原始输出全文 + 模型路由标识 + 请求 id + 时间戳，落盘 raw/（脱敏规则见下）
  4. parse:            独立 JSON 解析（不信任围栏/前后缀；失败即 REJECT_PARSE）
  5. typecheck:        P5 契约校验（d1 键=tau 数字、状态闭集、额外字段禁止）——引擎外独立执行
  6. permission_check: 白名单字段模型（d1/d2/d4/d5 only）；world_state_patch / unobserved_latent
                       / ledger 修改指令一律拒绝并记录（模型合法 JSON ≠ 操作获授权）
  7. to_world_op:      合法输出仅在引擎的评估通道内消费（D1 评估/错误计数），引擎无世界写入通道
  8. fault_handling:   不可用/超时/空/畸形 -> 计入 parse_failures、默认值兜底、事件可追溯
  9. accounting:       调用次数、延迟、原始输出字节数、失败分类计数
```

## 边界（冻结）

- 模型**不能**直接修改世界状态、公共账本、其他主体私有认知：引擎无该通道（P5 E4）+ 适配器 6 层显式拒绝（纵深防御）。
- 合法 JSON **不意味着**语义正确：语义评估（D1 对照真值）与权限校验分离报告。
- 适配器校验不可被模型输出跳过：校验在调用方进程，模型无法触及。
- 原始输出脱敏：不落盘任何凭据；模型路由只记非敏感标识（provider/模型名），不记系统提示全文以外的内部会话内容。

## 与 P7 冻结评估的关系

P8 只做**冒烟 + 故障注入 + 三次真实调用**（正常 / 越权指令 / 诱导类型违规）。P7 冻结的四配置受控评估（A/B/C/D 消融）需成批真实调用，受子智能体调用预算限制，本轮未执行，标记 NOT_RUN——不改判据、不声称执行了冻结实验。

## 测试矩阵（10 项）

1 真实成功（R1）；2 服务不可用（合成故障注入）；3 超时/异常（合成）；4 空输出（合成）；5 畸形 JSON（合成 + R3 真实诱导）；6 类型合法语义无效（合成 + R1 真实评分）；7 重复请求（合成：同 id 重放）；8 未授权操作请求（R2 真实 + 合成）；9 与世界转移规则冲突（真实输出按真值评分 + 合成注入）；10 日志关联（全案例 requestId 贯穿 raw/parse/check/final）。
