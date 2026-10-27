import sys
sys.path.insert(0,'/tmp/pylibs')
from fpdf import FPDF
pdf=FPDF(format='A4')
pdf.set_margins(15,15,15)
pdf.add_font(family='AU',fname='/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
pdf.set_font('AU',size=9)
pdf.set_auto_page_break(auto=True,margin=15)
pdf.add_page()
sample=('CMAWSE 资产重建冒烟测试：中文渲染 ΔE₁ ΔE₂ → ≠ ≤ ± × … ✓ ✗ '
        '「」『』【】（）：；，。——…· ├─└│ 变量 v17、c42；p<10⁻⁴；'
        'Apend-nlyLedger; RFC 6902; $H_{mid-1..6}$; ⻘州; 赛博⻘州; ⺟⽂⽅⽐⻓')
pdf.multi_cell(0,5,sample)
pdf.add_page()
for i in range(60):
    pdf.cell(0,5,f'第{i+1}行：核验行文本 ABC-123 中文内容 {i*7}',new_x='LMARGIN',new_y='NEXT')
pdf.output('/tmp/cmawse_full/smoke.pdf')
print('smoke pdf written')
