# -*- coding: utf-8 -*-
"""V8: .pages 片段级复核。方法：Snappy 字面量段字符串提取 + 与语料库/PDF 孪生交叉比对。
局限（必须如实记录）：IWA 全文解压未成功（自实现 Snappy 解包器在 Document.iwa 主块失步），
因此本核验为片段级，不是全文级。verdict 只能给 PARTIALLY_VERIFIED。"""
import zipfile, re, os, unicodedata
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
AR = os.path.join(ROOT, 'archive')
PT = os.path.join(ROOT, 'verification', 'artifacts', 'pdf_text')
LOG = os.path.join(ROOT, 'verification', 'logs', 'V8_pages_fragment.log')

def norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s))

corpus = ''
for f in ['CMAWSE启动.md', 'CMAWSE第一阶段.md', 'Evidence Registry.md', '整理执行一.txt',
          'CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md']:
    corpus += norm(open(os.path.join(AR, f), encoding='utf-8').read())

NOISE = re.compile(r'PingFang|Helvetica|Courier|TimesNewRoman|STIXTwoMath|DocumentStylesheet|paragraphStyle|liststyle|tile_paper|ginger/|bullet_circle|CalculationEngine|AnnotationAuthor|DocumentMetadata|ViewState|HeaderStorage|DataList|Storage|Subtitle|Oblique|Italic|Semibold|Medium|Regular|directional|referenceLine|legend|chart-|toc-entry|drop-cap|box-0|Note|Dash|default|category|Fill|Center|Top|SoftM|Edge|Key|Hard|soft|hard|Numbered|Harvar|副标题|破折号|删除线|哈佛|Note Taking|InspectorSegment|FormalSimplifiedChineseDecimal|captions|shapestyle|Object C')

rows = []
for p in sorted(os.listdir(AR)):
    if not p.endswith('.pages'):
        continue
    z = zipfile.ZipFile(os.path.join(AR, p))
    toks = []
    for n in z.namelist():
        if n.endswith('.iwa'):
            raw = z.read(n)
            for m in re.finditer(rb'[\x20-\x7e]{10,}', raw):
                toks.append(m.group(0).decode('latin-1'))
            for m in re.finditer(rb'(?:[\xe0-\xef][\x80-\xbf]{2}){4,}', raw):
                try:
                    toks.append(m.group(0).decode('utf-8'))
                except Exception:
                    pass
    twin = os.path.join(PT, p[:-6] + '.extracted.txt')
    twinn = norm(open(twin, encoding='utf-8').read()) if os.path.exists(twin) else ''
    uniq = []
    for t in toks:
        tn = norm(t)
        if len(tn) < 10 or NOISE.search(t):
            continue
        if tn in corpus or (twinn and tn in twinn):
            continue
        uniq.append(t.strip())
    uniq = sorted(set(uniq), key=len, reverse=True)
    kept = []
    for u in uniq:
        if not any(u != k and norm(u) in norm(k) for k in kept[:40]):
            kept.append(u)
    rows.append((p, len(toks), len(kept), kept[:3]))

out = ['V8: .pages 片段级复核（PARTIALLY_VERIFIED —— IWA 全文解压未成功，详见方法局限）', '']
for p, nt, nk, samples in rows:
    out.append(f'{p[:60]} | literal-run tokens={nt} | not-in-corpus/twin={nk}')
    for s in samples:
        out.append(f'     sample: {s[:90]}')
out.append('')
out.append('方法局限：Snappy 压缩块的回指(copy)段无法由字面量扫描恢复；本核验只能证明')
out.append('"未发现 .pages 含语料库/PDF 孪生之外的实质内容"，不能证明逐字节全文一致。')
out.append('V8 verdict: PARTIALLY_VERIFIED（全文级 = UNVERIFIED）')
open(LOG, 'w', encoding='utf-8').write(chr(10).join(out))
print(chr(10).join(out))
