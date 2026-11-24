#!/usr/bin/env python3
"""Genera páginas de enseñanza (plantilla v3 = ensenanzas/la-luz) a partir de specs JSON y
actualiza feed, sitemaps, /ensenanzas/, /predicadores/ y la página de cada predicador.
Uso (desde la raíz del repo):  python3 _tools/nueva-ensenanza.py _registro/datos/*.json
Después correr: python3 _tools/fechas-top10.py
Spec JSON: slug,title,id,date(AAAA-MM-DD),speaker("Profeta Hugo García"),speaker_slug,tag,card_tag,desc,lead,
 dur(segundos),keywords,items[html con <b>],sections[[titulo,[párrafos]]],verses[[ref,texto]],closing[párrafos],chips[refs]
Campos extra: cat ("ensenanza" por defecto | "discipulado" | "otro"). Registro en _registro/paginas.json.
Es idempotente (reconstruye listas desde el registro). El contenido de cada spec sale SOLO de Ask de YouTube (ver protocolo)."""
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


import unicodedata
PAGE = 12                       # tarjetas por página en listados
PAGE_P = 18                     # tarjetas por página en la página de cada predicador
TODAY = os.environ.get('HOY', '2026-11-23')
CATS = {'discipulado': dict(label='Discipulados', slug='discipulados', one='Discipulado', lead='Mensajes de los discipulados de Ebenezer Antigua: video, resumen y versículos citados.'),
        'otro': dict(label='Otros mensajes', slug='otros', one='Mensaje', lead='Otros mensajes compartidos en Ebenezer Antigua: video, resumen y versículos citados.')}
PHOTOS = {'hugo-garcia': ('hugo-azul.jpg', '50% 20%'), 'debora-de-garcia': ('debora-hd.jpg', '50% 12%'), 'rodrigo-ordonez': ('rodrigo-hd.jpg', '50% 20%'),
          'jose-carlos-mendez': ('mendez-hd.jpg', '50% 15%'), 'estuardo-soto': ('cruz-hd.jpg', '30% 12%'), 'gustavo-hernandez': ('gustavo-hd.jpg', '48% 22%')}
# Título que se MUESTRA en tarjetas y encabezados (el nombre guardado en cada enseñanza no cambia)
TITULOS = {'hugo-garcia': 'Profeta y Pastor', 'rodrigo-ordonez': 'Pastor y Maestro'}
specs = {}
for f in sys.argv[1:]:
    s = json.load(open(f, encoding='utf-8')); s.setdefault('cat', 'ensenanza'); specs[s['slug']] = s

feed = rd('ensenanzas/feed.xml')
idx = rd('ensenanzas/index.html')
IDX_PRE = re.sub(r'<link rel="(?:prev|next)" href="[^"]*">', '', idx[:idx.index('<main>')]); IDX_POST = idx[idx.index('<aside class="cta">'):].replace('<script src="/ensenanzas/buscar.js" defer></script>', '')

# ---------- registro de páginas (fuente de verdad) ----------
REG = os.path.join(R, '_registro/paginas.json')
if os.path.exists(REG):
    reg = {p['slug']: p for p in json.load(open(REG, encoding='utf-8'))}
else:  # migración única: feed + tarjetas existentes
    reg = {}
    cards0 = {m.group(1): m.group(0) for m in re.finditer(r'<a class="ec" href="\.\./ensenanzas/([^/]+)/">.*?</a>', idx, re.S)}
    for m in re.finditer(r'<item><title>(.*?) — (.*?)</title><link>https://ebenezerantigua\.com/ensenanzas/([^/]+)/</link>.*?<pubDate>\w+, (\d+) (\w+) (\d+)', feed, re.S):
        t, sp, sl, dd, mm, yy = m.groups(); c = cards0.get(sl, '')
        g = lambda rx: (re.search(rx, c, re.S).group(1) if re.search(rx, c, re.S) else '')
        small = html.unescape(g(r'<small>(.*?)</small>')); tag = small.split(' · ')[0]
        thumb = g(r'<img src="([^"]*)"').replace('../', '', 1) if g(r'<img src="([^"]*)"').startswith('../') else g(r'<img src="([^"]*)"')
        reg[sl] = dict(slug=sl, title=html.unescape(t), speaker=html.unescape(sp), date=f'{yy}-{MON3.index(mm)+1:02d}-{int(dd):02d}', cat='ensenanza',
                       card_tag=tag, thumb=thumb, ex=html.unescape(g(r'<span class="ex">(.*?)</span>')), id='')
for s in specs.values():
    reg[s['slug']] = dict(slug=s['slug'], title=s['title'], speaker=s['speaker'], date=s['date'], cat=s['cat'], card_tag=s['card_tag'],
                          thumb=f'https://i.ytimg.com/vi/{s["id"]}/mqdefault.jpg', ex=cut(s['lead']), id=s['id'])
def bycat(c): return sorted([p for p in reg.values() if p['cat'] == c], key=lambda p: (p['date'], p['slug']), reverse=True)
order = bycat('ensenanza')
def save_reg():
    os.makedirs(os.path.dirname(REG), exist_ok=True)
    json.dump(sorted(reg.values(), key=lambda p: (p['cat'], p['date'], p['slug']), reverse=True), open(REG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
save_reg()

# ---------- predicadores oficiales ----------
pidx = rd('predicadores/index.html')
speakers = {}
for m in re.finditer(r'<a class="ec pc" href="([^/]+)/"><small>(.*?)</small><b>(.*?)</b>', pidx):
    sl, pre, nom = m.groups(); pre0 = pre.split(' y ')[0]; speakers[f'{pre0} {nom}'] = dict(slug=sl, pre=pre0, nom=nom, tit=TITULOS.get(sl, pre))
for s in specs.values():
    if s['cat'] == 'ensenanza' and s['speaker'] not in speakers:
        pre, nom = s['speaker'].split(' ', 1)
        speakers[s['speaker']] = dict(slug=s.get('speaker_slug') or slugify(nom), pre=pre, nom=nom, tit=TITULOS.get(s.get('speaker_slug') or slugify(nom), pre))
def spk_html(name, up=2):
    if name in speakers: return f'<a class="pl" href="{"../"*up}predicadores/{speakers[name]["slug"]}/">{name}</a>'
    return esc(name)

# ---------- tarjetas ----------
def card(p, root):  # root = prefijo hacia la raíz del sitio
    th = p['thumb'] if p['thumb'].startswith('http') else root + p['thumb']
    tag = esc(p['card_tag']) + (f' · {corto(p["date"])}' if p['cat'] == 'ensenanza' else '')
    return (f'<a class="ec" href="{root}ensenanzas/{p["slug"]}/"><span class="ect"><img src="{th}" alt="{esc(p["title"])} — {esc(p["speaker"])}" loading="lazy" width="320" height="180"></span>'
            f'<small>{tag}</small><b>{esc(p["title"])}</b><span class="ew">{esc(p["speaker"])}</span><span class="ex">{esc(p["ex"])}</span></a>')

# ---------- página de enseñanza ----------
T = rd('ensenanzas/la-luz/index.html')
def build_page(s):
    t = T; cat = s['cat']; ci = CATS.get(cat)
    old_t = 'La Luz — Pastor Rodrigo Ordóñez'
    old_d = 'Resumen y artículo de la enseñanza «La Luz» del Pastor Rodrigo Ordóñez: ser luz en medio de la oscuridad de los tiempos finales. Ebenezer Antigua.'
    full = f'{s["title"]} — {s["speaker"]}'
    t = t.replace(old_t, full).replace(old_d, s['desc']).replace('9Gu2oq3Za-E', s['id']).replace('ensenanzas/la-luz/', f'ensenanzas/{s["slug"]}/')
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
    j = json.loads(m.group(1))
    for e in j['@graph']:
        ty = e.get('@type')
        if ty == 'Article':
            e.update(headline=full, name=s['title'], description=s['desc'], datePublished=TODAY, dateModified=TODAY, keywords=s['keywords'], about=s['title'])
        elif ty == 'BreadcrumbList':
            it = e['itemListElement'][:2]
            if ci: it.append({'@type': 'ListItem', 'position': 3, 'name': ci['label'], 'item': f'https://ebenezerantigua.com/ensenanzas/{ci["slug"]}/'})
            it.append({'@type': 'ListItem', 'position': len(it) + 1, 'name': s['title'], 'item': f'https://ebenezerantigua.com/ensenanzas/{s["slug"]}/'})
            e['itemListElement'] = it
        elif ty == 'VideoObject':
            h = s['dur']; e.update(uploadDate=s['date'], duration=f'PT{h//3600}H{h%3600//60}M{h%60}S', description=s['desc'])
    t = t.replace(m.group(1), json.dumps(j, ensure_ascii=False))
    pre = t[:t.index('<main>')]; post = t[t.index('<footer'):]
    words = sum(len(plain(x).split()) for x in s['items'] + [p for _, ps in s['sections'] for p in ps] + s['closing'] + [v[1] for v in s['verses']])
    mins = max(3, math.ceil(words / 200))
    sl = largo(s['date'])
    toc = [('en-resumen', 'En resumen')] + [(slugify(n), n) for n, _ in s['sections']] + [('versiculos', 'Versículos citados'), ('cierre', 'Cierre de la reunión')]
    bc = '<a href="../../">Inicio</a><a href="../../ensenanzas/">Enseñanzas</a>' + (f'<a href="../../ensenanzas/{ci["slug"]}/">{ci["label"]}</a>' if ci else '') + f'<span>{esc(s["title"])}</span>'
    meta = f'<span>{spk_html(s["speaker"])}</span>' + (f'<span>·</span><span>{sl}</span>' if not ci else '') + f'<span>·</span><span>{mins} min de lectura</span>'
    cap = (f'Video de la enseñanza, {sl}. ' if not ci else 'Video del mensaje. ')
    hero = (f'<main><section class="hero"><div class="w wide"><div class="hw yt"><div class="ht"><nav class="bc" aria-label="Migas de pan">{bc}</nav>'
            f'<div class="eyebrow">{esc(s["tag"])} · {ci["one"] if ci else "Enseñanza"}</div><h1>{esc(s["title"])}</h1><div class="meta">{meta}</div></div>'
            f'<figure class="hf yt vid" id="video"><iframe src="https://www.youtube-nocookie.com/embed/{s["id"]}" title="{esc(full)}" allow="accelerometer; encrypted-media; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
            f'<figcaption>{cap}<a href="https://www.youtube.com/watch?v={s["id"]}" target="_blank" rel="noopener">Ver en YouTube</a></figcaption></figure></div></div></section>\n')
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
    k = T.index('<p class="nota">'); k2 = T.index('<nav class="pn"')
    art += T[k:k2]
    lst = bycat(cat); i = next(n for n, p in enumerate(lst) if p['slug'] == s['slug'])
    nxt = lst[i-1] if i > 0 else None; prv = lst[i+1] if i+1 < len(lst) else None
    pn = '<nav class="pn" aria-label="Más enseñanzas">'
    if prv: pn += f'<a href="../../ensenanzas/{prv["slug"]}/"><small>← Anterior</small><b>{esc(prv["title"])}</b></a>'
    if nxt: pn += f'<a class="r" href="../../ensenanzas/{nxt["slug"]}/"><small>Siguiente →</small><b>{esc(nxt["title"])}</b></a>'
    pn += '</nav>'
    others = [p for p in lst if p['slug'] != s['slug']]
    near = others[max(0, min(i-1, len(others)-3)):][:3] if i > 0 else others[:3]
    back = f'../../ensenanzas/{ci["slug"]}/' if ci else '../../ensenanzas/'
    more = (f'<section class="more"><h2>{"Más enseñanzas" if not ci else "Más en " + ci["label"]}</h2><div class="eg">' + ''.join(card(p, '../../') for p in near)
            + f'</div><p class="all"><a class="b1" href="{back}">Ver {"todas las enseñanzas" if not ci else "todo en " + ci["label"]}</a></p></section></article></div></main>\n')
    return pre + hero + tocs + art + pn + more + post

for s in specs.values():
    wr(f'ensenanzas/{s["slug"]}/index.html', build_page(s))

# ---------- feed (solo enseñanzas) ----------
for s in specs.values():
    if s['cat'] != 'ensenanza' or f'/ensenanzas/{s["slug"]}/</link>' in feed: continue
    d = d_of(s['date'])
    item = (f'<item><title>{esc(s["title"])} — {s["speaker"]}</title><link>https://ebenezerantigua.com/ensenanzas/{s["slug"]}/</link><guid isPermaLink="true">https://ebenezerantigua.com/ensenanzas/{s["slug"]}/</guid>'
            f'<pubDate>{DIA3[d.weekday()]}, {d.day:02d} {MON3[d.month-1]} {d.year} 12:00:00 -0600</pubDate><description>{esc(s["desc"])}</description></item>\n')
    pos = None
    for m in re.finditer(r'<item>.*?<pubDate>\w+, (\d+) (\w+) (\d+)', feed, re.S):
        if f'{m.group(3)}-{MON3.index(m.group(2))+1:02d}-{int(m.group(1)):02d}' < s['date']: pos = m.start(); break
    feed = feed[:pos] + item + feed[pos:] if pos is not None else feed.replace('</channel>', item + '</channel>')
wr('ensenanzas/feed.xml', feed)

# ---------- listados con paginación ----------
def shift(h, e): return re.sub(r'(href|src)="\.\./', lambda m: f'{m.group(1)}="' + '../' * (e + 1), h) if e else h
def pager(base_rel, n, total):  # base_rel: ruta de la 1.ª página desde la actual; páginas numeradas bajo pagina/N/
    if total <= 1: return ''
    def href(k): return base_rel if k == 1 else (base_rel + f'pagina/{k}/')
    out = '<nav class="pager" aria-label="Páginas de enseñanzas">'
    if n > 1: out += f'<a rel="prev" href="{href(n-1)}">← Más recientes</a>'
    out += ''.join((f'<span class="cur" aria-current="page">{k}</span>' if k == n else f'<a href="{href(k)}">{k}</a>') for k in range(1, total + 1))
    if n < total: out += f'<a rel="next" href="{href(n+1)}">Más antiguas →</a>'
    return out + '</nav>'
HS_CSS = ('<style id="hs">.hero.hs{padding:1.5rem 0 1.3rem}.hero.hs .hg{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,540px);gap:2rem 3rem;align-items:center}'
          '.hero.hs .hgr .lead.sm{display:block;color:rgba(243,230,210,.72)!important;background:none!important;border:0!important;box-shadow:none!important;padding:0!important;margin:0 0 .8rem!important;max-width:none!important;font-size:.78rem!important;line-height:1.45!important;font-family:inherit}'
          '.hero.hs .sbar{margin:0}.hero.hs .sbar label{color:#f0cf7a}.hero.hs .sbar input{flex:1 1 100%;max-width:none;height:2.7rem}.hero.hs .sbar .sc{color:#f3e6d2}.hero.hs .sbar .sc:empty{display:none}'
          '.hero.hs .meta{flex-wrap:nowrap;white-space:nowrap}.hero.hs+.art.idx{padding-top:0}.hero.hs+.art.idx #slist>.eg:first-child{margin-top:1.3rem}'
          '@media(max-width:900px){.hero.hs .hg{grid-template-columns:1fr;gap:1rem}.hero.hs .meta{flex-wrap:wrap;white-space:normal}}</style>')

def list_page(items, n, total, dirp, ext, h1, eyebrow, lead, crumbs, extra, title, desc):
    """dirp: carpeta de la 1.ª página (p.ej. 'ensenanzas'); ext: niveles extra de profundidad de ESTA página respecto de ensenanzas/ ."""
    url = f'https://ebenezerantigua.com/{dirp}/' + ('' if n == 1 else f'pagina/{n}/')
    e = ext + (0 if n == 1 else 2); root = '../' * (1 + e)
    base_rel = '../' * (0 if n == 1 else 2) + ('' if n == 1 else '')
    first = './' if n == 1 else '../../'
    chunk = items[(n-1)*PAGE:n*PAGE]
    pre = IDX_PRE.replace('Enseñanzas y prédicas: resúmenes y videos | Ebenezer Antigua', title + (f' · página {n}' if n > 1 else ''))
    old_d = 'Todas las enseñanzas de Ebenezer Antigua (Jocotenango, Antigua Guatemala): video de cada prédica, resumen, puntos principales y versículos citados.'
    pre = pre.replace(old_d, desc).replace('"https://ebenezerantigua.com/ensenanzas/"', f'"{url}"', 4)
    pre = pre.replace(f'content="https://ebenezerantigua.com/ensenanzas/"', f'content="{url}"')
    pre = pre.replace('<link rel="canonical" href="https://ebenezerantigua.com/ensenanzas/">', f'<link rel="canonical" href="{url}">')
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', pre, re.S); j = json.loads(m.group(1))
    for g_ in j['@graph']:
        if g_.get('@type') == 'CollectionPage':
            g_.update(url=url, name=h1, description=desc); g_['@id'] = url + '#page'
            g_['mainEntity']['itemListElement'] = [dict(zip(['@type', 'position', 'url', 'name'], ['ListItem', (n-1)*PAGE+i+1, f'https://ebenezerantigua.com/ensenanzas/{p["slug"]}/', p['title']])) for i, p in enumerate(chunk)]
        if g_.get('@type') == 'BreadcrumbList':
            g_['itemListElement'] = [{'@type': 'ListItem', 'position': i+1, 'name': nm, 'item': it} for i, (nm, it) in enumerate([('Inicio', 'https://ebenezerantigua.com/')] + [(c[0], c[1]) for c in crumbs])]
    pre = pre.replace(m.group(1), json.dumps(j, ensure_ascii=False))
    pre = re.sub(r'(<link rel="alternate" hreflang="es-GT" href=")[^"]*(">)', lambda mm: mm.group(1) + url + mm.group(2), pre)
    pre = re.sub(r'(hreflang="x-default" href=")[^"]*(">)', lambda mm: mm.group(1) + url + mm.group(2), pre)
    if total > 1:
        extra_links = ''
        if n > 1: extra_links += f'<link rel="prev" href="https://ebenezerantigua.com/{dirp}/' + ('' if n == 2 else f'pagina/{n-1}/') + '">'
        if n < total: extra_links += f'<link rel="next" href="https://ebenezerantigua.com/{dirp}/pagina/{n+1}/">'
        pre = pre.replace('</head>', extra_links + '</head>', 1)
    pre = shift(pre, e); post = shift(IDX_POST, e)
    bcs = f'<a href="{root}">Inicio</a>' + ''.join(f'<a href="{c[2](e)}">{c[0]}</a>' for c in crumbs[:-1]) + f'<span>{crumbs[-1][0]}</span>'
    hl = (f'<nav class="bc" aria-label="Migas de pan">{bcs}</nav><div class="eyebrow">{eyebrow}</div><h1>{h1}{f" — página {n}" if n > 1 else ""}</h1>'
          f'<div class="meta"><span>{len(items)} publicado{"s" if len(items)!=1 else ""} · video, resumen y versículos de cada uno</span>' + (f'<span>·</span><span><a class="pl" href="{root}predicadores/">Ver por predicador</a></span>' if dirp == 'ensenanzas' else '') + '</div>')
    busc = ('<form class="sbar" role="search" onsubmit="return false"><label for="q">Buscar en todas las enseñanzas</label><input id="q" type="search" placeholder="Busca por tema, predicador o serie…" autocomplete="off" enterkeyhint="search"><span class="sc" id="sc" aria-live="polite"></span></form>') if dirp == 'ensenanzas' else ''
    if dirp == 'ensenanzas':
        hero = (HS_CSS + '<main><section class="hero sm hs"><div class="w wide"><div class="hg"><div class="hgl">' + hl + '</div><div class="hgr">'
                + (f'<p class="lead sm">{lead}</p>' if n == 1 else '') + busc + '</div></div></div></section>\n')
        sres = '<div class="eg" id="sres" hidden></div>'
        lead_html = ''
    else:
        hero = f'<main><section class="hero sm"><div class="w wide">{hl}</div></section>\n'
        sres = ''
        lead_html = f'<p class="lead sm">{lead}</p>' if n == 1 else ''
    body = (f'<div class="w art idx"><section>' + lead_html + sres + '<div id="slist"><div class="eg">' + ''.join(card(p, root) for p in chunk) + '</div>'
            + pager(first, n, total) + '</div></section>' + (extra(e, root) if n == 1 else ''))
    if dirp == 'ensenanzas': post = post.replace('</body>', '<script src="/ensenanzas/buscar.js" defer></script></body>')
    return pre + hero + body + post

def write_list(items, dirp, ext, h1, eyebrow, lead, crumbs, extra, title, desc):
    total = max(1, math.ceil(len(items) / PAGE)); made = []
    for n in range(1, total + 1):
        path = f'{dirp}/' + ('' if n == 1 else f'pagina/{n}/') + 'index.html'
        wr(path, list_page(items, n, total, dirp, ext, h1, eyebrow, lead, crumbs, extra, title, desc)); made.append(path)
    # limpiar páginas sobrantes
    pdir = os.path.join(R, dirp, 'pagina')
    if os.path.isdir(pdir):
        import shutil
        for d in os.listdir(pdir):
            if d.isdigit() and int(d) > total: shutil.rmtree(os.path.join(pdir, d))
    return total

def main_extra(e, root):
    out = ''
    cats = [(c, bycat(c)) for c in CATS if bycat(c)]
    if cats:
        out += '<section class="cats"><h2>Más contenido</h2><div class="eg">' + ''.join(
            f'<a class="ec" href="{root}ensenanzas/{CATS[c]["slug"]}/"><small>Categoría</small><b>{CATS[c]["label"]}</b><span class="ew">{len(l)} publicado{"s" if len(l)!=1 else ""}</span><span class="ex">{CATS[c]["lead"]}</span></a>' for c, l in cats) + '</div></section>'
    out += '<section class="byp"><h2>Por predicador</h2><ul>'
    for name, sp in sorted(speakers.items(), key=lambda kv: -sum(1 for p in reg.values() if p['speaker'] == kv[0])):
        k = sum(1 for p in reg.values() if p['speaker'] == name)
        if k: out += f'<li><a href="{root}predicadores/{sp["slug"]}/">{name}</a> <small>{k} publicada{"s" if k!=1 else ""}</small></li>'
    return out + '</ul></section>'

E_URL = 'https://ebenezerantigua.com/ensenanzas/'
tot_main = write_list(order, 'ensenanzas', 0, 'Enseñanzas', 'Año del Deleite 2026',
    'Cada enseñanza que se comparte en Ebenezer Antigua queda aquí: el video para verlo en esta página, un resumen de lo que se expuso y los versículos que se citaron. Se agregan nuevas enseñanzas cada semana y las anteriores permanecen disponibles.',
    [('Enseñanzas', E_URL, None)], main_extra, 'Enseñanzas y prédicas: resúmenes y videos | Ebenezer Antigua',
    'Todas las enseñanzas de Ebenezer Antigua (Jocotenango, Antigua Guatemala): video de cada prédica, resumen, puntos principales y versículos citados.')
# el listado principal enlaza a "Ver por predicador" en su hero original; se mantiene en la lead via predicadores/
tots = {'ensenanza': tot_main}
for c, ci in CATS.items():
    lst = bycat(c)
    if not lst: continue
    tots[c] = write_list(lst, f'ensenanzas/{ci["slug"]}', 1, ci['label'], f'Enseñanzas · {ci["label"]}', ci['lead'],
        [('Enseñanzas', E_URL, lambda e: '../' * (e) + ('' if e == 0 else '')), (ci['label'], E_URL + ci['slug'] + '/', None)], lambda e, root: '',
        f'{ci["label"]}: resúmenes y videos | Ebenezer Antigua', f'{ci["lead"]} Ebenezer Antigua, Jocotenango, Antigua Guatemala.')

# ---------- índice de búsqueda (todas las categorías; sin fechas) ----------
def _abs(t): return t if t.startswith('http') else '/' + t
wr('ensenanzas/buscar.json', json.dumps([dict(s=p['slug'], t=p['title'], p=p['speaker'], g=p['card_tag'], e=p['ex'], i=_abs(p['thumb'])) for p in sorted(reg.values(), key=lambda p: (p['date'], p['slug']), reverse=True)], ensure_ascii=False, separators=(',', ':')))

# ---------- sitemaps ----------
sm = rd('sitemap.xml'); vs = rd('video-sitemap.xml')
def add_sm(u, pr):
    global sm
    if f'<loc>{u}</loc>' not in sm: sm = sm.replace('</urlset>', f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>\n</urlset>')
for s in specs.values():
    u = f'https://ebenezerantigua.com/ensenanzas/{s["slug"]}/'
    add_sm(u, '0.8')
    if f'<loc>{u}</loc>' not in vs:
        vs = vs.replace('</urlset>', f'<url><loc>{u}</loc><video:video><video:thumbnail_loc>https://i.ytimg.com/vi/{s["id"]}/hqdefault.jpg</video:thumbnail_loc><video:title>{esc(s["title"])} — {esc(s["speaker"])}</video:title><video:description>{esc(s["desc"])}</video:description><video:player_loc>https://www.youtube.com/embed/{s["id"]}</video:player_loc><video:duration>{s["dur"]}</video:duration><video:publication_date>{s["date"]}T12:00:00-06:00</video:publication_date><video:family_friendly>yes</video:family_friendly><video:requires_subscription>no</video:requires_subscription><video:uploader info="https://www.youtube.com/@ebenezerantigua">Ebenezer Antigua</video:uploader></video:video></url>\n</urlset>')
for c, tcount in tots.items():
    base = E_URL + ('' if c == 'ensenanza' else CATS[c]['slug'] + '/')
    if c != 'ensenanza': add_sm(base, '0.6')
    for n in range(2, tcount + 1): add_sm(base + f'pagina/{n}/', '0.5')
for sp in speakers.values(): add_sm(f'https://ebenezerantigua.com/predicadores/{sp["slug"]}/', '0.7')
wr('sitemap.xml', sm); wr('video-sitemap.xml', vs)

# ---------- /predicadores/ y cada predicador ----------
def sub_eg(h, cards_html): return re.sub(r'(<div class="eg">).*?(</div>)', lambda m: m.group(1) + cards_html + m.group(2), h, count=1, flags=re.S)
def mine(n): return sorted([p for p in reg.values() if p['speaker'] == n], key=lambda p: (p['date'], p['slug']), reverse=True)
orden_sp = sorted([n for n in speakers if mine(n)], key=lambda n: mine(n)[0]['date'], reverse=True)
pc = ''
for n in orden_sp:
    sp = speakers[n]; ps = mine(n)
    pc += f'<a class="ec pc" href="{sp["slug"]}/"><small>{sp.get("tit", sp["pre"])}</small><b>{sp["nom"]}</b><span class="ew">{len(ps)} publicada{"s" if len(ps)!=1 else ""}</span><span class="ex">Última: {esc(ps[0]["title"])}' + (f' · {corto(ps[0]["date"])}' if ps[0]['cat'] == 'ensenanza' else '') + '</span></a>'
wr('predicadores/index.html', sub_eg(pidx, pc))
TPL = rd('predicadores/rodrigo-ordonez/index.html')
def dname(n, sp): return f'{sp.get("tit", sp["pre"])} {sp["nom"]}'
def hero_pf(n, sp, ps):
    ph = PHOTOS.get(sp['slug']); last = ps[0]
    pic = (f'<figure class="pfp"><img src="../../fotos/{ph[0]}" alt="{esc(n)}" width="120" height="120" style="object-position:{ph[1]}"></figure>' if ph else
           f'<figure class="pfp ini" aria-hidden="true"><span>{"".join(w[0] for w in sp["nom"].split()[:2]).upper()}</span></figure>')
    th = last['thumb'] if last['thumb'].startswith('http') else '../../' + last['thumb']
    return (f'<section class="hero sm pf"><div class="w wide"><nav class="bc" aria-label="Migas de pan"><a href="../../">Inicio</a><a href="../">Predicadores</a><span>{esc(n)}</span></nav>'
            f'<div class="pfg"><div class="pfl">{pic}<div><div class="eyebrow">{sp.get("tit", sp["pre"])} · Enseñanzas</div><h1>{esc(dname(n, sp))}</h1><div class="meta"><span>{len(ps)} publicada{"s" if len(ps)!=1 else ""} · Ebenezer Antigua, Jocotenango</span></div></div></div>'
            f'<a class="lastv" href="../../ensenanzas/{last["slug"]}/"><span class="lvt"><img src="{th}" alt="{esc(last["title"])}" width="320" height="180" loading="eager"></span><small>Última enseñanza</small><b>{esc(last["title"])}</b></a></div></div></section>')
def set_url(h, old, new): return h.replace(old, new)
for n in orden_sp:
    sp = speakers[n]; ps = mine(n)
    path = f'predicadores/{sp["slug"]}/index.html'
    h = rd(path) if os.path.exists(os.path.join(R, path)) else None
    if h is None:
        h = TPL.replace('rodrigo-ordonez', sp['slug']).replace('Pastor Rodrigo Ordóñez', n).replace('Rodrigo Ordóñez', sp['nom']).replace('el pastor ' + sp['nom'], 'el ' + sp['pre'].lower() + ' ' + sp['nom']).replace('del pastor ' + sp['nom'], 'del ' + sp['pre'].lower() + ' ' + sp['nom'])
        h = h.replace('"honorificPrefix": "Pastor"', f'"honorificPrefix": "{sp["pre"]}"')
    h = re.sub(r'<section class="hero sm[^"]*">.*?</section>', lambda m: hero_pf(n, sp, ps), h, count=1, flags=re.S)
    others = ''.join(f'<li><a href="../{speakers[o]["slug"]}/">{o}</a></li>' for o in orden_sp if o != n)
    h = re.sub(r'(<h2>Otros predicadores</h2><ul>).*?(</ul>)', lambda m: m.group(1) + others + m.group(2), h, count=1, flags=re.S)
    h = re.sub(r'<nav class="pager"[^>]*>.*?</nav>', '', h, flags=re.S); h = re.sub(r'<link rel="(?:prev|next)" href="[^"]*">', '', h)
    total_p = max(1, math.ceil(len(ps) / PAGE_P)); base_url = f'https://ebenezerantigua.com/predicadores/{sp["slug"]}/'
    for k in range(1, total_p + 1):
        chunk = ps[(k-1)*PAGE_P:k*PAGE_P]
        hk = re.sub(r'(<div class="eg">).*?(</div>)', lambda m: m.group(1) + ''.join(card(p, '../../') for p in chunk) + m.group(2) + '<!--PG-->', h, count=1, flags=re.S)
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', hk, re.S); j = json.loads(m.group(1))
        url = base_url + ('' if k == 1 else f'pagina/{k}/')
        for e in j['@graph']:
            if e.get('@type') == 'CollectionPage':
                e['mainEntity']['itemListElement'] = [dict(zip(['@type', 'position', 'url', 'name'], ['ListItem', (k-1)*PAGE_P+i+1, f'https://ebenezerantigua.com/ensenanzas/{p["slug"]}/', p['title']])) for i, p in enumerate(chunk)]
                if k > 1: e['url'] = url; e['@id'] = url + '#page'
        hk = hk.replace(m.group(1), json.dumps(j, ensure_ascii=False))
        hk = hk.replace('</head>', (f'<link rel="prev" href="{base_url}' + ('' if k == 2 else f'pagina/{k-1}/') + '">' if k > 1 else '') + (f'<link rel="next" href="{base_url}pagina/{k+1}/">' if k < total_p else '') + '</head>', 1) if total_p > 1 else hk
        if k == 1: wr(path, hk.replace('<!--PG-->', pager('./', 1, total_p))); continue
        hk = hk.replace(f'<link rel="canonical" href="{base_url}">', f'<link rel="canonical" href="{url}">').replace(f'hreflang="es-GT" href="{base_url}"', f'hreflang="es-GT" href="{url}"').replace(f'hreflang="x-default" href="{base_url}"', f'hreflang="x-default" href="{url}"').replace(f'<meta property="og:url" content="{base_url}">', f'<meta property="og:url" content="{url}">')
        hk = re.sub(r'(<title>)(.*?)( \| Ebenezer Antigua</title>)', lambda m: f'{m.group(1)}{m.group(2)} · página {k}{m.group(3)}', hk, count=1)
        hk = hk.replace(f'<h1>{esc(dname(n, sp))}</h1>', f'<h1>{esc(dname(n, sp))} — página {k}</h1>', 1)
        hk = re.sub(r'<p class="lead sm">.*?</p>', '', hk, count=1, flags=re.S)
        hk = shift(hk, 2).replace('<!--PG-->', pager('../../', k, total_p))
        hk = hk.replace(f'<span>{esc(dname(n, sp))}</span></nav>', f'<a href="../../">{esc(dname(n, sp))}</a><span>Página {k}</span></nav>', 1)
        wr(f'predicadores/{sp["slug"]}/pagina/{k}/index.html', hk)
    pdir = os.path.join(R, 'predicadores', sp['slug'], 'pagina')
    if os.path.isdir(pdir):
        import shutil
        for d in os.listdir(pdir):
            if d.isdigit() and int(d) > total_p: shutil.rmtree(os.path.join(pdir, d))
    for k in range(2, total_p + 1): add_sm(base_url + f'pagina/{k}/', '0.5')
wr('sitemap.xml', sm)
print('páginas nuevas:', len(specs), '· predicadores:', len(orden_sp), '· enseñanzas:', len(order), '· discipulados:', len(bycat('discipulado')), '· otros:', len(bycat('otro')), '· páginas de listado:', tots)
