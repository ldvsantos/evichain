(function () {
  // Registrar SW (PWA)
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function () {
        // silencioso: não bloqueia UX
      });
    });
  }

  // Menu mobile (somente se existir no DOM)
  function initMobileNav() {
    var toggle = document.querySelector('[data-mobile-nav-toggle]');
    var links = document.querySelector('[data-mobile-nav-links]');
    if (!toggle || !links) return;

    function setOpen(open) {
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      links.classList.toggle('is-open', open);
      document.body.classList.toggle('nav-open', open);
    }

    toggle.addEventListener('click', function () {
      var open = links.classList.contains('is-open');
      setOpen(!open);
    });

    // Fecha ao clicar em um link
    links.addEventListener('click', function (e) {
      var t = e.target;
      if (t && t.tagName === 'A') setOpen(false);
    });

    // Fecha ao redimensionar para desktop
    window.addEventListener('resize', function () {
      if (window.innerWidth > 768) setOpen(false);
    });
  }

  initMobileNav();
})();
