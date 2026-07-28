/* ============================================================================
   AXIONALYTICS — HOMEPAGE ONLY
   ----------------------------------------------------------------------------
   Referenced with `defer` from _build/pages/index.meta.html. It therefore runs
   after axio.js (a classic script at the end of <body> executes during parsing;
   a deferred script waits for parsing to finish), which matters: the scroll
   reveal observer is already wired before anything here touches the DOM.

   Modules: the axion field · the governed run · plane parallax

   WHY THERE IS NOT A LINE OF THREE.JS IN HERE
   _private/docs/Interactive 3D Web Implementation.md specifies WebGPU, Three.js
   with TSL, GSAP, Lenis and an OffscreenCanvas worker. Every one of those needs
   Node, a bundler and a lockfile, and three alone is roughly twice this site's
   entire current payload. The document's engineering discipline is worth keeping
   and its dependency list is not, so the guardrails it argues for are all
   implemented below against plain Canvas 2D:

     tiered degradation      point count scales with area, then with pointer type
     capped pixel ratio      devicePixelRatio is clamped to 1.6
     pause when not visible  IntersectionObserver stops the loop past the fold
     lifecycle management    a backgrounded tab stops the loop entirely
     reduced motion          one settled frame, then no rAF is ever scheduled
     no layout thrash        the loop reads no geometry and writes only transform

   Selectors here are deliberately class-based. check-links.py (build step 15)
   verifies that every id the scripts look up is rendered by some page; using
   classes keeps that contract trivially satisfied in both language trees.
   ============================================================================ */
(function () {
  'use strict';

  var doc = document;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarsePointer = window.matchMedia('(pointer: coarse)').matches;

  var hero = doc.querySelector('.ax-hero');
  var canvas = doc.querySelector('.ax-field');

  /* -------------------------------------------------------------------------
     THE AXION FIELD

     Scatter resolves into a lattice over 2.4s, then holds and drifts. A sweep
     crosses every 9s, lifting the points it passes — an instrument tuning across
     frequencies. The pointer is the detector: points inside its radius brighten
     and bond into a local graph.

     That radius is a performance decision before it is an aesthetic one. Linking
     every point to every other is O(n^2) on ~900 points, which is 400,000 checks
     a frame. Linking only what the detector has already selected is O(k^2) on
     k of about 50 — three orders of magnitude less work, and it looks better,
     because the connections mean "what the instrument is currently resolving"
     rather than "everything, always".
     ------------------------------------------------------------------------- */

  /* The brand spectrum, sampled from axio-config.js. Points take their hue from
     horizontal position, so the field carries the same teal-to-violet sweep the
     logo mark does. */
  var STOPS = ['#0EA5A5', '#22D3EE', '#3B82F6', '#4F46E5', '#A855F7'].map(function (h) {
    return [
      parseInt(h.slice(1, 3), 16),
      parseInt(h.slice(3, 5), 16),
      parseInt(h.slice(5, 7), 16)
    ];
  });

  function spectrum(u) {
    u = u < 0 ? 0 : u > 1 ? 1 : u;
    var s = u * (STOPS.length - 1);
    var i = Math.min(Math.floor(s), STOPS.length - 2);
    var f = s - i;
    var a = STOPS[i];
    var b = STOPS[i + 1];
    return Math.round(a[0] + (b[0] - a[0]) * f) + ',' +
           Math.round(a[1] + (b[1] - a[1]) * f) + ',' +
           Math.round(a[2] + (b[2] - a[2]) * f);
  }

  function initField(el, host) {
    var ctx = el.getContext && el.getContext('2d');
    if (!ctx) return;

    var w = 0, h = 0, pts = [], raf = 0;
    var t0 = 0, running = false, visible = true;
    var px = -9999, py = -9999, sx = -9999, sy = -9999;
    var DETECT = 165;
    var LINK = 74;

    function measure() {
      var r = el.getBoundingClientRect();
      if (!r.width || !r.height) return false;

      /* A 3x display would otherwise ask the GPU for nine times the fragments
         of a 1x one, for a field of 1px dots nobody can resolve at 3x anyway. */
      var dpr = Math.min(window.devicePixelRatio || 1, 1.6);
      w = r.width;
      h = r.height;
      el.width = Math.round(w * dpr);
      el.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return true;
    }

    function build() {
      /* Tier the density: by area first, then again for touch devices, which
         have no cursor to drive the detector and no active cooling. */
      var perPoint = coarsePointer ? 5200 : 2700;
      var target = Math.round(w * h / perPoint);
      target = Math.max(90, Math.min(coarsePointer ? 320 : 900, target));

      var cols = Math.max(3, Math.round(Math.sqrt(target * (w / h))));
      var rows = Math.max(3, Math.round(target / cols));
      var gx = w / cols;
      var gy = h / rows;

      pts = [];
      for (var j = 0; j < rows; j++) {
        for (var i = 0; i < cols; i++) {
          /* Offsetting alternate rows gives a triangular lattice. A square grid
             would read as the engineering grid already behind it. */
          var offset = (j % 2) ? gx * 0.5 : 0;
          pts.push({
            hx: i * gx + offset + gx * 0.5 + (Math.random() - 0.5) * gx * 0.55,
            hy: j * gy + gy * 0.5 + (Math.random() - 0.5) * gy * 0.55,
            nx: Math.random() * w,
            ny: Math.random() * h,
            x: 0, y: 0, a: 0, r: 0, b: 0,
            ph: Math.random() * Math.PI * 2,
            sp: 0.00016 + Math.random() * 0.00034,
            am: 1.6 + Math.random() * 3.4,
            hub: Math.random() < 0.024
          });
        }
      }
    }

    function draw(now) {
      if (!t0) t0 = now;
      var age = now - t0;

      // Scatter to lattice, easeOutCubic over 2.4s. Then it holds.
      var settle = Math.min(age / 2400, 1);
      settle = 1 - Math.pow(1 - settle, 3);

      sx += (px - sx) * 0.14;
      sy += (py - sy) * 0.14;

      var sweep = (((age % 9000) / 9000) * (w * 1.35)) - w * 0.18;
      var near = [];
      var i, j, p;

      ctx.clearRect(0, 0, w, h);

      for (i = 0; i < pts.length; i++) {
        p = pts[i];
        p.x = p.nx + (p.hx - p.nx) * settle + Math.cos(age * p.sp + p.ph) * p.am * settle;
        p.y = p.ny + (p.hy - p.ny) * settle + Math.sin(age * p.sp * 1.3 + p.ph) * p.am * settle;

        var alpha = (p.hub ? 0.42 : 0.13) + 0.20 * settle;
        var rad = p.hub ? 1.9 : 0.95;

        var sd = Math.abs(p.x - sweep);
        if (sd < 95) {
          var lift = 1 - sd / 95;
          alpha += lift * 0.42;
          rad += lift * 0.7;
        }

        var dx = p.x - sx;
        var dy = p.y - sy;
        var d2 = dx * dx + dy * dy;
        if (d2 < DETECT * DETECT) {
          p.b = 1 - Math.sqrt(d2) / DETECT;
          alpha += p.b * 0.55;
          rad += p.b * 1.5;
          near.push(p);
        }

        p.a = alpha > 1 ? 1 : alpha;
        p.r = rad;
      }

      if (near.length > 1) {
        ctx.lineWidth = 0.7;
        for (i = 0; i < near.length; i++) {
          for (j = i + 1; j < near.length; j++) {
            var a = near[i];
            var b = near[j];
            var lx = a.x - b.x;
            var ly = a.y - b.y;
            var ld = Math.sqrt(lx * lx + ly * ly);
            if (ld > LINK) continue;
            var la = a.b * b.b * (1 - ld / LINK) * 0.55;
            if (la < 0.012) continue;
            ctx.strokeStyle = 'rgba(' + spectrum(((a.x + b.x) / 2) / w) + ',' + la.toFixed(3) + ')';
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      for (i = 0; i < pts.length; i++) {
        p = pts[i];
        ctx.fillStyle = 'rgba(' + spectrum(p.x / w) + ',' + p.a.toFixed(3) + ')';
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, 6.2832);
        ctx.fill();
      }

      // The detector aperture, only once the pointer has actually entered.
      if (sx > -5000) {
        ctx.lineWidth = 1;
        ctx.strokeStyle = 'rgba(34,211,238,.055)';
        ctx.beginPath();
        ctx.arc(sx, sy, DETECT * 0.36, 0, 6.2832);
        ctx.stroke();
        ctx.strokeStyle = 'rgba(34,211,238,.03)';
        ctx.beginPath();
        ctx.arc(sx, sy, DETECT * 0.64, 0, 6.2832);
        ctx.stroke();
      }

      if (running) raf = window.requestAnimationFrame(draw);
    }

    /* Reduced motion gets the resolved lattice as a single still frame: the
       composition the design intends, with no rAF loop ever scheduled. */
    function drawStill() {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        ctx.fillStyle = 'rgba(' + spectrum(p.hx / w) + ',' + (p.hub ? 0.62 : 0.33) + ')';
        ctx.beginPath();
        ctx.arc(p.hx, p.hy, p.hub ? 1.9 : 0.95, 0, 6.2832);
        ctx.fill();
      }
    }

    function start() {
      if (running || !visible || reduceMotion) return;
      running = true;
      raf = window.requestAnimationFrame(draw);
    }

    function stop() {
      running = false;
      if (raf) window.cancelAnimationFrame(raf);
      raf = 0;
    }

    function init() {
      if (!measure()) return;
      build();
      t0 = 0;
      if (reduceMotion) drawStill();
      else start();
    }

    var resizeTimer;
    window.addEventListener('resize', function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () { stop(); init(); }, 180);
    }, { passive: true });

    // Past the fold the field is not on screen. It should not cost anything.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
        if (visible) start(); else stop();
      }, { threshold: 0 }).observe(el);
    }

    doc.addEventListener('visibilitychange', function () {
      if (doc.hidden) stop(); else start();
    });

    if (!coarsePointer && host) {
      host.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        px = e.clientX - r.left;
        py = e.clientY - r.top;
        // Land the detector where the pointer entered rather than flying it in.
        if (sx < -5000) { sx = px; sy = py; }
      }, { passive: true });

      host.addEventListener('pointerleave', function () {
        px = -9999;
        py = -9999;
      }, { passive: true });
    }

    init();
  }

  if (canvas) initField(canvas, hero);

  /* -------------------------------------------------------------------------
     THE GOVERNED RUN

     The terminal already contains a real agent trace. Playing it on a timeline
     turns a still image into a demonstration, and the hold before crm.update is
     the point of the whole sequence — the product's central claim expressed as
     timing rather than as a sentence.

     It reveals nodes that already exist rather than typing characters, so the
     bilingual engine in axio.css is untouched and both language trees play
     identically.
     ------------------------------------------------------------------------- */
  var run = doc.querySelector('.ax-run');

  if (run && !reduceMotion) {
    var rows = run.querySelectorAll('.ax-run-row');

    /* ms from start, indexed by data-run-t. The 1.3s gap between 4 and 5 is
       deliberate and should not be tightened: that pause is the write gate. */
    var CUES = [200, 820, 1240, 1680, 2120, 3400, 4700, 5300];

    if (rows.length) {
      // Only now do the CSS rules that hide rows begin to apply. Until this
      // class lands the terminal renders in full, so a script that never runs
      // leaves readable content rather than an empty frame.
      run.classList.add('is-armed');

      var played = false;
      var play = function () {
        if (played) return;
        played = true;
        Array.prototype.forEach.call(rows, function (row, i) {
          var t = parseInt(row.getAttribute('data-run-t'), 10);
          if (isNaN(t)) t = i;
          window.setTimeout(function () {
            row.classList.add('is-on');
          }, CUES[t] || t * 420);
        });
      };

      if ('IntersectionObserver' in window) {
        var runObserver = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            play();
            runObserver.unobserve(entry.target);
          });
        }, { threshold: 0.25 });
        runObserver.observe(run);
      } else {
        play();
      }
    }
  }

  /* -------------------------------------------------------------------------
     PLANE PARALLAX

     Depth without 3D: the grid sits furthest back, the field mid, the copy
     fixed in front. Only the two background planes move, by at most 7px. The
     copy deliberately does not — promoting the headline and the terminal to
     their own compositor layers to shift them a few pixels would cost real
     memory and risk text rasterisation for an effect nobody consciously sees.
     Relative motion against static type reads as depth just as well.

     The loop writes transform and reads nothing, so it never triggers layout,
     and it exits as soon as the planes have caught up with the pointer rather
     than idling at 60fps forever.
     ------------------------------------------------------------------------- */
  if (hero && canvas && !coarsePointer && !reduceMotion && window.innerWidth >= 960) {
    var planes = [
      { el: hero.querySelector('.ax-grid-bg'), k: 4 },
      { el: canvas, k: 7 }
    ].filter(function (p) { return !!p.el; });

    if (planes.length) {
      var tx = 0, ty = 0, cx = 0, cy = 0, ticking = false;

      var step = function () {
        cx += (tx - cx) * 0.07;
        cy += (ty - cy) * 0.07;

        for (var i = 0; i < planes.length; i++) {
          planes[i].el.style.transform =
            'translate3d(' + (cx * planes[i].k).toFixed(2) + 'px,' +
                             (cy * planes[i].k).toFixed(2) + 'px,0)';
        }

        if (Math.abs(tx - cx) > 0.001 || Math.abs(ty - cy) > 0.001) {
          window.requestAnimationFrame(step);
        } else {
          ticking = false;
        }
      };

      hero.addEventListener('pointermove', function (e) {
        var r = hero.getBoundingClientRect();
        tx = ((e.clientX - r.left) / r.width - 0.5) * 2;
        ty = ((e.clientY - r.top) / r.height - 0.5) * 2;
        if (!ticking) {
          ticking = true;
          window.requestAnimationFrame(step);
        }
      }, { passive: true });

      hero.addEventListener('pointerleave', function () {
        tx = 0;
        ty = 0;
        if (!ticking) {
          ticking = true;
          window.requestAnimationFrame(step);
        }
      }, { passive: true });
    }
  }
})();
