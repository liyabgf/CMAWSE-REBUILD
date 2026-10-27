import zipfile, re, os, unicodedata, glob

WS='/Users/liyang/Documents/CMAWSE'
def norm(s):
    s=unicodedata.normalize('NFKC',s)
    return re.sub(r'\s+','',s)

def pages_strings(zpath):
    z=zipfile.ZipFile(zpath)
    parts=[]
    for n in z.namelist():
        if n.endswith('.iwa'):
            raw=z.read(n)
            # collect printable/cjk runs >=8
            for m in re.finditer(rb'[\x20-\x7e\xe0-\xef\x80-\xbf]{8,}', raw):
                try: parts.append(m.group(0).decode('utf-8',errors='ignore'))
                except Exception: pass
    return norm(' '.join(parts))

def ids_from_text(text, minlen=12, limit=25):
    toks=sorted(set(re.findall(r'[A-Za-z_][A-Za-z0-9_\.\-]{%d,}'%(minlen-1), text)))
    # prefer distinctive ones
    return toks[:limit]

results=[]
for p in sorted(glob.glob(os.path.join(WS,'*.pages'))):
    name=os.path.basename(p)[:-6]
    pdf_txt=os.path.join('/tmp/cmawse_full', name+'.extracted.txt')
    pg=pages_strings(p)
    row={'pages':name,'pages_norm_chars':len(pg)}
    if os.path.exists(pdf_txt):
        pdf_raw=open(pdf_txt,encoding='utf-8').read()
        pdf_norm=norm(pdf_raw)
        ids=ids_from_text(pdf_raw, 14, 30)
        hit=[i for i in ids if norm(i) in pg]
        row['pdf_ids_checked']=len(ids); row['pdf_ids_in_pages']=len(hit)
        row['missing_ids']=[i for i in ids if norm(i) not in pg][:5]
        # reverse: distinctive ascii ids in pages not in pdf
        pg_ids=sorted(set(re.findall(r'[A-Za-z_][A-Za-z0-9_\.\-]{13,}', ' '.join(re.findall(r'[\x20-\x7e]{8,}', ' '.join([pg])))))) if False else []
    else:
        row['pdf_twin']='MISSING'
    results.append(row)

for r in results:
    print(f"{r['pages'][:64]}")
    print(f"   pages strings(norm)={r['pages_norm_chars']} | pdf-twin ids in pages: {r.get('pdf_ids_in_pages','-')}/{r.get('pdf_ids_checked','-')}")
    if r.get('missing_ids'): print(f"   missing from pages: {r['missing_ids']}")
    if r.get('pdf_twin')=='MISSING': print("   NO PDF TWIN")
