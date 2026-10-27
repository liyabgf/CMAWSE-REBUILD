# P6-B：重放真实性契约与实验结果

## 八项性质契约（定义先于实验；历史规格未定义项标 UNRESOLVED，新契约标 REWRITTEN）

| # | 性质 | 定义 | 契约来源 | 预期 |
|---|---|---|---|---|
| 1 | 重复执行 | 同种子同日志重放 | code+REPLAY_SPEC | ACCEPT |
| 2 | 顺序敏感重排 | 事件次序编码于 tick/对象轮转（语义有序） | code | REJECT |
| 3 | 重复/遗漏事件 | 长度与推进偏离 | code | REJECT |
| 4 | 跨会话重放 | session_idx 与 session_seed 派生一致但账本来自另一会话 | UNRESOLVED（规格未定义内容-会话绑定） | 未定 |
| 5 | 同结局 action 篡改 | action 改为结局不变的另一动作 | 历史规格未定义；REWRITTEN V3 契约：REJECT | V1/V2 ACCEPT，V3 REJECT |
| 6 | 内容与独立参照不符 | 账本与带外见证链根不符 | REWRITTEN V3 | REJECT |
| 7 | 坏 JSON 行/截断/中途异常 | json.loads 失败 | UNRESOLVED | 拒绝验证（UNDETERMINED），不得默认真实 |
| 8 | 来源/版本/校验信息缺失 | 见证缺失 | REWRITTEN V3 | UNDETERMINED |

## 独立真实性参照（REWRITTEN）

记录时见证包装器逐事件计算 SHA256 链（h_t = H(h_{t-1}‖tick‖action‖prev‖next‖object‖context‖status)），链根+session_idx+session_seed 提交带外 witness_store.json。**能证明**：账本内容与见证根一致（完整性+来源绑定到记录时刻）；**不能证明**：事件真实发生（记录时引擎已攻陷则无保护）、见证库本身可信（同时改写账本+见证→不可检出，实证见矩阵末行）。信任假设：见证库与被测账本独立存储且可信。

## 实测（REPLAY_AUTHENTICITY_RESULTS.csv，logs/B_replay.log）

12 案例 × V1（现行 CLI，一致性）/ V2（仅一致性）/ V3（链+带外根）/ V4（仅链自洽，演示无根重算攻击面）：
- 关键案例 tamper_action_same_outcome：V1/V2 ACCEPT（P5 盲区复现），**V3 REJECT** ✓。
- 合法记录：V3 ACCEPT（无误拒）✓。session 重贴标签：V3 UNDETERMINED（见证按 idx 绑定）✓。坏 JSON：V3 UNDETERMINED ✓。缺失见证：V3 UNDETERMINED ✓。
- 信任边界实证：账本+见证同时改写 → V3 ACCEPT(边界内不可检出)——如实记录。
- 判定分级达成：**一致性实现区分"自洽篡改"与"合法"失败，V3 成功；参照不足时返回 UNDETERMINED 而非默认真实。**
