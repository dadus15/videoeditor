#!/usr/bin/env python3
"""Contact sheet of rendered CGI shots over studio white: first/middle/last frames per shot.

    python3 cgi/render_sheet.py <res> S02,S03,S04 work/test/sheet.jpg [frames_per_shot]
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
res=sys.argv[1]; shots=sys.argv[2].split(','); out=sys.argv[3]; per=int(sys.argv[4]) if len(sys.argv)>4 else 3
root=Path(__file__).resolve().parents[1]/'work'/'cgi'/res
tiles=[]
for s in shots:
    fs=sorted((root/s).glob('f*.png'))
    if not fs: continue
    idx=[round(i*(len(fs)-1)/max(per-1,1)) for i in range(per)]
    for i in idx:
        im=Image.open(fs[i]); bg=Image.new('RGB',im.size,(236,235,231)); bg.paste(im,(0,0),im)
        d=ImageDraw.Draw(bg); d.text((4,4),f'{s} {i+1}/{len(fs)}',fill=(255,0,0))
        tiles.append(bg)
w,h=tiles[0].size; cols=per*2 if len(tiles)>per*3 else per
rows=(len(tiles)+cols-1)//cols
g=Image.new('RGB',(w*cols,h*rows),(0,0,0))
for k,t in enumerate(tiles): g.paste(t,((k%cols)*w,(k//cols)*h))
g.save(out)
