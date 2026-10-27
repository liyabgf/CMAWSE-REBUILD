import sys, os, re, unicodedata, random
sys.path.insert(0,'/tmp/pylibs')
from pdfminer.high_level import extract_text
WS='/Users/liyang/Documents/CMAWSE'
OUT=os.path.join(WS,'资产')
def norm(s):
    s=unicodedata.normalize('NFKC',s)
    return re.sub(r'\s+','',s)
random.seed(42)
for code,fname,srcpath in [('01','01_阶段一_项目起源与启动_原文全文.pdf',os.path.join(WS,'CMAWSE启动.md')),
                            ('09','09_阶段七_原始文本导出_整理执行一_原文全文.pdf',os.path.join(WS,'整理执行一.txt'))]:
    srcn=norm(open(srcpath,encoding='utf-8').read())
    pdfn=norm(extract_text(os.path.join(OUT,fname)))
    L=18
    pos=random.sample(range(len(srcn)-L),60)
    fails=[srcn[i:i+L] for i in pos if srcn[i:i+L] not in pdfn]
    print('==',fname,'failing probes:',len(fails))
    for f in fails:
        # locate in raw source and show context chars with codepoints
        print('  probe:',f)
        # find where each char exists in pdf
        for j,ch in enumerate(f):
            alt=f[:j]
        # try prefix matching to find first divergence
        k=0
        while k<L and f[:k+1] in pdfn: k+=1
        print('   diverges at char', k, repr(f[k]), hex(ord(f[k])) if k<L else '')
        # check char presence anywhere in pdf text
        ch=f[k] if k<L else None
        if ch: print('   char present in pdf anywhere:', ch in pdfn)
