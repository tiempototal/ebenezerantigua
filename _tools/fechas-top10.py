#!/usr/bin/env python3
"""Regla del sitio: solo las N (10) enseñanzas más recientes muestran fecha visible
(hero, bajo el video y tarjetas). Las que salen del top N pierden la fecha visible
(la fecha en JSON-LD/sitemap/feed NO se toca, es para SEO).
Uso (desde la raíz del repo, tras agregar la enseñanza nueva a ensenanzas/feed.xml):
    python3 _tools/fechas-top10.py            # N=10
    python3 _tools/fechas-top10.py 3 /ruta    # N y carpeta (pruebas)
Es idempotente. El orden sale de ensenanzas/feed.xml (más nueva primero)."""
import re, sys, glob, os
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
root = sys.argv[2] if len(sys.argv) > 2 else '.'
feed = open(os.path.join(root, 'ensenanzas/feed.xml'), encoding='utf-8').read()
slugs = re.findall(r'<link>https://ebenezerantigua\.com/ensenanzas/([^/]+)/</link>', feed)
old = slugs[N:]
LONG = r'(?:lunes|martes|miércoles|jueves|viernes|sábado|domingo) \d{1,2} de [a-záéíóú]+ de \d{4}'
SHORT = r' · \d{1,2} [a-záéíóú]{3,4}\.?'
changed = []
def sub(path, fn):
    t = open(path, encoding='utf-8').read(); n = fn(t)
    if n != t:
        open(path, 'w', encoding='utf-8').write(n); changed.append(path)
for slug in old:
    pg = os.path.join(root, 'ensenanzas', slug, 'index.html')
    if os.path.exists(pg):
        sub(pg, lambda t: re.sub(r', ' + LONG + r'\.', '.', re.sub(r'<span>·</span><span>' + LONG + r'</span>', '', t, count=1), count=1))
    e = re.escape(slug)
    ec = re.compile(r'(<a class="ec" href="[^"]*/' + e + r'/">(?:(?!</a>).)*?<small>[^<]*?)' + SHORT + r'(</small>)', re.S)
    msg = re.compile(r'(<a class="thumb" href="ensenanzas/' + e + r'/"(?:(?!</div>\s*<div class="msg).)*?<div class="by">[^<]*?)' + SHORT + r'(</div>)', re.S)
    li = re.compile(r'(<a href="[^"]*/' + e + r'/">[^<]*</a>) <small>' + LONG + r'</small>')
    for f in glob.glob(os.path.join(root, '**/*.html'), recursive=True):
        sub(f, lambda t: li.sub(r'\1', msg.sub(r'\1\2', ec.sub(r'\1\2', t))))
print(f'N={N}: {len(slugs)} enseñanzas; sin fecha visible: {old or "ninguna"}; archivos cambiados: {len(set(changed))}')
