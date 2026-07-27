/* ============================================================================
   AXIONALYTICS — ANALYTICS & CONVERSION TRACKING
   ----------------------------------------------------------------------------
   CONFIGURE ME: set `provider` and the matching id below, then redeploy.
   Until an id is filled in, this file is inert — it loads nothing and sends
   nothing, so it is safe to ship unconfigured.

   PROVIDER CHOICE
   ---------------
   Cookieless is the default deliberately. This site sells zero-egress,
   privacy-preserving AI to security architects; loading a cookie-based tracker
   that requires a consent banner undercuts the argument on the page. Cookieless
   providers also need no banner under GDPR/ePrivacy, which removes the single
   biggest conversion-rate tax on a B2B site.

     'cloudflare'  free, cookieless, no banner        <- recommended
     'plausible'   paid, cookieless, no banner
     'ga4'         free, cookie-based, NEEDS a consent banner (not included)
     'none'        disabled

   WHAT IT MEASURES
   ----------------
   Page views, plus the funnel steps that actually matter commercially:
   briefing CTA clicks, ROI calculator engagement, the email unlock, scenario
   selection, and outbound contact. Page views alone cannot tell you which
   pillar page produces briefings.
   ============================================================================ */
(function () {
  'use strict';

  var CONFIG = {
    provider: 'cloudflare',   // 'cloudflare' | 'plausible' | 'ga4' | 'none'

    // Cloudflare Web Analytics: Dash > Analytics > Web Analytics > add site,
    // then copy the token out of the snippet it gives you.
    cloudflareToken: '',      // e.g. 'a1b2c3d4e5f6...'

    // Plausible: the domain exactly as registered in your Plausible account.
    plausibleDomain: 'axionalytics.com',

    // GA4: Admin > Data Streams > your stream > Measurement ID.
    ga4Id: '',                // e.g. 'G-XXXXXXXXXX'

    // Honour the browser's Do Not Track signal. Costs a little data; consistent
    // with what the rest of this site claims to believe.
    respectDoNotTrack: true
  };

  /* ---------------------------------------------------------------------- */

  var doc = document;

  function dnt() {
    if (!CONFIG.respectDoNotTrack) return false;
    var v = navigator.doNotTrack || window.doNotTrack || navigator.msDoNotTrack;
    return v === '1' || v === 'yes';
  }

  function inject(src, attrs) {
    var s = doc.createElement('script');
    s.src = src;
    s.defer = true;
    Object.keys(attrs || {}).forEach(function (k) { s.setAttribute(k, attrs[k]); });
    doc.head.appendChild(s);
    return s;
  }

  var active = false;

  function boot() {
    if (dnt()) return;

    switch (CONFIG.provider) {
      case 'cloudflare':
        if (!CONFIG.cloudflareToken) return;
        inject('https://static.cloudflareinsights.com/beacon.min.js',
               { 'data-cf-beacon': '{"token":"' + CONFIG.cloudflareToken + '"}' });
        active = true;
        break;

      case 'plausible':
        if (!CONFIG.plausibleDomain) return;
        // The "manual" build exposes window.plausible() for custom events.
        inject('https://plausible.io/js/script.manual.js',
               { 'data-domain': CONFIG.plausibleDomain });
        window.plausible = window.plausible || function () {
          (window.plausible.q = window.plausible.q || []).push(arguments);
        };
        window.plausible('pageview');
        active = true;
        break;

      case 'ga4':
        if (!CONFIG.ga4Id) return;
        inject('https://www.googletagmanager.com/gtag/js?id=' + CONFIG.ga4Id);
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () { window.dataLayer.push(arguments); };
        window.gtag('js', new Date());
        window.gtag('config', CONFIG.ga4Id, { anonymize_ip: true });
        active = true;
        break;

      default:
        return;
    }
  }

  /* ----------------------------------------------------------------------
     Event dispatch — normalised across providers so the call sites below do
     not care which one is configured.
     ---------------------------------------------------------------------- */
  function track(name, props) {
    if (!active) return;
    try {
      if (CONFIG.provider === 'plausible' && window.plausible) {
        window.plausible(name, { props: props || {} });
      } else if (CONFIG.provider === 'ga4' && window.gtag) {
        window.gtag('event', name, props || {});
      }
      // Cloudflare Web Analytics is page-view only; custom events are a no-op.
    } catch (e) { /* never let measurement break the page */ }
  }

  // Exposed so other modules (the ROI calculator) can report without importing.
  window.axioTrack = track;

  /* ----------------------------------------------------------------------
     Funnel instrumentation
     ---------------------------------------------------------------------- */
  function page() {
    return (window.location.pathname.split('/').pop() || 'index.html');
  }

  doc.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a');
    if (!a) return;
    var href = a.getAttribute('href') || '';

    if (href.indexOf('calendar.app.google') > -1) {
      track('briefing_cta', { page: page() });
    } else if (href.indexOf('mailto:') === 0) {
      track('email_click', { page: page() });
    } else if (href.indexOf('wa.me') > -1) {
      track('whatsapp_click', { page: page() });
    } else if (href.indexOf('roi-calculator') > -1) {
      track('roi_open', { from: page() });
    }
  }, true);

  // Scroll depth on long-form pages tells you whether the argument is landing.
  var marks = [25, 50, 75, 100], hit = {};
  var isArticle = !!doc.querySelector('article .ax-prose');
  if (isArticle) {
    window.addEventListener('scroll', function () {
      var h = doc.documentElement;
      var pct = (h.scrollTop + window.innerHeight) / h.scrollHeight * 100;
      marks.forEach(function (m) {
        if (pct >= m && !hit[m]) {
          hit[m] = true;
          track('read_depth', { depth: m + '%', page: page() });
        }
      });
    }, { passive: true });
  }

  boot();
})();
