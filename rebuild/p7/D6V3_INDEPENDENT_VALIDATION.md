# P7-A1：d6v3 独立验证报告

## 数据与主体独立性

独立集 s11/s13：grep 全仓确认从未出现在 P3–P6 任何代码、报告或日志中；P7 主体类 6 个全部先于运行定义（P7_PLAN 冻结）。P6 的 s1/s5/s7 均已参与开发决策，不再复用为独立集。

## 结果（D6V3_RESULTS.csv，logs/A1_d6v3.log）

12 类主体 × 2 独立会话，判定逐主体逐会话完全一致（零方差）：

- **full 判据（E∧R2∧I）：误通过 0**。通过者仅 learn_table（P6 真等变参照）与 seen_correct_unseen_fail。
- seen_correct_unseen_fail 通过 = **范围澄清（冻结预案命中）**：d6v3 测等变响应性，不测正确性；该主体对已见组合标签敏感、未见组合回退 q0，仍是"响应性完整"的等变主体。正确性归 D1 职责。**不声称 d6v3 是正确性指标。**
- 投机探针 memoizer_gaming（首调缓存、acc=1.00 但对交换探针无响应）被 R2 击穿 ✓。
- tau_hash_rich（输出丰富与目标无关）被 R2 击穿 ✓（E/I 对其无鉴别力——E=0、I=1）。
- E 对第二变换 σ2（对象循环+动作反置，非 D6 原映射）行为一致：不依赖特定映射巧合。

## 分量必要性（消融矩阵）

| 配置 | 误通过主体类 |
|---|---|
| E_only | 5：constant, tau_keyed, tau_hash_rich, memoizer, order_sensitive |
| E∧R2（去 I） | 1：order_sensitive（I 必要性直接证据） |
| E∧I（去 R2） | 4：constant, tau_keyed, tau_hash_rich, memoizer |
| R2∧I（去 E） | 2：wrong_map, anti_equivariant |
| **full** | **0** |

三分量各自必要性均有专属反例：R2（4 类无响应主体）、I（order_sensitive）、E（wrong_map/anti_equivariant）。

## 边界与不确定性

- 样本 = 12 类脚本主体 × 2 会话；结论限于"该主体族与该协议"，不外推真实 LLM（P7-B NOT_RUN）。
- 未做统计置信区间（N=2 会话、判定零方差、无随机性来源——枚举式而非抽样式验证）。
- 已知投机空间：交换探针仅覆盖 (X,act) 字段与 PAIRS 对；对 tau 键控的等变"作弊者"（用 tau 查表给出可交换预测）理论可行——任何固定测试集均存在记忆化投机，d6v3 不声称抗记忆化下界（memoizer 探针只覆盖了朴素缓存）。
- 判定：**SUPPORTED（限于脚本主体族，含上述投机空间披露）**。
