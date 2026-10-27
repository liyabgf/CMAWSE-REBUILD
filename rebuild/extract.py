# -*- coding: utf-8 -*-
"""P1 提取管线：从对话导出中提取 python 代码块为可追踪的代码树。

规则：
- 块首 docstring 含 "模块：<path>.py"  -> src/cmawse/<path>（同名多版本分层，src/ 取最新）
- 块首含 "测试套件：/Phase x.y"        -> tests/test_phase_x_y.py（多版本同理）
- 块首含 "Experiment Harness"          -> phase2 骨架版本序列
- 无头 python 块                        -> fragments/（保留，不进 src）
- 模块/测试块 compile() 失败            -> quarantine/（不进 src，防伪完整文件）
- 每个输出文件头部注入 PROVENANCE 注释（RESTORED 标签 + 来源文件 + 行区间 + 哈希锚定）。
归一化：裸 schema.py / arbiter.py 归入 core/（同一契约模块的历史命名，报告注明）。
"""
import re, os, sys, json
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
AR = os.path.join(ROOT, 'archive')
EX = os.path.join(ROOT, 'extracted')
FENCE = chr(96) * 3
SRCFILE = 'CMAWSE第一阶段.md'

text = open(os.path.join(AR, SRCFILE), encoding='utf-8').read()
line_starts = []
pos = 0
for l in text.split(chr(10)):
    line_starts.append(pos)
    pos += len(l) + 1

def line_of(offset):
    import bisect
    return bisect.bisect_right(line_starts, offset)

blocks = []
for i, m in enumerate(re.finditer(FENCE + 'python' + chr(10) + '(.*?)' + FENCE, text, re.S)):
    body = m.group(1)
    start_line = line_of(m.start(1))
    end_line = start_line + body.count(chr(10))
    head = body[:600]
    mod = re.search(r'模块：\s*([\w/.\-]+\.py)', head)
    suite = re.search(r'测试套件：\s*(.+)', head)
    ph = re.search(r'Phase\s*([0-9]+(?:\.[0-9]+)+)', head)
    harness = 'Experiment Harness' in head or 'EXPERIMENT_HARNESS' in head
    if mod:
        kind, ident = 'module', mod.group(1)
    elif suite or ph:
        kind, ident = 'test', ('test_phase_' + ph.group(1).replace('.', '_') + '.py') if ph else 'test_suite_%03d.py' % i
    elif harness:
        kind, ident = 'harness', 'harness_%02d.py' % i
    else:
        kind, ident = 'fragment', 'frag_L%05d.py' % start_line
    try:
        compile(body, '<b>', 'exec')
        comp = 'OK'
    except SyntaxError as e:
        comp = 'FAIL:%d:%s' % (e.lineno or 0, (e.msg or '')[:48])
    blocks.append(dict(idx=i, kind=kind, ident=ident, start=start_line, end=end_line,
                       lines=body.count(chr(10)), compile=comp, body=body))

ALIAS = {'schema.py': 'core/schema.py', 'arbiter.py': 'core/arbiter.py'}
for b in blocks:
    if b['kind'] == 'module':
        b['ident'] = ALIAS.get(b['ident'], b['ident'])

def provenance(b, extra=''):
    return ('# ===== PROVENANCE =====\n'
            f'# status: RESTORED (verbatim extraction from conversation export)\n'
            f'# source: {SRCFILE} @ L{b["start"]}-L{b["end"]} (SHA-256 anchored, see manifests/SHA256SUMS.txt)\n'
            f'# block: python #{b["idx"]}  lines={b["lines"]}  compile={b["compile"]}\n'
            f'# kind: {b["kind"]}  ident: {b["ident"]}{extra}\n'
            '# edits: none. Header comment is the only addition.\n'
            '# ======================\n')

counts = {'module': 0, 'test': 0, 'harness': 0, 'fragment': 0, 'quarantine': 0}
report = []

# version groups for module/test
groups = {}
for b in blocks:
    if b['kind'] in ('module', 'test'):
        groups.setdefault((b['kind'], b['ident']), []).append(b)

for (kind, ident), bs in sorted(groups.items()):
    bs.sort(key=lambda b: b['start'])
    for n, b in enumerate(bs, 1):
        vdir = os.path.join(EX, 'versions', ('src' if kind == 'module' else 'tests'), ident.replace('/', '__'))
        os.makedirs(vdir, exist_ok=True)
        open(os.path.join(vdir, f'v{n}_L{b["start"]}.py'), 'w', encoding='utf-8').write(provenance(b, f'  version: {n}/{len(bs)}') + b['body'])
    latest = bs[-1]
    if latest['compile'] == 'OK':
        dest = os.path.join(EX, 'src' if kind == 'module' else 'tests', 'cmawse' if kind == 'module' else '', ident)
        dest = os.path.join(EX, 'src', 'cmawse', ident) if kind == 'module' else os.path.join(EX, 'tests', ident)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'w', encoding='utf-8').write(provenance(latest, f'  version: latest of {len(bs)} (selected by latest source line)') + latest['body'])
        counts[kind] += 1
        report.append((kind, ident, len(bs), latest['start'], 'src|tests (latest)'))
    else:
        counts['quarantine'] += 1
        qd = os.path.join(EX, 'quarantine')
        os.makedirs(qd, exist_ok=True)
        open(os.path.join(qd, ident.replace('/', '__') + f'_L{latest["start"]}.py'), 'w', encoding='utf-8').write(provenance(latest, '  REASON: latest version fails compile') + latest['body'])
        report.append((kind, ident, len(bs), latest['start'], 'quarantine(compile-fail)'))

# harness sequence
hs = [b for b in blocks if b['kind'] == 'harness']
hdir = os.path.join(EX, 'phase2')
os.makedirs(hdir, exist_ok=True)
for n, b in enumerate(sorted(hs, key=lambda b: b['start']), 1):
    open(os.path.join(hdir, f'harness_v{n}_L{b["start"]}.py'), 'w', encoding='utf-8').write(provenance(b, f'  harness version {n}/{len(hs)}') + b['body'])
if hs:
    counts['harness'] = len(hs)

# fragments
fdir = os.path.join(EX, 'fragments')
os.makedirs(fdir, exist_ok=True)
for b in blocks:
    if b['kind'] == 'fragment':
        open(os.path.join(fdir, b['ident']), 'w', encoding='utf-8').write(provenance(b) + b['body'])

# report
rep = ['# P1 提取报告（extract.py）', '',
       f'源：archive/{SRCFILE}（哈希锚定）；python 块总数 {len(blocks)}', '',
       f'入库统计: {json.dumps(counts, ensure_ascii=False)}', '',
       '模块/测试版本层（src|tests = 最新版；versions/ = 全部历史层）：', '',
       '| kind | ident | versions | latest@L | destination |', '|---|---|---|---|---|']
for r in report:
    rep.append(f'| {r[0]} | {r[1]} | {r[2]} | L{r[3]} | {r[4]} |')
rep += ['', '归一化说明：裸 schema.py/arbiter.py 映射为 core/schema.py、core/arbiter.py（同一契约模块的历史命名）。',
        'fragments/ 为对话内无模块头的 python 块（含语法残段），保留供追溯，不构成可构建代码。',
        'quarantine/ 为最新版编译失败者，防止拼装出"看似完整"的伪文件。']
open(os.path.join(EX, 'EXTRACTION_REPORT.md'), 'w', encoding='utf-8').write(chr(10).join(rep) + chr(10))
print(chr(10).join(rep[:12]))
print('...')
print('counts:', counts)
print('report:', os.path.join(EX, 'EXTRACTION_REPORT.md'))
