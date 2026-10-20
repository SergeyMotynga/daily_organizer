from pathlib import Path
import json,hashlib,re
from PIL import Image
root=Path(__file__).parent
catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
expected=[f"{s['id']}-{theme}.jpg" for s in catalog for theme in ('light','dark')]
actual=[p.name for p in (root/'exports').glob('*.jpg')]
assert set(actual)==set(expected),(len(actual),len(expected))
allowed=set(expected)
allowed={'exports/'+name for name in allowed}
allowed.update(['AUDIT.md','catalog.json','component-checks.json','DESIGN.md','geometry.json','index.html','manifest.json','mockup.css','mockup.html','mockup.js','README.md','tokens.json','VERIFICATION.md','verify.py'])
allowed.update('references/'+name for name in ['today-light.png','today-dark.png','logo-light.svg','logo-dark.svg','logo-with-name-light.svg','logo-with-name-dark.svg'])
inventory={str(p.relative_to(root)).replace('\\','/') for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert inventory==allowed, {'unexpected':sorted(inventory-allowed),'missing':sorted(allowed-inventory)}
files=[]
for name in expected:
    p=root/'exports'/name
    with Image.open(p) as im:
        assert im.size==(1920,1080),(name,im.size)
        im.verify()
    files.append({'file':'exports/'+name,'width':1920,'height':1080,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
geometry=json.loads((root/'geometry.json').read_text(encoding='utf-8'))
assert len(geometry)==36
assert all(not x['out'] and not x['overflow'] for x in geometry)
revision=json.loads((root/'component-checks.json').read_text(encoding='utf-8'))
assert len(revision['controls'])==4
assert all(button['height']==50 and button['y']==177 for screen in revision['controls'] for button in screen['buttons'])
panel_geometry=revision['panels'][0]['geometry']
assert all(panel['geometry']==panel_geometry for panel in revision['panels'])
pairs=[]
for page in catalog:
    a=next(x for x in geometry if x['screen']==page['id'] and x['theme']=='light')
    b=next(x for x in geometry if x['screen']==page['id'] and x['theme']=='dark')
    assert a['texts']==b['texts'],page['id']
    pairs.append({'screen':page['id'],'equal':True,'textCount':len(a['texts'])})
def lum(c):
    vals=[int(c[i:i+2],16)/255 for i in (1,3,5)]
    vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]
    return sum(a*b for a,b in zip(vals,[.2126,.7152,.0722]))
def contrast(a,b):
    x,y=sorted([lum(a),lum(b)])
    return (y+.05)/(x+.05)
palettes={
'light':{'bg':'#f7f6f2','surface':'#fdfdfc','selected':'#e8efe6','ink':'#101b23','muted':'#59626a','accent':'#18593f','on-accent':'#ffffff','orange':'#a95000','red':'#bb3036'},
'dark':{'bg':'#1c211f','surface':'#242a27','selected':'#303d31','ink':'#f3f5ef','muted':'#bdc6bf','accent':'#d4ed86','on-accent':'#131a0e','orange':'#ffb141','red':'#ff7d7f'}}
checks=[]
for theme,p in palettes.items():
    for fg,bg in [('ink','bg'),('ink','surface'),('ink','selected'),('muted','surface'),('accent','surface'),('on-accent','accent'),('orange','surface'),('red','surface')]:
        ratio=contrast(p[fg],p[bg])
        assert ratio>=4.5,(theme,fg,bg,ratio)
        checks.append({'theme':theme,'foreground':fg,'background':bg,'ratio':round(ratio,2)})
for required in ['index.html','mockup.html','mockup.css','mockup.js','references/logo-light.svg','references/logo-dark.svg','references/today-light.png','references/today-dark.png','AUDIT.md','README.md','VERIFICATION.md']:
    assert (root/required).is_file(),required
manifest={'status':'approved-for-implementation','approvedOn':'2026-10-20','dimensions':[1920,1080],'screens':18,'exports':36,'themePairs':pairs,'selectedContrastChecks':checks,'geometryScope':'visible content; table rows intentionally clipped by scroll container','files':files}
stored=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
assert stored==manifest, 'Manifest does not match approved exports or measurements'

print(json.dumps({'exports':36,'dimensions':[1920,1080],'matchingPairs':len(pairs),'unexpectedOverflow':0,'selectedContrastChecks':len(checks),'minimumContrast':min(c['ratio'] for c in checks),'totalBytes':sum(f['bytes'] for f in files)},ensure_ascii=False))



from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from xml.etree import ElementTree
class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links += [v for k,v in attrs if k in ('src','href') and v]
checked_links=0
for path in list(root.glob('*.html'))+list(root.glob('*.md')):
    text=path.read_text(encoding='utf-8')
    if path.suffix=='.html':
        parser=LinkCollector(); parser.feed(text); links=parser.links
    else:
        links=re.findall(r'!?\[[^\]]*\]\(([^)\s]+)\)',text)
    for link in links:
        url=urlsplit(link)
        if url.scheme or url.netloc or not url.path: continue
        if '${' in url.path: continue
        dest=(path.parent/unquote(url.path)).resolve()
        assert dest.is_relative_to(root.resolve()),(path.name,link)
        assert dest.exists(),(path.name,link)
        checked_links+=1
for svg in (root/'references').glob('*.svg'):
    ElementTree.parse(svg)
index=(root/'index.html').read_text(encoding='utf-8')
embedded=json.loads(re.search(r'const catalog=(\[.*?\]);',index).group(1))
assert embedded==catalog,'Gallery catalog differs'
css=(root/'mockup.css').read_text(encoding='utf-8')
tokens=json.loads((root/'tokens.json').read_text(encoding='utf-8'))
for theme,pattern in [('light',r':root\{([^}]+)\}'),('dark',r':root\[data-theme=dark\]\{([^}]+)\}')]:
    values=dict(re.findall(r'--([\w-]+):([^;]+)',re.search(pattern,css).group(1)))
    assert tokens['themes'][theme]==values,(theme,'CSS tokens differ')
for path in root.rglob('*'):
    if path.suffix in ('.md','.html','.js','.css','.json'):
        text=path.read_text(encoding='utf-8')
        assert not re.search(r'C:[/\\]Users[/\\]|127\.0\.0\.1:8867',text),path
print(json.dumps({'localLinks':checked_links,'svg':len(list((root/'references').glob('*.svg'))),'catalog':'matched','cssTokens':'matched'},ensure_ascii=False))
