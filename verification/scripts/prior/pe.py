import re, sys, zlib, glob, os

def streams(data):
    out=[]
    for m in re.finditer(rb'stream\r?\n', data):
        start=m.end(); e=data.find(b'endstream', start)
        if e<0: continue
        raw=data[start:e]
        try: out.append(zlib.decompress(raw))
        except Exception:
            try: out.append(zlib.decompressobj().decompress(raw))
            except Exception: pass
    return out

def parse_cmaps(slist):
    cmap={}
    for s in slist:
        if b'beginbfchar' not in s and b'beginbfrange' not in s: continue
        txt=s.decode('latin-1')
        for blk in re.findall(r'beginbfchar(.*?)endbfchar', txt, re.S):
            for a,b in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
                try: cmap[int(a,16)]=''.join(chr(int(b[i:i+4],16)) for i in range(0,len(b),4))
                except Exception: pass
        for blk in re.findall(r'beginbfrange(.*?)endbfrange', txt, re.S):
            for a,b,c in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
                try:
                    lo,hi,dst=int(a,16),int(b,16),int(c,16)
                    for k in range(lo,min(hi,lo+4096)+1): cmap[k]=chr(dst+(k-lo))
                except Exception: pass
    return cmap

def hexstr(h,cmap):
    b=bytes.fromhex(re.sub(r'\s','',h))
    if cmap and len(b)%2==0:
        return ''.join(cmap.get(int.from_bytes(b[i:i+2],'big'),'\ufffd') for i in range(0,len(b),2))
    try: return b.decode('utf-8')
    except Exception: return b.decode('latin-1')

def litstr(s,cmap):
    s=s.replace('\\(','(').replace('\\)',')').replace('\\\\','\\')
    try: raw=s.encode('latin-1')
    except Exception: return s
    if cmap and len(raw)%2==0:
        return ''.join(cmap.get(int.from_bytes(raw[i:i+2],'big'),chr(raw[i])) for i in range(0,len(raw),2))
    try: return raw.decode('utf-8')
    except Exception: return s

def extract(path):
    data=open(path,'rb').read()
    slist=streams(data); cmap=parse_cmaps(slist); out=[]
    for s in slist:
        if b'Tj' not in s and b'TJ' not in s: continue
        txt=s.decode('latin-1'); buf=[]
        for m in re.finditer(r'\[(.*?)\]\s*TJ|<([0-9A-Fa-f\s]+)>\s*Tj|\(((?:\\.|[^\\()])*)\)\s*Tj|TD|Td|T\*|ET', txt, re.S):
            if m.group(0) in ('TD','Td','T*','ET'): buf.append('\n'); continue
            if m.group(1) is not None:
                for h,l in re.findall(r'<([0-9A-Fa-f\s]+)>|\(((?:\\.|[^\\()])*)\)', m.group(1)):
                    buf.append(hexstr(h,cmap) if h else litstr(l,cmap))
            elif m.group(2) is not None: buf.append(hexstr(m.group(2),cmap))
            elif m.group(3) is not None: buf.append(litstr(m.group(3),cmap))
        if buf: out.append(''.join(buf))
    t='\n'.join(out)
    return re.sub(r'\n{3,}','\n\n',t), bool(cmap)

outdir=sys.argv[1]
for p in sorted(glob.glob('*.pdf')):
    try:
        t,c=extract(p)
        base=os.path.splitext(p)[0].replace('/','_')
        with open(os.path.join(outdir, base+'.extracted.txt'),'w',encoding='utf-8') as f: f.write(t)
        print(f'{p} | chars={len(t)} | cmap={c}')
    except Exception as e:
        print(f'{p} | ERROR {e}')
