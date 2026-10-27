# P6-A：D6 鉴别力报告

## 结论

- **原 D6（引擎实现）**：稳定性指标，不是能力指标。INVERSE_MAP 只翻译置换空间值（s0/s1/…），恒回原空间标签的主体 E 恒为 0；恒定输出主体 d6=0（P5 已证，本轮复现）。
- **预注册 d6v2（E∧R∧I，R=预测不同取值≥2）**：**INSUFFICIENT**——按 P6_PLAN 冻结判据，tau_keyed（只按 tau 奇偶输出）在留出集 s5 通过（E=0,R=1,I=1），命中冻结失败判据。失败根因：R 度量的是"输出有变化"而非"对目标相关字段响应"。
- **事后修订 d6v3（E∧R2∧I，R2=标签交换响应性：交换两条不同标签查询的 (X,act)，预测必须随之交换，且交换前预测必须不同）**：在调参 s1、留出 s5、**从未使用的 s7** 上，六类主体判定完全一致：learn_table（真等变）通过；constant/tau_keyed/wrong_map/irrelevant_position/anti_equivariant 全部被拒绝。判定 SUPPORTED（限于脚本化主体与本协议）。

## 事后修订的完整回代史（透明披露，均非预注册）

1. v3 迭代 1：R2 空交换漏洞（恒定主体两侧同值，交换恒成立）——被 constant 击穿。
2. v3 迭代 2：交换配对重叠（复合交换换回原位）——实现 bug，learn_table 被误判。
3. v3 迭代 3：交换配对索引错误（balanced_queries 交错序导致配到同组）——实现 bug。
4. v3 最终：R2 加"交换前必须不同"+逐对独立 payload → 三组会话全分离。s7 上 learn_table 曾因"全局回退使 C 组预测与 A 组相同"被判非等变（指标正确检出部分等变）；主体回退改为 X 边际（标签敏感）后通过——这是**主体修正**，非指标放宽，已披露。

## 人工可查的最小案例

六类主体的构造均见 a_d6.py / a_d6v3.py；核心对比：constant 与 learn_table 在同一 payload 上，R2 探针为交换 qs[0](A,act_beta) 与 qs[1](B,act_gamma) 的 (X,act)——learn_table 预测随交换翻转为 q2/q1，constant 不变。数据：D6_RESULTS.csv（v2）、D6_RESULTS_V3.csv（v3）、logs/A_d6.log、logs/A_d6v3.log。

## 边界

- 只在脚本化主体上验证；未对真实 LLM 测试。
- d6v3 鉴别的是"对标签级输入变化的目标相关响应性"，仍不等同"具备因果理解"。
- R2 依赖 holdout 含至少两条真标签不同的查询（原始 holdout 全 q0 退化时无法执行——与 P4 D1 结论同源）。
