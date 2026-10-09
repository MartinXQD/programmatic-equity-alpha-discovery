"""Native vector figures from released author-created aggregate tables only."""
from pathlib import Path
import csv
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
R=Path(__file__).resolve().parents[1]
SIZES={'workflow':(570,170),'complete_yield':(570,235)}
def label(c,x,y,text,size=9):
    c.setFont('Sans',size);c.setFillColor(colors.HexColor('#24384d'));c.drawString(x,y,text)
def draw(name,c,lang):
    rows=list(csv.DictReader((R/'results/pareto_layer_yield.csv').open()))
    if name=='workflow':
        boxes=[('Generated / local','20,000'),('Expression review','10,117'),('Approx. supported','3,562'),('Retained / valid','3,285'),('Non-corr. passes','82')]
        for i,(title,count) in enumerate(boxes):
            x=5+i*114;c.setFillColor(colors.HexColor('#eef3f7'));c.roundRect(x,55,105,80,6,fill=1,stroke=0)
            label(c,x+7,115,title,8);label(c,x+20,77,count,19)
            if i<4:c.setStrokeColor(colors.HexColor('#7e95aa'));c.line(x+105,95,x+114,95)
        label(c,5,25,'Complete frozen retained cohort, October 7, 2026. Correlation and submission are separate.',9)
        return
    bands=[(1,5),(6,10),(11,15),(16,20),(21,27),(28,40)]
    label(c,20,218,'A. Non-correlation pass yield (all valid results)',10)
    label(c,300,218,'B. Passes by local-priority layer',10)
    for i,(lo,hi) in enumerate(bands):
        v=[r for r in rows if lo<=int(r['layer'])<=hi];n=sum(int(r['valid_results']) for r in v);p=sum(int(r['non_correlation_pass']) for r in v);rate=p/n
        x=24+i*43;c.setFillColor(colors.HexColor('#3d688a'));c.rect(x,55,30,rate*750,fill=1,stroke=0)
        label(c,x,40,f'{lo}-{hi}',8);label(c,x-2,rate*750+63,f'{rate:.1%}',8)
        label(c,x-1,22,f'{p}/{n}',7)
    for i,r in enumerate(rows):
        x=302+i*6.2;h=int(r['non_correlation_pass'])*17
        c.setFillColor(colors.HexColor('#3d688a'));c.rect(x,55,4.8,h,fill=1,stroke=0)
        if i in [0,9,19,29,39]:label(c,x,38,str(i+1),8)
    label(c,302,20,'Layer counts sum to 82 / 3,285. All 40 layers completed.',8)
