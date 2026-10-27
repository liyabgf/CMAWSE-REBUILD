import re, glob, os, unicodedata

WS='/Users/liyang/Documents/CMAWSE'
def norm(s):
    s=unicodedata.normalize('NFKC',s)
    s=s.replace('\u2019',"'").replace('\u2018',"'").replace('\u201c','"').replace('\u201d','"')
    return re.sub(r'\s+','',s)

corpus_parts={}
for f in ['CMAWSE启动.md','CMAWSE第一阶段.md','Evidence Registry.md','整理执行一.txt','CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md']:
    corpus_parts[f]=norm(open(os.path.join(WS,f),encoding='utf-8').read())
corpus=''.join(corpus_parts.values())
print(f'CORPUS normalized chars: {len(corpus)}')
print()

def probes(text, n=60, ln=28):
    t=norm(text)
    if len(t)<ln*2: return [t] if t else []
    step=max(1,(len(t)-ln)//n)
    return [t[i:i+ln] for i in range(0,len(t)-ln,step)][:n]

rows=[]
for p in sorted(glob.glob('/tmp/cmawse_full/*.extracted.txt')):
    name=os.path.basename(p).replace('.extracted.txt','')
    raw=open(p,encoding='utf-8').read()
    pr=probes(raw)
    hit=sum(1 for x in pr if x in corpus)
    # which md file holds the hits
    per={}
    for f,c in corpus_parts.items():
        per[f]=sum(1 for x in pr if x in c)
    best=max(per.items(), key=lambda kv: kv[1])
    rows.append((name,len(raw),len(pr),hit,best[0],best[1],{k:v for k,v in per.items() if v>0}))

for name,n,pc,h,bf,bh,per in rows:
    pct=100.0*h/pc if pc else 0
    print(f'{pct:5.1f}% ({h}/{pc}) chars={n:>6}  {name}')
    print(f'        best: {bf} {bh}/{pc}   others: { {k.split(".")[0]:v for k,v in per.items() if k!=bf} }')
