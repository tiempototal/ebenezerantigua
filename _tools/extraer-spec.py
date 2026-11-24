#!/usr/bin/env python3
"""Reconstruye _registro/datos/<slug>.json desde una página ya publicada (para artículos hechos a mano antes del generador).
Uso: python3 _tools/extraer-spec.py slug [slug...]   (desde la raíz del repo)"""
import re, json, sys, html
def un(x): return html.unescape(x)
for slug in sys.argv[1:]:
    h = open(f'ensenanzas/{slug}/index.html', encoding='utf-8').read()
    j = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S).group(1))
    art = next(e for e in j['@graph'] if e.get('@type') == 'Article'); vid = next((e for e in j['@graph'] if e.get('@type') == 'VideoObject'), {})
    title = un(re.search(r'<h1>(.*?)</h1>', h).group(1)); speaker = art['headline'].split(' — ', 1)[1]
    iid = (re.search(r'youtube-nocookie\.com/embed/([\w-]+)', h) or [None, ''])[1]
    tag = un(re.search(r'<div class="eyebrow">(.*?) · ', h).group(1))
    dur = vid.get('duration', 'PT0H0M0S'); mm = re.match(r'PT(\d+)H(\d+)M(\d+)S', dur); secs = int(mm.group(1))*3600+int(mm.group(2))*60+int(mm.group(3)) if mm else 0
    lead = un(re.search(r'<p class="lead">(.*?)</p>', h, re.S).group(1))
    items = [re.sub(r'\s+', ' ', x) for x in re.findall(r'<li style="--i:\d+"><span class="n">\d+</span><p>(.*?)</p></li>', h, re.S)]
    chips = [un(x) for x in re.findall(r'<div class="sum-v">.*?</div>', h, re.S)[0:1] and re.findall(r'<a href="#versiculos">(.*?)</a>', re.findall(r'<div class="sum-v">.*?</div>', h, re.S)[0])]
    sections = []
    for m in re.finditer(r'<section id="([^"]+)"><h2>(.*?)</h2>(.*?)</section>', h, re.S):
        sid, n, body = m.groups()
        if sid in ('versiculos', 'cierre'): continue
        sections.append([un(n), [(x[3:-4] if x.startswith('<p>') else x) for x in re.findall(r'<p>.*?</p>|<ul>.*?</ul>|<ol>.*?</ol>|<blockquote>.*?</blockquote>', body, re.S)]])
    verses = [[un(r), x] for r, x in re.findall(r'<li><b>(.*?)</b> (.*?)</li>', re.search(r'<section id="versiculos">.*?</section>', h, re.S).group(0), re.S)]
    closing = re.findall(r'<p>(.*?)</p>', re.search(r'<section id="cierre">.*?</section>', h, re.S).group(0), re.S)
    allc = re.search(r'"keywords": ?"(.*?)"', h)
    spec = dict(slug=slug, title=title, id=iid, date=vid.get('uploadDate', ''), speaker=speaker, tag=tag, card_tag=tag, dur=secs, cat='ensenanza', desc=art['description'],
                keywords=art.get('keywords', ''), lead=lead, items=items, chips=[v[0] for v in verses], sections=sections, verses=verses, closing=closing)
    json.dump(spec, open(f'_registro/datos/{slug}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(slug, '| items', len(items), '| secciones', len(sections), '| versículos', len(verses), '| id', iid, '| date', spec['date'], '| dur', secs, '| tag', tag)
