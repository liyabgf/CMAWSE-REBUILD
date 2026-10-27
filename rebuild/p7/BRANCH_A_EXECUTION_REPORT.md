# P7-C：Branch A 认知沙盒执行报告

## 状态变更：UNVERIFIED → **PARTIALLY_VERIFIED（子集执行）+ 精确断裂面**

## 断裂面（可复现，先于一切结论）

- extracted/src/cmawse 无任何 __init__.py（包结构缺失，pytest 导入即失败）。
- 测试导入链断裂：cmawse.agent.cognitive_state / agent.deliberation / agent.representation 在提取树中不存在（全仓 grep 无对应类定义）——**这些是认知投影、审议、表征主张的承重模块**。
- agent/llm_boundary.py 仅存于 quarantine，compile=FAIL（L84 语法断裂，P1 已记录）。
- pytest 9.2.0 本轮安装（环境级，未动历史文件）。

## P7 副本执行（REWRITTEN 包装）

rebuild/p7/branch_a_copy/：仅复制自洽子集 cmawse/core/schema.py + cmawse/world/bus.py 并添加 __init__.py；模块源码与 extracted **字节一致（sha256 比对，见 BRANCH_A_RESULTS.csv PROVENANCE 行）**。

## 认知隔离的操作化与实测（8 案例）

私有 = 各主体 PrivateHorizon（视野内坐标、可闻声学切片、剥夺者全部感知）；公共 = 经目击资格仲裁的 VerifiedEventEntry。实测（BRANCH_A_RESULTS.csv）：

- C1 视距外（100m>15m）主体不进入 visible_actors：PASS（**空间信息隔离实际生效**）。
- C2 视距内可见：PASS（隔离不是"全盲"）。
- C3a horizon 属性赋值被 pydantic frozen 拒绝：PASS。
- **C3b horizon 容器内容变异（hz.visible_actors['b']=pos）被接受：FAIL——真实机制缺口**。frozen=True 只冻结属性赋值，不冻结 dict 内容；与 P3 重建引擎用深拷贝解决的正是同类问题。Branch A 原始实现未闭合该通道。
- C4 声学衰减（60dB@100m 不可闻、@2m 可闻 31.8dB）：PASS。
- C5 感官剥夺者（10m 内 90dB）空视界：PASS。
- C6 generate_horizons 确定性重放：PASS。
- C7 目击资格：直接参与者合格、视距外非参与者不合格：PASS。

## 判定

- **bus/schema 子集的"感知级认知隔离"：7/8 PASS，机制实际执行**（此前 UNVERIFIED → 现在有可复现执行证据）。
- **C3b 为反例**：内存级不变性未闭合（容器内容变异可行）。Branch A 的"认知隔离"= 感知门控（视距/声学/剥夺/目击资格）有效；**不变性保护不完整**。
- agent 层认知隔离（认知投影、审议、表征、LLM 边界）：**仍 UNVERIFIED**（模块缺失，静态存在≠执行验证）。不得以子集结果外推。
- 概念区分（对 P5/P6 结论）：Branch A 感知门控 ≈ 投影机制的信息子集（同类：信息可见性），但 C3b 缺口 ≠ 深拷贝机制（内存隔离），且无权限模型（允许/禁止读写的显式规则）——三者在本仓库分别处于"子集已执行/已重建验证/不存在"状态。
