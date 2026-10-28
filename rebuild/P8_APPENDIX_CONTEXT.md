# CMAWSE-REBUILD 全景上下文（P0–P8，供 LLM 单文件阅读）

> 本文件是仓库 CMAWSE-REBUILD（github.com/liyabgf/CMAWSE-REBUILD，master@6e38d38）的自包含摘要。
> 证据等级词：SUPPORTED / PARTIALLY_SUPPORTED / INSUFFICIENT / UNVERIFIED / UNRESOLVED / NOT_RUN / BLOCKED。
> 全部历史文件不可变；新产物标 REWRITTEN。原始 CSV/日志/脚本在压缩包内对应路径。

## 项目背景
CMAWSE（约束驱动的复杂叙事仿真引擎）v1.x：约束式世界状态机 + LLM 主体认知层。本仓库是对话导出档案的独立重建：P0 验证档案 → P1 提取代码 → P3 重写 Phase II 实验引擎 → P4–P8 逐层效度与机制审计。核心纪律：区分 RESTORED（原样提取）与 REWRITTEN（重写），不把"实现可用"当作"主张成立"，每个结论带反例与边界。

## 阶段结论速查

- **P0**（6167df4）：11/11 PDF 无损核验；Phase II 配对审计 FAIL（配对断言不成立，登记 P2_GATE）；V1–V8 报告见 verification/。
- **P1**（13966b3）：提取树 22 模块、14 测试、7 phase2 块、fragments、quarantine；Branch A 认知链模块缺失（cognitive_state/deliberation/representation）与 llm_boundary compile=FAIL 是 P7 执行验证的关键断裂面。
- **P3**（ac6911b/cbc52c4）：REWRITTEN Phase II 引擎（v6 基座 + F1 软零似然熔断 + F1 计数器 + F2 D1 全局众数先现序 tie-break）；v7 一致性测试 7/7 ×2。
- **P4**（7fdcf75）：D1 敏感度矩阵 1008 行——原始 D1 判据 INSUFFICIENT（账本三方平局、holdout 全 q0、平凡主体高分、排列/命名翻转）。
- **P5**（cdf8b07）：2^3 机制消融（投影/深拷贝/审计）、类型边界三臂、重放阴性对照 11 例（核心发现：**内部一致≠内容真实**，同结局 action 篡改对一致性校验不可见）、对抗探针 5 类。
- **P6**（f53511e）：D6 预注册修订 v2 INSUFFICIENT（tau_keyed 反例：R2 只测"输出有变化"）；事后 d6v3（E∧R2∧I，标签交换响应性）六类主体全分离；重放真实性 V3（事件哈希链+带外见证库，检出同结局篡改，缺失见证→UNDETERMINED）；D1 预注册 d1v2 INSUFFICIENT（N=9 零功效）→事后 d1v2b（N=36）oracle 唯一通过；typecheck 原生化可行但非必须（v7 回归 7/7）。
- **P7**（9700952）：独立集 s11/s13 复验——d6v3 12 类主体误通过 0、三分量各有专属反例；d1v2b oracle 泄漏审计（无标签泄漏，优势=预编码世界物理）；LLM 受控接入 NOT_RUN（当时无任何模型接口）；Branch A 部分执行（bus/schema 子集 7/8：视距/声学/剥夺/目击门控生效；**C3b 缺口：frozen 不挡容器内容变异**）。
- **P8**（6e38d38）：经 Harness 受支持扩展点（子智能体）完成 3 次真实模型调用作为 CMAWSE 主体（正常 9/9 / 越权指令被适配器独立拒绝 / 诱导类型违规被拒）；独立程序 SDK 路径机械验证但 BLOCKED(ACCOUNT_SIGN_IN_REQUIRED)；四层能力判定见 rebuild/p8/llm_integration/LLM_INTEGRATION_FEASIBILITY.md。

## 机制证据总表（最终）

| 性质 | 机制 | 等级 |
|---|---|---|
| 潜变量不可见 | 认知投影 | SUPPORTED（E1 消融） |
| 账本变异封禁 | history 深拷贝 | SUPPORTED |
| fail-closed（结构级） | 解析守卫 | SUPPORTED |
| 非法动作拒绝 | world.step | SUPPORTED |
| 类型边界 | P5/P6 typecheck（外挂=原生等价） | SUPPORTED |
| 重放一致性 | CLI 重执行 | SUPPORTED（但不证真实性） |
| 重放真实性 | V3 哈希链+带外见证 | PARTIALLY_SUPPORTED（信任假设内；账+证同改不可检出） |
| D6 鉴别力 | d6v3（REWRITTEN） | SUPPORTED（限脚本主体族） |
| D1 效度 | d1v2b（REWRITTEN） | SUPPORTED（限条件 C 平衡构造） |
| LLM 主体行为 | P8 适配器 | PARTIALLY_SUPPORTED（3 次真实调用；成批受控评估 NOT_RUN） |
| Branch A 感知门控 | PrivateHorizon/仲裁 | PARTIALLY_SUPPORTED（子集 7/8，C3b 容器缺口） |
| Branch A agent 认知链 | — | UNVERIFIED（模块缺失） |
| D4 上下文因果 / Hmid | — | UNRESOLVED/BLOCKED（规格缺失） |

## 下一步优先级（P8 裁决）
1. 获得 DEEPSEEK_API_KEY 或账户登录 → 独立程序直连 → 原样执行 P7 冻结的四配置受控评估（A/B/C/D 消融）。
2. C3b 修复（不可变容器 horizon，P7 副本内验证）。
3. Branch A 缺失模块原始来源回溯（对话导出 grep 认知类代码块）。
暂停：d6v3/d1v2b 主体族再扩充、原始 D1/D6 实现层修补、大规模模拟。

## 深入阅读顺序
rebuild/MECHANISM.md → rebuild/P3_REPORT.md → rebuild/p4/（审计报告）→ p5/E1-E4 报告 → p6/P6_REPORT.md（七问+证据矩阵）→ p7/P7_REPORT.md → p8/llm_integration/（三份 md）。各阶段判定细节、冻结判据、迭代史（含失败与回代）都在对应目录。
