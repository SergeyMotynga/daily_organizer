from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
B=Path(__file__).resolve().parent/'staging';B.mkdir(exist_ok=True);R=Path(__file__).resolve().parent.parent
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
def sheet(ids,themes,filename,cols=3,tw=480,th=350):
 total=len(ids)*len(themes);out=Image.new('RGB',(cols*tw,math.ceil(total/cols)*(th+45)),'#E7E9E7');d=ImageDraw.Draw(out)
 for i,(sid,theme) in enumerate((s,t) for s in ids for t in themes):
  im=Image.open(R/'renders'/f'{sid}-{theme}.png').convert('RGB');im.thumbnail((tw-18,th-12));x=i%cols*tw+9;y=i//cols*(th+45)+9;out.paste(im,(x,y));d.text((x,y+th),sid+' · '+theme,font=font,fill='#101820')
 out.save(filename,optimize=True)
ids=[s['id'] for s in json.loads((R/'manifest.json').read_text(encoding='utf-8'))['screens']]
for theme in ['light','dark']:
 sheet(ids,[theme],B/f'qa-contact-{theme}.png',4,440,310)
 sheet([s+'-mobile' for s in ids],[theme],B/f'qa-contact-mobile-{theme}.png',6,230,620)
sheet(['today','planning','calendar-month','projects','project-board','task-create'],['light','dark'],R/'contact-sheet.png')
sheet(['today-mobile','planning-mobile','calendar-month-mobile','project-board-mobile','task-create-mobile','login-mobile'],['light','dark'],R/'mobile-contact-sheet.png',6,230,620)
out=Image.new('RGB',(1616,550),'#E7E9E7');d=ImageDraw.Draw(out)
for i,(file,label) in enumerate([('references/approved-today-light.png','Утверждённый эталон'),('renders/today-light.png','Векторное восстановление')]):
 im=Image.open(R/file).convert('RGB');im.thumbnail((793,496));x=10+i*808;out.paste(im,(x,42));d.text((x,12),label,font=font,fill='#101820')
out.save(R/'comparison-today.png',optimize=True)
print('Created reference comparison and all overview sheets')
