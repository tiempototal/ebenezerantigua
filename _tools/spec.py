#!/usr/bin/env python3
"""Ayudante para escribir specs de enseñanza sin repetir JSON a mano.
Uso desde Python:  import sys; sys.path.insert(0,'_tools'); from spec import mk
mk(slug,title,id,date,speaker,tag,dur,lead,items,sections,verses,closing,cat='ensenanza',card_tag=None)
- items: ["Título: texto", ...]  (lo anterior a los dos puntos se pone en negrita)
- sections: [[titulo,[parrafos]], ...]   - verses: [[ref,texto], ...] (las refs también son los chips)
- speaker: nombre completo con prefijo ("Profeta Hugo García"); para discipulados sin predicador usar "Ebenezer Antigua".
Escribe _registro/datos/<slug>.json (el generador nueva-ensenanza.py lo convierte en página)."""
import json, re, unicodedata
def _slug(t):
    t = unicodedata.normalize('NFD', t.lower()); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')
def mk(slug, title, id, date, speaker, tag, dur, lead, items, sections, verses, closing, cat='ensenanza', card_tag=None, speaker_slug=None):
    kind = {'ensenanza': 'la enseñanza', 'discipulado': 'el discipulado', 'otro': 'el mensaje'}[cat]
    first = re.split(r'(?<=[.!?])\s', lead)[0]
    desc = f'Resumen de {kind} «{title}» ({speaker}): {first[:130].rstrip(" .,;:")}. Ebenezer Antigua.'
    s = dict(slug=slug, title=title, id=id, date=date, speaker=speaker, tag=tag, card_tag=card_tag or tag, dur=dur, cat=cat, desc=desc,
             keywords=', '.join([title, tag, speaker] + [v[0] for v in verses[:3]]), lead=lead,
             items=[re.sub(r'^([^:]{2,90}):', r'<b>\1:</b>', x, count=1) for x in items], chips=[v[0] for v in verses], sections=sections, verses=verses, closing=closing)
    if speaker_slug: s['speaker_slug'] = speaker_slug
    json.dump(s, open(f'_registro/datos/{slug}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def enrich(slug, patron, momentos, citas, reflexion, inicio=None):
    """Añade a un spec existente: momentos [{t,e,titulo,txt}] (transcripción literal), citas [{t,txt}] (2-5), reflexion [preguntas], patron 'A'|'B'|'C'."""
    p = f'_registro/datos/{slug}.json'; s = json.load(open(p, encoding='utf-8'))
    s.update(patron=patron, momentos=momentos, citas=citas, reflexion=reflexion)
    if inicio: s['inicio'] = int(inicio)  # segundo donde empieza la prédica (salta alabanza/oración); el embed usa &start=
    json.dump(s, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
