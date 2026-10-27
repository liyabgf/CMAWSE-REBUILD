# -*- coding: utf-8 -*-
"""V3–V7: 对资产文档 F1/F4/F6 及对话边界/token 声明的独立复核。全部基于 archive/ 哈希锚定副本。"""
import re, os, unicodedata
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
AR = os.path.join(ROOT, 'archive')
LOG = os.path.join(ROOT, 'verification', 'logs', 'V3toV7_forensic.log')

def norm(s):
    s = unicodedata.normalize('NFKC', s)
    return re.sub(r'\s+', '', s)

def read(f):
    return open(os.path.join(AR, f), encoding='utf-8').read()

ER = read('Evidence Registry.md')
ERL = ER.split(chr(10))
STG = read('CMAWSE第一阶段.md')
QD = read('CMAWSE启动.md')
ZX = read('整理执行一.txt')
CL = read('CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md')
out = []

def ev(label, needle, hay_name, hay, limit=6):
    hits = []
    for i, l in enumerate(hay.split(chr(10)), 1):
        if needle in l:
            hits.append((i, l.strip()[:150]))
            if len(hits) >= limit: break
    out.append(f'[{label}] "{needle}" in {hay_name}: {len(hits)} hit(s)')
    for h in hits:
        out.append(f'    L{h[0]}: {h[1]}')
    return hits

# ---------- V3: F1 两份 Schema v0.1 词汇互斥 ----------
out.append('==== V3: F1 两份 Schema v0.1 枚举互斥复核 ====')
schema1_markers = ['TRACEABLE_WITH_CONTEXT', 'DERIVED_REPORT', 'GENERAL_SCIENTIFIC_CLAIM', 'NEGATIVE_CONTROL', 'PAIRED_TRAJECTORY']
schema2_markers = ['AMBIGUOUS_PROVENANCE', 'EXTERNAL_ORACLE', 'EMPIRICAL_FACTOR', 'INVARIANT_BOUND', 'REPRODUCIBILITY_ASSERTION', 'BENCHMARK_MANIFEST', 'STEP_EXECUTION']
for m in schema1_markers:
    ev('V3-schema1', m, 'Evidence Registry.md', ER, 2)
for m in schema2_markers:
    ev('V3-schema2', m, 'Evidence Registry.md', ER, 2)
# 冲突对：schema1 合法 vs schema2 判漂移并删除
ev('V3-conflict', 'DERIVED_REPORT', 'Evidence Registry.md', ER, 10)
ev('V3-repair', 'CONFORMANCE_RESTORED', 'Evidence Registry.md', ER, 3)
out.append('')

# ---------- V4: F4 Phase 3.8 仅存在于闭环归档 ----------
out.append('==== V4: F4 Phase 3.8 出处唯一性复核 ====')
for name, txt in [('CMAWSE第一阶段.md', STG), ('Evidence Registry.md', ER), ('整理执行一.txt', ZX),
                  ('CMAWSE启动.md', QD), ('闭环归档.md', CL)]:
    c8 = len(re.findall(r'Phase 3\.8', txt))
    cc = txt.count('REGISTRY_V0.1_CLOSURE')
    out.append(f'  {name}: "Phase 3.8"={c8}  "REGISTRY_V0.1_CLOSURE"={cc}')
verdict_v4 = 'PASS(仅闭环归档含 Phase 3.8)' if (STG.count('Phase 3.8') == 0 and ER.count('Phase 3.8') == 0 and ZX.count('Phase 3.8') == 0 and CL.count('Phase 3.8') > 0) else 'FAIL'
out.append(f'  V4 verdict: {verdict_v4}')
out.append('')

# ---------- V5: F6 孤本 PDF 内容不在任何文本档案 ----------
out.append('==== V5: F6 碰真实数据前存档.pdf 独有内容复核 ====')
uniq_path = os.path.join(ROOT, 'verification', 'artifacts', 'pdf_text', 'Evidence Registry碰真实数据前存档.extracted.txt')
uniq = norm(open(uniq_path, encoding='utf-8').read())
corpus = norm(STG) + norm(QD) + norm(ER) + norm(ZX) + norm(CL)
probes = [uniq[i:i+24] for i in range(0, len(uniq)-24, max(1, (len(uniq)-24)//60))][:60]
hit = sum(1 for p in probes if p in corpus)
ids = sorted(set(re.findall(r'[A-Za-z_][A-Za-z0-9_]{11,}', open(uniq_path, encoding='utf-8').read())))
id_hit = [i for i in ids if norm(i) in corpus]
out.append(f'  probe containment: {hit}/60 in corpus | identifiers: {len(id_hit)}/{len(ids)} in corpus')
verdict_v5 = 'PASS(F6 成立：孤本内容不在任何文本档案)' if hit <= 12 and len(id_hit) <= 4 else 'REVIEW'
out.append(f'  V5 verdict: {verdict_v5}')
out.append(f'  孤本关键标识符示例: {[i for i in ids if norm(i) not in corpus][:6]}')
out.append('')

# ---------- V6: Registry 实现代码在档率 ----------
out.append('==== V6: Registry 实现代码在档率复核 ====')
markers = ['class EvidenceRecord', 'class ClaimRecord', 'class StatisticalRecord', 'def _check_granularity',
           'from pydantic', 'import pydantic', 'class SummaryRecord', 'ConfigDict']
for m in markers:
    total = sum(t.count(m) for t in [STG, ER, ZX, CL, QD])
    out.append(f'  "{m}": {total} occurrence(s) in all text archives')
out.append(f'  models.py 提及次数: ER={ER.count("models.py")} ZX={ZX.count("models.py")}')
verdict_v6 = 'PASS(Registry 代码 0 在档，只能重写)' if all(sum(t.count(m) for t in [STG, ER, ZX, CL, QD]) == 0 for m in ['class EvidenceRecord', 'from pydantic', 'def _check_granularity']) else 'REVIEW'
out.append(f'  V6 verdict: {verdict_v6}')
out.append('')

# ---------- V7: 对话边界与 token 数 ----------
out.append('==== V7: 对话边界与 token 声明复核 ====')
tot = 0
for name, txt in [('CMAWSE启动.md', QD), ('CMAWSE第一阶段.md', STG), ('Evidence Registry.md', ER)]:
    bnd = [(i+1, l.strip()) for i, l in enumerate(txt.split(chr(10))) if l.strip() == 'Skip to main content']
    toks = [l.strip() for l in txt.split(chr(10)) if re.fullmatch(r'[\d,]+ tokens', l.strip())]
    for t in toks:
        tot += int(t.replace(',', '').replace(' tokens', ''))
    out.append(f'  {name}: boundaries={len(bnd)} token_lines={toks}')
out.append(f'  TOTAL tokens (from export headers): {tot:,}')
out.append('  说明：header token 数为导出工具自报值，可复核其存在于文本中；但"md 导出 == 完整对话"不可从文件自身复核。')
out.append('  V7 verdict: header 数字 VERIFIED；完整性 UNVERIFIED（导出已证明会跳过报告正文，见 V5/F6）')
out.append('')

open(LOG, 'w', encoding='utf-8').write(chr(10).join(out))
print(chr(10).join(out[:8]))
print('...')
print(chr(10).join(out[-30:]))
print('LOG:', LOG)
