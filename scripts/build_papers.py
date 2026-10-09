"""Typeset the editable manuscripts with embedded fonts and native mathematical layout."""
from pathlib import Path
from html import escape
import json,re,os,sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Image,KeepTogether,Spacer,Flowable
from paper_figures import draw as draw_figure, SIZES
import reportlab.lib.textsplit as textsplit
import reportlab.platypus.paragraph as paragraph_module

# Extend the CJK hanging-punctuation list for Simplified Chinese; do not
# modify the installed library or the editable manuscript's wording.
textsplit.ALL_CANNOT_START += '，；：！？…’”》〉'
paragraph_module.ALL_CANNOT_START = textsplit.ALL_CANNOT_START

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[0]/'artifacts/paper_qa'
OUT.mkdir(parents=True,exist_ok=True)
HERE=HERE.parents[0]/'paper'
FONTS=Path(os.environ.get('ALPHA_PAPER_FONT_DIR', '/System/Library/Fonts/Supplemental' if sys.platform=='darwin' else 'paper_fonts'))
for name,file in [('Serif','Times New Roman.ttf'),('SerifBold','Times New Roman Bold.ttf'),('SerifItalic','Times New Roman Italic.ttf'),('Sans','Arial.ttf'),('Unicode','Arial Unicode.ttf'),('Courier','Courier New.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONTS/file)))
pdfmetrics.registerFontFamily('Serif',normal='Serif',bold='SerifBold',italic='SerifItalic',boldItalic='SerifBold')
pdfmetrics.registerFontFamily('Unicode',normal='Unicode',bold='Unicode',italic='Unicode',boldItalic='Unicode')

# Three explicit display equations use native vector text, true subscripts/superscripts,
# fraction bars and radicals. These small layout primitives do not evaluate formulas.
class Box:
    def __init__(self,width,above,below,draw):self.width=width;self.above=above;self.below=below;self.draw=draw

def txt(value,size=11.5,font='SerifItalic'):
    width=pdfmetrics.stringWidth(value,font,size)
    def draw(c,x,y):c.setFont(font,size);c.drawString(x,y,value)
    return Box(width,size*.8,size*.2,draw)
def seq(*boxes,gap=2.5):
    width=sum(b.width for b in boxes)+gap*(len(boxes)-1)
    def draw(c,x,y):
        for b in boxes:b.draw(c,x,y);x+=b.width+gap
    return Box(width,max(b.above for b in boxes),max(b.below for b in boxes),draw)
def script(base,sub=None,sup=None,small=7.7):
    sub=txt(sub,small,'Unicode' if any(ord(c)>127 for c in sub) else 'SerifItalic') if sub else None
    sup=txt(sup,small) if sup else None
    width=base.width+max(sub.width if sub else 0,sup.width if sup else 0)+.6
    def draw(c,x,y):
        base.draw(c,x,y)
        if sub:sub.draw(c,x+base.width+.5,y-4)
        if sup:sup.draw(c,x+base.width+.5,y+6)
    return Box(width,max(base.above,12.2 if sup else 0),max(base.below,5.6 if sub else 0),draw)
def fraction(numerator,denominator):
    width=max(numerator.width,denominator.width)+8
    def draw(c,x,y):
        c.setLineWidth(.55);c.line(x,y+3,x+width,y+3)
        numerator.draw(c,x+(width-numerator.width)/2,y+7+numerator.below)
        denominator.draw(c,x+(width-denominator.width)/2,y-3-denominator.above)
    return Box(width,7+numerator.below+numerator.above,3+denominator.above+denominator.below,draw)
def sigma(lower):
    b=txt('∑',17,'Unicode')
    if lower in ['j ∈ Uₜ','i ∈ Hₜ']:
        s=seq(txt(lower[0],7.1),txt('∈',7.1,'Unicode'),script(txt('U' if lower[0]=='j' else 'H',7.1),'t',small=5.6),gap=.5)
    else:s=txt(lower,7.1)
    width=max(b.width,s.width)
    def draw(c,x,y):b.draw(c,x+(width-b.width)/2,y);s.draw(c,x+(width-s.width)/2,y-8)
    return Box(width,13.6,8+s.below,draw)
def bar(b):
    def draw(c,x,y):b.draw(c,x,y);c.setLineWidth(.55);c.line(x,y+b.above+1,x+b.width,y+b.above+1)
    return Box(b.width,b.above+2,b.below,draw)
def root(b):
    def draw(c,x,y):
        b.draw(c,x+14,y);c.setLineWidth(.7);p=c.beginPath();p.moveTo(x,y+1);p.lineTo(x+3,y+4);p.lineTo(x+7,y-8);p.lineTo(x+12,y+b.above+3);p.lineTo(x+14+b.width,y+b.above+3);c.drawPath(p)
    return Box(b.width+14,b.above+4,max(b.below,8),draw)
def op(value):return txt(value,11.5,'Unicode')
def w(sub='i,t'):return script(txt('w'),sub)
def ret(sup='g'):return script(txt('R'),'t',sup)
def eqbox(n):
    if n==1:
        denominator=seq(sigma('j ∈ Uₜ'),op('|'),script(txt('s'),'j,t'),op('|'),gap=1)
        f=fraction(seq(txt('2',font='Serif'),script(txt('s'),'i,t')),denominator)
        return seq(w(),op('='),f,op(','),sigma('i'),op('|'),w(),op('|'),op('='),txt('2',font='Serif'),op(','),sigma('i'),w(),op('='),txt('0',font='Serif'))
    if n==2:
        return seq(script(txt('R'),'t+1','gross'),op('='),sigma('i ∈ Hₜ'),w(),script(txt('r'),'i,t→t+1'))
    numerator=seq(op('|'),txt('252',font='Serif'),bar(script(txt('R'),sup='gross')),op('|'),gap=1.5)
    denominator=seq(txt('max',font='Serif'),op('('),bar(txt('T')),op(','),txt('0.125',font='Serif'),op(')'),gap=1)
    return seq(script(txt('F'),'local'),op('='),script(txt('S'),'local'),root(fraction(numerator,denominator)))

LATEX=[r'w_{i,t}=\frac{2s_{i,t}}{\sum_{j\in U_t}|s_{j,t}|},\qquad \sum_i|w_{i,t}|=2,\qquad \sum_iw_{i,t}=0. \tag{1}',
 r'R^{\mathrm{gross}}_{t+1}=\sum_{i\in H_t}w_{i,t}r_{i,t\to t+1}. \tag{2}',
 r'F_{\mathrm{local}}=S_{\mathrm{local}}\sqrt{\frac{|252\,\overline{R}^{\mathrm{gross}}|}{\max(\overline{T},0.125)}}. \tag{3}']
class Equation(Flowable):
    def __init__(self,n,width):super().__init__();self.n=n;self.width=width;self.b=eqbox(n);self.height=self.b.above+self.b.below+10;self.qa_id=f'equation:{n}'
    def draw(self):
        assert self.b.width<self.width-35,(self.n,self.b.width,self.width)
        self.canv.setFillColor(colors.black);self.b.draw(self.canv,(self.width-self.b.width)/2,self.b.below+5)
        self.canv.setFont('Serif',10.5);self.canv.drawRightString(self.width,self.b.below+5,f'({self.n})')
class Doc(SimpleDocTemplate):
    def afterFlowable(self,f):
        if hasattr(f,'qa_id'):self.locations.append(dict(id=f.qa_id,page=self.page))
def track(f,c,x,y):
    if hasattr(f,'qa_id') and hasattr(c,'_paper_doc'):
        c._paper_doc.geometry.append(dict(id=f.qa_id,page=c.getPageNumber(),x=x,y=y,width=getattr(f,'width',getattr(f,'_width',0)),height=getattr(f,'height',getattr(f,'_height',0))))
class TrackedParagraph(Paragraph):
    def drawOn(self,c,x,y,_sW=0):
        track(self,c,x,y);super().drawOn(c,x,y,_sW)
class TrackedTable(Table):
    def drawOn(self,c,x,y,_sW=0):
        track(self,c,x,y);super().drawOn(c,x,y,_sW)
class VectorFigure(Flowable):
    def __init__(self,name,lang,width):
        super().__init__();self.name=name;self.lang=lang;self.width=width;self.height=width*SIZES[name][1]/570;self.qa_id='figure:'+name
    def draw(self):
        self.canv.saveState();self.canv.scale(self.width/570,self.width/570);draw_figure(self.name,self.canv,self.lang);self.canv.restoreState()
    def drawOn(self,c,x,y,_sW=0):
        track(self,c,x,y);super().drawOn(c,x,y,_sW)
def rich(s):
    inline={r'U_t':'<i>U</i><sub>t</sub>',r's_{i,t}':'<i>s</i><sub>i,t</sub>',r'H_t':'<i>H</i><sub>t</sub>',r'\overline{R}^{\mathrm{gross}}':'<font name="Unicode">R̄</font><super>gross</super>',r'S_{\mathrm{local}}':'<i>S</i><sub>local</sub>',r'\overline{T}':'<font name="Unicode">T̄</font>'}
    s=escape(s)
    s=re.sub(r'\\\((.*?)\\\)',lambda m:inline[m[1]],s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'\*([^*]+)\*',r'<i>\1</i>',s)
    s=re.sub(r'`([^`]+)`',lambda m:'<font name="'+('Unicode' if any(ord(c)>127 for c in m[1]) else 'Courier')+'" size="9.4">'+m[1]+'</font>',s)
    return re.sub(r'(https://[^\s]+?)(?=[。\s]|$)',lambda m:'<link href="'+m.group(1).rstrip('.')+'" color="#2b4b68">'+m.group(1)+'</link>',s)
def make_styles(lang):
    cn=lang=='CN';body='Unicode' if cn else 'Serif';bold='Unicode' if cn else 'SerifBold'
    base=dict(fontName=body,fontSize=11,leading=15.5 if cn else 14.0,spaceAfter=5.5,wordWrap='CJK' if cn else None,allowWidows=0,allowOrphans=0)
    d={n:ParagraphStyle(n,**base) for n in ['body','title','meta','h1','h2','caption','cell','headcell','reference']}
    d['title'].fontName=bold;d['title'].fontSize=18 if cn else 16;d['title'].leading=24 if cn else 21;d['title'].spaceAfter=10
    d['meta'].fontName='Unicode' if cn else 'Sans';d['meta'].fontSize=9.4;d['meta'].leading=12;d['meta'].spaceAfter=5
    for name,size in [('h1',12.5),('h2',11.7)]:
        d[name].fontName=bold;d[name].fontSize=size;d[name].leading=16;d[name].spaceBefore=8;d[name].spaceAfter=5;d[name].keepWithNext=True
    d['caption'].fontSize=9.5;d['caption'].leading=12;d['caption'].spaceAfter=7
    for n in ['cell','headcell']:d[n].fontSize=9.4;d[n].leading=12.4;d[n].spaceAfter=0
    d['headcell'].fontName=bold
    d['reference'].fontSize=9.6;d['reference'].leading=12.4;d['reference'].spaceAfter=5
    return d
def footer(c,doc,lang):
    c._paper_doc=doc
    c.saveState();c.setStrokeColor(colors.HexColor('#bec8d1'));c.setLineWidth(.4);c.line(60,39,A4[0]-60,39)
    c.setFillColor(colors.HexColor('#586777'));c.setFont('Unicode' if lang=='CN' else 'Sans',8)
    c.drawString(60,27,'展示改编版 · 程序化股票因子发现' if lang=='CN' else 'PUBLIC DISPLAY ADAPTATION | Programmatic Equity Alpha Discovery')
    c.drawRightString(A4[0]-60,27,str(doc.page));c.restoreState()
def build(lang):
    lines=(HERE/f'Research_Paper_Public_{lang}.md').read_text().splitlines();s=make_styles(lang);story=[];i=0;tn=0;eq=0;ref=False;pn=0;width=A4[0]-124
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line:continue
        if line.startswith('# '):
            story.append(TrackedParagraph(rich(line[2:]),s['title']));continue
        if line.startswith('## '):
            ref=line[3:] in ['References','参考文献'];p=TrackedParagraph(rich(line[3:]),s['h1']);p.qa_id='section:'+line[3:];story.append(p);continue
        if line.startswith('### '):
            p=TrackedParagraph(rich(line[4:]),s['h2']);p.qa_id='subsection:'+line[4:];story.append(p);continue
        if line.startswith('$$ '):
            eq+=1;assert line[3:-3]==LATEX[eq-1],f'Equation source differs; update its native layout: {eq}'
            introduction=story.pop()
            heading=[]
            if story and getattr(story[-1],'qa_id','').startswith(('section:','subsection:')):
                heading=[story.pop()]
            story.append(KeepTogether(heading+[introduction,Spacer(1,2),Equation(eq,width),Spacer(1,6)]));continue
        if line.startswith('!['):
            caption,path=re.match(r'!\[(.*?)\]\((.*?)\)',line).groups();name='workflow' if 'workflow' in path else 'complete_yield';fig=VectorFigure(name,lang,width)
            block=KeepTogether([Spacer(1,2),fig,Spacer(1,5),TrackedParagraph(rich(caption),s['caption'])]);block.qa_id='figure:'+path;story.append(block);continue
        if line.startswith('|'):
            raw=[]
            while True:
                vals=[v.strip() for v in line.strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',v) for v in vals):raw.append(vals)
                if i>=len(lines) or not lines[i].strip().startswith('|'):break
                line=lines[i].strip();i+=1
            tn+=1;fracs={1:[.23,.36,.41],2:[.33,.14,.53],3:[.185,.09,.22,.205,.30]}[tn]
            table=TrackedTable([[Paragraph(rich(v),s['headcell'] if row==0 else s['cell']) for v in vals] for row,vals in enumerate(raw)],colWidths=[width*f for f in fracs],hAlign='LEFT',repeatRows=1)
            table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f4')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f7f8')]),('LINEABOVE',(0,0),(-1,0),.6,colors.HexColor('#38536a')),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#38536a')),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#38536a')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
            table.qa_id=f'table:{tn}'
            caption=[story.pop()] if story and getattr(story[-1],'is_table_caption',False) else []
            block=KeepTogether(caption+[table,Spacer(1,7)]);story.append(block);continue
        paragraph=line
        while i<len(lines) and lines[i].strip():paragraph+=' '+lines[i].strip();i+=1
        style=s['reference'] if ref else s['body']
        if paragraph.startswith('**Qidian '):
            paragraph=re.sub(r'\*\*\s+UCLA','**<br/>UCLA',paragraph);paragraph=re.sub(r'Engineering\s+\*\*','Engineering<br/>**',paragraph);style=s['meta']
        is_caption=bool(re.match(r'\*\*(Table|表) [123][.｜]',paragraph))
        if is_caption:style=ParagraphStyle('table_caption',parent=s['caption'],keepWithNext=True,spaceBefore=4)
        formatted = rich(paragraph)
        if style is s['meta']:
            formatted = formatted.replace('&lt;br/&gt;', '<br/>')
        pn+=1;p=TrackedParagraph(formatted,style);p.qa_id=f'paragraph:{pn}';p.is_table_caption=is_caption
        is_case=paragraph.startswith(('Case A ','Case B ','Case C ','Case D ','案例 A ','案例 B ','案例 C ','反例是案例 D'))
        story.append(KeepTogether([p]) if is_case else p)
    assert (tn,eq)==(2,3)
    # Keep the short reference list together so a lone citation cannot form a page.
    story=story[:-4]+[KeepTogether(story[-4:])]
    d=Doc(str(HERE/f'Research_Paper_Public_{lang}.pdf'),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=53,bottomMargin=53,title='From Formula Generation to Platform Evaluation' if lang=='EN' else '从公式生成到平台检验',author='Qidian (Martin) Xing',pageCompression=1)
    d.locations=[];d.geometry=[];d.build(story,onFirstPage=lambda c,p:footer(c,p,lang),onLaterPages=lambda c,p:footer(c,p,lang))
    (OUT/f'LAYOUT_LOCATIONS_{lang}.json').write_text(json.dumps(d.locations,ensure_ascii=False,indent=2))
    (OUT/f'LAYOUT_GEOMETRY_{lang}.json').write_text(json.dumps(d.geometry,ensure_ascii=False,indent=2))
    print(lang,'pages',d.page)
if __name__=='__main__':
    for language in ['CN','EN']:build(language)
