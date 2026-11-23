#!/usr/bin/env python3
"""Genera páginas de enseñanza (plantilla v3 = ensenanzas/la-luz) a partir de specs JSON y
actualiza feed, sitemaps, /ensenanzas/, /predicadores/ y la página de cada predicador.
Uso (desde la raíz del repo):  python3 _tools/nueva-ensenanza.py _registro/datos/*.json
Después correr: python3 _tools/fechas-top10.py
Spec JSON: slug,title,id,date(AAAA-MM-DD),speaker("Profeta Hugo García"),speaker_slug,tag,card_tag,desc,lead,
 dur(segundos),keywords,items[html con <b>],sections[[titulo,[párrafos]]],verses[[ref,texto]],closing[párrafos],chips[refs]
Es idempotente (reconstruye listas desde el feed). El contenido de cada spec sale SOLO de Ask de YouTube (ver protocolo)."""
import json, re, sys, math, html, datetime, os
R = '.'
def rd(p): return open(os.path.join(R, p), encoding='utf-8').read()
def wr(p, s):
    os.makedirs(os.path.dirname(os.path.join(R, p)), exist_ok=True)
    open(os.path.join(R, p), 'w', encoding='utf-8').write(s)
DIAS = ['lunes','martes','miércoles','jueves','viernes','sábado','domingo']
MES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
MES3 = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
DIA3 = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']; MON3 = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
def d_of(s): return datetime.date.fromisoformat(s)
def largo(s): d = d_of(s); return f'{DIAS[d.weekday()]} {d.day} de {MES[d.month-1]} de {d.year}'
def corto(s): d = d_of(s); return f'{d.day} {MES3[d.month-1]}'
def esc(t): return html.escape(t, quote=False)
def slugify(t):
    import unicodedata
    t = unicodedata.normalize('NFD', t.lower()); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', t)).strip('-')
def plain(h): return html.unescape(re.sub(r'<[^>]+>', '', h))
def cut(t, n=150):
    t = plain(t)
    if len(t) <= n: return t
    return t[:n].rsplit(' ', 1)[0].rstrip(',;:. ') + '…'

specs = {}
for f in sys.argv[1:]:
    s = json.load(open(f, encoding='utf-8')); specs[s['slug']] = s

# ---------- registro de todas las páginas (desde feed + tarjetas existentes) ----------
feed = rd('ensenanzas/feed.xml')
idx = rd('ensenanzas/index.html')
cards = {m.group(1): m.group(0) for m in re.finditer(r'<a class="ec" href="\.\./ensenanzas/([^/]+)/">.*?</a>', idx, re.S)}
pages = {}
for m in re.finditer(r'<item><title>(.*?) — (.*?)</title><link>https://ebenezerantigua\.com/ensenanzas/([^/]+)/</link>.*?<pubDate>\w+, (\d+) (\w+) (\d+)', feed, re.S):
    t, sp, sl, dd, mm, yy = m.groups()
    pages[sl] = dict(slug=sl, title=html.unescape(t), speaker=html.unescape(sp), date=f'{yy}-{MON3.index(mm)+1:02d}-{int(dd):02d}')
for sl, s in specs.items():
    pages.setdefault(sl, dict(slug=sl, title=s['title'], speaker=s['speaker'], date=s['date']))
order = sorted(pages.values(), key=lambda p: p['date'], reverse=True)

# ---------- predicadores conocidos ----------
pidx = rd('predicadores/index.html')
speakers = {}  # nombre completo -> dict(slug,prefijo,nombre)
for m in re.finditer(r'<a class="ec pc" href="([^/]+)/"><small>(.*?)</small><b>(.*?)</b>', pidx):
    sl, pre, nom = m.groups(); speakers[f'{pre} {nom}'] = dict(slug=sl, pre=pre, nom=nom)
for s in specs.values():
    if s['speaker'] not in speakers:
        pre, nom = s['speaker'].split(' ', 1)
        speakers[s['speaker']] = dict(slug=s.get('speaker_slug') or slugify(nom), pre=pre, nom=nom)

def spk_link(name, up=2): return '../' * up + 'predicadores/' + speakers[name]['slug'] + '/'

# ---------- tarjetas ----------
def card(s, base):  # base: prefijo para rutas desde la página que lo contiene
    img = f'https://i.ytimg.com/vi/{s["id"]}/mqdefault.jpg'
    return (f'<a class="ec" href="{base}ensenanzas/{s["slug"]}/"><span class="ect"><img src="{img}" alt="{esc(s["title"])} — {s["speaker"]}" loading="lazy" width="320" height="180"></span>'
            f'<small>{esc(s["card_tag"])} · {corto(s["date"])}</small><b>{esc(s["title"])}</b><span class="ew">{s["speaker"]}</span><span class="ex">{esc(cut(s["lead"]))}</span></a>')
def card_from(slug, base):
    if slug in specs: return card(specs[slug], base)
    c = cards[slug]  # existente, ya relativo a /ensenanzas/ (../ensenanzas/..., ../fotos/...)
    if base == '../../':
        c = c.replace('href="../ensenanzas/', 'href="../../ensenanzas/').replace('src="../fotos/', 'src="../../fotos/')
    return c
def card_for(slug, base):
    # guarda en cards el HTML relativo a /ensenanzas/ para reusar
    return card_from(slug, base)

# ---------- página de enseñanza ----------
T = rd('ensenanzas/la-luz/index.html')
def build_page(s):
    t = T
    old_t = 'La Luz — Pastor Rodrigo Ordóñez'
    old_d = 'Resumen y artículo de la enseñanza «La Luz» del Pastor Rodrigo Ordóñez: ser luz en medio de la oscuridad de los tiempos finales. Ebenezer Antigua.'
    full = f'{s["title"]} — {s["speaker"]}'
    t = t.replace(old_t, full).replace(old_d, s['desc']).replace('9Gu2oq3Za-E', s['id']).replace('ensenanzas/la-luz/', f'ensenanzas/{s["slug"]}/')
    # JSON-LD
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
    j = json.loads(m.group(1))
    for e in j['@graph']:
        ty = e.get('@type')
        if ty == 'Article':
            e.update(headline=full, name=s['title'], description=s['desc'], datePublished=TODAY, dateModified=TODAY, keywords=s['keywords'], about=s['title'])
        elif ty == 'BreadcrumbList':
            e['itemListElement'][2]['name'] = s['title']
        elif ty == 'VideoObject':
            h = s['dur']; e.update(uploadDate=s['date'], duration=f'PT{h//3600}H{h%3600//60}M{h%60}S', description=s['desc'])
    t = t.replace(m.group(1), json.dumps(j, ensure_ascii=False))
    pre = t[:t.index('<main>')]; post = t[t.index('<footer'):]
    words = sum(len(plain(x).split()) for x in s['items'] + [p for _, ps in s['sections'] for p in ps] + s['closing'] + [v[1] for v in s['verses']])
    mins = max(3, math.ceil(words / 200))
    sl = largo(s['date'])
    toc = [('en-resumen', 'En resumen')] + [(slugify(n), n) for n, _ in s['sections']] + [('versiculos', 'Versículos citados'), ('cierre', 'Cierre de la reunión')]
    hero = (f'<main><section class="hero"><div class="w wide"><div class="hw yt"><div class="ht"><nav class="bc" aria-label="Migas de pan"><a href="../../">Inicio</a><a href="../../ensenanzas/">Enseñanzas</a><span>{esc(s["title"])}</span></nav>'
            f'<div class="eyebrow">{esc(s["tag"])} · Enseñanza</div><h1>{esc(s["title"])}</h1><div class="meta"><span><a class="pl" href="{spk_link(s["speaker"])}">{s["speaker"]}</a></span><span>·</span><span>{sl}</span><span>·</span><span>{mins} min de lectura</span></div></div>'
            f'<figure class="hf yt vid" id="video"><iframe src="https://www.youtube-nocookie.com/embed/{s["id"]}" title="{esc(full)}" allow="accelerometer; encrypted-media; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
            f'<figcaption>Video de la enseñanza, {sl}. <a href="https://www.youtube.com/watch?v={s["id"]}" target="_blank" rel="noopener">Ver en YouTube</a></figcaption></figure></div></div></section>\n')
    tocs = ('<div class="w art two"><aside class="tocs" aria-label="Índice de la enseñanza"><nav class="toc" aria-label="Contenido"><b>En esta página</b><ol>'
            + ''.join(f'<li><a href="#{a}">{esc(b)}</a></li>' for a, b in toc)
            + '</ol><div class="tp" aria-hidden="true"><span><i></i></span><small>Leído <em>0%</em></small></div></nav></aside>')
    chips = s['chips']; shown = chips[:6]
    sumv = '<div class="sum-v"><small>Pasajes citados</small>' + ''.join(f'<a href="#versiculos">{esc(c)}</a>' for c in shown) + (f'<a class="mas" href="#versiculos">+{len(chips)-6} más</a>' if len(chips) > 6 else '') + '</div>'
    lis = ''.join(f'<li style="--i:{i}"><span class="n">{i+1:02d}</span><p>{x}</p></li>' for i, x in enumerate(s['items']))
    art = (f'<article><p class="lead">{esc(s["lead"])}</p><section id="en-resumen" class="sum"><div class="sum-h"><span class="sum-k">Lectura rápida</span><h2>En resumen</h2><div class="sum-m"><span>{len(s["items"])} ideas clave</span><span>{mins} min de lectura</span><span>{len(chips)} pasajes citados</span></div></div><ol class="sum-l">{lis}</ol>{sumv}</section>')
    for n, ps in s['sections']:
        art += f'<section id="{slugify(n)}"><h2>{esc(n)}</h2>' + ''.join(f'<p>{p}</p>' for p in ps) + '</section>'
    art += '<section id="versiculos"><h2>Versículos citados</h2><ul class="vs">' + ''.join(f'<li><b>{esc(r)}</b> {x}</li>' for r, x in s['verses']) + '</ul></section>'
    art += '<section id="cierre"><h2>Cierre de la reunión</h2>' + ''.join(f'<p>{p}</p>' for p in s['closing']) + '</section>'
    # notas + CTA (idénticos a la plantilla)
    k = T.index('<p class="nota">'); k2 = T.index('<nav class="pn"')
    art += T[k:k2]
    i = order.index(next(p for p in order if p['slug'] == s['slug']))
    nxt = order[i-1] if i > 0 else None; prv = order[i+1] if i+1 < len(order) else None
    pn = '<nav class="pn" aria-label="Más enseñanzas">'
    if prv: pn += f'<a href="../../ensenanzas/{prv["slug"]}/"><small>← Anterior</small><b>{esc(prv["title"])}</b></a>'
    if nxt: pn += f'<a class="r" href="../../ensenanzas/{nxt["slug"]}/"><small>Siguiente →</small><b>{esc(nxt["title"])}</b></a>'
    pn += '</nav>'
    others = [p for p in order if p['slug'] != s['slug']]
    near = others[max(0, min(i-1, len(others)-3)):][:3] if i > 0 else others[:3]
    more = '<section class="more"><h2>Más enseñanzas</h2><div class="eg">' + ''.join(card_from(p['slug'], '../../') for p in near) + '</div><p class="all"><a class="b1" href="../../ensenanzas/">Ver todas las enseñanzas</a></p></section></article></div></main>\n'
    return pre + hero + tocs + art + pn + more + post

TODAY = '2026-11-23'
for s in specs.values():
    wr(f'ensenanzas/{s["slug"]}/index.html', build_page(s))

# ---------- feed ----------
for s in specs.values():
    if f'/ensenanzas/{s["slug"]}/</link>' in feed: continue
    d = d_of(s['date'])
    item = (f'<item><title>{esc(s["title"])} — {s["speaker"]}</title><link>https://ebenezerantigua.com/ensenanzas/{s["slug"]}/</link><guid isPermaLink="true">https://ebenezerantigua.com/ensenanzas/{s["slug"]}/</guid>'
            f'<pubDate>{DIA3[d.weekday()]}, {d.day:02d} {MON3[d.month-1]} {d.year} 12:00:00 -0600</pubDate><description>{esc(s["desc"])}</description></item>\n')
    pos = None
    for m in re.finditer(r'<item>.*?<pubDate>\w+, (\d+) (\w+) (\d+)', feed, re.S):
        if f'{m.group(3)}-{MON3.index(m.group(2))+1:02d}-{int(m.group(1)):02d}' < s['date']: pos = m.start(); break
    feed = feed[:pos] + item + feed[pos:] if pos is not None else feed.replace('</channel>', item + '</channel>')
wr('ensenanzas/feed.xml', feed)

# ---------- sitemaps ----------
sm = rd('sitemap.xml'); vs = rd('video-sitemap.xml')
for s in specs.values():
    u = f'https://ebenezerantigua.com/ensenanzas/{s["slug"]}/'
    if f'<loc>{u}</loc>' not in sm:
        sm = sm.replace('</urlset>', f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>0.8</priority></url>\n</urlset>')
    if f'<loc>{u}</loc>' not in vs:
        vs = vs.replace('</urlset>', f'<url><loc>{u}</loc><video:video><video:thumbnail_loc>https://i.ytimg.com/vi/{s["id"]}/hqdefault.jpg</video:thumbnail_loc><video:title>{esc(s["title"])} — {s["speaker"]}</video:title><video:description>{esc(s["desc"])}</video:description><video:player_loc>https://www.youtube.com/embed/{s["id"]}</video:player_loc><video:duration>{s["dur"]}</video:duration><video:publication_date>{s["date"]}T12:00:00-06:00</video:publication_date><video:family_friendly>yes</video:family_friendly><video:requires_subscription>no</video:requires_subscription><video:uploader info="https://www.youtube.com/@ebenezerantigua">Ebenezer Antigua</video:uploader></video:video></url>\n</urlset>')
for sp in speakers.values():
    u = f'https://ebenezerantigua.com/predicadores/{sp["slug"]}/'
    if f'<loc>{u}</loc>' not in sm: sm = sm.replace('</urlset>', f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>\n</urlset>')
wr('sitemap.xml', sm); wr('video-sitemap.xml', vs)

# ---------- /ensenanzas/ ----------
def sub_eg(h, cards_html): return re.sub(r'(<div class="eg">).*?(</div>)', lambda m: m.group(1) + cards_html + m.group(2), h, count=1, flags=re.S)
idx = sub_eg(idx, ''.join(card_from(p['slug'], '../') for p in order))
by = '<section class="byp"><h2>Por predicador</h2>'
for name, sp in sorted(speakers.items(), key=lambda kv: -sum(1 for p in order if p['speaker'] == kv[0])):
    ps = [p for p in order if p['speaker'] == name]
    if not ps: continue
    by += f'<h3><a href="../predicadores/{sp["slug"]}/">{name}</a></h3><ul>' + ''.join(f'<li><a href="../ensenanzas/{p["slug"]}/">{esc(p["title"])}</a> <small>{largo(p["date"])}</small></li>' for p in ps) + '</ul>'
idx = re.sub(r'<section class="byp">.*?</section>', lambda m: by + '</section>', idx, count=1, flags=re.S)
wr('ensenanzas/index.html', idx)

# ---------- /predicadores/ y cada predicador ----------
orden_sp = sorted([n for n in speakers if any(p['speaker'] == n for p in order)], key=lambda n: (-1 if False else 0, [p['date'] for p in order if p['speaker'] == n][0]), reverse=True)
pc = ''
for n in orden_sp:
    sp = speakers[n]; ps = [p for p in order if p['speaker'] == n]
    pc += f'<a class="ec pc" href="{sp["slug"]}/"><small>{sp["pre"]}</small><b>{sp["nom"]}</b><span class="ew">{len(ps)} enseñanza{"s" if len(ps)!=1 else ""}</span><span class="ex">Última: {esc(ps[0]["title"])} · {corto(ps[0]["date"])}</span></a>'
wr('predicadores/index.html', sub_eg(pidx, pc))
TPL = rd('predicadores/rodrigo-ordonez/index.html')
for n in orden_sp:
    sp = speakers[n]; ps = [p for p in order if p['speaker'] == n]
    path = f'predicadores/{sp["slug"]}/index.html'
    h = rd(path) if os.path.exists(os.path.join(R, path)) else None
    if h is None:  # crear desde plantilla (Rodrigo)
        h = TPL.replace('rodrigo-ordonez', sp['slug']).replace('Pastor Rodrigo Ordóñez', n).replace('Rodrigo Ordóñez', sp['nom']).replace('el pastor ' + sp['nom'], 'el ' + sp['pre'].lower() + ' ' + sp['nom']).replace('del pastor ' + sp['nom'], 'del ' + sp['pre'].lower() + ' ' + sp['nom'])
        h = re.sub(r'<div class="eyebrow">[^<]*· Enseñanzas</div>', f'<div class="eyebrow">{sp["pre"]} · Enseñanzas</div>', h)
        h = h.replace('"honorificPrefix": "Pastor"', f'"honorificPrefix": "{sp["pre"]}"')
    h = sub_eg(h, ''.join(card_from(p['slug'], '../../') for p in ps))
    h = re.sub(r'\d+ enseñanzas? publicadas?', f'{len(ps)} enseñanza{"s" if len(ps)!=1 else ""} publicada{"s" if len(ps)!=1 else ""}', h, count=1)
    # JSON-LD ItemList
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S); j = json.loads(m.group(1))
    for e in j['@graph']:
        if e.get('@type') == 'CollectionPage':
            e['mainEntity']['itemListElement'] = [dict(zip(['@type', 'position', 'url', 'name'], ['ListItem', i+1, f'https://ebenezerantigua.com/ensenanzas/{p["slug"]}/', p['title']])) for i, p in enumerate(ps)]
    h = h.replace(m.group(1), json.dumps(j, ensure_ascii=False))
    others = ''.join(f'<li><a href="../{speakers[o]["slug"]}/">{o}</a></li>' for o in orden_sp if o != n)
    h = re.sub(r'(<h2>Otros predicadores</h2><ul>).*?(</ul>)', lambda m: m.group(1) + others + m.group(2), h, count=1, flags=re.S)
    wr(path, h)
print('páginas:', len(specs), '· predicadores:', len(orden_sp), '· total enseñanzas:', len(order))
