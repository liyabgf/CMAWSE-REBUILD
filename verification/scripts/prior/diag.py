import re, os, unicodedata
WS='/Users/liyang/Documents/CMAWSE'
def norm(s):
    s=unicodedata.normalize('NFKC',s)
    for a,b in [('\u2019',"'"),('\u2018',"'"),('\u201c','"'),('\u201d','"')]: s=s.replace(a,b)
    return re.sub(r'\s+','',s)
corpus_parts={f:norm(open(os.path.join(WS,f),encoding='utf-8').read()) for f in
  ['CMAWSE启动.md','CMAWSE第一阶段.md','Evidence Registry.md','整理执行一.txt','CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md']}
corpus=''.join(corpus_parts.values())

targets=['Evidence Registry碰真实数据前存档','CMAWSE_Evidence_Registry_Schema_Drift_Conformance_Repair_Phase3.1-3.3.md',
         'CMAWSE Phase II: 规范完备性与可实现性法医审计报告 (v0.1)','CMAWSE Evidence Registry Phase 3.7']
for name in targets:
    p=f'/tmp/cmawse_full/{name}.extracted.txt'
    t=norm(open(p,encoding='utf-8').read())
    ln=14; step=max(1,(len(t)-ln)//40)
    probes=[t[i:i+ln] for i in range(0,len(t)-ln,step)][:40]
    fails=[x for x in probes if x not in corpus]
    print('='*8, name, f'| normchars={len(t)} | short-probe fail {len(fails)}/{len(probes)}')
    for f in fails[:8]: print('   MISS:', f)
    # long identifier search
    ids=set(re.findall(r'[A-Za-z_][A-Za-z0-9_\.]{10,}', open(p,encoding='utf-8').read()))
    missing=[i for i in sorted(ids) if norm(i) not in corpus]
    print(f'   identifiers: {len(ids)} total, {len(missing)} absent from corpus')
    for m in missing[:10]: print('   ID-MISS:', m)
