"""Convert the supplied headshot to ASCII. Requires Pillow; crop is specific to this photo."""
from PIL import Image, ImageOps
from pathlib import Path
import json, hashlib, argparse

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("headshot", type=Path)
args = parser.parse_args()
source=args.headshot
im=ImageOps.exif_transpose(Image.open(source)).convert('RGB').crop((100,45,600,660))
w,h=68,56
im=im.resize((w,h), Image.Resampling.LANCZOS)
# Silhouette bounds in original photo: exclude the studio backdrop.
outline=[(340,65),(410,67),(470,90),(510,135),(529,210),(520,280),(504,335),(485,389),(468,451),(474,514),(535,548),(599,582),(650,638),(670,766),(0,766),(0,687),(77,630),(161,577),(225,539),(249,483),(222,431),(204,372),(195,314),(181,269),(180,215),(191,163),(221,113),(271,82)]
from PIL import ImageDraw
mask=Image.new('L',(672,766));ImageDraw.Draw(mask).polygon(outline,fill=255)
mask=mask.crop((100,45,600,660)).resize((w,h))
ramp=' .,:;irsXA253hMHGS#9B&@'
lines=[];colors=[]
for y in range(h):
 line='';row=[]
 for x in range(w):
  rgb=im.getpixel((x,y));lum=sum(c*k for c,k in zip(rgb,(.2126,.7152,.0722)))
  char=ramp[round((1-lum/255)*(len(ramp)-1))] if mask.getpixel((x,y))>128 else ' '
  line+=char;row.append('#%02x%02x%02x'%rgb)
 lines.append(line);colors.append(row)
(ROOT / 'assets/portrait.txt').write_text('\n'.join(lines)+'\n')
(ROOT / 'assets/portrait.json').write_text(json.dumps({'columns':w,'rows':h,'source':'User-provided Headshot.jpeg','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'crop':[100,45,600,660],'colors':colors},indent=2)+'\n')
