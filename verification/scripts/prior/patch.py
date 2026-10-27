# -*- coding: utf-8 -*-
src = open('/tmp/cmawse_full/build_assets.py', encoding='utf-8').read()

old = r'''    for (kind,path,start,end,label) in sources:
        if kind=='text':
            ls=read_lines(path)[start-1:(end if end else None)]
            body='
'.join(ls)
            parts.append((label,body))
        else:
            body=clean(open(path,encoding='utf-8').read())
            parts.append((label,body))'''

new = r'''    for (kind,path,start,end,label) in sources:
        if kind=='inline':
            body=label
            label='阶段 PDF 总表（本文件生成）'
        elif kind=='text':
            ls=read_lines(path)[start-1:(end if end else None)]
            body='
'.join(ls)
        else:
            body=clean(open(path,encoding='utf-8').read())
        parts.append((label,body))'''

assert old in src, 'loop block not found'
src = src.replace(old, new)
open('/tmp/cmawse_full/build_assets.py', 'w', encoding='utf-8').write(src)
print('patched OK')
