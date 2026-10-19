"""Рисует автономные SVG-макеты и их PNG-превью. Не обращается к приложению."""
import json, math, re, html, shutil, sys, hashlib, argparse, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent.parent
STAGE=Path(__file__).resolve().parent/'staging'
STAGE.mkdir(exist_ok=True)
TEXTS={}
WRITTEN=[]
OUT=ROOT/'renders';OUT.mkdir(parents=True,exist_ok=True)
FONTS=Path('C:/Windows/Fonts')
LIGHT=dict(bg='#F7F6F3',surface='#FDFCFA',context='#F3F3EB',fg='#101820',muted='#555D63',line='#E7E9E7',accent='#194F3A',accentTop='#2C7057',on='#FFFFFF',sel='#E9EFE7',selEnd='#EDF2E9',warn='#E46600',warnbg='#FFF1DF',danger='#CF2424',dangerbg='#FCEAE7')
DARK=dict(bg='#1C1F1F',surface='#242728',context='#242927',fg='#F1F2ED',muted='#AFB6B2',line='#3E4942',accent='#CFEA83',on='#1B2619',sel='#2D3731',selEnd='#29352F',accentTop='#DFEFAD',warn='#F6BF6D',warnbg='#3C3426',danger='#FF9A90',dangerbg='#402E2C')
LIGHT['control']='#7D8387';DARK['control']='#78867B'
LIGHT['faint']='#939A9F';DARK['faint']='#89938E'
SCREENS=[('today','Сегодня','План дня и раскрытая задача','Основные'),('today-empty','Сегодня · пусто','Первый день без задач','Основные'),('planning','Задачи','Даты, статусы и сортировки','Основные'),('planning-filter','Фильтр по периоду','Диапазон дат и быстрые фильтры','Основные'),('planning-empty','Поиск · пусто','Нет совпадений и сброс фильтров','Основные'),('calendar-week','Календарь · неделя','План, дедлайны и повторения','Основные'),('calendar-month','Календарь · месяц','Обзор месяца и выбранный день','Основные'),('archive','Архив','Восстановление и удаление','Основные'),('archive-empty','Архив · пусто','Нет архивированных задач','Основные'),('archive-confirm','Архив · удаление','Подтверждение удаления','Основные'),('projects','Проекты','Прогресс, поиск и сортировка','Проекты'),('projects-archived','Архивные проекты','Восстановление проекта','Проекты'),('projects-empty','Проекты · пусто','Создание первого проекта','Проекты'),('project-board','Доска проекта','Этапы и карточки задач','Проекты'),('project-list','Список проекта','Таблица и пагинация','Проекты'),('project-bulk','Массовые действия','Перемещение и выполнение','Проекты'),('project-empty','Пустая доска','Добавление и перемещение','Проекты'),('project-create','Создание проекта','Описание и стандартные этапы','Проекты'),('project-settings','Настройки проекта','Порядок и завершающий этап','Проекты'),('project-settings-confirm','Удаление проекта','Задачи остаются без проекта','Проекты'),('task-create','Создание задачи','Независимые план и дедлайн','Формы задач'),('task-edit','Редактирование задачи','Сохранение и удаление','Формы задач'),('task-details','Детали задачи','Свойства, история и действия','Формы задач'),('task-recurring','Повторяющаяся задача','Интервал, начало и окончание','Формы задач'),('task-occurrence','Детали повторения','Выполнение на конкретную дату','Формы задач'),('task-delete','Удаление задачи','Подтверждение и отмена','Формы задач'),('login','Вход','Логин, пароль и сессия','Авторизация'),('login-error','Ошибка входа','Повторная попытка входа','Авторизация'),('register','Регистрация','Имя, логин и пароль','Авторизация'),('register-error','Ошибки регистрации','Ошибки рядом с полями','Авторизация'),('register-success','Аккаунт создан','Переход ко входу','Авторизация'),('states','Состояния интерфейса','Загрузка, ошибка и сохранение','Система'),('components','Компоненты и палитра','Размеры, фокус и семантика','Система'),('logo','Логотип Маршрут','Знак и версия с названием','Система')]
TASKS=[('09:30','Читать 20 минут','Личное · Каждый день'),('10:00','Собрать референсы интерфейса','Обновление интерфейса · В работе'),('14:00','Подготовить спецификацию компонентов','Обновление интерфейса · В работе'),('18:30','Разобрать рабочую почту','Личное · По будням'),('','Сверить существующие сценарии','Обновление интерфейса · К выполнению'),('','Обновить документацию','Обновление интерфейса · Подготовка')]
ROWS=[('Обновить документацию','Активная','Сегодня','18 окт · просрочено','Подготовка'),('Спецификация компонентов','Активная','Сегодня, 14:00','Сегодня, 18:00','В работе'),('Собрать референсы интерфейса','Активная','Сегодня, 10:00','20 окт','В работе'),('Утренний обзор задач','Повторяется','Сегодня, 09:00','—','Бэклог'),('Купить продукты по списку','Активная','Без даты','—','—'),('Еженедельный обзор проекта','Повторяется','20 окт','—','Бэклог'),('Проверить контраст текста','Выполненная','20 окт','—','Готово'),('Зафиксировать палитру','Выполненная','Сегодня','—','Готово')]
COLS=['Бэклог','К выполнению','В работе','На проверке','Готово']
SCREENS += [('task-recurrence-options','Варианты повторения','Каждый день, по будням и раз в N недель','Формы задач'),('task-no-project','Задача без проекта','Отключённый выбор этапа','Формы задач'),('task-invalid','Ошибка формы задачи','Название и предупреждение о датах','Формы задач'),('project-column-edit','Редактирование колонки','Переименование, порядок и завершение','Проекты'),('controls','Меню и фильтры','Все варианты списков и календаря','Система')]

class Drawing:
 def __init__(self,w,h,c,title):
  self.w,self.h,self.c=w,h,c;self.mobile=w<600;self.exact=False;self.fonts={};self.bounds=[]
  self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{html.escape(title)}</title><defs><linearGradient id="button" x2="0" y2="1"><stop stop-color="{c["accentTop"]}"/><stop offset="1" stop-color="{c["accent"]}"/></linearGradient><linearGradient id="selection" x2="1" y2="1"><stop stop-color="{c["sel"]}"/><stop offset="1" stop-color="{c["selEnd"]}"/></linearGradient></defs><rect width="100%" height="100%" fill="{c["bg"]}"/>']
 def color(self,c):return self.c.get(c,c)
 def size(self,s):
  if self.exact:return s
  if self.mobile:return {10:11,11:12,12:13,13:14}.get(s,s)
  return {10:12,11:14,12:15,13:16,14:18,15:18,16:20,17:20,18:22,19:24,20:24,21:26,22:28,23:28,25:30,26:30,28:34,29:34,30:36,31:36,32:36}.get(s,s)
 def font(self,size=15,bold=False):
  size=self.size(size);key=(size,bold)
  if key not in self.fonts:self.fonts[key]=ImageFont.truetype(str(FONTS/('arialbd.ttf' if bold else 'arial.ttf')),size)
  return self.fonts[key]
 def rect(self,x,y,w,h,fill='surface',r=0,stroke=None):
  assert w>=0 and h>=0,(x,y,w,h)
  fill='url(#button)' if fill=='accent' else 'url(#selection)' if fill=='sel' else self.color(fill)
  self.parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r}" fill="{fill}"'+(f' stroke="{self.color(stroke)}"' if stroke else '')+'/>')
 def line(self,x1,y1,x2,y2,c='line',width=1):
  self.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{self.color(c)}" stroke-width="{width}" stroke-linecap="round"/>')
 def circle(self,x,y,r,fill=None,stroke='muted',width=1):
  self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{self.color(fill) if fill else "none"}" stroke="{self.color(stroke) if stroke else "none"}" stroke-width="{width}"/>')
 def text(self,x,y,t,size=15,bold=False,c='fg',maxw=None,lines=5,align='left'):
  t=str(t);font=self.font(size,bold);s=self.size(size);out=[]
  if t.startswith('↻'):
   self.icon(x,y-1,'repeat',c,s+2);x+=s+7;t=t.removeprefix('↻').lstrip()
   if maxw:maxw-=s+7
  for para in t.split('\n'):
   if not maxw:out.append(para);continue
   line=''
   for word in para.split(' '):
    candidate=(line+' '+word).strip()
    if font.getlength(candidate)>maxw and line:out.append(line);line=word
    else:line=candidate
   out.append(line)
  if len(out)>lines:
   out=out[:lines];out[-1]=out[-1].rstrip()+'…'
   if maxw:
    while font.getlength(out[-1])>maxw and len(out[-1])>1:out[-1]=out[-1][:-2]+'…'
  for i,line in enumerate(out):
   if not line:continue
   tw=font.getlength(line);xx=x-tw/2 if align=='center' else x-tw if align=='right' else x;yy=y+i*s*1.4
   key=hashlib.sha256(f'{s}|{bold}|{line}'.encode()).hexdigest()[:20]
   TEXTS[key]=dict(text=line,size=s,bold=bold)
   self.parts.append(f'<g data-text="{html.escape(line,quote=True)}" data-font-size="{s}" data-x="{xx:.3f}" data-y="{yy:.3f}" data-width="{tw:.3f}" fill="{self.color(c)}"><use xlink:href="#t{key}" transform="translate({xx:.3f} {yy:.3f})"/></g>')
   self.bounds.append(dict(text=line,x=round(xx,2),y=round(yy,2),width=round(tw,2),height=s,clip=maxw))
  return len(out)*s*1.4
 def logo(self,x,y,s=32,c='accent'):
  col=self.color(c);self.parts.append(f'<g transform="translate({x} {y}) scale({s/100})" fill="none" stroke="{col}" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10H82Q92 10 92 20V82Q92 92 82 92H18Q8 92 8 82V61"/><path d="M39 35H64Q68 35 68 39V61"/></g>');self.circle(x+50*s/100,y+61*s/100,6.5*s/100,c,None)
 def button(self,x,y,label,w=None,style='outline',ic=None,h=38,size=14):
  s=self.size(size);minw=self.font(size).getlength(label)+26+(25 if ic else 0);w=w or minw
  # Явно заданные размеры сохраняются; подпись переносить внутри кнопки нельзя.
  if minw>w and label:
   while s>11 and self.font(size).getlength(label)+26+(25 if ic else 0)>w:size-=1;s=self.size(size)
  fill='accent' if style=='primary' else 'sel' if style=='selected' else 'dangerbg' if style=='danger' else 'surface' if style=='outline' else 'bg';fg='on' if style=='primary' else 'accent' if style=='selected' else 'danger' if style=='danger' else 'fg' if style=='outline' else 'muted'
  self.rect(x,y,w,h,fill,10,'line' if style=='outline' else None);xx=x+13
  if ic:self.icon(xx,y+(h-20)/2,ic,fg,20);xx+=25
  self.text(xx,y+(h-s)/2,label,size,False,fg);return w
 def pill(self,x,y,t,style='normal',size=12):
  s=self.size(size);w=self.font(size).getlength(t)+18;hh=max(26,s+12);bg='sel' if style=='selected' else 'warnbg' if style=='warn' else 'dangerbg' if style=='danger' else 'context';fg='accent' if style=='selected' else 'warn' if style=='warn' else 'danger' if style=='danger' else 'muted';self.rect(x,y,w,hh,bg,7);self.text(x+9,y+6,t,size,False,fg);return w
 def check(self,x,y,done=False,square=False):
  r=11 if self.mobile else 13
  if square:self.rect(x-r+2,y-r+2,2*r-4,2*r-4,'sel' if done else 'surface',4,'accent' if done else 'muted')
  else:self.circle(x,y,r,'sel' if done else None,'accent' if done else 'control',2)
  if done:self.icon(x-9,y-9,'check','accent',18)
 def save(self,name):
  (STAGE/(name+'.svg')).write_text(''.join(self.parts)+'</svg>',encoding='utf-8')
  (STAGE/(name+'.layout.json')).write_text(json.dumps(self.bounds,ensure_ascii=False),encoding='utf-8')
  WRITTEN.append(STAGE/(name+'.svg'))
 def shade(self,y):
  color='#000000' if self.c==DARK else '#18241E';alpha=.55 if self.c==DARK else .24
  self.parts.append(f'<rect x="0" y="{y}" width="{self.w}" height="{self.h-y}" fill="{color}" opacity="{alpha}" data-overlay="true"/>')
 def icon(self,x,y,name,c='muted',s=18):
  k=s/24
  def l(a,b):self.line(x+a[0]*k,y+a[1]*k,x+b[0]*k,y+b[1]*k,c,2 if s>20 else 1)
  if name in ['left','right','down','up']:
   a={'left':[(15,5),(8,12),(15,19)],'right':[(8,5),(15,12),(8,19)],'down':[(5,8),(12,15),(19,8)],'up':[(5,16),(12,9),(19,16)]}[name];l(a[0],a[1]);l(a[1],a[2])
  elif name=='plus':l((12,4),(12,20));l((4,12),(20,12))
  elif name=='close':l((6,6),(18,18));l((18,6),(6,18))
  elif name=='check':l((5,12),(10,17));l((10,17),(20,6))
  elif name=='more':
   for dx in [5,12,19]:self.circle(x+dx*k,y+12*k,1.1*k,c,None)
  elif name=='search':self.circle(x+10*k,y+10*k,6*k,None,c);l((15,15),(21,21))
  elif name=='clock':self.circle(x+12*k,y+12*k,9*k,None,c);l((12,6),(12,12));l((12,12),(16,15))
  elif name=='calendar':
   self.rect(x+3*k,y+5*k,18*k,16*k,'surface',3,c);l((3,10),(21,10));l((8,2),(8,7));l((16,2),(16,7))
  elif name=='folder':
   for a,b in [((3,8),(3,20)),((3,20),(21,20)),((21,20),(21,8)),((21,8),(11,8)),((11,8),(8,5)),((8,5),(3,5)),((3,5),(3,8))]:l(a,b)
  elif name=='archive':self.rect(x+3*k,y+4*k,18*k,5*k,'surface',1,c);self.rect(x+5*k,y+9*k,14*k,12*k,'surface',2,c);l((10,13),(14,13))
  elif name=='repeat':
   for a,b in [((3,11),(3,6)),((3,6),(20,6)),((20,6),(16,2)),((20,6),(16,10)),((21,13),(21,18)),((21,18),(4,18)),((4,18),(8,14)),((4,18),(8,22))]:l(a,b)
  elif name=='trash':
   for a,b in [((4,6),(20,6)),((8,6),(8,3)),((8,3),(16,3)),((16,3),(16,6)),((6,6),(7,21)),((7,21),(17,21)),((17,21),(18,6)),((10,10),(10,17)),((14,10),(14,17))]:l(a,b)
  elif name=='edit':
   for a,b in [((4,20),(5,15)),((5,15),(17,3)),((17,3),(21,7)),((21,7),(9,19)),((9,19),(4,20)),((14,6),(18,10))]:l(a,b)
  elif name=='sun':
   self.circle(x+12*k,y+12*k,5*k,None,c)
   for a in range(8):
    ang=a*math.pi/4;l((12+8*math.cos(ang),12+8*math.sin(ang)),(12+11*math.cos(ang),12+11*math.sin(ang)))
  elif name=='grip':
   for yy in [5,12,19]:
    for xx in [9,15]:self.circle(x+xx*k,y+yy*k,1,c,None)
  elif name=='alert':
   for a,b in [((12,3),(2,21)),((2,21),(22,21)),((22,21),(12,3)),((12,9),(12,14))]:l(a,b)
   self.circle(x+12*k,y+17*k,1,c,None)
  elif name=='eye':self.circle(x+12*k,y+12*k,8*k,None,c);self.circle(x+12*k,y+12*k,3*k,None,c)
  else:self.circle(x+12*k,y+12*k,8*k,None,c)

def header(d,active='Сегодня',mobile=False):
 prev=d.exact;d.exact=True;h=110 if mobile else 64
 d.line(0,h,d.w,h);d.logo(18 if mobile else 42,17 if mobile else 14,33 if mobile else 35);d.text(63 if mobile else 91,24,'Daily Organizer',18 if mobile else 20,True)
 nav=['Сегодня','Задачи','Календарь','Проекты','Архив'];widths=[116,106,136,126,102] if not mobile else [76,67,91,78,62];xx=12 if mobile else (d.w-sum(widths))/2
 for t,w in zip(nav,widths):
  yy=66 if mobile else 5;hh=39 if mobile else 53
  if active==t:d.rect(xx,yy,w,hh,'sel',11);d.line(xx+9,yy+hh,xx+w-9,yy+hh,'accent',2)
  d.text(xx+w/2,yy+(13 if mobile else 18),t,13 if mobile else 18,active==t,'accent' if active==t else 'muted',align='center');xx+=w
 ax=d.w-69 if mobile else d.w-114;d.circle(ax,32,19,'sel',None);d.text(ax,25,'A',16,False,align='center')
 gx=d.w-37 if mobile else d.w-63;gy=31
 # Контур шестерёнки — выбранный в эталоне вход в настройки.
 d.parts.append(f'<g transform="translate({gx-13} {gy-13})" fill="none" stroke="{d.color("muted")}" stroke-width="2.2" stroke-linejoin="round"><path d="M10 1h6l1 4 3 2 4-1 3 5-3 3v3l3 3-3 5-4-1-3 2-1 4h-6l-1-4-3-2-4 1-3-5 3-3v-3l-3-3 3-5 4 1 3-2z" transform="scale(.85)"/><circle cx="11" cy="13" r="4"/></g>')
 d.exact=prev;return h

def toolbar(d,title,sub='',mobile=False,new='Новая задача'):
 prev=d.exact;d.exact=True;x=16 if mobile else 34;y=132 if mobile else 92
 d.text(x,y,title,28 if mobile else 36,True,maxw=250 if mobile else 1020,lines=2)
 if sub:d.text(x,y+(43 if mobile else 47),sub,13 if mobile else 16,False,'muted',maxw=d.w-32 if mobile else 1100,lines=2)
 if not mobile:d.button(d.w-217,81,new,191,'primary','plus',46,20)
 elif title not in ['Обновление интерфейса','Состояния','Компоненты','Маршрут']:d.button(d.w-109,126,'Проект' if new=='Новый проект' else 'Задача',93,'primary','plus',42,13)
 d.exact=prev;return 215 if mobile and sub else 191 if mobile else 180 if sub else 145

def mini(d,x,y,w,range_=False):
 prev=d.exact;d.exact=True;large=w>330;fs=24 if large else 19;row=46 if large else 34
 d.text(x,y,'Октябрь 2026',fs,True);d.icon(x+w-65,y+2,'left',s=21);d.icon(x+w-25,y+2,'right',s=21);cw=w/7
 for i,t in enumerate(['Пн','Вт','Ср','Чт','Пт','Сб','Вс']):d.text(x+cw*(i+.5)-(13 if large else 0),y+(53 if large else 43),t,14 if large else 12,False,'muted',align='center')
 for i in range(35):
  n=28+i if i<3 else i-2;yy=y+(97 if large else 76)+(i//7)*row;xx=x+cw*(i%7+.5)-(13 if large else 0)
  if n==19 and i>3:d.circle(xx,yy+7,22 if large else 16,'accent',None)
  elif range_ and 19<n<25:d.rect(xx-cw/2,yy-8,cw,30,'sel',2)
  d.text(xx,yy,str(n if n<=31 else n-31),16 if large else 13,False,'on' if n==19 else 'faint' if i<3 or n>31 else 'fg',align='center')
 d.exact=prev

def empty(d,x,y,w,h,title,desc,action='',ic='calendar'):
 d.rect(x,y,w,h,'surface',16,'line');cx=x+w/2;d.rect(cx-29,y+78,58,58,'sel',20);d.icon(cx-13,y+94,ic,'accent',26);th=d.text(cx,y+160,title,21,True,maxw=w-40,align='center');dy=y+160+th+16;dh=d.text(cx,dy,desc,14,False,'muted',maxw=min(350,w-36),align='center')
 if action:d.button(cx-87,dy+dh+25,action,174,'primary','plus')
def smalltask(d,x,y,t,w,date=None):
 d.check(x+10,y+10);d.text(x+32,y,t,14,False,maxw=w-32-(60 if date else 0),lines=2)
 if date:d.text(x+w,y,date,12,False,'warn',align='right')
def today(d,m=False,isempty=False):
 header(d,'Сегодня',m);prev=d.exact;d.exact=True
 if m:
  y=toolbar(d,'Сегодня','Пн, 19 октября',True);x=14;lw=d.w-28;rh=0
 else:
  y=145;x=22;lw=d.w-470;d.text(34,92,'Сегодня',36,True)
  for xx,ic in [(203,'left'),(253,'right')]:d.button(xx,83,'',42,h=44);d.icon(xx+12,95,ic,'fg',20)
  d.text(320,100,'Пн, 19 октября',18);d.text(d.w-240,102,'6 в плане  ·  2 выполнены',16,False,'muted',align='right');d.button(d.w-217,81,'Новая задача',191,'primary','plus',46,20)
 if isempty:
  empty(d,x,y,lw,590 if m else 831,'На сегодня всё спокойно','Добавьте задачу или выберите дату для дел из входящих.','Новая задача');end=y+(620 if m else 831)
 else:
  ph=1040 if m else 831;d.rect(x,y,lw,ph,'surface',20,'line');d.text(x+29,y+28,'План на день',21 if m else 24,True);d.icon(x+(192 if m else 194),y+29,'down',s=17)
  if not m:
   d.icon(x+lw-377,y+26,'clock','warn',23);d.text(x+lw-341,y+33,'3 дедлайна сегодня',16,False,'warn');d.text(x+lw-181,y+33,'·',16,False,'muted');d.circle(x+lw-153,y+38,9,None,'danger',2);d.line(x+lw-153,y+31,x+lw-153,y+38,'danger',2);d.text(x+lw-130,y+33,'2 просрочено',16,False,'danger')
  else:d.text(x+20,y+65,'3 дедлайна  ·  2 просрочено',13,False,'warn')
  sep=y+(95 if m else 69);d.line(x+21,sep,x+lw-21,sep)
  entries=[('09:30','Читать 20 минут','Личное · Ежедневно'),('10:00','Подготовить структуру backend','Daily Organizer'),('14:00','Написать тесты авторизации','Daily Organizer'),('18:30','Английский 15 минут','Личное · По будням')]
  yy=sep+17
  for i,(time,title,meta) in enumerate(entries):
   selected=i==2;hh=(322 if m else 232) if selected else (99 if m else 67 if i==3 else 76)
   if selected:d.rect(x+12,yy-16,lw-24,hh,'sel',14)
   tx=x+52 if m else x+174;cy=yy+15;cx=x+26 if m else x+132
   if not m:d.text(x+30,yy+10,time,20,selected)
   else:d.text(tx,yy,time,13,False,'muted')
   d.circle(cx,cy+(12 if m else 0),13,None,'accent' if selected else 'control',2)
   ty=yy+(23 if m else 3 if selected else 8 if i==3 else 0);th=d.text(tx,ty,title,18 if m else 20,selected,maxw=lw-(tx-x)-(70 if m else 44),lines=2)
   metay=ty+(th+8 if m else 29);d.icon(tx,metay-3,'folder',s=18);d.text(tx+28,metay,meta,13 if m else 16,False,'muted');d.icon(x+lw-(39 if m else 60),yy+(20 if m else 8),'more',s=24)
   if m and not selected:hh=max(99,metay-yy+33)
   if selected:
    ex=x+20 if m else tx;ey=yy+(100 if m else 74);d.text(ex,ey,'Проверить вход, обновление сессии и выход.',16 if m else 18,maxw=lw-(ex-x)-30,lines=2)
    py=ey+(58 if m else 47)
    for j,(ic,label,dx) in enumerate([('calendar','План: 19 окт, 14:00',0),('clock','Дедлайн: 19 окт, 18:00',227),('repeat','Не повторяется',479)]):
     px=ex if m else ex+dx;ly=py+j*30 if m else py;d.icon(px,ly-3,ic,s=22);d.text(px+37,ly,label,14 if m else 16,False,'muted')
    fy=yy+(254 if m else 156);d.line(ex,fy,x+lw-32,fy);d.icon(ex,fy+20,'edit','accent',23);d.text(ex+37,fy+25,'Редактировать',15 if m else 16,False,'accent');d.icon(x+lw-(55 if m else 139),fy+20,'archive',s=24)
    if not m:d.text(x+lw-98,fy+25,'В архив',16,False,'muted');d.icon(x+lw-184,yy+3,'clock','warn',22);d.text(x+lw-151,yy+8,'до 18:00',16,False,'warn')
   elif i<2:d.line(x+21,yy+(hh-12 if m else 59),x+lw-21,yy+(hh-12 if m else 59))
   yy+=hh
  yy+=5 if m else 3;d.line(x+21,yy-5,x+lw-21,yy-5);d.text(x+29,yy+19,'Без времени · 2',18 if m else 20,True);yy+=61
  for title,meta in [('Обновить документацию','Daily Organizer'),('Разобрать входящие','Личное')]:
   d.circle(x+(26 if m else 61),yy+14,13,None,'control',2);tx=x+(52 if m else 108);d.text(tx,yy,title,17 if m else 20,maxw=lw-(tx-x)-(70 if m else 44),lines=2);d.icon(tx,yy+27,'folder',s=18);d.text(tx+28,yy+30,meta,13 if m else 16,False,'muted');d.icon(x+lw-(39 if m else 60),yy-3 if m else yy+4,'more',s=24);d.line(x+21,yy+51,x+lw-21,yy+51);yy+=66
  qy=yy-12;d.rect(x+21,qy,lw-42,52,'surface',11,'control');d.icon(x+46,qy+15,'plus',s=25);d.text(x+89,qy+19,'Что нужно сделать?',15 if m else 18,False,'faint');d.icon(x+28,qy+72,'right',s=18);d.text(x+56,qy+75,'Выполнено сегодня  ·  2',15 if m else 18,False,'muted');end=y+ph
 if m:rx=x;rw=lw;sy=end+16;d.rect(rx,sy,rw,785,'context',20,'line');mini(d,rx+26,sy+30,rw-52);by=sy+330
 else:rx=d.w-436;rw=420;sy=y;d.rect(rx,sy,rw,831,'context',20,'line');mini(d,rx+35,sy+33,rw-55);by=530
 d.line(rx+25,by,rx+rw-25,by);d.text(rx+27,by+33,'Входящие  ·  '+('0' if isempty else '12'),20,True)
 inbox=['Посмотреть идеи для главной','Разобрать сохранённые ссылки','Ответить на письмо']
 if isempty:d.text(rx+27,by+83,'Здесь появятся задачи без даты.',15,False,'muted',maxw=rw-50)
 else:
  for i,t in enumerate(inbox):
   yy=by+78+i*42;d.circle(rx+40,yy+7,12,None,'control',2);d.text(rx+75,yy,t,15 if m else 16,maxw=rw-96,lines=2)
  d.text(rx+27,by+207,'Все входящие  →',16,False,'accent')
 dy=by+250;d.line(rx+25,dy,rx+rw-25,dy);d.text(rx+27,dy+33,'Ближайшие дедлайны',20,True)
 if not isempty:
  for i,(t,date) in enumerate([('Рефакторинг сервиса задач','21 окт'),('Обновить README','23 окт')]):
   yy=dy+80+i*43;d.circle(rx+40,yy+5,12,None,'control',2);d.text(rx+75,yy,t,15 if m else 16,maxw=rw-150,lines=2);d.text(rx+rw-28,yy,date,16,False,'warn',align='right')
 d.exact=prev

def filters(d,y,m=False,project=False,archive=False):
 x=14 if m else 22;w=d.w-(2*x if m else x+16)
 if project:
  d.rect(x,y,172,36,'context',10);d.button(x+4,y+3,'Доска',78,'selected' if d.mode not in ['project-list','project-bulk'] else 'quiet',h=30,size=13);d.button(x+88,y+3,'Список',80,'selected' if d.mode in ['project-list','project-bulk'] else 'quiet',h=30,size=13);y+=48 if m else 0;xx=x if m else x+190
 else:xx=x
 sw=w if m else 530 if project else w-264 if archive else w-484
 d.rect(xx,y,sw,39,'surface',9,'line');d.icon(xx+12,y+11,'search');d.text(xx+41,y+11,'Поиск по проекту' if project else 'Поиск в архиве' if archive else 'Поиск по названию и описанию',13,False,'muted')
 if m:y+=50;xx=x
 else:xx=xx+sw+12
 if archive:d.button(xx,y,'Сначала новые задачи',230 if not m else 220,ic='down');return y+54
 if project:
  for t in ['Все даты','Все этапы','Все статусы']:xx+=d.button(xx,y,t,style='outline',ic='down',size=12 if m else 13)+8
 else:
  if not m:
   d.button(xx,y,'Дата',100,ic='calendar',size=13);d.button(xx+108,y,'Период',126,ic='calendar',size=13);d.button(xx+242,y,'По дедлайну',230,ic='down')
  else:d.button(x,y,'По дедлайну',141,ic='down',size=12);d.button(x+150,y,'Дата',84,ic='calendar',size=12);d.button(x+242,y,'Период',120,ic='calendar',size=12)
 return y+54
def table(d,x,y,w,m=False,project=False,bulk=False,archive=False):
 rs=[('Разобрать входящие записи','В архиве','19 окт','—',''),('Старые заметки по дизайну','В архиве','12 окт','15 окт',''),('Проверить мобильную навигацию','В архиве','10 окт','—','')] if archive else ROWS
 if project:rs=[('Обновить документацию','Активная','Сегодня','18 окт · просрочено','К выполнению'),ROWS[1],ROWS[2],('Согласовать пустые состояния','Активная','Без даты','—','Бэклог'),('Проверить мобильную навигацию','Активная','20 окт','—','К выполнению'),ROWS[5],ROWS[6],ROWS[7]]
 if bulk:
  d.rect(x,y,w,97 if m else 55,'sel',13);d.text(x+16,y+17,'Выбрано: 2',13,True,'accent')
  xx=x+15 if m else x+145;by=y+48 if m else y+9
  for t in ['В работе','Переместить','Выполнить']:xx+=d.button(xx,by,t,style='outline',h=31,size=11 if m else 13)+8
  y+=112 if m else 67
 if m:
  for i,r in enumerate(rs):
   h=151 if archive else 124;d.rect(x,y,w,h,'surface',13,'line');d.check(x+22,y+28,bulk and i<2,project);d.text(x+46,y+18,r[0],16,False,maxw=w-83,lines=2);d.icon(x+w-30,y+20,'more');d.pill(x+46,y+65,r[4] if project else r[1],'selected' if r[1]=='Выполненная' else 'normal',11);d.text(x+46,y+103,'План: '+r[2],12,False,'muted')
   if r[3]!='—':d.text(x+w-14,y+103,'Срок: '+r[3],11,False,'danger' if i==0 else 'warn',align='right')
   if archive:d.button(x+46,y+105,'Вернуть',102,ic='repeat',h=32,size=12);d.icon(x+w-42,y+111,'trash','danger')
   y+=h+10
  d.text(x,y+6,'Всего '+('в архиве: 3' if archive else 'задач: 8'),12,False,'muted');d.button(x+w-136,y,'20 на странице',136,h=31,size=11);return
 headers=['Задача','Когда была запланирована','Дедлайн','Архивировано','Действия'] if archive else ['Задача','Этап' if project else 'Статус','Когда делать','Дедлайн','Обновлено','']
 widths=[.30,.24,.12,.18,.16] if archive else [.33,.15,.16,.17,.15,.04];xs=[x]
 for f in widths[:-1]:xs.append(xs[-1]+w*f)
 d.rect(x,y,w,49+len(rs)*69+55,'surface',16,'line');d.rect(x+1,y+1,w-2,49,'context',15)
 for i,h in enumerate(headers):d.text(xs[i]+19,y+18,h,12,False,'muted')
 for i,r in enumerate(rs):
  yy=y+49+i*69
  if bulk and i<2:d.rect(x+1,yy,w-2,69,'sel')
  d.line(x+16,yy,x+w-16,yy);d.check(x+27,yy+29,bulk and i<2 if project else r[1]=='Выполненная',project);d.text(x+52,yy+16,r[0],14,False,maxw=w*.33-67,lines=1);d.text(x+52,yy+40,'В архиве' if archive else '↻ Каждый день' if i==3 and not project else 'Без проекта' if r[4]=='—' else 'Обновление интерфейса',11,False,'muted')
  if archive:
   vals=[r[2],r[3],'19 окт, 16:26']
   for j,t in enumerate(vals):d.text(xs[j+1]+18,yy+24,t,13,False,'muted' if j==2 else 'fg')
   d.button(xs[4]+12,yy+16,'Вернуть',101,ic='repeat',h=34,size=12);d.icon(xs[4]+130,yy+23,'trash','danger')
  else:
   d.pill(xs[1]+16,yy+19,r[4] if project else r[1],'selected' if r[1]=='Выполненная' else 'normal');d.text(xs[2]+18,yy+24,r[2],13);d.text(xs[3]+18,yy+24,r[3],12,False,'danger' if i==0 else 'warn' if i==1 else 'fg');d.text(xs[4]+18,yy+24,'19 окт, 16:24',12,False,'muted');d.icon(xs[5]+5,yy+22,'more')
 fy=y+49+len(rs)*69;d.line(x+16,fy,x+w-16,fy);d.text(x+18,fy+20,'Всего '+('в архиве: 3' if archive else 'задач: 8'),12,False,'muted');d.button(x+w-260,fy+10,'20 на странице',149,h=33,size=12);d.icon(x+w-90,fy+18,'left');d.pill(x+w-60,fy+13,'1','selected');d.icon(x+w-27,fy+18,'right')
def planning(d,m=False,mode='planning'):
 header(d,'Задачи',m);y=toolbar(d,'Задачи','Все задачи, даты и фильтры',m);y=filters(d,y,m);x=14 if m else 22;w=d.w-(2*x if m else x+16)
 d.rect(x,y,w,112 if m else 72,'context',12);d.text(x+14,y+11,'Быстрые фильтры',11,False,'muted');xx=x+12
 for i,t in enumerate(['Все','Сегодня','Завтра','Неделя','Без даты']):xx+=d.button(xx,y+32,t,style='selected' if i==0 else 'quiet',h=30,size=11 if m else 13)+3
 sy=y+80 if m else y+27;xx=x+15 if m else x+w-287
 for t in ['Активные','Выполненные']:d.check(xx+7,sy+10,True,True);d.text(xx+24,sy+3,t,12,False,'muted');xx+=135
 y+=128 if m else 91
 if mode=='planning-empty':empty(d,x,y,w,415,'Ничего не найдено','Попробуйте другой запрос или сбросьте фильтры.','Сбросить фильтры','search')
 else:table(d,x,y,w,m)
 if mode=='planning-filter':
  px=20 if m else d.w-415;py=340 if m else 290;pw=350 if m else 315;d.rect(px+5,py+8,pw,377,'context',15);d.rect(px,py,pw,377,'surface',15,'line');d.parts[-1]=d.parts[-1].replace('/>',' data-overlay="true"/>');mini(d,px+20,py+22,pw-40,True);d.line(px+18,py+293,px+pw-18,py+293);d.text(px+20,py+315,'19–25 октября',13,False,'muted');d.button(px+pw-131,py+309,'Применить',111,'primary',h=36,size=12)
def archive(d,m=False,mode='archive'):
 header(d,'Архив',m);y=toolbar(d,'Архив','Скрытые задачи. Выполнение и архив независимы.',m);y=filters(d,y,m,archive=True);x=14 if m else 22;w=d.w-(2*x if m else x+16)
 if mode=='archive-empty':empty(d,x,y,w,410,'Архив пока пуст','Здесь появятся задачи, которые вы отправите в архив.','','archive')
 else:table(d,x,y,w,m,archive=True)
 if mode=='archive-confirm':confirm(d,m)
def projects(d,m=False,mode='projects'):
 header(d,'Проекты',m);y=toolbar(d,'Проекты','Связанные задачи и понятный прогресс',m,'Новый проект');x=14 if m else 22;w=d.w-(2*x if m else x+16);d.rect(x,y,226,38,'context',10);d.button(x+4,y+3,'Активные',104,'selected' if mode!='projects-archived' else 'quiet',h=32,size=13);d.button(x+115,y+3,'Архивные',106,'selected' if mode=='projects-archived' else 'quiet',h=32,size=13)
 sy=y+50 if m else y;xx=x if m else x+245;sw=w if m else w-487;d.rect(xx,sy,sw,38,'surface',9,'line');d.icon(xx+12,sy+11,'search');d.text(xx+42,sy+11,'Поиск по проектам',13,False,'muted')
 if m:d.button(x,sy+49,'Сначала новые',w,ic='down');y=sy+105
 else:d.button(d.w-246,sy,'Сначала новые',230,ic='down');y=sy+57
 if mode=='projects-empty':empty(d,x,y,w,455,'Первый проект начинается с идеи','Объедините связанные задачи и настройте удобные этапы.','Новый проект','folder');return
 ps=[('Личный план','Повседневные дела и планы на месяц.',0,0,0)] if mode=='projects-archived' else [('Обновление интерфейса','Компактная навигация, спокойная палитра и все сценарии приложения.',25,2,8),('Личный план','Учёба, повседневные дела и планы на месяц.',43,3,7),('Подготовка релиза','Сверить сценарии и подготовить материалы.',0,0,6)]
 for i,(title,desc,progress,done,total) in enumerate(ps):
  cw=w if m else (w-32)/3;cx=x if m else x+i*(cw+16);cy=y+i*285 if m else y;d.rect(cx,cy,cw,267,'surface',16,'line');d.rect(cx+20,cy+20,34,34,'sel',10);d.icon(cx+28,cy+28,'folder','accent');d.icon(cx+cw-40,cy+27,'more');d.text(cx+20,cy+72,title,18,True);d.text(cx+20,cy+106,desc,14,False,'muted',maxw=cw-45,lines=2);d.rect(cx+20,cy+179,cw-40,5,'line',3);d.rect(cx+20,cy+179,(cw-40)*progress/100,5,'accent',3);d.text(cx+20,cy+196,f'Выполнено {done} из {total}',12,False,'muted');d.text(cx+cw-20,cy+196,str(progress)+'%',13,True,align='right');d.text(cx+20,cy+237,'Обновлён 19 окт',12,False,'muted');d.text(cx+cw-20,cy+237,'Восстановить' if mode=='projects-archived' else 'Открыть →',13,False,'accent',align='right')
def project(d,m=False,mode='project-board'):
 header(d,'Проекты',m);d.text(16 if m else 34,123 if m else 85,'Проекты / Обновление интерфейса',12,False,'muted');ty=158 if m else 118;th=d.text(16 if m else 34,ty,'Обновление интерфейса',25 if m else 22,True,maxw=350 if m else 900,lines=2);dy=ty+th+10;d.text(16 if m else 34,dy,'Все сценарии — в одной системе.',13,False,'muted')
 if m:d.button(16,dy+33,'Новая задача',163,'primary','plus');d.icon(345,dy+42,'more');y=dy+84
 else:d.button(d.w-193,ty,'Новая задача',163,'primary','plus');d.icon(d.w-243,ty+10,'more');y=ty+86
 y=filters(d,y,m,project=True);x=14 if m else 22;w=d.w-(2*x if m else x+16)
 if mode in ['project-list','project-bulk']:table(d,x,y,w,m,True,mode=='project-bulk');return
 cs=[['Согласовать пустые состояния','Еженедельный обзор проекта'],['Обновить документацию','Проверить мобильную навигацию'],['Собрать референсы интерфейса','Спецификация компонентов'],[],['Проверить контраст текста','Зафиксировать палитру']]
 if m:d.parts.append(f'<defs><clipPath id="board-viewport"><rect x="{x}" y="{y}" width="{w}" height="557" rx="15"/></clipPath></defs><g clip-path="url(#board-viewport)">')
 for i,col in enumerate(COLS[:2] if m else COLS):
  cw=280 if m else (w-52)/5;cx=x+i*(cw+13);d.rect(cx,y,cw,557,'context',15);d.text(cx+16,y+18,col,14,True);d.pill(cx+cw-52,y+13,str(0 if mode=='project-empty' else len(cs[i])),'normal',11);yy=y+62
  if mode=='project-empty' or not cs[i]:d.text(cx+cw/2,yy+37,'Перетащите задачу сюда',12,False,'muted',maxw=cw-30,align='center');yy+=105
  else:
   for j,t in enumerate(cs[i]):
    hh=135 if t=='Спецификация компонентов' else 119;d.rect(cx+10,yy,cw-20,hh,'surface',11,'line');d.text(cx+24,yy+17,t,16 if m else 14,False,maxw=cw-48,lines=2);d.icon(cx+24,yy+hh-34,'repeat' if 'обзор' in t else 'check' if i==4 else 'calendar','muted',15);d.text(cx+47,yy+hh-33,'Раз в 2 недели' if 'обзор' in t else 'Без даты' if i==0 else 'Сегодня',12,False,'muted')
    if t=='Спецификация компонентов':d.text(cx+24,yy+hh-55,'Дедлайн: до 18:00',12,False,'warn')
    yy+=hh+10
  d.icon(cx+18,yy+13,'plus');d.text(cx+44,yy+15,'Добавить задачу',13,False,'muted')
 if m:d.parts.append('</g>')
 if m:d.text(16,y+588,'Листайте доску вправо →',12,False,'muted')
def calendar(d,m=False,mode='calendar-week'):
 header(d,'Календарь',m);y=toolbar(d,'Календарь','Задачи и повторения по дням',m);x=14 if m else 22;w=d.w-(2*x if m else x+16);month=mode=='calendar-month';d.rect(x,y,174,37,'context',10);d.button(x+4,y+3,'Неделя',80,'quiet' if month else 'selected',h=31,size=13);d.button(x+88,y+3,'Месяц',82,'selected' if month else 'quiet',h=31,size=13);d.button(x+188,y,'Сегодня',84,h=37,size=12);d.icon(x+287,y+10,'left');d.icon(x+328,y+10,'right');y+=57
 d.text(x,y,'Октябрь 2026' if month else '19–25 октября',19,True)
 if not m:d.button(x+w-150,y-5,'19.10.2026',150,ic='calendar',size=12)
 y+=42;cw=w if m else w-432;right=x+cw+12
 d.rect(x,y,cw,390 if month and m else 555 if month else 620,'surface',16,'line');cell=cw/7 if month else 133 if m else cw/7
 if m and not month:d.parts.append(f'<defs><clipPath id="week-viewport"><rect x="{x}" y="{y}" width="{cw}" height="620" rx="16"/></clipPath></defs><g clip-path="url(#week-viewport)">')
 for i,t in enumerate(['Пн','Вт','Ср','Чт','Пт','Сб','Вс']):
  xx=x+i*cell
  if m and not month and i>2:break
  d.text(xx+cell/2,y+16,t,11,False,'muted',align='center')
  if not month:d.text(xx+cell/2,y+42,str(19+i),22,True,i==0 and 'accent' or 'fg',align='center')
  d.line(xx,y+38 if month else y+86,xx,y+(390 if month and m else 555 if month else 620))
 if month:
  ch=103 if not m else 70;d.line(x,y+39,x+cw,y+39)
  for i in range(35):
   n=28+i if i<3 else i-2;xx=x+(i%7)*cell;yy=y+40+(i//7)*ch
   if n==19 and i>3:d.rect(xx+1,yy+1,cell-1,ch-1,'sel');d.circle(xx+19 if not m else xx+cell/2,yy+18,12,'accent',None)
   d.text(xx+19 if not m else xx+cell/2,yy+12,str(n if n<=31 else n-31),12 if not m else 11,False,'on' if n==19 else 'muted' if i<3 or n>31 else 'fg',align='center')
   if 19<=n<=31 and i>3:
    if m:
     d.circle(xx+cell/2-5,yy+42,2,'accent',None)
     if n in [19,20,23]:d.circle(xx+cell/2+4,yy+42,2,'warn',None)
    else:
     label='Собрать референсы' if n==19 else 'Обзор проекта' if n==20 else 'Экспорт SVG' if n==23 else 'Утренний обзор';d.rect(xx+5,yy+36,cell-10,25,'context',5);d.text(xx+10,yy+42,label,10,False,maxw=cell-20,lines=1)
     if n in [19,20,23]:d.rect(xx+5,yy+65,cell-10,25,'warnbg',5);d.text(xx+10,yy+71,'Дедлайн: '+('18:00' if n==19 else 'референсы' if n==20 else 'SVG'),10,False,'warn',maxw=cell-20,lines=1)
   d.line(x,yy+ch,x+cw,yy+ch)
  end=y+40+5*ch
 else:
  for i in range(3 if m else 7):
   xx=x+i*cell;yy=y+105;d.text(xx+12,yy,'Без времени',10,False,'muted');yy+=30
   cards=[('Утренний обзор','↻ Каждый день','context')]
   if i==0:cards += [('Собрать референсы','10:00 · План','context'),('Спецификация','14:00 · План','context'),('Спецификация','18:00 · Дедлайн','warnbg')]
   elif i==1:cards += [('Обзор проекта','↻ Раз в 2 нед.','context'),('Референсы','Дедлайн','warnbg')]
   elif i<5:cards += [('Разобрать почту','↻ По будням','context')]
   for title,tag,color in cards:
    d.rect(xx+7,yy,cell-14,78,color,7);d.text(xx+15,yy+10,tag,10,False,'warn' if color=='warnbg' else 'muted',maxw=cell-28,lines=1);d.text(xx+15,yy+31,title,12,False,'warn' if color=='warnbg' else 'fg',maxw=cell-28,lines=2);yy+=88
  end=y+620
 if m and not month:d.parts.append('</g>')
 d.circle(x+3,end+28,3,'accent',None);d.text(x+13,end+21,'План',11,False,'muted');d.circle(x+70,end+28,3,'warn',None);d.text(x+80,end+21,'Дедлайн',11,False,'muted');d.icon(x+156,end+20,'repeat','muted',14);d.text(x+178,end+21,'Повторение',11,False,'muted')
 sy=end+66 if m else y;rx=x if m else right;rw=w if m else 420;d.rect(rx,sy,rw,530 if m else 555 if month else 620,'context',16,'line');d.text(rx+20,sy+22,'Выбранный день',11,False,'muted');d.text(rx+20,sy+48,'Пн, 19 октября',19,True);dy=sy+96
 for title,items in [('План',[('09:30','Читать 20 минут'),('10:00','Собрать референсы'),('14:00','Спецификация компонентов')]),('Дедлайн',[('18:00','Спецификация компонентов')]),('Без времени',[('','Сверить сценарии')])]:
  d.text(rx+20,dy,title,14,True,'warn' if title=='Дедлайн' else 'fg');dy+=34
  for time,t in items:d.text(rx+20,dy,time,11,False,'warn' if title=='Дедлайн' else 'muted');d.text(rx+(72 if time else 20),dy,t,13,False,maxw=rw-94 if time else rw-40,lines=2);dy+=46
  d.line(rx+20,dy,rx+rw-20,dy);dy+=20
 d.text(rx+20,dy,'Показать в задачах →',12,False,'accent')

def formfield(d,x,y,w,label,value,kind='text',error=None):
 d.text(x,y,label,13,True);yy=y+25;h=76 if kind=='area' else 43;d.rect(x,yy,w,h,'context' if kind=='disabled' else 'surface',9,'danger' if error else 'control');d.text(x+12,yy+13,value,14,False,'muted' if value.startswith(('Выберите','Без даты','Не указ')) else 'fg',maxw=w-(40 if kind in ['select','date','time','password'] else 24),lines=2 if kind=='area' else 1)
 if kind in ['select','date','time','password']:d.icon(x+w-29,yy+13,{'select':'down','date':'calendar','time':'clock','password':'eye'}[kind],s=16)
 if error:d.text(x,yy+h+7,error,12,False,'danger',maxw=w,lines=2);return y+105
 return yy+h+17
def sheet_base(d,m,title,sub='',height=None):
 # Подложка отрисована нативно: диаграмма не управляет браузером.
 d.shade(104 if m else 64)
 sw=d.w if m else 494;sx=0 if m else d.w-sw-20;sy=119 if m else 82;sh=height or d.h-sy-19;d.rect(sx,sy,sw,sh,'surface',17,'line');d.text(sx+24,sy+23,title,21,True,maxw=sw-80,lines=1);d.icon(sx+sw-45,sy+26,'close')
 if sub:d.text(sx+24,sy+57,sub,12,False,'muted',maxw=sw-75,lines=1)
 hy=sy+(88 if sub else 72);d.line(sx,hy,sx+sw,hy);return sx+24,hy+22,sw-48,sx,sy,sh
def formfooter(d,x,w,y,primary='Сохранить',delete=False):
 d.line(x-24,y-14,x+w+24,y-14)
 if delete:d.icon(x,y+10,'trash','danger');d.text(x+25,y+12,'Удалить',12,False,'danger')
 d.button(x+w-225,y,'Отмена',98,h=39,size=13);d.button(x+w-116,y,primary,116,'primary',h=39,size=13)
def task_form(d,m=False,mode='task-create'):
 planning(d,m);rec=mode=='task-recurring';edit=mode=='task-edit';x,y,w,sx,sy,sh=sheet_base(d,m,'Редактирование задачи' if edit else 'Новая задача');y=formfield(d,x,y,w,'Название *','Не указано' if mode=='task-invalid' else 'Еженедельный обзор проекта' if rec else 'Спецификация компонентов',error='Введите название задачи.' if mode=='task-invalid' else None);y=formfield(d,x,y,w,'Описание','Зафиксировать размеры, отступы и состояния компонентов.','area');fw=(w-12)/2
 y1=formfield(d,x,y,fw,'Проект','Без проекта' if mode=='task-no-project' else 'Обновление интерфейса','select');formfield(d,x+fw+12,y,fw,'Этап','Недоступен' if mode=='task-no-project' else 'В работе','disabled' if mode=='task-no-project' else 'select');y=y1;d.text(x,y,'Выберите проект, чтобы назначить этап.' if mode=='task-no-project' else 'Также появится в планировании и календаре.',11,False,'muted',maxw=w);y+=35
 if not rec:d.text(x,y,'Статус',14,True);d.button(x,y+27,'Активная',114,'selected',ic='check',h=35,size=12);d.button(x+123,y+27,'Выполненная',137,h=35,size=12);y+=87
 d.line(x,y-4,x+w,y-4);d.text(x,y+12,'Когда делать · план',15,True);y+=45;xx=x
 for i,t in enumerate(['Сегодня','Завтра','Без даты']):xx+=d.button(xx,y,t,style='selected' if i==0 else 'outline',h=31,size=12)+8
 y+=48;y1=formfield(d,x,y,fw,'Дата','19 октября 2026','date');formfield(d,x+fw+12,y,fw,'Время','14:00','time');y=y1+8;d.line(x,y-6,x+w,y-6);d.text(x,y+9,'Дедлайн · необязательно',15,True);y+=43;y1=formfield(d,x,y,fw,'Дата','Выберите дату' if rec else '18 октября 2026' if mode=='task-invalid' else '19 октября 2026','date');formfield(d,x+fw+12,y,fw,'Время','—' if rec else '18:00','time');y=y1+8;d.line(x,y-5,x+w,y-5);y=formfield(d,x,y+12,w,'Повторение','Каждую неделю' if rec else 'Не повторять','select')
 if rec:
  y1=formfield(d,x,y,fw,'Интервал в неделях','2');formfield(d,x+fw+12,y,fw,'Начало','19 октября 2026','date');y=formfield(d,x,y1,w,'Окончание','Без даты окончания','date');d.rect(x,y,w,61,'sel',9);d.text(x+12,y+12,'Раз в 2 недели. Выполнение отмечается на каждую дату отдельно.',12,False,'accent',maxw=w-24,lines=2);y+=80
 if mode=='task-invalid':d.rect(x,y,w,58,'warnbg',9);d.text(x+12,y+12,'План позже дедлайна. Проверьте даты. Задачу можно сохранить.',12,False,'warn',maxw=w-24,lines=2);y+=76
 formfooter(d,x,w,y+24,'Сохранить' if edit else 'Создать',edit)
def details(d,m=False,rec=False):
 planning(d,m);x,y,w,sx,sy,sh=sheet_base(d,m,'Задача');d.pill(x,y,'Повторяется' if rec else 'Активная','selected');y+=48;y+=d.text(x,y,'Еженедельный обзор проекта' if rec else 'Спецификация компонентов',25,True,maxw=w,lines=2)+25;d.text(x,y,'Описание',14,True);y+=31;y+=d.text(x,y,'Зафиксировать размеры, отступы и состояния компонентов. Сверить набор полей с текущим приложением.',14,False,maxw=w,lines=3)+30
 for label,value in [('Проект','Обновление интерфейса\nВ работе'),('Когда делать','19 октября 2026, 14:00'),('Дедлайн','19 октября 2026, 18:00'),('Повторение','Раз в 2 недели с 19 октября, без даты окончания' if rec else 'Не повторяется'),('Создано','19 октября, 10:24'),('Обновлено','19 октября, 14:10')]:
  d.text(x,y,label,13,False,'muted');rh=d.text(x+110,y,value,13,False,'warn' if label=='Дедлайн' else 'fg',maxw=w-115,lines=3);y+=max(43,rh+14)
 d.line(x,y,x+w,y);y+=25;d.button(x,y,'Редактировать',155,ic='edit',size=12);y+=52;d.button(x,y,'Выполнить сегодня' if rec else 'Выполнить',w,'primary','check',size=13);y+=67;d.icon(x,y,'archive');d.text(x+28,y+1,'В архив',13,False,'muted');d.icon(x+w-95,y,'trash','danger');d.text(x+w-65,y+1,'Удалить',13,False,'danger');d.line(x,y+65,x+w,y+65);d.button(x+w-110,y+82,'Закрыть',110,h=38,size=13)
def project_form(d,m=False,mode='project-create'):
 project(d,m);settings=mode!='project-create';confirm_=mode.endswith('confirm');x,y,w,sx,sy,sh=sheet_base(d,m,'Настройки проекта' if settings else 'Новый проект','Обновление интерфейса' if settings else 'Пространство для связанных задач');y=formfield(d,x,y,w,'Название *','Обновление интерфейса' if settings else 'Подготовка релиза');y=formfield(d,x,y,w,'Описание','Все сценарии приложения — в одной системе.','area');d.line(x,y,x+w,y);y+=22;d.text(x,y,'Колонки доски',16,True);y+=31;y+=d.text(x,y,'Перетащите за точки или используйте стрелки. Нажмите название для переименования.' if settings else 'Стандартные этапы появятся после создания. Изменить их можно в настройках проекта.',12,False,'muted',maxw=w,lines=2)+18
 for i,t in enumerate(COLS):
  if settings:d.icon(x,y+7,'grip');d.text(x+28,y+9,t,13,True,maxw=w-230 if i<4 else w-185,lines=1)
  else:d.rect(x,y,w,43,'context',9);d.text(x+13,y+12,t,14)
  if i==4:d.pill(x+w-103,y+3,'Завершает','selected',11)
  elif settings:d.button(x+w-190,y+3,'Завершать',84,h=27,size=10);d.icon(x+w-99,y+8,'up',s=16);d.icon(x+w-69,y+8,'down',s=16);d.icon(x+w-31,y+7,'trash',s=17)
  if settings and i<4:d.line(x,y+41,x+w,y+41)
  y+=51
 if settings:
  d.rect(x,y,w-104,40,'surface',9,'line');d.text(x+12,y+12,'Название колонки',13,False,'muted');d.button(x+w-95,y,'Добавить',95,h=40,size=12);y+=68;d.line(x,y-2,x+w,y-2);d.text(x,y+17,'Опасная зона',15,True);y+=52;d.button(x,y,'Архивировать',158,ic='archive',size=12);d.button(x+169,y,'Удалить проект',w-169,'danger',h=38,size=12);y+=57
  if confirm_:
   d.rect(x,y,w,138,'dangerbg',10);d.text(x+13,y+13,'Удалить проект?',14,True,'danger');d.text(x+13,y+43,'Проект и колонки будут удалены. Задачи останутся без проекта.',12,False,maxw=w-26,lines=2);d.button(x+13,y+91,'Отмена',94,h=32,size=12);d.button(x+119,y+91,'Удалить',101,'danger',h=32,size=12);y+=155
 formfooter(d,x,w,y+25,'Сохранить' if settings else 'Создать проект')
def confirm(d,m=False):
 d.shade(104 if m else 64);w=350 if m else 430;x=(d.w-w)/2;y=280 if m else 345;d.rect(x,y,w,285,'surface',17,'line');d.icon(x+26,y+24,'trash','danger',24);d.text(x+26,y+67,'Удалить задачу?',22,True);d.text(x+26,y+112,'«Разобрать входящие записи» будет удалена навсегда. Восстановить её не получится.',14,False,'muted',maxw=w-52,lines=3);d.button(x+w-242,y+220,'Отмена',100);d.button(x+w-130,y+220,'Удалить',104,'danger')
def auth(d,m=False,mode='login'):
 reg=mode.startswith('register');err=mode.endswith('error');success=mode.endswith('success');w=334 if m else 370;x=28 if m else (d.w-w)/2 if reg else 205;y=48 if m else 120
 d.logo(x,y,31);d.text(x+44,y+4,'Daily Organizer',18,True);y+=107
 if success:
  d.rect(x+w/2-33,y,66,66,'sel',22);d.icon(x+w/2-15,y+18,'check','accent',30);y+=103;d.text(x+w/2,y,'Аккаунт создан',29,True,align='center');d.text(x+w/2,y+58,'Теперь можно войти и составить первый план на день.',15,False,'muted',maxw=w,align='center');d.button(x,y+140,'Перейти ко входу',w,'primary',h=46);return
 d.text(x,y,'Создать аккаунт' if reg else 'С возвращением',29 if m else 32,True);y+=53;y+=d.text(x,y,'Начните с простого плана на день.' if reg else 'Ваши задачи, проекты и планы — в одном месте.',15,False,'muted',maxw=w,lines=2)+25
 if err:
  hh=62 if reg else 82;d.rect(x,y,w,hh,'dangerbg',9);d.text(x+13,y+12,'Проверьте отмеченные поля.' if reg else 'Неверный логин или пароль. Проверьте регистр и попробуйте ещё раз.',13,False,'danger',maxw=w-26,lines=3);y+=hh+21
 if reg:y=formfield(d,x,y,w,'Имя','Не указано' if err else 'Алексей',error='Введите имя.' if err else None)
 y=formfield(d,x,y,w,'Логин','qa ui' if reg and err else 'alexey' if reg else 'qa_ui36_20261019',error='Логин не должен содержать пробелы.' if reg and err else None);y=formfield(d,x,y,w,'Пароль','••••••••••','password',error='Нужно 8–30 латинских букв и цифр.' if reg and err else None)
 if reg:
  if not err:d.text(x,y-3,'8–30 латинских букв и цифр, без пробелов.',11,False,'muted');y+=24
  y=formfield(d,x,y,w,'Повторите пароль','••••••••','password',error='Пароли не совпадают.' if err else None)
 else:d.check(x+8,y+9,True,True);d.text(x+29,y+2,'Оставаться в системе',13,False,'muted');y+=40
 d.button(x,y+10,'Создать аккаунт' if reg else 'Войти',w,'primary',h=46,size=15);d.text(x+w/2,y+84,'Уже есть аккаунт? Войти' if reg else 'Нет аккаунта? Создать аккаунт',14,False,'accent',align='center')
 if not m and not reg:
  rx=760;d.rect(rx,24,d.w-rx-24,d.h-48,'sel',24);d.text(rx+50,79,'ЛИЧНЫЙ ОРГАНАЙЗЕР',11,False,'muted');d.text(rx+50,126,'Свой маршрут.\nСпокойный ритм.',41,True,maxw=480,lines=2);d.text(rx+50,269,'Планируйте день, объединяйте задачи в проекты и двигайтесь шаг за шагом.',16,False,'muted',maxw=410);d.rect(rx+165,457,275,275,'bg',80);d.logo(rx+225,512,150);d.text(rx+50,d.h-83,'Daily Organizer · 2026',12,False,'muted')
def states(d,m=False,comp=False):
 header(d,'',m);y=toolbar(d,'Компоненты' if comp else 'Состояния','Единые размеры и семантика в обеих темах',m);x=14 if m else 22;w=d.w-(2*x if m else x+16)
 if comp:
  labels=[('Фон','bg'),('Поверхность','surface'),('Акцент','accent'),('Выбранное','sel')];sw=(w-18)/2 if m else (w-48)/4
  for i,(label,c) in enumerate(labels):
   xx=x+(i%2)*(sw+18) if m else x+i*(sw+16);yy=y+(i//2)*125 if m else y;d.rect(xx,yy,sw,105,'surface',12,'line');d.rect(xx+1,yy+1,sw-2,65,c,11);d.text(xx+13,yy+79,label,12)
  y+=270 if m else 140;xx=x
  for i,(t,s) in enumerate([('Новая задача','primary'),('Редактировать','outline'),('Удалить','danger')]):
   if m and i==2:xx=x;y+=55
   xx+=d.button(xx,y,t,style=s,size=13)+10
  y+=80;d.rect(x,y,w,125,'surface',14,'line');d.text(x+20,y+20,'Статусы и даты',17,True);px=x+18;py=y+59
  for i,(t,s) in enumerate([('Активная','normal'),('Выполненная','selected'),('До 18:00','warn'),('Просрочено','danger')]):
   if m and i==2:px=x+18;py+=37
   px+=d.pill(px,py,t,s,11 if m else 12)+10
  y+=157;y=formfield(d,x,y,w if m else 460,'Название *','Не указано',error='Введите название задачи.');y+=34;d.text(x,y,'Заголовок · 36 px',30,True,maxw=w);d.text(x,y+58,'Раздел · 24 px',20,True);d.text(x,y+103,'Основной текст · 20 px',16);d.text(x,y+143,'Подписи · 16 px',13,False,'muted');d.text(x,y+189,'Радиусы: 16 / 12 / 9 px.\nШаг отступов: 4 px.\nПоле: 44 px. Кнопка: 38 / 44 px.',13,False,'muted',maxw=w)
  return
 for i,title in enumerate(['Загрузка списка','Не удалось загрузить задачи','Валидация','Повторение выполнено','Изменение сохранено','Архивированная задача']):
  cw=w if m else (w-18)/2;cx=x if m else x+(i%2)*(cw+18);cy=y+i*218 if m else y+(i//2)*242;d.rect(cx,cy,cw,201 if m else 222,'surface',14,'line');d.text(cx+20,cy+20,title,16,True,maxw=cw-40)
  if i==0:
   for j,ww in enumerate([.83,.64,.73]):d.rect(cx+20,cy+64+j*29,(cw-40)*ww,12,'line',6)
   d.text(cx+20,cy+167,'Загружаем задачи…',12,False,'muted')
  elif i==1:d.text(cx+20,cy+62,'Проверьте подключение и попробуйте ещё раз.',14,False,'muted',maxw=cw-40,lines=2);d.button(cx+20,cy+133,'Повторить',135,'primary',ic='repeat',h=36,size=12)
  elif i==2:
   d.rect(cx+20,cy+63,cw-40,43,'surface',9,'danger');d.text(cx+32,cy+77,'Название задачи',13,False,'muted');d.text(cx+20,cy+117,'Введите название задачи.',12,False,'danger');d.text(cx+20,cy+157,'План позже дедлайна. Можно сохранить.',12,False,'warn',maxw=cw-40)
  elif i==3:d.pill(cx+20,cy+63,'Выполнено сегодня · 19 октября','selected');d.text(cx+20,cy+108,'Правило повторения продолжает действовать.',13,False,'muted',maxw=cw-40);d.button(cx+20,cy+157,'Снять выполнение сегодня',cw-40 if m else 240,h=33,size=12)
  elif i==4:d.pill(cx+20,cy+64,'Задача сохранена','selected');d.button(cx+20,cy+123,'Сохраняем…',155,'primary',h=36,size=13)
  else:d.pill(cx+20,cy+63,'В архиве');d.text(cx+20,cy+109,'Архивировано 19 октября, 16:26',13,False,'muted');d.button(cx+20,cy+153,'Вернуть из архива',190,ic='repeat',h=34,size=12)
def logos(d,m=False):
 header(d,'',m);y=toolbar(d,'Маршрут','Векторный знак и версия с рабочим названием',m);x=14 if m else 22;w=d.w-(2*x if m else x+16)
 for i in range(4):
  cw=w if m else (w-20)/2;xx=x if m else x+(i%2)*(cw+20);yy=y+i*272 if m else y+(i//2)*325;d.rect(xx,yy,cw,254 if m else 301,'context' if i==3 else 'surface',18,'line')
  if i==0:d.logo(xx+cw/2-58,yy+52,116);d.text(xx+cw/2,yy+210,'Самостоятельный знак',13,False,'muted',align='center')
  elif i==1:
   s=43 if m else 58;start=xx+30 if m else xx+115;d.logo(start,yy+99,s);d.text(start+s+17,yy+109,'Daily Organizer',23 if m else 34,True);d.text(xx+cw/2,yy+210,'Горизонтальная версия',13,False,'muted',align='center')
  elif i==2:
   for j,s in enumerate([16,24,32,48]):d.logo(xx+35+j*(cw-70)/4,yy+100-s/2,s);d.text(xx+35+j*(cw-70)/4+s/2,yy+155,str(s)+' px',12,False,'muted',align='center')
   d.text(xx+cw/2,yy+210,'Проверка малого размера',13,False,'muted',align='center')
  else:d.logo(xx+cw/2-58,yy+52,116);d.text(xx+cw/2,yy+210,'Прозрачный фон · один цвет',13,False,'muted',align='center')
def controls(d,m=False,rec=False,column=False):
 header(d,'Проекты' if column else 'Задачи',m);y=toolbar(d,'Колонки' if column else 'Повторение' if rec else 'Меню и фильтры','Все состояния сохраняют существующие возможности.',m);x=14 if m else 22;w=d.w-(2*x if m else x+16)
 if column:items=[('Переименование',['Название колонки','На проверке','Сохранить название','Отменить переименование']),('Порядок колонок',['Перетащить за точки','Переместить выше','Переместить ниже','На границе стрелка недоступна']),('Завершающий этап',['Сделать завершающей','Готово · Завершает','Завершающую колонку нельзя удалить','Один завершающий этап на проект']),('Новая колонка',['Название новой колонки','Добавить','Колонки принадлежат этому проекту'])]
 elif rec:items=[('Правило повторения',['Не повторять','Каждый день','По будням','Каждую неделю']),('Каждые N дней',['Интервал в днях: 3','Начало: 19 октября 2026','Окончание: 31 октября 2026','Повторять каждые 3 дня']),('По будням',['Понедельник — пятница','Начало: 19 октября 2026','Окончание: без даты','Без отдельного поля интервала']),('Каждые N недель',['Интервал в неделях: 2','Начало: 19 октября 2026','Окончание: без даты','Выполнение отмечается на дату'])]
 else:items=[('Быстрые фильтры',['Все','Сегодня','Завтра','Эта неделя','Без даты']),('Сортировка задач',['Ближайшие дедлайны','По плановой дате','Сначала новые','Сначала старые']),('Даты проекта',['Все даты','Сегодня','Завтра','Эта неделя','Просроченные','Конкретная дата']),('Проект и статус',['Без проекта / выбор проекта','Этап: все или выбранная колонка','Все статусы','Активные','Выполненные']),('Сортировка проектов',['Сначала новые','Сначала старые','По названию','По прогрессу']),('Пагинация и аккаунт',['10 / 20 / 50 задач на странице','Назад / номер страницы / вперёд','Меню аккаунта: Выйти','Тема: светлая / тёмная']),('Календарный выбор',['Месяц: октябрь ▼','Год: 2026 ▼','Предыдущий / следующий месяц','Сегодня / очистить дату / закрыть','Период: начало и окончание']),('Архив и выполнение',['Сначала новые / старые задачи','Вернуть из архива','Удалить: подтверждение Да / Нет','Выполнить / вернуть в активные','Повторение: выполнить сегодня'])]
 for i,(title,options) in enumerate(items):
  cw=w if m else (w-18)/2;cx=x if m else x+(i%2)*(cw+18);rh=275 if not rec and not column else 247;cy=y+i*(rh+16) if m else y+(i//2)*(rh+16);d.rect(cx,cy,cw,rh,'surface',14,'line');d.text(cx+20,cy+20,title,17,True);yy=cy+63
  for j,opt in enumerate(options):
   if j==0:d.rect(cx+10,yy-7,cw-20,30,'sel',7)
   d.text(cx+22,yy,opt,13 if not m else 12,False,'accent' if j==0 else 'fg',maxw=cw-44,lines=2);yy+=35
def render(mode,theme,m=False):
 h=(2600 if mode=='controls' else 2080 if mode=='today' else 900 if mode=='today-empty' else 1650 if mode=='states' else 1490 if mode=='task-recurring' else 1320 if mode in ['project-settings-confirm','calendar-week','task-no-project','task-invalid','task-recurrence-options','project-column-edit'] else 1250 if mode in ['project-settings','calendar-month','project-bulk','planning','project-list','planning-filter','task-create','task-edit','task-details','task-occurrence','logo'] else 1150 if mode in ['project-board','project-empty','register-error','components'] else 1100) if m else (1490 if mode=='controls' else 1320 if mode=='task-recurring' else 1270 if mode=='project-settings-confirm' else 1250 if mode=='task-invalid' else 1130 if mode in ['task-create','task-edit','project-settings','task-no-project'] else 992)
 if m and mode in ['planning','planning-filter']:h=1620
 if m and mode=='project-list':h=1680
 if m and mode=='projects':h=1260
 if m and mode=='today-empty':h=1700
 if m and mode=='project-bulk':h=1800
 if m and mode=='calendar-week':h=1600
 if m and mode=='calendar-month':h=1350
 if mode=='task-occurrence' and not m:h=1100
 if m and mode in ['components','logo']:h+=60
 d=Drawing(390 if m else 1586,h,DARK if theme=='dark' else LIGHT,dict((s[0],s[1]) for s in SCREENS)[mode]+' · '+theme);d.mode=mode
 if mode.startswith('today'):today(d,m,mode.endswith('empty'))
 elif mode.startswith('planning'):planning(d,m,mode)
 elif mode.startswith('calendar'):calendar(d,m,mode)
 elif mode.startswith('archive'):archive(d,m,mode)
 elif mode.startswith('projects'):projects(d,m,mode)
 elif mode=='project-column-edit':controls(d,m,column=True)
 elif mode in ['project-create','project-settings','project-settings-confirm']:project_form(d,m,mode)
 elif mode.startswith('project-'):project(d,m,mode)
 elif mode=='task-recurrence-options':controls(d,m,rec=True)
 elif mode in ['task-create','task-edit','task-recurring','task-no-project','task-invalid']:task_form(d,m,mode)
 elif mode in ['task-details','task-occurrence']:details(d,m,mode=='task-occurrence')
 elif mode=='task-delete':planning(d,m);confirm(d,m)
 elif mode.startswith(('login','register')):auth(d,m,mode)
 elif mode in ['states','components']:states(d,m,mode=='components')
 elif mode=='logo':logos(d,m)
 elif mode=='controls':controls(d,m)
 d.save(mode+('-mobile' if m else '')+'-'+theme)
 return dict(screen=mode,theme=theme,mobile=m,width=d.w,height=d.h)
def gallery():
 css='''*{box-sizing:border-box}body{margin:0;background:#F6F5F0;color:#19241E;font:15px/1.5 "Segoe UI",Arial,sans-serif}main{max-width:1250px;margin:auto;padding:42px 28px}h1{font-size:42px;letter-spacing:-1.3px;line-height:1.15;margin:45px 0 16px}h2{margin:44px 0 20px;font-size:22px}p{color:#626D65;max-width:780px}a{color:#214E3D;text-decoration:none}a:hover{text-decoration:underline}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{border:1px solid #DEE1D8;border-radius:16px;overflow:hidden;background:#FFFEFA}.card img{width:100%;aspect-ratio:1.6;object-fit:contain;object-position:top;display:block;background:#F0F0E8}.inside{padding:17px}.inside h3{margin:0;font-size:16px}.inside p{font-size:13px;margin:7px 0 15px}.links{display:flex;gap:13px;flex-wrap:wrap;font-size:12px}.note{border:1px solid #DEE1D8;border-radius:13px;padding:16px 20px;margin:28px 0;color:#626D65;font-size:13px}.brand{font-size:19px;font-weight:650;display:flex;align-items:center;gap:13px}.brand img{width:31px;height:31px}.nav{display:flex;gap:17px;flex-wrap:wrap;font-size:14px}.foot{margin-top:50px;font-size:13px}@media(max-width:800px){.grid{grid-template-columns:1fr 1fr}h1{font-size:34px}}@media(max-width:520px){main{padding:28px 18px}.grid{grid-template-columns:1fr}.inside h3{font-size:18px}.links{font-size:14px}}'''
 body='<div class="brand"><img src="assets/route-light.svg" alt="Маршрут">Daily Organizer</div><h1>Daily Organizer<br>Альбом экранов</h1><p>39 экранов и состояний в светлой и тёмной темах. Компактная верхняя навигация, тёплый фон, глубокий зелёный и графит с лаймом.</p><div class="nav"><a href="comparison.html">Эталон и восстановленный Today</a><a href="AUDIT.md">Аудит приложения</a><a href="DESIGN.md">Правила интерфейса</a><a href="assets/route-light.svg">SVG-знак</a><a href="assets/route-lockup-light.svg">SVG с названием</a><a href="contact-sheet.png">Обзор всех экранов</a></div><div class="note">Issue #36 · Исправлено после сверки с эталоном · 156 макетов: 39 состояния × 2 темы × desktop/mobile. SVG содержит контуры шрифта. PNG получен из этого же SVG. Общий комплект ожидает согласования. В интерфейсе показаны вымышленные данные. Новая реализация отслеживается отдельно в #37, тестирование — в #38.</div>'
 for category in dict.fromkeys(s[3] for s in SCREENS):
  body+=f'<h2>{category}</h2><div class="grid">'
  for sid,title,desc,cat in SCREENS:
   if cat!=category:continue
   body+=f'<article class="card"><a href="renders/{sid}-light.svg"><img loading="lazy" src="renders/{sid}-light.png" alt="{html.escape(title)}"></a><div class="inside"><h3>{html.escape(title)}</h3><p>{desc}</p><div class="links">'+''.join(f'<a href="renders/{sid}{suffix}-{theme}.svg">{label}</a>' for suffix,theme,label in [('', 'light','Светлая ↗'),('','dark','Тёмная ↗'),('-mobile','light','Мобильная ↗'),('-mobile','dark','Моб. тёмная ↗')])+f'</div><div class="links" style="margin-top:12px">'+''.join(f'<a href="renders/{sid}{suffix}-{theme}.png">PNG {label}</a>' for suffix,theme,label in [('', 'light','светлая'),('','dark','тёмная'),('-mobile','light','мобильная'),('-mobile','dark','моб. тёмная')])+'</div></div></article>'
  body+='</div>'
 body+='<p class="foot">Название Daily Organizer пока рабочее. Все макеты являются предложением, окончательное согласование пользователя ещё не получено. Альбом работает локально без сервера и без внешних зависимостей.</p>'
 body=body.replace('34 экрана','39 экранов').replace('156 макетов: 39','156 макетов: 39')
 (ROOT/'mockups.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Daily Organizer · UI36</title><style>'+css+'</style><main>'+body+'</main></html>',encoding='utf-8')


def finalize():
 (STAGE/'texts.json').write_text(json.dumps(TEXTS,ensure_ascii=False),encoding='utf-8')
 subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(Path(__file__).with_name('outline.ps1')),'-Directory',str(STAGE)],check=True)
 paths=json.loads((STAGE/'paths.json').read_text(encoding='utf-8-sig'))
 for p in WRITTEN:
  svg=p.read_text(encoding='utf-8');keys=set(re.findall(r'#t([0-9a-f]+)',svg));defs=[]
  for key in sorted(keys):
   item=paths[key];defs.append(f'<path id="t{key}" d="{item["path"]}" transform="translate(0 {-item["top"]})"/>')
  svg=svg.replace('</defs>',''.join(defs)+'</defs>',1);(OUT/p.name).write_text(svg,encoding='utf-8')
 subprocess.run(['node',str(Path(__file__).with_name('rasterize.cjs')),str(OUT)],check=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--screens',nargs='*');args=parser.parse_args();manifest=[]
 for sid,*_ in SCREENS:
  if args.screens and sid not in args.screens:continue
  for theme in ['light','dark']:
   for mobile in [False,True]:manifest.append(render(sid,theme,mobile))
 finalize()
 if not args.screens:
  for item in manifest:
   name=item['screen']+('-mobile' if item['mobile'] else '')+'-'+item['theme']
   for extension in ['svg','png']:item[extension+'Sha256']=hashlib.sha256((OUT/(name+'.'+extension)).read_bytes()).hexdigest()
  gallery();(ROOT/'manifest.json').write_text(json.dumps(dict(screens=[dict(id=s[0],title=s[1],description=s[2],category=s[3]) for s in SCREENS],renders=manifest),ensure_ascii=False,indent=2),encoding='utf-8')
  subprocess.run([sys.executable,str(Path(__file__).with_name('proof_sheets.py'))],check=True)
 print(f'Rendered {len(manifest)} mockups')
