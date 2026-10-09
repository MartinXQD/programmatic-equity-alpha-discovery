"""Render aggregate vector figures for Markdown using optional paper dependencies."""
from pathlib import Path
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from paper_figures import draw,SIZES
import os,sys

root=Path(__file__).resolve().parents[1]
fonts=Path(os.environ.get('ALPHA_PAPER_FONT_DIR','/System/Library/Fonts/Supplemental' if sys.platform=='darwin' else 'paper_fonts'))
pdfmetrics.registerFont(TTFont('Sans',str(fonts/'Arial.ttf')))
work=root/'artifacts/figures';work.mkdir(parents=True,exist_ok=True)
for name in SIZES:
    target=work/(name+'.pdf');c=canvas.Canvas(str(target),pagesize=SIZES[name]);draw(name,c,'EN');c.save()
    subprocess.run(['pdftoppm','-r','240','-singlefile','-png',str(target),str(root/'paper'/name)],check=True)
assets=root/'docs/assets';assets.mkdir(parents=True,exist_ok=True)
(assets/'layer_yield.png').write_bytes((root/'paper/complete_yield.png').read_bytes())
print('PASS: aggregate workflow and yield figures rendered')
