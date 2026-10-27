import zipfile, io, re, sys, os

def varint(b,i):
    v=0; shift=0
    while True:
        c=b[i]; i+=1
        v |= (c & 0x7f) << shift
        if not c & 0x80: return v,i
        shift+=7

def snappy_block(b):
    ul,i=varint(b,0); out=bytearray()
    while i<len(b):
        t=b[i]; i+=1; tag=t&3
        if tag==0:
            ln=t>>2
            if ln>=60:
                extra=ln-59  # 60..63 -> 1..4 bytes
                ln=int.from_bytes(b[i:i+extra],'little'); i+=extra
            out+=b[i:i+ln]; i+=ln
        else:
            if tag==1:
                ln=((t>>2)&7)+4; d=(t>>5)<<8 | b[i]; i+=1
            elif tag==2:
                ln=(t>>2)+1; d=int.from_bytes(b[i:i+2],'little'); i+=2
            else:
                ln=(t>>2)+1; d=int.from_bytes(b[i:i+4],'little'); i+=4
            start=len(out)-d
            for k in range(ln):
                out.append(out[start+k] if start>=0 else 0)
    return bytes(out)

def iwa_decompress(data):
    out=bytearray(); i=0
    if data[:1]==b'\xff':
        i=10  # skip stream identifier chunk
    while i+4<=len(data):
        tag=data[i]; ln=data[i+1]|data[i+2]<<8|data[i+3]<<16; i+=4
        chunk=data[i:i+ln]; i+=ln
        if tag==0x00:
            try: out+=snappy_block(chunk)
            except Exception: pass
        elif tag==0x01:
            out+=chunk
    return bytes(out)

def utf_strings(b, minlen=6):
    res=[]; cur=bytearray()
    def ok(x):
        try: s=x.decode('utf-8'); return True
        except Exception: return False
    i=0
    while i<len(b):
        c=b[i]
        if 32<=c<127 or c>=0xC2:
            j=i; buf=bytearray()
            while j<len(b):
                d=b[j]
                if 32<=d<127: buf.append(d); j+=1
                elif d>=0xC2:
                    # try utf-8 sequence
                    n=2+(d>=0xE0)+(d>=0xF0)
                    seq=b[j:j+n]
                    if ok(seq): buf+=seq; j+=n
                    else: break
                else: break
            if len(buf)>=minlen:
                s=buf.decode('utf-8',errors='ignore')
                if re.search(r'[\u4e00-\u9fffA-Za-z]{3}', s): res.append(s)
            i=max(j,i+1)
        else:
            i+=1
    return res

def pages_text(path):
    z=zipfile.ZipFile(path)
    pieces=[]
    for n in z.namelist():
        if n.startswith('Index/') and n.endswith('.iwa') and ('Document' in n or 'Metadata' in n):
            raw=z.read(n)
            dec=iwa_decompress(raw)
            pieces.append(' '.join(utf_strings(dec)))
    return '\n'.join(pieces)

WS='/Users/liyang/Documents/CMAWSE'
os.chdir(WS)
import glob
for p in sorted(glob.glob('*.pages')):
    try:
        t=pages_text(p)
        cjk=len(re.findall(r'[\u4e00-\u9fff]', t))
        print(f'{p}')
        print(f'   extracted strings: {len(t)} chars, CJK chars: {cjk}')
        head=' '.join(t[:400].split())
        print(f'   HEAD: {head[:400]}')
    except Exception as e:
        print(f'{p} ERROR: {e}')
