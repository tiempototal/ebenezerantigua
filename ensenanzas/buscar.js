/* Buscador de /ensenanzas/: filtra en el navegador todas las enseñanzas, discipulados y otros mensajes (índice: buscar.json). */
(function () {
  var q = document.getElementById('q'), list = document.getElementById('slist'), res = document.getElementById('sres'), sc = document.getElementById('sc');
  if (!q || !list || !res) return;
  var data = null, loading = false, timer = null;
  function norm(t) { return (t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function card(p) {
    return '<a class="ec" href="/ensenanzas/' + p.s + '/"><span class="ect"><img src="' + esc(p.i) + '" alt="' + esc(p.t + ' — ' + p.p) + '" loading="lazy" width="320" height="180"></span><small>' + esc(p.g) + '</small><b>' + esc(p.t) + '</b><span class="ew">' + esc(p.p) + '</span><span class="ex">' + esc(p.e) + '</span></a>';
  }
  function run() {
    var terms = norm(q.value).split(/\s+/).filter(Boolean);
    if (!terms.length) { res.hidden = true; list.hidden = false; sc.textContent = ''; return; }
    if (!data) { sc.textContent = 'Buscando…'; load(run); return; }
    var out = data.filter(function (p) { var h = p.h; return terms.every(function (t) { return h.indexOf(t) > -1; }); });
    list.hidden = true; res.hidden = false;
    res.innerHTML = out.slice(0, 60).map(card).join('') || '';
    sc.textContent = out.length ? (out.length + (out.length === 1 ? ' resultado' : ' resultados') + (out.length > 60 ? ' (se muestran los primeros 60; afina tu búsqueda)' : '')) : 'No encontramos resultados. Prueba con otra palabra, un tema o el nombre del predicador.';
  }
  function load(cb) {
    if (loading) return; loading = true;
    fetch('/ensenanzas/buscar.json').then(function (r) { return r.json(); }).then(function (d) {
      d.forEach(function (p) { p.h = norm(p.t + ' ' + p.p + ' ' + p.g + ' ' + p.e); }); data = d; cb && cb();
    }).catch(function () { loading = false; sc.textContent = 'No se pudo cargar la búsqueda. Inténtalo de nuevo.'; });
  }
  q.addEventListener('focus', function () { if (!data) load(); }, { once: true });
  q.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 120); });
}());
