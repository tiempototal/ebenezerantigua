/* Enlaces a YouTube (canal, "Ver en vivo", "Ver transmisión", "Ver en YouTube"):
   en celular intentan abrir la app de YouTube y, si no se puede, abren la web.
   En escritorio no hace nada: los enlaces se abren normal. */
(function () {
  var ua = navigator.userAgent || '';
  var android = /Android/i.test(ua);
  var ios = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  if (!android && !ios) return;

  function isYT(a) {
    return /^(www\.|m\.)?youtube\.com$/i.test(a.hostname) &&
      (/^\/@ebenezerantigua(\/|$)/i.test(a.pathname) || a.pathname === '/watch');
  }

  function openApp(a) {
    var web = a.href.split('#')[0];
    var rest = a.pathname + a.search;
    var done = false;
    function stop() { done = true; }
    // Si la app se abre, esta página pasa a segundo plano: se cancela el respaldo web.
    document.addEventListener('visibilitychange', function () { if (document.hidden) stop(); });
    addEventListener('pagehide', stop);
    setTimeout(function () { if (!done && !document.hidden) location.href = web; }, 1600);
    if (android) {
      location.href = 'intent://www.youtube.com' + rest +
        '#Intent;scheme=https;package=com.google.android.youtube;S.browser_fallback_url=' +
        encodeURIComponent(web) + ';end';
    } else {
      location.href = 'youtube://www.youtube.com' + rest;
    }
  }

  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest('a[href]');
    // Los enlaces de minuto (data-t) los maneja el script del video de cada enseñanza.
    if (!a || a.hasAttribute('data-t') || !isYT(a)) return;
    e.preventDefault();
    openApp(a);
  });
})();
