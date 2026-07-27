/* ============================================================================
   AXIONALYTICS — SHARED BEHAVIOR
   Loaded at the end of <body> on every page.

   Modules: language toggle · mobile drawer · header scroll state ·
            scroll reveal · accordions · animated counters · active nav ·
            copy-to-clipboard · tab groups

   Every module is defensive: if its markup is absent on a given page, it
   no-ops rather than throwing, so one shared file serves every template.
   ============================================================================ */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* -------------------------------------------------------------------------
     1. BILINGUAL TOGGLE
     The <head> of each page applies the saved class before first paint to
     avoid a flash of English; this only wires up the controls.
     ------------------------------------------------------------------------- */
  var LANG_KEY = 'axio-lang';

  function readLang() {
    try { return localStorage.getItem(LANG_KEY) === 'es' ? 'es' : 'en'; }
    catch (e) { return 'en'; }
  }

  function applyLang(lang) {
    var isEs = lang === 'es';
    root.classList.toggle('lang-es', isEs);
    root.lang = isEs ? 'es' : 'en';

    each('[data-lang-code]', function (el) { el.textContent = isEs ? 'ES' : 'EN'; });
    each('[data-lang-name]', function (el) { el.textContent = isEs ? 'Español' : 'English'; });
    each('[data-lang-toggle]', function (el) {
      el.setAttribute('aria-label', isEs ? 'Cambiar a inglés' : 'Switch to Spanish');
    });

    try { localStorage.setItem(LANG_KEY, lang); } catch (e) { /* private mode */ }
  }

  applyLang(readLang());

  each('[data-lang-toggle]', function (el) {
    el.addEventListener('click', function () {
      applyLang(readLang() === 'en' ? 'es' : 'en');
    });
  });

  /* -------------------------------------------------------------------------
     2. MOBILE DRAWER
     ------------------------------------------------------------------------- */
  var drawer = doc.getElementById('ax-drawer');
  var scrim = doc.getElementById('ax-scrim');
  var openBtn = doc.getElementById('ax-drawer-open');
  var closeBtn = doc.getElementById('ax-drawer-close');

  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle('is-open', open);
    drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
    if (openBtn) openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (scrim) {
      scrim.style.opacity = open ? '1' : '0';
      scrim.style.pointerEvents = open ? 'auto' : 'none';
    }
    doc.body.style.overflow = open ? 'hidden' : '';
    if (open && closeBtn) closeBtn.focus();
  }

  if (openBtn) openBtn.addEventListener('click', function () { setDrawer(true); });
  if (closeBtn) closeBtn.addEventListener('click', function () { setDrawer(false); });
  if (scrim) scrim.addEventListener('click', function () { setDrawer(false); });
  if (drawer) {
    each('a', function (a) { a.addEventListener('click', function () { setDrawer(false); }); }, drawer);
  }
  doc.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('is-open')) setDrawer(false);
  });

  /* -------------------------------------------------------------------------
     3. HEADER SCROLL STATE
     ------------------------------------------------------------------------- */
  var header = doc.getElementById('ax-header');
  if (header) {
    var ticking = false;
    var syncHeader = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 24);
      ticking = false;
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { window.requestAnimationFrame(syncHeader); ticking = true; }
    }, { passive: true });
    syncHeader();
  }

  /* -------------------------------------------------------------------------
     4. SCROLL REVEAL
     ------------------------------------------------------------------------- */
  var revealTargets = doc.querySelectorAll('.ax-reveal, .ax-stagger');

  if (reduceMotion || !('IntersectionObserver' in window)) {
    each('.ax-reveal, .ax-stagger', function (el) { el.classList.add('is-in'); });
  } else if (revealTargets.length) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

    revealTargets.forEach(function (el) { revealObserver.observe(el); });
  }

  /* -------------------------------------------------------------------------
     5. ACCORDIONS
     Buttons carry [data-acc-trigger]; the .ax-acc wrapper holds open state.
     ------------------------------------------------------------------------- */
  each('[data-acc-trigger]', function (btn) {
    btn.addEventListener('click', function () {
      var item = btn.closest('.ax-acc');
      if (!item) return;

      var willOpen = !item.classList.contains('is-open');
      var group = item.getAttribute('data-acc-group');

      // Single-open behavior within a named group
      if (group) {
        each('.ax-acc[data-acc-group="' + group + '"]', function (sibling) {
          if (sibling === item) return;
          sibling.classList.remove('is-open');
          var sibBtn = sibling.querySelector('[data-acc-trigger]');
          if (sibBtn) sibBtn.setAttribute('aria-expanded', 'false');
        });
      }

      item.classList.toggle('is-open', willOpen);
      btn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });
  });

  /* -------------------------------------------------------------------------
     6. ANIMATED COUNTERS
     <span data-count-to="1848" data-count-suffix="+">0</span>
     ------------------------------------------------------------------------- */
  var counters = doc.querySelectorAll('[data-count-to]');

  function runCounter(el) {
    var target = parseFloat(el.getAttribute('data-count-to')) || 0;
    var decimals = parseInt(el.getAttribute('data-count-decimals') || '0', 10);
    var prefix = el.getAttribute('data-count-prefix') || '';
    var suffix = el.getAttribute('data-count-suffix') || '';
    var duration = parseInt(el.getAttribute('data-count-duration') || '1600', 10);
    var start = null;

    function fmt(v) {
      return prefix + v.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      }) + suffix;
    }

    if (reduceMotion) { el.textContent = fmt(target); return; }

    function frame(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      el.textContent = fmt(target * eased);
      if (p < 1) window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);
  }

  if (counters.length) {
    if (!('IntersectionObserver' in window)) {
      counters.forEach(runCounter);
    } else {
      var countObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          runCounter(entry.target);
          countObserver.unobserve(entry.target);
        });
      }, { threshold: 0.5 });
      counters.forEach(function (el) { countObserver.observe(el); });
    }
  }

  /* -------------------------------------------------------------------------
     7. TAB GROUPS
     [data-tab-group="x"][data-tab="id"] buttons ↔ [data-tab-panel="id"] panels
     ------------------------------------------------------------------------- */
  each('[data-tab]', function (btn) {
    btn.addEventListener('click', function () {
      var group = btn.getAttribute('data-tab-group');
      var id = btn.getAttribute('data-tab');
      if (!group || !id) return;

      each('[data-tab-group="' + group + '"]', function (b) {
        var on = b === btn;
        b.setAttribute('aria-selected', on ? 'true' : 'false');
        b.classList.toggle('is-active', on);
      });

      each('[data-tab-panel][data-tab-group-panel="' + group + '"]', function (panel) {
        panel.hidden = panel.getAttribute('data-tab-panel') !== id;
      });
    });
  });

  /* -------------------------------------------------------------------------
     8. COPY TO CLIPBOARD
     ------------------------------------------------------------------------- */
  each('[data-copy]', function (btn) {
    btn.addEventListener('click', function () {
      var sel = btn.getAttribute('data-copy');
      var src = sel ? doc.querySelector(sel) : null;
      if (!src || !navigator.clipboard) return;

      navigator.clipboard.writeText(src.textContent.trim()).then(function () {
        var label = btn.querySelector('[data-copy-label]') || btn;
        var original = label.textContent;
        label.textContent = 'Copied';
        setTimeout(function () { label.textContent = original; }, 1800);
      }).catch(function () { /* clipboard blocked — silently ignore */ });
    });
  });

  /* -------------------------------------------------------------------------
     9. ACTIVE NAV HIGHLIGHT
     Marks the nav link matching the current file so each page doesn't have to
     hand-maintain its own "current" styling.
     ------------------------------------------------------------------------- */
  var here = window.location.pathname.split('/').pop() || 'index.html';
  each('[data-nav-for]', function (link) {
    if (link.getAttribute('data-nav-for') === here) {
      link.setAttribute('aria-current', 'page');
      link.classList.add('text-white');
      link.classList.remove('text-white/70');
    }
  });

  /* -------------------------------------------------------------------------
     10. CURRENT YEAR
     ------------------------------------------------------------------------- */
  each('[data-year]', function (el) { el.textContent = String(new Date().getFullYear()); });

  /* -------------------------------------------------------------------------
     Helper
     ------------------------------------------------------------------------- */
  function each(selector, fn, scope) {
    var list = (scope || doc).querySelectorAll(selector);
    Array.prototype.forEach.call(list, fn);
  }
})();
