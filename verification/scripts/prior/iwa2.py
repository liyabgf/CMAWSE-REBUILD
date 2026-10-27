import zipfile, re, sys
sys.path.insert(0,'/tmp/cmawse_full')
from iwa import snappy_block

def analyze(zpath, name):
    z=zipfile.ZipFile(zpath)
    raw=z.read(name)
    i=0; total=0; ok=0; fail=0; chunks=0
    if raw[:1]==b'\xff': i=10
    data_all=bytearray()
    while i+4<=len(raw):
        tag=raw[i]; ln=raw[i+1]|raw[i+2]<<8|raw[i+3]<<16; i+=4
        chunk=raw[i:i+ln]; i+=ln
        if tag==0x00:
            chunks+=1
            try:
                d=snappy_block(chunk); ok+=1; total+=len(d); data_all+=d
            except Exception as e:
                fail+=1
        elif tag==0x01:
            total+=len(chunk); data_all+=chunk
    print(f'{zpath[:50]} | {name}: compressed chunks {chunks}, ok {ok}, fail {fail}, decompressed {total} bytes')
    for kw in [b'fixture', b'adversarial', b'validator', b'CMAWSE', b'Evidence']:
        n=data_all.count(kw)
        if n: print(f'   keyword {kw}: {n}')
    return data_all

d=analyze('/Users/liyang/Documents/CMAWSE/Evidence Registry碰真实数据前存档.pages','Index/Document.iwa')
# find CJK and ascii text runs in full decompressed data
import re
s=[]
cur=bytearray()
i=0
b=bytes(d)
while i<len(b):
    c=b[i]
    if 32<=c<127 or c>=0xC2:
        j=i; buf=bytearray()
        while j<len(b):
            x=b[j]
            if 32<=x<127: buf.append(x); j+=1
            elif x>=0xC2:
                n=2+(x>=0xE0)+(x>=0xF0)
                try: buf+=b[j:j+n]; j+=n
                except Exception: break
            else: break
        try:
            t=buf.decode('utf-8')
            if len(t)>=8 and re.search(r'[\u4e00-\u9fff]', t): s.append(t)
        except Exception: pass
        i=max(j,i+1)
    else: i+=1
print(f'CJK text runs found: {len(s)}')
for x in s[:25]: print('  |', x[:90])
