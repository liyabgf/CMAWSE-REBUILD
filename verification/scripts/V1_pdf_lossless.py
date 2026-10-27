# -*- coding: utf-8 -*-
"""V1: 11 份资产 PDF 无损渲染独立复核。
依据 manifests/asset_manifest.json 锚定的 assets/*.pdf 副本与 archive/ 原始导出，
重新构造源文本（阶段→文件/行区间映射），用 pdfminer 反向提取，做字符多重集亏空对账。
亏空仅为已留档替换字符时判 PASS；其余判 FAIL。"""
import sys, os, re, json, collections, unicodedata
sys.path.insert(0, '/tmp/pylibs')
from pdfminer.high_level import extract_text

ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
AR = os.path.join(ROOT, 'archive')
AS = os.path.join(ROOT, 'assets')
LOG = os.path.join(ROOT, 'verification', 'logs', 'V1_pdf_lossless.log')

RAD = {0x2e9f:'母',0x2f42:'文',0x2f74:'立',0x2f24:'大',0x2faf:'面',0x2f64:'用',0x2f00:'一',0x2f40:'支',
0x2f8f:'行',0x2f84:'至',0x2f94:'言',0x2f29:'小',0x2f6c:'目',0x2f0a:'入',0x2f46:'无',0x2f26:'子',
0x2f50:'比',0x2ed4:'门',0x2f83:'自',0x2ed3:'长',0x2fae:'非',0x2f1d:'口',0x2f12:'力'}
# 已在生成端声明并留档的替换（构建时附录）：char -> 等价字形
SUBST = {0x26a0:'△',0x27e8:'〈',0x27e9:'〉',0x3f5:'ε',0x27f9:'⇒',0x1f449:'▶',0x1f4cb:'▤',0xe020:'□'}

def clean(s):
    return ''.join(SUBST.get(ord(c), RAD.get(ord(c), c)) for c in s)

def norm(s):
    s = unicodedata.normalize('NFKC', s)
    return re.sub(r'\s+', '', s)

def strip_chrome(t):
    t = re.sub(r'CMAWSE-ASSET-REBUILD-2026[0-9]*', '', t)
    t = re.sub(r'第[0-9]+/[0-9]+页', '', t)
    return t

def lines_of(path):
    return open(path, encoding='utf-8').read().split(chr(10))

STG = os.path.join(AR, 'CMAWSE第一阶段.md')
ER  = os.path.join(AR, 'Evidence Registry.md')
UNIQ = os.path.join(ROOT, 'verification', 'artifacts', 'pdf_text',
                    'Evidence Registry碰真实数据前存档.extracted.txt')

SRCMAP = {
 '00': ('archive', [open(os.path.join(AR, 'CMAWSE_资产文档_ARCHIVE_ASSET_MAP_v1.md'), encoding='utf-8').read()]),
 '01': ('archive', [open(os.path.join(AR, 'CMAWSE启动.md'), encoding='utf-8').read()]),
 '02': ('archive', [chr(10).join(lines_of(STG)[0:23242])]),
 '03': ('archive', [chr(10).join(lines_of(STG)[23242:30446]), chr(10).join(lines_of(STG)[30446:49030])]),
 '04': ('archive', [chr(10).join(lines_of(STG)[49030:50133])]),
 '05': ('archive', [chr(10).join(lines_of(STG)[50133:63032])]),
 '06': ('archive', [chr(10).join(lines_of(ER)[0:4203])]),
 '07': ('archive', [chr(10).join(lines_of(ER)[4203:5428])]),
 '08': ('pdf_text_artifact', [clean(open(UNIQ, encoding='utf-8').read())]),
 '09': ('archive', [open(os.path.join(AR, '整理执行一.txt'), encoding='utf-8').read()]),
 '10': ('archive', [open(os.path.join(AR, 'CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md'), encoding='utf-8').read()]),
}

results = []
for fname in sorted(os.listdir(AS)):
    if not fname.endswith('.pdf'):
        continue
    code = fname[:2]
    srcn = norm(''.join(SRCMAP[code][1]))
    pdfn = norm(strip_chrome(extract_text(os.path.join(AS, fname))))
    cs, cp = collections.Counter(srcn), collections.Counter(pdfn)
    deficit = {c: n for c, n in cs.items() if n > cp.get(c, 0)}
    d = sum(deficit.values())
    verdict = 'PASS' if d == 0 else 'PASS(documented-subst)' if set(map(ord, deficit)) <= set(SUBST) else 'FAIL'
    results.append((fname, len(srcn), len(pdfn), d, sorted(hex(ord(c)) for c in deficit), verdict))

with open(LOG, 'w', encoding='utf-8') as f:
    f.write('V1 独立复核：资产 PDF 无损渲染（字符多重集亏空对账）\n')
    f.write('基线：manifests/asset_manifest.json 锚定的 assets/ 副本；源文本从 archive/ 原件重构\n\n')
    for fn, s, p, d, keys, v in results:
        f.write(f'{fn} | src={s:,} pdf={p:,} deficit={d} {keys} -> {v}\n')
    f.write('\n')
    n_pass = sum(1 for r in results if r[5].startswith('PASS'))
    f.write(f'SUMMARY: {n_pass}/{len(results)} PASS (含 documented-subst)；FAIL={len(results)-n_pass}\n')
    f.write('说明：deficit 非 0 的文件，亏空字符必须全部属于构建端已声明并写入 PDF 附录留档的替换表 (SUBST)，否则 FAIL。\n')
print(open(LOG, encoding='utf-8').read())
