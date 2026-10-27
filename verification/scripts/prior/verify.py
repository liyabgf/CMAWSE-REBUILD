import sys, os, re, unicodedata, random
sys.path.insert(0,'/tmp/pylibs')
from pdfminer.high_level import extract_text
WS='/Users/liyang/Documents/CMAWSE'
OUT=os.path.join(WS,'资产')
def norm(s):
    s=unicodedata.normalize('NFKC',s)
    s=s.replace(chr(0x2019),"'").replace(chr(0x2018),"'").replace(chr(0x201c),'"').replace(chr(0x201d),'"')
    s=s.replace(chr(0x2e9f),'母')  # in case
    return re.sub(r'\s+','',s)

# source text per pdf (same construction as build)
def read_lines(p):
    return open(p,encoding='utf-8').read().split(chr(10))
STG=os.path.join(WS,'CMAWSE第一阶段.md'); ER=os.path.join(WS,'Evidence Registry.md')
srcmap={
 '00': open(os.path.join(WS,'CMAWSE_资产文档_ARCHIVE_ASSET_MAP_v1.md'),encoding='utf-8').read(),
 '01': open(os.path.join(WS,'CMAWSE启动.md'),encoding='utf-8').read(),
 '02': chr(10).join(read_lines(STG)[0:23242]),
 '03': chr(10).join(read_lines(STG)[23242:30446])+chr(10).join(read_lines(STG)[30446:49030]),
 '04': chr(10).join(read_lines(STG)[49030:50133]),
 '05': chr(10).join(read_lines(STG)[50133:63032]),
 '06': chr(10).join(read_lines(ER)[0:4203]),
 '07': chr(10).join(read_lines(ER)[4203:5428]),
 '08': open('/tmp/cmawse_full/Evidence Registry碰真实数据前存档.extracted.txt',encoding='utf-8').read(),
 '09': open(os.path.join(WS,'整理执行一.txt'),encoding='utf-8').read(),
 '10': open(os.path.join(WS,'CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md'),encoding='utf-8').read(),
}
random.seed(42)
for fname in sorted(os.listdir(OUT)):
    if not fname.endswith('.pdf'): continue
    code=fname[:2]
    src=srcmap[code]
    srcn=norm(src)
    pdftxt=extract_text(os.path.join(OUT,fname))
    pdfn=norm(pdftxt)
    # probes: 60 random 18-char windows from source
    L=18; probes=[]
    if len(srcn)>L*2:
        pos=random.sample(range(len(srcn)-L),60)
        probes=[srcn[i:i+L] for i in pos]
    hit=sum(1 for p in probes if p in pdfn)
    # reverse: probes from pdf found in source
    rprobes=[]
    if len(pdfn)>L*2:
        pos=random.sample(range(len(pdfn)-L),60)
        rprobes=[pdfn[i:i+L] for i in pos]
    rhit=sum(1 for p in rprobes if p in srcn)
    print(f'{fname} | src_chars={len(srcn):,} pdf_chars={len(pdfn):,} ({100*len(pdfn)/max(1,len(srcn)):.1f}%) | src->pdf {hit}/60 | pdf->src {rhit}/60')
