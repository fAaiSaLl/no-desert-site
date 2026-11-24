#!/usr/bin/env python3
"""يبني موقع مقالات «لا للتصحر» (GitHub Pages) من site_src/guides إلى مجلد المستودع العام.

Usage: python3 _src/build.py   (run from the repo root; builds the site into the repo root)

اللغات: ar = عربي فصحى (الرئيسية /)   en = English (/en/)
كل مقال: site_src/guides/<lang>/<slug>.html وأوله تعليقات title / description / date.

"""
import html, json, os, re, shutil, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, 'guides')
IMG = os.path.join(HERE, 'img')
BASE = 'https://faaisall.github.io/no-desert-site/'
APP_ID = '6836084405'
STORE = f'https://apps.apple.com/app/id{APP_ID}'
PRIVACY = 'https://no-desert.expo.app/privacy/'
SUPPORT = 'https://no-desert.expo.app/support/'
LANGS = ('ar', 'en')
PREFIX = {'ar': '', 'en': 'en/'}

T = {
    'ar': dict(html='ar', dir='rtl', name='لا للتصحر', cta='حمّل تطبيق «لا للتصحر» من App Store',
               cta_sub='تطبيق تذكير بشرب الماء بأسلوب ممتع وشخصيات طريفة. مجاني للآيفون والآيباد.',
               guides='المقالات', updated='آخر مراجعة', more='مقالات أخرى', privacy='الخصوصية',
               support='الدعم', sources='المصادر', note='المعلومات هنا للتوعية العامة ولا تغني عن استشارة الطبيب، خاصة لمن لديه مرض في الكلى أو القلب أو تعليمات بتقييد السوائل.',
               iphone='للآيفون والآيباد'),
    'en': dict(html='en', dir='ltr', name='No Desert', cta='Get No Desert on the App Store',
               cta_sub='A water reminder with funny personas that nag you until you drink. Free for iPhone and iPad.',
               guides='Guides', updated='Last reviewed', more='Keep reading', privacy='Privacy',
               support='Support', sources='Sources', note='This is general information, not medical advice. If you have kidney or heart disease or a fluid restriction, follow your doctor.',
               iphone='For iPhone and iPad'),
}

HOME = {
    'ar': ('لا للتصحر: تطبيق تذكير بشرب الماء بأسلوب ممتع',
           'تطبيق للآيفون يذكّرك بشرب الماء بشخصيات طريفة، مع حاسبة لكمية الماء حسب الوزن، ووضع رمضان، وتنبيه الأيام الحارة.',
           'تذكير بشرب الماء… بأسلوب مختلف',
           'اختر من يذكّرك: المدرب الصارم، أو المذيع العاجل، أو الصديق الساخر، أو الوضع اللطيف. عبارات جديدة كل يوم، وتسجيل الكوب من الإشعار مباشرة، ووضع خاص لرمضان.'),
    'en': ('No Desert: a funny water reminder app for iPhone',
           'A water reminder with personas that roast, coach or report the news until you drink. Water intake calculator, hot-day reminders and Ramadan mode.',
           'A water reminder you won’t ignore',
           'Pick who nags you: The Strict Coach, Breaking News, The Roaster or Kind Mode. Fresh lines every day, log a glass straight from the notification, and a Ramadan mode.'),
}

CSS = """
:root{--bg:#000;--card:#0d0d0f;--card2:#16161a;--line:#232329;--text:#fff;--muted:#b4b4bd;--neon:#19C3FF;--deep:#0A6FA8;--sand:#F2B36B}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:17px/1.75 "IBM Plex Sans Arabic",-apple-system,BlinkMacSystemFont,"Segoe UI",Tahoma,sans-serif}
a{color:var(--neon)}
img{max-width:100%;height:auto}
.wrap{max-width:780px;margin:0 auto;padding:0 18px}
header{position:sticky;top:0;z-index:5;background:rgba(0,0,0,.82);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
header .wrap{display:flex;align-items:center;gap:10px;height:60px}
header .logo{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-weight:700}
header .logo img{width:34px;height:34px;border-radius:9px}
header nav{margin-inline-start:auto;display:flex;gap:6px}
header nav a{color:var(--muted);text-decoration:none;font-size:14px;padding:6px 10px;border-radius:999px;border:1px solid var(--line)}
header nav a.on{color:#001018;background:var(--neon);border-color:var(--neon);font-weight:700}
.hero{position:relative;overflow:hidden;background:radial-gradient(120% 80% at 50% 0%,#0d4a6e 0%,#06192a 48%,#000 100%);padding:46px 0 0}
.hero .wrap{display:grid;grid-template-columns:1.1fr .9fr;gap:24px;align-items:end}
.hero h1{font-size:38px;line-height:1.25;margin:0 0 12px}
.hero p{color:#cfe9f7;margin:0 0 22px;font-size:18px}
.hero .mascot{align-self:center;justify-self:center;width:100%;max-width:300px;margin-bottom:30px;filter:drop-shadow(0 0 40px rgba(25,195,255,.45));animation:bob 3.2s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
@media (prefers-reduced-motion:reduce){.hero .mascot{animation:none}}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 26px}
.badges span{font-size:14px;color:#cfe9f7;border:1px solid #1d3a50;border-radius:999px;padding:4px 12px}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--neon);color:#001018;padding:14px 22px;border-radius:16px;font-weight:700;text-decoration:none;font-size:17px}
.btn small{display:block;font-weight:500;font-size:12px;opacity:.75}
.hero .cta-row{margin-bottom:46px}
section.feat{padding:40px 0 10px}
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
section.feat h2{margin-top:0}
.feat-grid div{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px}
.feat-grid img{width:72px;height:72px;object-fit:contain}
.feat-grid b{display:block;margin:6px 0 2px}
.feat-grid span{color:var(--muted);font-size:15px}
.shots{display:flex;gap:12px;justify-content:center;margin:22px 0 0;overflow:hidden}
.shots img{width:32%;max-width:220px;border-radius:22px;border:4px solid #1d3a50}
section.ben{padding:30px 0 0}
section.ben ul{padding-inline-start:22px}
.btn.ghost{background:transparent;color:var(--neon);border:1px solid var(--neon);padding:10px 18px;font-size:16px}
h1{font-size:32px;line-height:1.3;margin:34px 0 8px}
h2{font-size:24px;line-height:1.35;margin:34px 0 10px}
h3{font-size:19px;margin:24px 0 6px}
p,li{color:#e8e8ec}
.meta{color:var(--muted);font-size:14px;margin-bottom:20px}
article p:first-of-type{font-size:18px}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:16px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:9px 12px;text-align:start;vertical-align:top}
th{background:var(--card2);color:#fff}
td{background:var(--card)}
.box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:18px 0}
.box.warn{border-color:#5a2a2a;background:#160b0b}
.cta{display:flex;align-items:center;gap:16px;margin:38px 0;padding:18px;border-radius:20px;background:linear-gradient(135deg,#0B3A57,#08111C);border:1px solid #1d3a50;color:#fff;text-decoration:none}
.cta img{width:84px;height:84px;object-fit:contain;flex:none}
.cta b{display:block;font-size:19px;color:var(--neon)}
.cta span{color:#cfe9f7;font-size:15px}
.cards{list-style:none;padding:0;display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.cards a{display:block;height:100%;padding:16px;border:1px solid var(--line);border-radius:16px;background:var(--card);text-decoration:none;color:#fff}
.cards a:hover{border-color:var(--deep)}
.cards b{display:block;line-height:1.5}
.cards span{color:var(--muted);font-size:14px;display:block;margin-top:4px}
.cards i{font-style:normal;font-size:12px;color:var(--neon);border:1px solid #1d3a50;border-radius:999px;padding:1px 8px;margin-bottom:6px;display:inline-block}
.sources{font-size:14px;color:var(--muted)}
.sources a{word-break:break-word}
.tool{background:var(--card);border:1px solid #1d3a50;border-radius:20px;padding:18px;margin:20px 0}
.tool label{display:block;font-size:15px;color:var(--muted);margin:10px 0 4px}
.tool input,.tool select{width:100%;font:inherit;color:#fff;background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.tool .row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.tool .out{margin-top:16px;padding:16px;border-radius:16px;background:#06192a;border:1px solid #1d3a50;text-align:center}
.tool .out b{display:block;font-size:34px;color:var(--neon);line-height:1.3}
.tool .out span{color:#cfe9f7;font-size:15px}
.tool table{display:table}
footer{border-top:1px solid var(--line);margin-top:50px;color:var(--muted);font-size:14px}
footer .wrap{padding-top:18px;padding-bottom:34px;display:flex;gap:16px;flex-wrap:wrap;align-items:center}
footer a{color:var(--muted)}
@media (max-width:720px){
 .hero .wrap{grid-template-columns:1fr}
 .hero h1{font-size:30px}
 .hero .mascot{max-width:220px;margin-bottom:24px}
 .hero .cta-row{margin-bottom:26px}
 .feat-grid,.cards{grid-template-columns:1fr}
 h1{font-size:27px}
 header nav a{padding:5px 8px}
}
"""

FONT = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;700&display=swap" rel="stylesheet">'


def esc(s):
    return html.escape(s, quote=True)


def js(s):
    return json.dumps(s, ensure_ascii=False)


def read_guides():
    out = []
    for lang in LANGS:
        d = os.path.join(SRC, lang)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith('.html'):
                continue
            raw = open(os.path.join(d, f), encoding='utf-8').read()
            meta = dict(re.findall(r'<!--\s*(title|description|date|kind):\s*(.*?)\s*-->', raw))
            for k in ('title', 'description', 'date'):
                if not meta.get(k):
                    sys.exit(f'{lang}/{f}: missing {k}')
            body = re.sub(r'<!--\s*(title|description|date|kind):.*?-->\s*', '', raw, flags=re.S).strip()
            out.append(dict(lang=lang, slug=f[:-5], body=body, kind=meta.get('kind', 'article'),
                            title=meta['title'], description=meta['description'], date=meta['date'],
                            path=PREFIX[lang] + f[:-5] + '/'))
    out.sort(key=lambda g: (g['kind'] != 'tool', g['date']), reverse=False)
    out.sort(key=lambda g: g['date'], reverse=True)
    out.sort(key=lambda g: g['kind'] != 'tool')
    return out


def page(lang, title, desc, path, body, ld='', alt=None):
    t = T[lang]
    url = BASE + path
    alts = ''
    if alt:
        for l, p in alt.items():
            alts += f'<link rel="alternate" hreflang="{T[l]["html"]}" href="{BASE + p}">'
    nav = ''.join(f'<a class="{"on" if l == lang else ""}" href="{BASE + PREFIX[l]}">{n}</a>'
                  for l, n in (('ar', 'عربي'), ('en', 'EN')))
    return f"""<!doctype html>
<html lang="{t['html']}" dir="{t['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#000000">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">{alts}
<meta name="apple-itunes-app" content="app-id={APP_ID}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(t['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}img/icon.png">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{BASE}img/icon.png">
<link rel="apple-touch-icon" href="{BASE}img/apple-touch-icon.png">
{FONT}
<style>{CSS}</style>
{ld}
</head>
<body>
<header><div class="wrap"><a class="logo" href="{BASE + PREFIX[lang]}"><img src="{BASE}img/icon.png" alt="" width="34" height="34">{esc(t['name'])}</a><nav>{nav}</nav></div></header>
{body}
<footer><div class="wrap"><a href="{STORE}">App Store</a><a href="{PRIVACY}">{t['privacy']}</a><a href="{SUPPORT}">{t['support']}</a><span>© {date.today().year} No Desert</span></div></footer>
</body>
</html>
"""


def cta(lang, img='drop-glass'):
    t = T[lang]
    return (f'<a class="cta" href="{STORE}"><img src="{BASE}img/{img}.webp" alt="" loading="lazy">'
            f'<div><b>{esc(t["cta"])}</b><span>{esc(t["cta_sub"])}</span></div></a>')


def card_list(gs):
    return '<ul class="cards">' + ''.join(
        f'<li><a href="{BASE}{g["path"]}">'
        f'<b>{esc(g["title"])}</b><span>{esc(g["description"])}</span></a></li>' for g in gs) + '</ul>'


# ───────── الأدوات التفاعلية ─────────

CALC_TXT = {
    'ar': dict(w='الوزن (كغ)', a='مستوى النشاط', a0='خفيف (عمل مكتبي)', a1='متوسط (مشي وحركة)', a2='عالٍ (رياضة شبه يومية)',
               h='الطقس', hc='بارد', h0='معتدل', h1='حار (38° فأكثر)', res='الهدف اليومي المقترح', cups='أي نحو {c} كوبًا (250 مل)',
               bad='أدخل وزنك بالكيلوغرام', note='هذا تقدير أولي قابل للتعديل، والطعام يوفر جزءًا من الماء أيضًا.'),
    'en': dict(w='Your weight', a='Activity', a0='Light (desk and couch)', a1='Medium (walking around)', a2='High (workouts most days)',
               h='Weather', hc='Cold', h0='Mild', h1='Hot (100°F / 38°C+)', res='Suggested daily goal', cups='About {c} cups (8 oz) or {o} oz',
               bad='Enter your weight', note='A starting estimate you can adjust. Food also provides some of your water.'),
}


def tool_calc(lang):
    t = CALC_TXT[lang]
    unit = ('<div class="row"><div><label>' + t['w'] + '</label><input id="w" type="number" inputmode="decimal" min="20" max="250" placeholder="70"></div>'
            '<div><label>&nbsp;</label><select id="u"><option value="lb">lb</option><option value="kg">kg</option></select></div></div>') if lang == 'en' else \
           (f'<label>{t["w"]}</label><input id="w" type="number" inputmode="decimal" min="20" max="250" placeholder="70">')
    return f"""<div class="tool" id="calc">
{unit}
<div class="row"><div><label>{t['a']}</label><select id="a"><option value="0">{t['a0']}</option><option value="350" selected>{t['a1']}</option><option value="700">{t['a2']}</option></select></div>
<div><label>{t['h']}</label><select id="h"><option value="0">{t['hc']}</option><option value="0" selected>{t['h0']}</option><option value="500">{t['h1']}</option></select></div></div>
<div class="out" aria-live="polite"><span>{t['res']}</span><b id="r">—</b><span id="c">{t['bad']}</span></div>
<p class="meta" style="margin:10px 0 0">{t['note']}</p>
</div>
<script>
(function(){{
var L={js(lang)},$=function(i){{return document.getElementById(i)}};
function f(){{
 var w=parseFloat($('w').value);var u=$('u')?$('u').value:'kg';
 if(!w||w<20){{$('r').textContent='—';$('c').textContent={js(t['bad'])};return}}
 var kg=u==='lb'?w*0.4536:w;
 var ml=33*kg+ +$('a').value+ +$('h').value;
 ml=Math.round(Math.max(1500,Math.min(4500,ml))/100)*100;
 var cups=Math.round(ml/250);
 if(L==='en'){{var oz=Math.round(ml/29.57);$('r').textContent=(ml/1000).toFixed(1)+' L';$('c').textContent={js(t['cups'])}.replace('{{c}}',Math.round(oz/8)).replace('{{o}}',oz);}}
 else{{$('r').textContent=(ml/1000).toFixed(1).replace('.0','')+' لتر';$('c').textContent={js(t['cups'])}.replace('{{c}}',cups);}}
}}
['w','a','h','u'].forEach(function(i){{var e=$(i);if(e)e.addEventListener('input',f)}});
}})();
</script>"""


RAM_TXT = {
    'ar': dict(m='وقت المغرب (الإفطار)', f='وقت الفجر (نهاية السحور)', g='الهدف اليومي (لتر)', go='أنشئ الجدول', th=('الوقت', 'الكمية'),
               first='كوب 250 مل مع الإفطار', mid='كوب 250 مل', sahur='كوب 250 مل مع السحور', note='تجنّب شرب كمية كبيرة دفعة واحدة، ووزّعها كما في الجدول.'),
    'en': dict(m='Sunset (iftar)', f='Dawn (end of suhoor)', g='Daily goal (liters)', go='Build my schedule', th=('Time', 'Drink'),
               first='1 cup (250 ml) at iftar', mid='1 cup (250 ml)', sahur='1 cup (250 ml) at suhoor', note='Don’t drink a large amount at once; spread it out like this.'),
}


def tool_ramadan(lang):
    t = RAM_TXT[lang]
    return f"""<div class="tool" id="ram">
<div class="row"><div><label>{t['m']}</label><input id="rm" type="time" value="17:45"></div><div><label>{t['f']}</label><input id="rf" type="time" value="05:10"></div></div>
<label>{t['g']}</label><input id="rg" type="number" inputmode="decimal" min="1" max="4" step="0.5" value="2.5">
<div class="out"><table id="rt"><thead><tr><th>{t['th'][0]}</th><th>{t['th'][1]}</th></tr></thead><tbody></tbody></table></div>
<p class="meta" style="margin:10px 0 0">{t['note']}</p>
</div>
<script>
(function(){{
var T={js(t)},$=function(i){{return document.getElementById(i)}};
function mins(v){{var p=v.split(':');return +p[0]*60+ +p[1]}}
function fmt(m){{m=((m%1440)+1440)%1440;var h=Math.floor(m/60),mi=m%60;return (h<10?'0':'')+h+':'+(mi<10?'0':'')+mi}}
function f(){{
 var a=mins($('rm').value||'17:45'),b=mins($('rf').value||'05:10');if(b<=a)b+=1440;
 var start=a,end=b-30,cups=Math.max(3,Math.min(16,Math.round(parseFloat($('rg').value||2.5)*4)));
 var step=(end-start)/(cups-1),rows='';
 for(var i=0;i<cups;i++){{var lab=i===0?T.first:(i===cups-1?T.sahur:T.mid);rows+='<tr><td>'+fmt(Math.round(start+i*step))+'</td><td>'+lab+'</td></tr>'}}
 $('rt').querySelector('tbody').innerHTML=rows;
}}
['rm','rf','rg'].forEach(function(i){{$(i).addEventListener('input',f)}});f();
}})();
</script>"""


TOOLS = {'calc': tool_calc, 'ramadan': tool_ramadan}


def render_body(g):
    body = g['body']
    for name, fn in TOOLS.items():
        body = body.replace(f'<!-- tool: {name} -->', fn(g['lang']))
    return body


def guide_page(g, all_g):
    t = T[g['lang']]
    same = [o for o in all_g if o['lang'] == g['lang'] and o is not g][:6]
    ld = ('<script type="application/ld+json">' + json.dumps({
        '@context': 'https://schema.org', '@type': 'Article', 'headline': g['title'], 'description': g['description'],
        'datePublished': g['date'], 'dateModified': g['date'], 'inLanguage': t['html'],
        'author': {'@type': 'Organization', 'name': 'No Desert'}, 'publisher': {'@type': 'Organization', 'name': 'No Desert'},
        'image': BASE + 'img/icon.png', 'mainEntityOfPage': BASE + g['path']}, ensure_ascii=False) + '</script>')
    body = f"""<main class="wrap"><article>
<h1>{esc(g['title'])}</h1>
<div class="meta">{t['updated']}: {g['date']}</div>
{render_body(g)}
<div class="box warn">{esc(t['note'])}</div>
</article>
{cta(g['lang'])}
{('<h2>' + t['more'] + '</h2>' + card_list(same)) if same else ''}
</main>"""
    return page(g['lang'], g['title'], g['description'], g['path'], body, ld)


FEATS = {
    'ar': [('drop-cool', 'شخصيات تذكّرك بأسلوبها', 'اختر من يذكّرك: المدرب الصارم، أو المذيع العاجل، أو الصديق الساخر، أو الوضع اللطيف. وتصلك عبارات جديدة كل يوم.'),
           ('drop-glass', 'سجّل الكوب بضغطة', 'سجّل الماء من الإشعار نفسه دون فتح التطبيق، أو من الأزرار السريعة: كوب، قنينة، شاي، قهوة، عصير، مشروب طاقة.'),
           ('drop-thumbs', 'هدف يناسبك', 'يقترح التطبيق هدفًا يوميًا حسب وزنك ونشاطك، ويمكنك تعديله. وفيه خيار لمن لديه تعليمات طبية بتقليل السوائل.'),
           ('drop-jump', 'رمضان والأيام الحارة', 'في رمضان تصلك التذكيرات من الإفطار إلى السحور فقط. وإذا حددت مدينتك يزيد التذكير في الأيام الحارة.'),
           ('drop-tea', 'إحصائيات وشارات', 'تابع معدلك الأسبوعي والشهري، وسلسلة الأيام التي حققت فيها هدفك، واكسب الشارات.'),
           ('drop-coffee', 'ودجت ومزامنة', 'نسبتك اليوم على الشاشة الرئيسية، وتسجيل اختياري بحساب Apple أو Google ليُحفظ سجلك إن غيّرت جوالك.')],
    'en': [('drop-cool', 'Personas with attitude', 'Pick who nags you: The Strict Coach, Breaking News, The Roaster or Kind Mode. Fresh lines every day.'),
           ('drop-glass', 'Log a glass in one tap', 'Log water right from the notification, or use quick buttons for a glass, bottle, tea, coffee, juice or energy drink.'),
           ('drop-thumbs', 'A goal that fits you', 'A daily goal suggested from your weight and activity, fully editable, with an option for people on a fluid restriction.'),
           ('drop-jump', 'Heat and Ramadan', 'Extra reminders on hot days in your city, and a Ramadan mode that reminds you only between iftar and suhoor.'),
           ('drop-tea', 'Stats and badges', 'See your weekly and monthly average, your streak of goal days, and earn badges along the way.'),
           ('drop-coffee', 'Widget and sync', 'Today\u2019s progress on your Home Screen, plus optional sign-in with Apple or Google to keep your log on a new phone.')],
}
BENEFITS = {
    'ar': dict(h='لماذا يحتاج جسمك إلى الماء؟',
               intro='يدخل الماء في كل وظيفة تقريبًا في الجسم. وبحسب المراكز الأمريكية لمكافحة الأمراض (CDC) وMayo Clinic، يساعدك الماء على:',
               items=['الحفاظ على درجة حرارة الجسم طبيعية، خاصة في الحر وأثناء الرياضة.',
                      'تليين المفاصل وحمايتها.',
                      'حماية النخاع الشوكي والأنسجة الحساسة.',
                      'التخلص من الفضلات عبر البول والعرق.',
                      'نقل العناصر الغذائية إلى الخلايا.'],
               after='وعندما لا تشرب ما يكفي، قد تشعر بالعطش والتعب والصداع، ويصبح لون البول داكنًا. ويزداد الخطر في الحر وعند كبار السن والأطفال.',
               more='اعرف كم تحتاج يوميًا', src='المصادر'),
    'en': dict(h='Why your body needs water',
               intro='Water is involved in nearly everything your body does. According to the CDC and Mayo Clinic, water helps you:',
               items=['Keep a normal body temperature, especially in the heat and during exercise.',
                      'Lubricate and cushion your joints.',
                      'Protect your spinal cord and other sensitive tissues.',
                      'Get rid of wastes through urine and sweat.',
                      'Carry nutrients to your cells.'],
               after='When you don\u2019t drink enough, you may feel thirsty, tired or headachy, and your urine turns darker. The risk goes up in hot weather and for older adults and children.',
               more='How much do you need?', src='Sources'),
}
BEN_SRC = ('<a href="https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/">CDC: About Water and Healthier Drinks</a> · '
           '<a href="https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/water/art-20044256">Mayo Clinic: Water</a> · '
           '<a href="https://www.health.harvard.edu/staying-healthy/symptoms-of-dehydration-what-they-are-and-what-to-do-if-you-experience-them">Harvard Health: Symptoms of dehydration</a>')
HOW = {'ar': 'ماذا يفعل التطبيق؟', 'en': 'What the app does'}
TAGS = {
    'ar': ['مجاني', 'بالعربية والإنجليزية', 'ودجت للشاشة الرئيسية', 'دون تسجيل'],
    'en': ['Free', 'English and Arabic', 'Home Screen widget', 'No sign-up needed'],
}


def home_page(lang, gs):
    title, desc, h, p = HOME[lang]
    t = T[lang]
    mine = [g for g in gs if g['lang'] == lang]
    ld = ('<script type="application/ld+json">' + json.dumps({
        '@context': 'https://schema.org', '@type': 'MobileApplication', 'name': t['name'], 'operatingSystem': 'iOS',
        'applicationCategory': 'HealthApplication', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
        'url': STORE, 'image': BASE + 'img/icon.png', 'inLanguage': t['html']}, ensure_ascii=False) + '</script>')
    feats = ''.join(f'<div><img src="{BASE}img/{i}.webp" alt="" loading="lazy" width="72" height="72"><b>{esc(a)}</b><span>{esc(b)}</span></div>'
                    for i, a, b in FEATS[lang])
    tags = ''.join(f'<span>{esc(x)}</span>' for x in TAGS[lang])
    B = BENEFITS[lang]
    body = f"""<section class="hero"><div class="wrap">
<div><h1>{esc(h)}</h1><p>{esc(p)}</p><div class="badges">{tags}</div>
<div class="cta-row"><a class="btn" href="{STORE}"><span>{esc(t['cta'])}<small>{esc(t['iphone'])}</small></span></a></div></div>
<img class="mascot" src="{BASE}img/drop-hero.webp" alt="" width="300" height="400">
</div></section>
<section class="feat"><div class="wrap"><h2>{HOW[lang]}</h2><div class="feat-grid">{feats}</div></div></section>
<section class="ben"><div class="wrap"><h2>{esc(B['h'])}</h2><p>{esc(B['intro'])}</p><ul>{''.join('<li>' + esc(x) + '</li>' for x in B['items'])}</ul><p>{esc(B['after'])}</p>
<p><a class="btn ghost" href="{BASE + PREFIX[lang]}{'hasibat-kamiyat-almaa/' if lang == 'ar' else 'water-intake-calculator/'}">{esc(B['more'])}</a></p>
<div class="sources"><b>{esc(B['src'])}:</b> {BEN_SRC}</div></div></section>
<main class="wrap">
<h2>{t['guides']}</h2>
{card_list(mine)}
</main>"""
    alt = {l: PREFIX[l] for l in LANGS}
    return page(lang, title, desc, PREFIX[lang], body, ld, alt)


def build(out):
    gs = read_guides()
    for name in os.listdir(out):
        if name in ('.git', '_src', 'CNAME', 'README.md') or name.startswith('google'):
            continue
        p = os.path.join(out, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

    def w(rel, s):
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(s)

    for g in gs:
        w(g['path'] + 'index.html', guide_page(g, gs))
    for lang in LANGS:
        w(PREFIX[lang] + 'index.html', home_page(lang, gs))
    shutil.copytree(IMG, os.path.join(out, 'img'))
    w('.nojekyll', '')
    w('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n')
    today = date.today().isoformat()
    urls = [(BASE + PREFIX[l], today) for l in LANGS] + [(BASE + g['path'], g['date']) for g in gs]
    w('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      ''.join(f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n' for u, d in urls) + '</urlset>\n')
    w('404.html', page('ar', 'الصفحة غير موجودة', 'الصفحة غير موجودة', '404.html',
                       f'<main class="wrap"><h1>الصفحة غير موجودة</h1><p><a href="{BASE}">الرجوع للرئيسية</a></p></main>'))
    print(f'built {len(gs)} guides into {out}')


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else ROOT)
