# CMAWSE 重建机制（REBUILD MECHANISM）

## 总则
1. **只读输入**：archive/、assets/（SHA-256 锚定，manifests/SHA256SUMS.txt）永不修改；一切产物写入 extracted/、rebuild/、verification/。
2. **双语义标签，强制不可混用**：
   - `RESTORED` —— 逐字提取自档案（仅允许加 PROVENANCE 注释头），来源文件+行区间可回溯。
   - `REWRITTEN` —— 按在档规范新写。必须附：规格来源（文件+行区间）、验收基线（在档测试/数字）、重写者与日期。
   - 任何文件不得默认无标签。这是对档案 MF-REG-01（实现反向注入规范）警告的镜像防护：防止"重建反向注入历史"。
3. **门禁前置**：没有通过对应门禁的构件，不得宣称与档案一致。

## 流水线（P0–P4）
- **P0 档案层（已完成）**：哈希锚定 + 只读副本 + V1–V8 核验（见 verification/VERIFICATION_REPORT.md）。
- **P1 提取（已完成，可重放）**：`rebuild/extract.py` → extracted/ 树。规则：模块头归属 → src/cmawse/；测试套件 → tests/；harness → phase2/；无头块 → fragments/；最新版编译失败 → quarantine/。同名多版本全部保留于 versions/，src 取"源内最新行"版本。
- **P2 装配门禁（已执行，Phase II FAIL，见 verification/P2_GATE_SUMMARY.md）**：引擎×测试全配对矩阵实跑；以档案内验收声明为基线。教训：**"最新引擎+最新测试"不是合法配对假设**，必须矩阵化实证。
- **P3 重写层（待执行）**：两个 REWRITTEN 目标——Phase II 最终引擎（蓝图 phase2_rewrite_blueprint.md）、Registry models/validator（蓝图 registry_rewrite_blueprint.md，前置 F1 裁决）。
- **P4 证据链**：重写产物测试输出 → 与 REG-01~10 唯一合法数字表对照 → 报告。任何新数字必须另立编号，不得混入 REG 表。

## 硬前置：F1 Schema 裁决
两份互斥 Schema v0.1（V3 已核验）在重写 Registry 前必须择一为准：
- 方案 A（以孤本 Phase 2 报告的实现词汇为准）：DERIVED_REPORT/GENERAL_SCIENTIFIC_CLAIM 合法，Phase 3.1 的"漂移删除"记为改判。
- 方案 B（以 Phase 3.1 审计基线为准）：8 枚举 28 值闭式，孤本报告词汇记为历史阶段。
裁决必须显式记录于 rebuild/DECISIONS.md 并给出理由；未裁决前 Registry 重写不得开工。

## 验收纪律
- 测试通过 ≠ 规范完备（档案 L62786 原话："仅证明测试脚本自身通过了断言"）。P3 重写验收 = v7 7/7 + 规范对账 + REG 数字对照三重。
- 重建产物中的任何差异（包括 24 个字体替换字符级的已知替换）必须可追溯到本仓库文档。
