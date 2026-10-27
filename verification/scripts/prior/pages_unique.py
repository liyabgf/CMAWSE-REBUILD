import zipfile, re, os, unicodedata, glob
WS='/Users/liyang/Documents/CMAWSE'
def norm(s):
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
corpus=''
for f in ['CMAWSE启动.md','CMAWSE第一阶段.md','Evidence Registry.md','整理执行一.txt','CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md']:
    corpus+=norm(open(os.path.join(WS,f),encoding='utf-8').read())

NOISE=re.compile(r'PingFang|Helvetica|Courier|TimesNewRoman|STIXTwoMath|DocumentStylesheet|paragraphStyle|liststyle|tile_paper|ginger/|bullet_circle|CalculationEngine|AnnotationAuthor|DocumentMetadata|ViewState|HeaderStorage|DataList|Storage|Subtitle|Oblique|Italic|Semibold|Medium|Regular|directional|referenceLine|legend|chart-|toc-entry|drop-cap|box-0|Note|Dash|default|category|Fill|Center|Top|SoftM|Edge|Key|Hard|soft|hard|Numbered|Harvar|副标题|破折号|删除线|哈佛|Note Taking')

def pages_tokens(zpath):
    z=zipfile.ZipFile(zpath); parts=[]
    for n in z.namelist():
        if n.endswith('.iwa'):
            raw=z.read(n)
            for m in re.finditer(rb'[\x20-\x7e]{10,}', raw):
                parts.append(m.group(0).decode('latin-1'))
            for m in re.finditer(rb'(?:[\xe0-\xef][\x80-\xbf]{2}){4,}', raw):
                try: parts.append(m.group(0).decode('utf-8'))
                except Exception: pass
    return parts

print('== .pages 独有内容检测（token 不在 MD/TXT 语料 + 不在 PDF 孪生中） ==')
grand=[]
for p in sorted(glob.glob(os.path.join(WS,'*.pages'))):
    name=os.path.basename(p)[:-6]
    twin=os.path.join('/tmp/cmawse_full', name+'.extracted.txt')
    twin_norm=norm(open(twin,encoding='utf-8').read()) if os.path.exists(twin) else ''
    toks=pages_tokens(p)
    uniq=[]
    for t in toks:
        tn=norm(t)
        if len(tn)<10 or NOISE.search(t): continue
        if tn in corpus or (twin_norm and tn in twin_norm): continue
        uniq.append(t.strip())
    # dedupe substrings
    uniq=sorted(set(uniq), key=len, reverse=True)
    kept=[]
    for u in uniq:
        if not any(u!=k and norm(u) in norm(k) for k in kept[:40]): kept.append(u)
    print(f'{name[:58]} | tokens={len(toks)} unique-not-anywhere={len(kept)}')
    for k in kept[:6]: print(f'     · {k[:110]}')
    grand.append((name,len(kept)))
print()
print('TOTAL flagged tokens:', sum(c for _,c in grand))
