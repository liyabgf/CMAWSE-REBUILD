# -*- coding: utf-8 -*-
"""V2: 对话导出内 python 代码块独立复核（数量、行数、compile 门禁、省略检测）。"""
import re, os, json
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
AR = os.path.join(ROOT, 'archive')
LOG = os.path.join(ROOT, 'verification', 'logs', 'V2_code_compile.log')
FENCE = chr(96) * 3
total = {'blocks': 0, 'lines': 0, 'ok': 0, 'fail': 0, 'elision': 0}
rows = []
for f in ['CMAWSE启动.md', 'CMAWSE第一阶段.md', 'Evidence Registry.md', '整理执行一.txt',
          'CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md']:
    t = open(os.path.join(AR, f), encoding='utf-8').read()
    blocks = re.findall(FENCE + '([a-zA-Z0-9_+-]*)' + chr(10) + '(.*?)' + FENCE, t, re.S)
    py = [b for b in blocks if b[0].lower() in ('python', 'py')]
    for lang, body in py:
        total['blocks'] += 1
        total['lines'] += body.count(chr(10))
        el = bool(re.search(r'^\s*\.\.\.(?: existing code)?\s*$', body, re.M))
        if el:
            total['elision'] += 1
        try:
            compile(body, '<block>', 'exec')
            total['ok'] += 1
            stat = 'OK'
        except SyntaxError as e:
            total['fail'] += 1
            stat = f'SYNTAXFAIL:{e.lineno}:{str(e.msg)[:40]}'
        line_no = t[:t.find(FENCE + lang + chr(10) + body)].count(chr(10)) + 1 if body else 0
        rows.append((f, line_no, body.count(chr(10)), el, stat))
with open(LOG, 'w', encoding='utf-8') as f:
    f.write('V2 独立复核：对话导出 python 代码块 compile 门禁\n\n')
    for r in rows:
        f.write(f'{r[0]} @L{r[1]} lines={r[2]} elision={r[3]} {r[4]}\n')
    f.write('\nTOTAL: ' + json.dumps(total) + chr(10))
print(f"blocks={total['blocks']} lines={total['lines']} ok={total['ok']} fail={total['fail']} elision={total['elision']}")
import json
print('log:', LOG)
