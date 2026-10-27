# -*- coding: utf-8 -*-
import sys, os, unicodedata, datetime, re
sys.path.insert(0,'/tmp/pylibs')
from fpdf import FPDF

WS='/Users/liyang/Documents/CMAWSE'
OUT=os.path.join(WS,'资产')
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
STAMP=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

RAD={0x2f42:'文',0x2f74:'立',0x2f24:'大',0x2faf:'面',0x2f64:'用',0x2f00:'一',
0x2f40:'支',0x2f8f:'行',0x2f84:'至',0x2f94:'言',0x2e9f:'母',0x2f29:'小',0x2f6c:'目',
0x2f0a:'入',0x2f46:'无',0x2f26:'子',0x2f50:'比',0x2ed4:'门',0x2f83:'自',0x2ed3:'长',
0x2fae:'非',0x2f1d:'口',0x2f12:'力',
0x2ed8:'青',0x2f8a:'见',0x2ed1:'韦',0x2ed2:'齿',0x2ed6:'风',0x2ed7:'飞',0x2ed9:'食',
0x2eda:'马',0x2edb:'骨',0x2edc:'鬼',0x2edd:'鱼',0x2edf:'鸟',0x2ee0:'卤',0x2ee1:'麦',
0x2ee2:'黄',0x2ee3:'黾',0x2ee4:'齐',0x2ee6:'龟',0x2ee5:'龙',
0x2f01:'丨',0x2f02:'丶',0x2f03:'丿',0x2f04:'乙',0x2f05:'亅',0x2f06:'二',0x2f07:'亠',
0x2f08:'人',0x2f09:'儿',0x2f0b:'八',0x2f0c:'冂',0x2f0d:'冖',0x2f0e:'冫',0x2f0f:'几',
0x2f10:'凵',0x2f11:'刀',0x2f13:'勹',0x2f14:'匕',0x2f15:'匚',0x2f16:'匸',0x2f17:'十',
0x2f18:'卜',0x2f19:'卩',0x2f1a:'厂',0x2f1b:'厶',0x2f1c:'又',0x2f1e:'囗',0x2f1f:'土',
0x2f20:'士',0x2f21:'夂',0x2f22:'夊',0x2f23:'夕',0x2f27:'女',0x2f28:'子2',0x2f2a:'宀',
0x2f2b:'寸',0x2f2c:'小2',0x2f2d:'尸',0x2f2e:'屮',0x2f2f:'山',0x2f30:'巛',0x2f31:'工',
0x2f32:'己',0x2f33:'巾',0x2f34:'干',0x2f35:'幺',0x2f36:'广',0x2f37:'廴',0x2f38:'廾',
0x2f39:'弋',0x2f3b:'彐',0x2f3c:'彡',0x2f3d:'彳',0x2f3e:'心',0x2f3f:'戈',0x2f41:'戶',
0x2f43:'斗',0x2f44:'斤',0x2f47:'日',0x2f48:'曰',0x2f49:'月',0x2f4a:'木',0x2f4b:'欠',
0x2f4c:'止',0x2f4d:'歹',0x2f4e:'殳',0x2f4f:'毋',0x2f51:'毛',0x2f52:'氏',0x2f53:'气',
0x2f54:'水',0x2f55:'火',0x2f56:'爪',0x2f57:'父',0x2f58:'爻',0x2f59:'爿',0x2f5a:'片',
0x2f5b:'牙',0x2f5c:'牛',0x2f5d:'犬',0x2f5e:'玄',0x2f5f:'玉',0x2f60:'瓜',0x2f61:'瓦',
0x2f62:'甘',0x2f63:'生',0x2f65:'田',0x2f66:'疋',0x2f67:'疒',0x2f68:'癶',0x2f69:'白',
0x2f6a:'皮',0x2f6b:'皿',0x2f6d:'矛',0x2f6e:'矢',0x2f6f:'石',0x2f70:'示',0x2f71:'禸',
0x2f72:'禾',0x2f73:'穴',0x2f75:'竹',0x2f76:'米',0x2f77:'糸',0x2f78:'缶',0x2f79:'网',
0x2f7a:'羊',0x2f7b:'羽',0x2f7c:'老',0x2f7d:'而',0x2f7e:'耒',0x2f7f:'耳',0x2f80:'聿',
0x2f81:'肉',0x2f82:'臣',0x2f85:'臼',0x2f86:'舌',0x2f87:'舛',0x2f88:'舟',0x2f89:'艮',
0x2f8b:'血',0x2f8c:'行2',0x2f8d:'衣',0x2f8e:'襾',0x2f90:'角',0x2f91:'言2',0x2f92:'谷',
0x2f93:'豆',0x2f95:'貝',0x2f96:'赤',0x2f97:'走',0x2f98:'足',0x2f99:'身',0x2f9a:'車',
0x2f9b:'辛',0x2f9c:'辰',0x2f9d:'辵',0x2f9e:'邑',0x2f9f:'酉',0x2fa0:'釆',0x2fa1:'里',
0x2fa2:'金',0x2fa3:'長',0x2fa4:'門2',0x2fa5:'阜',0x2fa6:'隶',0x2fa7:'雨',0x2fa8:'青2',
0x2fa9:'非2',0x2fab:'面2',0x2fac:'革',0x2fad:'韋',0x2fb0:'香',0x2fb1:'馬',0x2fb2:'骨2',
0x2fb3:'鬼2',0x2fb4:'魚2',0x2fb5:'鳥',0x2fb6:'鹵',0x2fb7:'鹿',0x2fb8:'麥',0x2fb9:'麻',
0x2fba:'黃',0x2fbb:'黍',0x2fbc:'黑',0x2fbd:'黹',0x2fbe:'黽',0x2fbf:'鼎',0x2fc0:'鼓',
0x2fc1:'鼠',0x2fc2:'鼻',0x2fc3:'齊',0x2fc4:'齒',0x2fc5:'龍',0x2fc6:'龜',0x2fc7:'龠'}
# dedupe mistakes (approximate entries with trailing 2 were defensive guesses; drop entries mapping to non-existent forms)
RAD={k:v for k,v in RAD.items() if not v.endswith('2')}

STRIP=set('\u200b\u200c\u200d\ufeff\u00ad\u2060\u0000\u0001\u0002\u0003\u0004\u0005\u0006\u0007\u0008\u000b\u000c\u000e\u000f\u001b\u007f')

SUBST={0x26a0:'△',0x27e8:'〈',0x27e9:'〉',0x3f5:'ε',0x27f9:'⇒',0x1f449:'▶',0x1f4cb:'▤',0xe020:'□'}
SUBST_LOG={}
def clean(s):
    out=[]
    for ch in s:
        o=ord(ch)
        if o in STRIP: continue
        if o in RAD: ch=RAD[o]
        if o in SUBST:
            SUBST_LOG[o]=SUBST_LOG.get(o,0)+1
            ch=SUBST[o]
        out.append(ch)
    return ''.join(out)

def wrap(line, max_units=106):
    line=line.replace('\t','    ')
    if not line: return ['']
    res=[]; cur=[]; units=0
    for ch in line:
        u=2 if unicodedata.east_asian_width(ch) in 'WF' else 1
        if units+u>max_units:
            res.append(''.join(cur)); cur=[ch]; units=u
        else:
            cur.append(ch); units+=u
    if cur: res.append(''.join(cur))
    return res

class Doc(FPDF):
    def __init__(self,htxt):
        super().__init__(format='A4')
        self.htext=htxt
        self.alias_nb_pages()
    def header(self):
        if self.page_no()==1: return
        self.set_font('AU',size=7)
        self.set_text_color(120,120,120)
        self.cell(0,4,self.htext,align='C',new_x='LMARGIN',new_y='NEXT')
        self.set_text_color(0,0,0)
        self.set_y(self.t_margin+6)
    def footer(self):
        self.set_y(-12)
        self.set_font('AU',size=7)
        self.set_text_color(120,120,120)
        self.cell(0,5,f'第 {self.page_no()} / {{nb}} 页  ·  CMAWSE-ASSET-REBUILD-2026',align='C')
        self.set_text_color(0,0,0)

def read_lines(path):
    with open(path,encoding='utf-8') as f: return f.read().split('\n')

def render(fname, code, title, subtitle, sources, note):
    SUBST_LOG.clear()
    parts=[]
    total_chars=0
    for (kind,path,start,end,label) in sources:
        if kind=='inline':
            body=label
            label='阶段 PDF 总表（本文件生成）'
        elif kind=='text':
            ls=read_lines(path)[start-1:(end if end else None)]
            body=clean(chr(10).join(ls))
        else:
            body=clean(open(path,encoding='utf-8').read())
        parts.append((label,body))
        total_chars+=len(parts[-1][1])
    htxt=f'CMAWSE 资产重建 · {code} · {title}'
    pdf=Doc(htxt)
    pdf.set_margins(15,15,15)
    pdf.set_auto_page_break(auto=True,margin=16)
    pdf.add_font(family='AU',fname=FONT)
    pdf.set_font('AU',size=9)
    pdf.add_page()
    # cover
    pdf.set_font('AU',size=16)
    pdf.multi_cell(0,9,title,align='C'); pdf.ln(2)
    pdf.set_font('AU',size=11)
    pdf.multi_cell(0,7,subtitle,align='C'); pdf.ln(4)
    pdf.set_font('AU',size=9)
    info=f'文号：CMAWSE-ASSET-REBUILD-2026-{code}\n生成时间：{STAMP}\n原始字符总量：{total_chars:,}\n'
    srcs='\n'.join(f'原始来源 {i+1}：{label}' for i,(label,_) in enumerate(parts))
    pdf.multi_cell(0,6,info+srcs)
    pdf.ln(2)
    pdf.multi_cell(0,6,'编制原则：\n1. 原文全文收录，零删改、零摘要化；本 PDF 为原始导出的逐字重排。\n2. 仅为可渲染性做的最小处理：Kangxi 部首伪影映射回正字、制表符展开为空格、零宽字符剔除。\n3. 阶段划分与原始文件对照关系见 00 号总索引。')
    if note:
        pdf.ln(2); pdf.multi_cell(0,6,'来源说明：'+note)
    pdf.ln(3)
    pdf.set_font('AU',size=7); pdf.set_text_color(120,120,120)
    pdf.multi_cell(0,4.5,'———— 以下为原始全文 ————',align='C')
    pdf.set_text_color(0,0,0)
    pdf.set_font('AU',size=9)
    nlines=0
    for label,body in parts:
        pdf.add_page()
        pdf.set_font('AU',size=8); pdf.set_text_color(60,60,60)
        pdf.multi_cell(0,5,'【原始来源：'+label+'】')
        pdf.set_text_color(0,0,0); pdf.set_font('AU',size=9)
        for raw in body.split('\n'):
            for seg in wrap(raw):
                pdf.cell(0,4.6,seg,new_x='LMARGIN',new_y='NEXT')
                nlines+=1
    if SUBST_LOG:
        pdf.add_page()
        pdf.set_font('AU',size=12)
        pdf.cell(0,8,'附录：不可渲染字符替换留档（原始字符 → 替换字形）',new_x='LMARGIN',new_y='NEXT')
        pdf.set_font('AU',size=9)
        pdf.ln(2)
        for o in sorted(SUBST_LOG):
            pdf.cell(0,5.5,'U+%04X → %s    共 %d 处（原始字符无法以嵌入字体渲染，按本表替换，信息经此留档无损）'%(o,SUBST[o],SUBST_LOG[o]),new_x='LMARGIN',new_y='NEXT')
    out=os.path.join(OUT,fname)
    pdf.output(out)
    sz=os.path.getsize(out)
    print(f'{fname} | chars={total_chars:,} | lines={nlines:,} | pages={pdf.page_no()} | {sz/1024:.0f} KB')
    return total_chars, pdf.page_no()

UNIQ='/tmp/cmawse_full/Evidence Registry碰真实数据前存档.extracted.txt'
ASSETDOC=os.path.join(WS,'CMAWSE_资产文档_ARCHIVE_ASSET_MAP_v1.md')

# 00 总索引：资产文档全文 + 阶段总表
stage_table='''CMAWSE 资产重建 · 阶段 PDF 总表（原始数据无遗漏对照）

| 编号 | 阶段 | 内容 | 原始来源（文件 / 行区间） |
| 00 | 全局 | 资产总索引与阶段地图 | CMAWSE_资产文档_ARCHIVE_ASSET_MAP_v1.md（全文） |
| 01 | 阶段一 | 项目起源与启动（白皮书原型与启动讨论） | CMAWSE启动.md（全文，120,377 tokens 对话导出） |
| 02 | 阶段二 | v1.2 系统构建规范与核心实现 | CMAWSE第一阶段.md L1–23242（对话1，544,605 tokens） |
| 03 | 阶段三 | Branch A 契约一致性修复与审计闭环 | CMAWSE第一阶段.md L23243–30446（对话2）+ L30447–49030（对话3） |
| 04 | 阶段四 | 系统架构深度评析 | CMAWSE第一阶段.md L49031–50133（对话4） |
| 05 | 阶段五 | 独立重建研究与 Phase II | CMAWSE第一阶段.md L50134–63032（对话5，684,187 tokens） |
| 06 | 阶段六 | 档案考古与三阶审计（PASS 1/1.5/2 + 证据账本 + SPEC/SCHEMA v0.1） | Evidence Registry.md L1–4203（对话1，756,606 tokens） |
| 07 | 阶段七 | Registry 实现与 Schema 加固（Phase 1→3.7） | Evidence Registry.md L4204–5428（对话2，728,970 tokens） |
| 08 | 阶段七 | Registry Phase 2 对抗测试报告（全工作区唯一孤本，含提取伪影说明） | Evidence Registry碰真实数据前存档.pdf 文本提取（3,052 字符） |
| 09 | 阶段七 | 原始文本导出（整理执行一，与 07 同源对话的独立导出件） | 整理执行一.txt（全文） |
| 10 | 阶段八 | Registry 闭环归档 3.1–3.8（含 Phase 3.8 唯一记录） | CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md（全文） |

覆盖声明：以上 11 份 PDF 覆盖本工作区全部 8 段对话导出、全部唯一孤本报告与最终闭环归档，
对应工作区 20 个实体文件的信息总量（其余 15 份 PDF 与 11 份 .pages 经包含性核验均为上述来源的重复快照）。'''

render('00_资产总索引与阶段地图.pdf','00','CMAWSE 资产总索引与阶段地图','ARCHIVE ASSET MAP — MASTER INDEX',
       [('text',ASSETDOC,1,None,'CMAWSE_资产文档_ARCHIVE_ASSET_MAP_v1.md（全文）'),
        ('text',None,None,None,'__STAGE_TABLE__') if False else ('inline',None,None,None,None)] if False else
       [('text',ASSETDOC,1,None,'CMAWSE_资产文档_ARCHIVE_ASSET_MAP_v1.md（全文）'),
        ('inline',None,None,None,stage_table)],
       None)

render('01_阶段一_项目起源与启动_原文全文.pdf','01','阶段一：项目起源与启动','原始对话全文 · 白皮书原型与可行性讨论',
       [('text',os.path.join(WS,'CMAWSE启动.md'),1,None,'CMAWSE启动.md（全文）')],None)

render('02_阶段二_v1.2规范与核心实现_原文全文.pdf','02','阶段二：v1.2 系统构建规范与核心实现','原始对话全文 · 白皮书 → Phase 1 核心 → Phase 2 可供性门禁',
       [('text',os.path.join(WS,'CMAWSE第一阶段.md'),1,23242,'CMAWSE第一阶段.md L1–23242（对话「CMAWSE v1.2 系统构建规范」）')],None)

render('03_阶段三_契约修复与审计闭环_原文全文.pdf','03','阶段三：Branch A 契约修复与审计闭环','原始对话全文 · Phase 3.1.5 契约一致性 → Phase 3.2.6 正交审计终局',
       [('text',os.path.join(WS,'CMAWSE第一阶段.md'),23243,30446,'CMAWSE第一阶段.md L23243–30446（对话「CMAWSE 3.1.5 契约一致性修复」）'),
        ('text',os.path.join(WS,'CMAWSE第一阶段.md'),30447,49030,'CMAWSE第一阶段.md L30447–49030（对话「CMAWSE 审计一致性最终闭环」）')],None)

render('04_阶段四_架构深度评析_原文全文.pdf','04','阶段四：系统架构深度评析','原始对话全文',
       [('text',os.path.join(WS,'CMAWSE第一阶段.md'),49031,50133,'CMAWSE第一阶段.md L49031–50133（对话「CMAWSE 系统架构深度评析」）')],None)

render('05_阶段五_独立重建与PhaseII_原文全文.pdf','05','阶段五：独立重建研究与 Phase II','原始对话全文 · Reconstruct-v2 + Micro-World + v1.0.x + Phase II 全程',
       [('text',os.path.join(WS,'CMAWSE第一阶段.md'),50134,63032,'CMAWSE第一阶段.md L50134–63032（对话「CMAWSE 系统独立重建研究」）')],None)

render('06_阶段六_档案考古与三阶审计_原文全文.pdf','06','阶段六：档案考古与三阶审计','原始对话全文 · PASS 1/1.5/2 + 证据账本 + 二阶/三阶审计 + SPEC/SCHEMA v0.1',
       [('text',os.path.join(WS,'Evidence Registry.md'),1,4203,'Evidence Registry.md L1–4203（对话「CMAWSE 档案考古索引构建」）')],None)

render('07_阶段七_Registry实现与Schema加固_原文全文.pdf','07','阶段七：Registry 实现与 Schema 加固','原始对话全文 · Validator Phase 1/2 思考流 → Phase 3.1–3.7',
       [('text',os.path.join(WS,'Evidence Registry.md'),4204,5428,'Evidence Registry.md L4204–5428（对话「CMAWSE Schema 粒度加固」）')],None)

render('08_阶段七_RegistryPhase2对抗测试报告_孤本原文.pdf','08','Registry Phase 2 对抗测试报告（孤本）','Adversarial Fixtures · 全工作区唯一未进入任何对话导出的报告原文',
       [('raw',UNIQ,None,None,'Evidence Registry碰真实数据前存档.pdf 全文文本提取（Registry Validator Phase 2: Adversarial Fixtures）')],
       '本报告为全工作区唯一含独有内容的文件（资产文档 v1.1 发现 F6）：Evidence Registry.md 对话导出跳过了本报告正文。'
       '文本经 ToUnicode CMap 提取，含少量字形伪影（已按 Kangxi 部首映射表回正为正字）。')

render('09_阶段七_原始文本导出_整理执行一_原文全文.pdf','09','原始文本导出：整理执行一','与 07 号同源对话的独立 TXT 导出件',
       [('text',os.path.join(WS,'整理执行一.txt'),1,None,'整理执行一.txt（全文）')],
       '本文件与 07 号 PDF 的第二段对话同源（「CMAWSE Schema 粒度加固」，728,970 tokens），为独立导出件，按原始数据无遗漏原则一并收录。')

render('10_阶段八_Registry闭环归档3.1-3.8_原文全文.pdf','10','阶段八：Registry 闭环归档 3.1–3.8','Phase 3.1–3.8 编译版闭环归档 · Phase 3.8 的唯一在档记录',
       [('text',os.path.join(WS,'CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md'),1,None,'CMAWSE Evidence Registry Phase 3.1–3.8 闭环归档.md（全文）')],None)

print('ALL DONE')
