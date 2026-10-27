# P5 报告：机制消融、重放负对照与对抗主体实验

日期：2026-10-28 ｜ 环境：macOS / Python 3.13（仅标准库）｜ 被测对象：rebuild/out 引擎（REWRITTEN）+ rebuild/p4/generic_twin.py（REWRITTEN 对照）+ rebuild/p5 消融/校验组件（REWRITTEN）。种子 0x5A3F；会话 1/2；CONDITION_C。所有指标可追溯到 rebuild/p5/logs/。

## 一、已证实事实

**基线复核（P5.1）**：P4 的 E1/E2 原脚本复跑，数值与 P4 报告一致（潜变量 0/21 对 21/21；感染 0 对 1；none/str/raise 三畸形 parse_fail=23 记录完整；malformed_type 崩溃）。历史日志未覆盖，P4 产物零改动。

**E1 全因子消融（2^3=8 配置 × 2 主体，logs/E1_ablation.log，E1_ABLATION_MATRIX.csv）**：
- 机制在码形态先核实：PROJECTION=project_observation 结构性限缩；DEEPCOPY=history 深拷贝（交互+批次两处）；AUDIT=ledger.append+解析失败计数。**账本变异守卫在 Phase II 引擎中不存在独立机制**（事件由 world.step 产出后无条件入账），无法单独消融——结论限定在组合层面。
- 主效应：P 单变量决定潜变量暴露（0↔21/21，无交互）；C 单变量决定账本变异击穿（C=0且A=1 时 BREACH=1/22；C=1 时 INTERCEPTED）；A 单变量决定记录完整性（A=0 时 13 键+21 条账本不成立）。
- 交互效应：C×A——A=0 时变异"机制未触发（无通道：账本为空）"而非被拦截，**没有观察到失败 ≠ 机制有效**，三态区分已在矩阵逐行标注。
- 非预期状态变化率 0/21 于全部 8 配置：主体对世界内部状态**没有写入通道**（payload 为每调用新建 dict，额外返回字段被忽略）——该性质不依赖消融的三机制，属循环结构事实。
- 误拒检查：oracle 在 P1C1A1/P0C1A1/P1C0A1/P0C0A1（A=1）四配置 d1_pass=True；A=0 时 d1_pass=False 因账本为空导致基线退化（评估语义被审计关闭，非保护）。

**E2 类型边界（三臂 48 行，logs/E2_typeboundary.log，E2_TYPE_BOUNDARY_MATRIX.csv）**：
- 调用链定位（逐行读引擎源码）：agent_callable → try/except 取 4 字段（解析守卫，覆盖"调用异常/缺字段"）→ evaluate_d1/d2/d4/d5（守卫外）。评估器局部守卫：d2 有 isinstance(matrix,dict) 顶层守卫；d5 纯比较（任何垃圾判错）；**d1/d4 假定 dict → int/None/list 直接 AttributeError 逃逸（DOS 洞）**。
- 失效边界三态：解析守卫拦截（none/str/raise/list，pf=2，记录完整）；评估器局部守卫静默判错（d2/d5 类垃圾，pf=0，**拒绝不可追溯**——无 parse 计数、无原因字段，仅表现为指标为 0）；崩溃（d1_int/multi_field，记录不完整）。
- A_check 臂（REWRITTEN typecheck 包装，不改引擎本体：校验失败抛异常由引擎既有 except 接住）：15 畸形全部 pf=2、记录完整、拒绝原因逐条可追溯；valid_oracle 与 welltyped_semantically_invalid 正常放行（pf=0）——无误拒；任何臂任何畸形均无 d*_pass=True（垃圾从未被当作有效状态接受）。
- "解析成功但语义无效"（恒 q0 预测）在三臂都进入评估流程被计为错误而非拒绝——正确行为（类型校验不得替代能力评估）。

**E3 重放负对照（11 场景，logs/E3_replay.log，E3_REPLAY_RESULTS.csv）**：
- 代码契约（读 execute_replay_cli）：种子派生校验 + 以账本 action 为源重建世界 + json 规范化逐字对账。**契约是内部一致性，不是真实性**——action 篡改若结局不变（C 对象任意动作→q0）则双方同步变化，SUCCESS（tamper_action_equivalent）；结局改变的 action 篡改被检出。
- 检出：seed 翻转、next_state 篡改、异结局 action 篡改、重排、重复、遗漏（全部 REJECTED，MATCH）。
- UNRESOLVED：坏 JSON 行 → JSONDecodeError 崩溃（规格未定义坏行处理）；session_idx+seed 一致性重贴标签 → SUCCESS（内容-会话绑定规格未定义，不升级解读）；记录级额外字段 → SUCCESS（审计范围=seed+ledger，评估字段不受重放审计——范围发现）。
- REPLAY_SPEC v0.3 prose 的 1e-9 浮点容差未见于 CLI（实现为逐字相等，比规格更严）——差异已记录。

**E4 对抗主体（18 行，logs/E4_adversarial.log，E4_ADVERSARIAL_RESULTS.csv；脚本化探针，无 LLM 参与，不外推普遍安全性）**：
- A1 潜变量窃取：engine 两臂 INTERCEPTED（0/21）；消融臂 BREACH（21/21）。
- A2 账本伪造：engine 两臂 INTERCEPTED（0/22）；消融臂 BREACH（1/22）。
- A3 类型混淆多步：engine_orig/消融臂 DOS_CRASH 成功；engine_check 被解析守卫拒绝（pf=2，记录完整）。
- A4 状态写入注入：三臂 NO_CHANNEL（0/21）——世界状态无写入通道。
- A5a D6 恒定输出伪装：engine 两臂 **成功**——恒定 'q0' 主体 d6_divergence=0.0，无需任何等变能力（指标盲区，非保护失败）。
- A5b 公共/私有混合：NO_CHANNEL（Phase II 无混合通道；d5_acc=0.0 判错无混淆）。
- 正常对照：oracle 三臂 d1_pass=True，无误拒。

## 二、解释性推断

- 投影、深拷贝、解析守卫、world.step 拒绝四项性质由**确定性组件结构直接保证**（消融实验逐项归因），不是统计观察行为；A5a 是**指标语义盲区**：D6 只检验"输出对置换等变"，恒定输出平凡等变——D6=0 不蕴含"具备双射一致性能力"，主张应收窄为"对置换扰动的输出稳定性检验，对恒定输出无鉴别力"。
- 类型混淆 DOS 的根因是**评估器层假定 dict**，与投影/深拷贝/审计三机制正交（消融臂同样崩溃）——历史 llm_boundary.py（pydantic、extra=forbid、枚举、重复键拒止）正是补此层缺口的组件，Phase II 因 callable 接口+无 pydantic 依赖从未接入。A_check 证明该层可以在不动引擎本体的前提下外挂补齐。

## 三、P4 结论的修正

- **加强**：潜变量不可见性、账本变异封禁、畸形输出记录完整性（E1 消融归因到单机制；E4 攻击全部实测）。
- **收窄**：重放等价契约——验"一致性"不验"真实性"（E3 两场景实证）；D6 置换不变性主张——恒定输出盲区（E4-A5a）。
- **推翻**：P4 类别 3 中"账本变异守卫"作为独立机制的表述——Phase II 不存在该机制，账本完整性实际由 deepcopy（写入隔离）+ world.step（字段来源封闭）保证。
- **维持**：非法动作拒绝属世界组件（两臂同 0）；类型校验通用组件更强（现引擎有实测缺口，A_check 补齐）。
- 边界声明：以上"优于对照"仅指优于 rebuild/p4/generic_twin.py 这一最小对照与消融配置，**不构成"优于所有通用 Harness"的主张**。

## 四、未解决问题

- U-P5-1：坏 JSON 行与会话重贴标签的重放行为无规格（UNRESOLVED）。
- U-P5-2：D6 恒定输出盲区的规格意图未定义——应加鉴别性对照还是接受该检验的弱主张（UNRESOLVED）。
- U-P5-3：typecheck 是否应作为引擎原生层并入（需裁决 llm_boundary 历史组件的归属，超本轮范围）。
- U-P5-4（继承 P4）：D1 效度 INSUFFICIENT；查询生成器历史形态、置换检验缺失、阈值量级依据。
- U-P5-5：消融未覆盖"账本变异守卫"（不存在独立实现）；E4 主体为脚本化探针，未测试真实 LLM 生成攻击（无模型/提示/采样可记录——若未来引入需按规范记录运行次数与参数）。

## 五、统一分析小结

主效应：P→暴露、C→变异、A→记录完整性（E1 因子化实证）。交互：C×A 通道遮蔽（审计关闭使变异无靶）。反例：A3 解析守卫不覆盖评估器类型假定（崩溃）；A5a 恒定输出骗取 d6=0；tamper_action_equivalent 不可检出。未覆盖：世界状态写入通道（三臂均无）、坏行处理、真实性绑定。设计限制：单种子、CONDITION_C、脚本化主体、twin 为最小对照。
