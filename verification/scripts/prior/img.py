import re, zlib, struct, sys, os

def png(w,h,data,cs):
    ch = 3 if cs in (b'DeviceRGB',b'RGB') else (1 if cs in (b'DeviceGray',b'Gray') else 4)
    if len(data) < w*h*ch: return None
    raw=b''.join(b'\x00'+data[y*w*ch:(y+1)*w*ch] for y in range(h))
    def chunk(t,d):
        c=t+d; return struct.pack('>I',len(d))+c+struct.pack('>I',zlib.crc32(c)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2 if ch==3 else (0 if ch==1 else 6),0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

def images(path,outdir):
    data=open(path,'rb').read()
    results=[]
    for m in re.finditer(rb'/Subtype\s*/Image', data):
        seg=data[max(0,m.start()-400):m.start()+1200]
        try:
            w=int(re.search(rb'/Width\s+(\d+)',seg).group(1))
            h=int(re.search(rb'/Height\s+(\d+)',seg).group(1))
            cs=(re.search(rb'/ColorSpace\s*/(\w+)',seg) or [None,b'DeviceRGB'])[1]
        except Exception: continue
        sm=re.search(rb'stream\r?\n',data[m.start():m.start()+2000])
        if not sm: continue
        s=m.start()+sm.end(); e=data.find(b'endstream',s)
        if e<0: continue
        try: raw=zlib.decompress(data[s:e])
        except Exception: continue
        results.append((w,h,cs,raw))
    results.sort(key=lambda r:-(r[0]*r[1]))
    out=[]
    for idx,(w,h,cs,raw) in enumerate(results[:8]):
        if w*h>50000:
            p=png(w,h,raw,cs)
            if p:
                fp=os.path.join(outdir,f'{os.path.basename(path)[:20]}_{idx}.png')
                open(fp,'wb').write(p); out.append((fp,w,h,len(raw)))
    return len(results), out

outdir='/tmp/cmawse_full/pages'
for path in ['/Users/liyang/Documents/CMAWSE/当前阶段.pdf','/Users/liyang/Documents/CMAWSE/实现和实验数据.pdf','/Users/liyang/Documents/CMAWSE/执行阶段一.pdf']:
    total,out=images(path,outdir)
    print(os.path.basename(path), f'images decoded: {total}, saved top {len(out)}')
    for fp,w,h,sz in out[:5]: print(f'   {fp} {w}x{h} raw={sz}')
