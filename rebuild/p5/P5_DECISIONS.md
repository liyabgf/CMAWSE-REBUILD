# P5 机制裁决（保留 / 替换 / 继续验证 / 暂不裁决）

标记：EXTRACTED / REWRITTEN / UNRESOLVED。证据全部指向 rebuild/p5/logs 与四份 CSV。

## 保留（有对照实验证据支持）

| 机制 | 证据 | 裁决理由 |
|---|---|---|
| 认知投影 PROJECTION（潜变量不可见） | E1：P=1→暴露 0/21；P=0→21/21（8 配置无交互）；E4-A1 消融臂 BREACH | 单变量决定性质，通用循环不自带；P4 结论加强 |
| 状态隔离 DEEPCOPY（history 深拷贝） | E1：C=0且A=1→变异击穿 1/22；C=1→INTERCEPTED；E4-A2 同 | 同上；注意 C×A 交互（审计关闭时无通道，不能记作"拦截"） |
| 解析守卫（调用+取键 try/except） | E2：none/str/raise/list 4 例 pf=2 记录完整；A_twin 全崩 | fail-closed 核心组件，但覆盖层有限（见替换项） |
| world.step 非法动作拒绝 | E1/E4：三臂均 0 非法提交 | 性质来自世界组件（非循环非 harness），归属修正后保留 |
| AUDIT 账本记录完整性 | E1：A=0→记录不完整、d1 评估语义失效 | 记录完整性是评估的前提，审计机制不可关 |
| CLI 重放一致性校验 | E3：8/8 检出类场景全部 REJECTED（种子/结局/重排/重复/遗漏） | 内部一致性契约成立且严格 |

## 替换 / 补强（有实测缺口）

| 机制 | 证据 | 裁决 |
|---|---|---|
| 字段类型边界（d1/d4 裸洞） | E2-A3/E4-A3：d1_predictions=int → AttributeError 逃逸（DOS）；消融臂同样崩溃（与 P/C/A 正交） | 以 rebuild/p5/typecheck.py（REWRITTEN）包装补齐已验证可行（15/15 畸形 pf=2+原因可追溯，无误拒）；**是否并入引擎原生层为 U-P5-3，本轮不裁决** |
| d2/d5 评估器局部守卫的静默判错 | E2：7 例 pf=0 无拒绝原因 | 替换为"判错 + 可追溯拒绝原因"双轨（A_check 已示范），避免把"类型垃圾"与"能力不足"混为同一指标 0 |
| REPLAY_SPEC 1e-9 浮点容差 vs CLI 逐字相等 | E3 代码契约 | 实现比规格更严——不替换，但在规格侧记录差异（UNRESOLVED 裁决） |

## 继续验证（主张需收窄或补对照）

| 机制 | 证据 | 下一步 |
|---|---|---|
| D6 置换不变性 | E4-A5a：恒定 'q0' 主体 d6_div=0.0（盲区实证） | 主张收窄为"输出对置换扰动的稳定性"；加鉴别性对照（恒定输出主体必须 d6>0 或与 d1 联合判据）后再裁决 |
| 重放真实性绑定 | E3：tamper_action_equivalent SUCCESS；session 重贴标签 SUCCESS | 规格未定义（U-P5-1/2）；若要求真实性需账本内容哈希/签名机制——设计后再验证 |
| D1 效度 | P4 判定 INSUFFICIENT（排列敏感+holdout 退化+置换检验缺失） | E5（P4 设计）：新查询生成器（REWRITTEN）+ 置换检验接入后重测 oracle/naive/random 分离 |

## 暂不裁决

- llm_boundary.py 历史组件归属（Branch A 范围，quarantine 编译失败@L84 截断——EXTRACTED 证据不完整）。
- Registry、Schema A/B（任务范围外）。
- 真实 LLM 生成攻击的失败率外推（本轮全部为脚本化探针；无模型版本/提示/采样参数可记录——若引入必须记录运行次数与参数后方可作任何统计主张）。
