#!/usr/bin/env python3
"""Actualiza sitemap.xml y video-sitemap.xml (una vez por semana, desde GitHub Actions).
Añade las páginas de /ensenanzas/ y /predicadores/ que falten, quita las que ya no existen
y pone lastmod = fecha del último commit que tocó cada archivo. No toca la home ni las demás URLs."""
import os, re, json, subprocess, datetime, html
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(R)
BASE = 'https://ebenezerantigua.com/'
TODAY = datetime.date.today().isoformat()
def lastmod(path):
    try:
        d = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path], capture_output=True, text=True).stdout.strip()
        return d or TODAY
    except Exception: return TODAY
def indexable(p):
    h = open(p, encoding='utf-8').read(6000).lower()
    return 'noindex' not in h and 'http-equiv="refresh"' not in h
pages = {}
for top in ('ensenanzas', 'predicadores'):
    for d, _, fs in os.walk(top):
        if 'index.html' in fs:
            p = os.path.join(d, 'index.html')
            if indexable(p): pages[BASE + d.replace(os.sep, '/') + '/'] = p
pages[BASE + 'ensenanzas/'] = 'ensenanzas/index.html'
sm = open('sitemap.xml', encoding='utf-8').read()
def prio(u):
    if '/pagina/' in u: return '0.5'
    if re.search(r'/ensenanzas/[^/]+/$', u) and not re.search(r'/ensenanzas/(discipulados|otros)/$', u): return '0.8'
    if u.endswith('/predicadores/'): return '0.7'
    return '0.7' if '/predicadores/' in u else '0.6'
cur = set(re.findall(r'<loc>([^<]+)</loc>', sm))
managed = lambda u: u.startswith(BASE + 'ensenanzas/') or u.startswith(BASE + 'predicadores/')
add = rm = 0
for u in sorted(cur):
    if managed(u) and u not in pages:
        sm = re.sub(r'<url><loc>' + re.escape(u) + r'</loc>.*?</url>\n?', '', sm, flags=re.S); rm += 1
for u, p in pages.items():
    lm = lastmod(p)
    if u in cur:
        sm = re.sub(r'(<loc>' + re.escape(u) + r'</loc><lastmod>)[^<]*(</lastmod>)', r'\g<1>' + lm + r'\g<2>', sm, count=1)
    else:
        sm = sm.replace('</urlset>', f'<url><loc>{u}</loc><lastmod>{lm}</lastmod><priority>{prio(u)}</priority></url>\n</urlset>'); add += 1
open('sitemap.xml', 'w', encoding='utf-8').write(sm)
vs = open('video-sitemap.xml', encoding='utf-8').read(); vadd = 0
esc = lambda x: html.escape(x, quote=False)
for f in sorted(os.listdir('_registro/datos')):
    s = json.load(open('_registro/datos/' + f, encoding='utf-8'))
    u = f'{BASE}ensenanzas/{s["slug"]}/'
    if u in vs or not s.get('id') or u not in pages: continue
    vs = vs.replace('</urlset>', f'<url><loc>{u}</loc><video:video><video:thumbnail_loc>https://i.ytimg.com/vi/{s["id"]}/hqdefault.jpg</video:thumbnail_loc><video:title>{esc(s["title"])} — {esc(s["speaker"])}</video:title><video:description>{esc(s["desc"])}</video:description><video:player_loc>https://www.youtube.com/embed/{s["id"]}</video:player_loc><video:duration>{s["dur"]}</video:duration><video:publication_date>{s["date"]}T12:00:00-06:00</video:publication_date><video:family_friendly>yes</video:family_friendly><video:requires_subscription>no</video:requires_subscription><video:uploader info="https://www.youtube.com/@ebenezerantigua">Ebenezer Antigua</video:uploader></video:video></url>\n</urlset>'); vadd += 1
open('video-sitemap.xml', 'w', encoding='utf-8').write(vs)
print(f'sitemap: +{add} -{rm} · video-sitemap: +{vadd}')
