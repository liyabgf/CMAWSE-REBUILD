# CMAWSE Archive & Rebuild

约束驱动的复杂叙事仿真引擎（CMAWSE）项目档案库与重建工作区。

## 结构
- `archive/` —— 原始工作区文件的只读副本（SHA-256 锚定，`manifests/SHA256SUMS.txt`）。
- `assets/` —— 11 份阶段化资产 PDF（原文全文重排，V1 核验 11/11 无损）。
- `docs/` —— 资产地图（ASSET_MAP v1.1）。
- `verification/` —— 独立核验：V1–V8 脚本、日志、`VERIFICATION_REPORT.md`（含 UNVERIFIED 清单）、`P2_GATE_SUMMARY.md`。
- `extracted/` —— P1 提取树（RESTORED）：`src/cmawse/`、`tests/`、`phase2/`、`versions/`（全版本层）、`fragments/`、`quarantine/`。
- `rebuild/` —— 重建机制：`MECHANISM.md`、`extract.py`、两个 REWRITTEN 蓝图。

## 版本纪律（继承档案声明）
- v1.0.3 是 **FREEZE-CANDIDATE**，非 FROZEN；不得宣称跨平台比特一致（C40 UNVERIFIED）。
- 全部产物遵守 RESTORED / REWRITTEN 双标签制（见 `rebuild/MECHANISM.md`）。
- 唯一合法数字来源：REG-01~10 登记表（见 docs/ASSET_MAP_v1.1.md）。

## 快速核验
```bash
python3 verification/scripts/V1_pdf_lossless.py     # 11/11 PASS
python3 verification/scripts/V2_code_compile.py     # 93 块统计
python3 rebuild/extract.py                          # 重放 P1 提取
```

## 已知事实（勿混淆）
- Registry 实现代码 0 在档 → 只能 REWRITTEN。
- Phase II 最终引擎无法从档案复现 7/7 OK（P2 门禁 FAIL）→ 装配层需 REWRITTEN。
- Branch A 核心模块（schema/arbiter/bus/agent/cognitive/runtime）有完整模块头清单，RESTORED 可行。
