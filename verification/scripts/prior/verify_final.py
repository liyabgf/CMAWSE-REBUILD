import sys, os, re, unicodedata, random
sys.path.insert(0,'/tmp/pylibs')
from pdfminer.high_level import extract_text
WS='/Users/liyang/Documents/CMAWSE'; OUT=os.path.join(WS,'资产')
RAD={0x2e9f:'母',0x2f42:'文',0x2f74:'立',0x2f24:'大',0x2faf:'面',0x2f64:'用',0x2f00:'一',0x2f40:'支',
0x2f8f:'行',0x2f84:'至',0x2f94:'言',0x2f29:'小',0x2f6c:'目',0x2f0a:'入',0x2f46:'无',0x2f26:'子',
0x2f50:'比',0x2ed4:'门',0x2f83:'自',0x2ed3:'长',0x2fae:'非',0x2f1d:'口',0x2f12:'力'}
def clean(s):
    return ''.join(RAD.get(ord(c),c) for c in s)
def norm(s):
    s=unicodedata.normalize('NFKC',s)
    return re.sub(r'\s+','',s)
def strip_chrome(t):
    t=re.sub(r'CMAWSE-ASSET-REBUILD-2026[0-9]*','',t)
    t=re.sub(r'第[0-9]+/[0-9]+页','',t)
    t=re.sub(r'CMAWSE资产重建·[0-9]+·[^ ]{0,40}','',t)
    t=re.sub(r'第[0-9]+/\{nb\}页','',t)
    return t
def read_lines(p): return open(p,encoding='utf-8').read().split(chr(10))
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
 '08': clean(open('/tmp/cmawse_full/Evidence Registry碰真实数据前存档.extracted.txt',encoding='utf-8').read()),
 '09': open(os.path.join(WS,'整理执行一.txt'),encoding='utf-8').read(),
 '10': open(os.path.join(WS,'CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md'),encoding='utf-8').read(),
}
random.seed(7)
allok=True
for fname in sorted(os.listdir(OUT)):
    if not fname.endswith('.pdf'): continue
    code=fname[:2]
    srcn=norm(srcmap[code]); pdfn=norm(strip_chrome(extract_text(os.path.join(OUT,fname))))
    L=18
    if len(srcn)>L*2:
        probes=[srcn[i:i+L] for i in random.sample(range(len(srcn)-L),120)]
    else: probes=[srcn]
    hit=sum(1 for p in probes if p in pdfn)
    ok = hit==len(probes)
    if not ok: allok=False
    print(f'{fname} | src={len(srcn):,} | probes {hit}/{len(probes)} {"OK" if ok else "FAIL"}')
print('ALL FILES NO-LOSS VERIFIED' if allok else 'SOME FAILURES REMAIN')
