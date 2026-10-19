"""Проверяет статические артефакты. Не запускает и не тестирует приложение."""
from pathlib import Path
import hashlib, json, re, sys, xml.etree.ElementTree as ET
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

ROOT=Path(__file__).resolve().parent.parent
NS={'s':'http://www.w3.org/2000/svg'}
errors=[];overlaps=[];bounds=[];links=0;labels=0
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
assert len(manifest['screens'])==39 and len(manifest['renders'])==156
for item in manifest['renders']:
 name=item['screen']+('-mobile' if item['mobile'] else '')+'-'+item['theme']
 p=ROOT/'renders'/f'{name}.svg';svg=p.read_text(encoding='utf-8');root=ET.fromstring(svg)
 if '<image' in svg or '<text' in svg or '@font-face' in svg:errors.append([name,'external-font-or-raster'])
 ids={e.attrib['id'] for e in root.iter() if 'id' in e.attrib}
 for e in root.findall('.//s:use',NS):
  target=e.attrib.get('{http://www.w3.org/1999/xlink}href','').lstrip('#')
  if target not in ids:errors.append([name,'missing-outline',target])
 for e in root.findall('.//s:path',NS):
  if not re.match(r'^[Mm]',e.attrib.get('d','')) or 'System.' in e.attrib.get('d',''):errors.append([name,'invalid-path'])
 for ext in ['svg','png']:
  digest=hashlib.sha256((ROOT/'renders'/f'{name}.{ext}').read_bytes()).hexdigest()
  if digest!=item[ext+'Sha256']:errors.append([name,'hash',ext])
 with Image.open(ROOT/'renders'/f'{name}.png') as im:
  if im.size!=(item['width'],item['height']):errors.append([name,'png-size'])
  im.verify()
 if (int(root.attrib['width']),int(root.attrib['height']))!=(item['width'],item['height']):errors.append([name,'svg-size'])
 elements=list(root);start=0
 for i,e in enumerate(elements):
  if e.attrib.get('data-overlay')=='true':start=i
 visible=[];horizontal=item['mobile'] and item['screen'] in ['project-board','project-empty','calendar-week']
 for e in (node for container in elements[start:] for node in container.iter()):
  a=e.attrib
  if 'data-text' not in a:continue
  x,y,tw,s=(float(a[k]) for k in ['data-x','data-y','data-width','data-font-size']);labels+=1
  if horizontal and x>=item['width']:continue
  if x<0 or y<0 or y+s>item['height']-5 or (x+tw>item['width']-4 and not horizontal):bounds.append([name,a['data-text'],x,y,tw,s])
  visible.append((a['data-text'],x,y,tw,s*.9))
 for i,a in enumerate(visible):
  for b in visible[i+1:]:
   dx=min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]);dy=min(a[2]+a[4],b[2]+b[4])-max(a[2],b[2])
   if dx>3 and dy>3:overlaps.append([name,a[0],b[0],round(dx,2),round(dy,2)])
for p in (ROOT/'assets').glob('*.svg'):
 svg=p.read_text(encoding='utf-8');root=ET.fromstring(svg)
 if '<image' in svg or '<text' in svg:errors.append([p.name,'non-vector-logo'])
 for e in root.findall('.//s:path',NS):
  if not re.match(r'^[Mm]',e.attrib.get('d','')):errors.append([p.name,'invalid-logo-path'])
for p in [ROOT/'mockups.html',ROOT/'comparison.html']:
 for url in re.findall(r'(?:href|src)="([^"#]+)"',p.read_text(encoding='utf-8')):
  if not url.startswith(('https:','http:')) and not (p.parent/url).exists():errors.append([p.name,'link',url])
  links+=1
for p in ROOT.glob('*.md'):
 for url in re.findall(r'\]\(([^\s)]+)\)',p.read_text(encoding='utf-8')):
  if not url.startswith(('https:','http:','#')) and not (p.parent/url.split('#')[0]).exists():errors.append([p.name,'markdown-link',url])
tokens=json.loads((ROOT/'tokens.json').read_text(encoding='utf-8'))
for ref in re.findall(r'\{(primitive\.[^}]+)\}',json.dumps(tokens)):
 value=tokens
 for key in ref.split('.'):
  if key not in value:errors.append(['token',ref]);break
  value=value[key]
def contrast(a,b):
 def luminance(s):
  v=[int(s[i:i+2],16)/255 for i in [1,3,5]];v=[n/12.92 if n<=.04045 else ((n+.055)/1.055)**2.4 for n in v]
  return .2126*v[0]+.7152*v[1]+.0722*v[2]
 lo,hi=sorted([luminance(a),luminance(b)]);return round((hi+.05)/(lo+.05),2)
p=tokens['primitive'];contrast_results=[]
for theme,text,surface in [('light','ink','creamSurface'),('light','grayText','creamSurface'),('light','white','forest'),('light','amberText','amberSurface'),('light','coralText','coralSurface'),('dark','lightText','graphiteSurface'),('dark','grayText','graphiteSurface'),('dark','darkOnLime','lime'),('dark','amberText','amberSurface'),('dark','coralText','coralSurface')]:
 ratio=contrast(p[theme][text],p[theme][surface]);contrast_results.append(dict(theme=theme,text=text,surface=surface,ratio=ratio,atLeast4_5=ratio>=4.5))
today=ET.parse(ROOT/'renders/today-light.svg').getroot();rectangles=today.findall('s:rect',NS)
for x,y,w,h in [(22,145,1116,831),(1150,145,420,831),(34,367,1092,232)]:
 if not any(all(abs(float(r.attrib.get(k,-1))-n)<.1 for k,n in zip(['x','y','width','height'],[x,y,w,h])) for r in rectangles):errors.append(['today','reference-anchor',x,y,w,h])
report=dict(screens=len(manifest['screens']),renders=len(manifest['renders']),svg=165,png=156,localHtmlLinks=links,visibleLabels=labels,errors=errors,bounds=bounds,overlaps=overlaps,contrast=contrast_results,limitations=['Проверка прямоугольников текста не доказывает отсутствие любых визуальных дефектов.','Фон за открытой формой/поповером проверяется отдельно на основном экране.','Частично видимые соседние колонки доски и недели на mobile разрешены.','Оранжевый текст из выбранной палитры не достигает 4.5:1; см. VERIFICATION.md.','Проверка браузерного отображения альбома инструментом не выполнялась.'])
(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(bool(errors or bounds or overlaps))
