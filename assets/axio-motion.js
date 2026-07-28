/* ============================================================================
   AXIONALYTICS — MOTION LAYER
   ----------------------------------------------------------------------------
   Loaded with `defer` from the shared head partial, so it runs after axio.js
   (a classic script at the end of <body> executes during parsing; a deferred
   script waits for parsing to finish) and the scroll-reveal observer is already
   wired before anything here touches the DOM.

   Modules: the axion field · the governed run · plane parallax
   The last two are homepage markup and no-op everywhere else, in keeping with
   the convention in axio.js that one shared file serves every template.

   HOW VARIATION WORKS

   Every page gets a hero field, and no two pillars get the same one. The
   parameters are not decorative choices — they are read off structure that
   already governs this site:

     topology   The four constellations on the homepage pillar cards become the
                fields of the four pages those cards link to. Hovering the tree
                glyph and then landing on a hero that resolves into a tree is
                the same idea stated twice, which is what makes the site feel
                like one object rather than a set of pages.

     hue        The brand spectrum is partitioned across the five pillars, one
                slice each. The homepage spans the whole thing, because it is
                the whole company; a pillar page occupies its own band. Every
                article and glossary entry inherits the band of the pillar it
                declares in the ARTICLES / TERMS manifests, so a cluster page
                is lit in the colour of the pillar it links back to.

     density    Falls with how much reading the page expects. Landing pages
                resolve and sweep; long-form pages get `drift`, which never
                performs a resolve and never sweeps, because ambient motion
                above an 1,800-word technical argument is a cost with no
                return. Legal pages get no field at all.

   WHY THERE IS NOT A LINE OF THREE.JS IN HERE
   _private/docs/Interactive 3D Web Implementation.md specifies WebGPU, Three.js
   with TSL, GSAP, Lenis and an OffscreenCanvas worker. Every one of those needs
   Node, a bundler and a lockfile, and three alone is roughly twice this site's
   entire payload. The document's engineering discipline is worth keeping and
   its dependency list is not, so its guardrails are implemented below against
   plain Canvas 2D: point count tiers by page then by area then by pointer type,
   devicePixelRatio is clamped to 1.6, an IntersectionObserver stops the loop
   past the fold, a backgrounded tab stops it entirely, reduced motion draws one
   settled frame and never schedules a rAF, and the loops read no geometry so
   they cannot thrash layout.

   Selectors here are class-based on purpose. check-links.py (build step 15)
   verifies that every id the scripts look up is rendered by some page; using
   classes keeps that contract trivially satisfied in both language trees.
   ============================================================================ */
(function () {
  'use strict';

  var doc = document;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarsePointer = window.matchMedia('(pointer: coarse)').matches;

  /* -------------------------------------------------------------------------
     1. THE PAGE TABLE

     The whole system, readable at once. That is deliberate: a table one screen
     tall can be reasoned about and retuned, where the same information spread
     across 39 body files as data attributes could not.

     Keyed on filename, which works unchanged in both language trees because
     /es/pricing.html and /pricing.html share a basename.
     ------------------------------------------------------------------------- */

  /* Each pillar owns a slice of the brand spectrum defined in axio-config.js.
     Adjacent slices overlap slightly, so neighbouring pillars read as related
     rather than rationed. */
  var HUE = {
    testing:  [0.00, 0.28],   // teal   -> cyan
    bi:       [0.24, 0.52],   // cyan   -> blue
    security: [0.48, 0.74],   // blue   -> indigo
    agentic:  [0.60, 0.88],   // indigo -> violet
    revenue:  [0.82, 1.00],   // violet -> magenta
    full:     [0.00, 1.00]    // the entire mark
  };

  /* `base` and `lift` set how present the field is: a point rests at base, and
     gains lift as the topology resolves. They are tiered rather than constant
     because the shapes have to be legible to be worth having — a topology
     nobody can make out is just noise — while a page carrying 1,800 words of
     argument wants the opposite. So a landing page resolves to about 0.45 and
     an article settles near 0.22, against the same hero background. */
  var TIER = {
    // area/point · detector · base · lift · resolves? · sweeps?
    full:   { per: 2700, detect: 165, base: 0.17, lift: 0.28, resolve: true,  sweep: true  },
    medium: { per: 4000, detect: 145, base: 0.14, lift: 0.22, resolve: true,  sweep: true  },
    sparse: { per: 6800, detect: 120, base: 0.13, lift: 0.09, resolve: false, sweep: false }
  };

  // slug -> [topology, hue, tier].  null means no field on that page.
  var PAGES = {
    'index.html':                         ['lattice',   'full',     'full'],

    // The five pillars. Topology matches the constellation on the homepage
    // card that links here.
    'agentic-test-engineering.html':      ['tree',      'testing',  'full'],
    'enterprise-agentic-ai.html':         ['mesh',      'agentic',  'full'],
    'agentic-business-intelligence.html': ['funnel',    'bi',       'full'],
    'agentic-revenue-development.html':   ['chain',     'revenue',  'full'],
    'enterprise-ai-security.html':        ['perimeter', 'security', 'full'],

    // Company and tools. Topology says something about the page's job: the
    // calculator funnels inputs down to one number, case studies are a
    // sequence, about is a network of people.
    'solutions.html':                     ['lattice',   'full',     'medium'],
    'roi-calculator.html':                ['funnel',    'bi',       'medium'],
    'case-studies.html':                  ['chain',     'full',     'medium'],
    'pricing.html':                       ['lattice',   'full',     'medium'],
    'about.html':                         ['mesh',      'full',     'medium'],
    'contact.html':                       ['drift',     'full',     'medium'],

    // Indexes are scanned rather than read, but they are not landings either.
    'blog.html':                          ['drift',     'full',     'sparse'],
    'glossary.html':                      ['drift',     'full',     'sparse'],

    // Legal pages are read start to finish, often under obligation. Nothing
    // should move behind them.
    'privacy.html':       null,
    'terms.html':         null,
    'accessibility.html': null
  };

  /* Cluster pages inherit their pillar's band. These assignments are copied
     from the ARTICLES and TERMS manifests in _build/scripts/, which are also
     what decide the internal link each page carries back to its pillar — so
     the colour and the link always agree. */
  var CLUSTER = {
    'why-ai-pilots-fail-security-review':   'security',
    'prompt-injection-tool-abuse-defense':  'security',
    'byoc-vs-saas-enterprise-ai':           'security',
    'what-is-byoc':                         'security',
    'what-is-prompt-injection':             'security',

    'outbound-research-not-volume':         'revenue',
    'email-deliverability-firewall':        'revenue',
    'what-is-email-deliverability':         'revenue',

    'human-in-the-loop-ai-architecture':    'agentic',
    'agentic-data-exploration-at-scale':    'agentic',
    'ai-tools-for-business':                'agentic',
    'what-is-agentic-ai':                   'agentic',
    'what-is-human-in-the-loop':            'agentic',

    'requirements-traceability-automation': 'testing',
    'coverage-gap-analysis':                'testing',
    'legacy-test-suite-modernization':      'testing',
    'what-is-requirements-traceability':    'testing',

    'bi-backlog-bottleneck':                'bi',
    'excel-vs-power-bi':                    'bi',
    'data-analytics-roi':                   'bi',
    'business-dashboard-guide':             'bi',
    'what-is-a-semantic-layer':             'bi'
  };

  function profile() {
    var slug = window.location.pathname.split('/').pop() || 'index.html';
    if (Object.prototype.hasOwnProperty.call(PAGES, slug)) return PAGES[slug];

    var stem = slug.replace(/\.html$/, '');
    if (CLUSTER[stem]) return ['drift', CLUSTER[stem], 'sparse'];

    // Anything not yet in the table reads as long-form until told otherwise.
    return ['drift', 'full', 'sparse'];
  }

  /* -------------------------------------------------------------------------
     2. COLOUR

     The spectrum sampled from axio-config.js. A point takes its hue from its
     horizontal position, remapped into whichever slice the page owns.
     ------------------------------------------------------------------------- */
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

  /* -------------------------------------------------------------------------
     3. TOPOLOGIES

     Each decides where a point comes to rest. The scatter every mode starts
     from is identical — what differs is the order it resolves into, which is
     the whole idea: the same instrument, tuned to a different signal.
     ------------------------------------------------------------------------- */
  var TOPOLOGY = {
    // Triangular, so it never reads as the engineering grid already behind it.
    lattice: function (p, i, n, w, h) {
      var cols = Math.max(3, Math.round(Math.sqrt(n * (w / h))));
      var rows = Math.max(3, Math.round(n / cols));
      var gx = w / cols, gy = h / rows;
      var col = i % cols, row = Math.floor(i / cols) % rows;
      p.hx = col * gx + ((row % 2) ? gx * 0.5 : 0) + gx * 0.5 + (Math.random() - 0.5) * gx * 0.55;
      p.hy = row * gy + gy * 0.5 + (Math.random() - 0.5) * gy * 0.55;
    },

    // One source fanning out into progressively finer detail: a specification
    // becoming sections becoming individual tests.
    tree: function (p, i, n, w, h) {
      var depth = 5;
      var t = (i % depth) / (depth - 1);
      var spread = h * (0.05 + 0.42 * t);
      p.hx = w * (0.10 + 0.78 * t) + (Math.random() - 0.5) * w * 0.05;
      p.hy = h * 0.5 + (Math.random() - 0.5) * 2 * spread;
    },

    // Discrete cells, each its own neighbourhood — isolated subsystems that can
    // still reach one another.
    mesh: function (p, i, n, w, h) {
      var hubs = 6;
      var k = i % hubs;
      var cx = w * (0.14 + 0.72 * ((k * 0.37) % 1));
      var cy = h * (0.20 + 0.60 * ((k * 0.61) % 1));
      p.hx = cx + (Math.random() - 0.5) * w * 0.17;
      p.hy = cy + (Math.random() - 0.5) * h * 0.36;
    },

    // Many governed sources collapsing to one artifact. The bias makes density
    // rise toward the throat rather than spacing evenly along it.
    funnel: function (p, i, n, w, h) {
      var t = Math.pow(Math.random(), 0.6);
      var squeeze = 1 - 0.82 * t;
      p.hx = w * (0.06 + 0.86 * t);
      p.hy = h * 0.5 + (Math.random() - 0.5) * h * 0.92 * squeeze;
    },

    // Stages that each gate the one after: discover, research, verify, stop.
    chain: function (p, i, n, w, h) {
      var nodes = 5;
      var k = i % nodes;
      p.hx = w * (0.12 + 0.76 * (k / (nodes - 1))) + (Math.random() - 0.5) * w * 0.10;
      p.hy = h * ((k % 2) ? 0.34 : 0.66) + (Math.random() - 0.5) * h * 0.24;
    },

    // A boundary with the interior left deliberately empty. On the security
    // page, the perimeter is where the work is.
    perimeter: function (p, i, n, w, h) {
      // Distributed by index rather than at random, so the ring is even instead
      // of clumping and leaving gaps — a boundary with holes in it reads as an
      // accident on a page arguing that the boundary holds.
      var ang = (i / n) * 6.2832 + (Math.random() - 0.5) * 0.22;
      var band = 0.95 + (Math.random() - 0.5) * 0.09;
      p.hx = w * 0.5 + Math.cos(ang) * w * 0.44 * band;
      p.hy = h * 0.5 + Math.sin(ang) * h * 0.42 * band;
    },

    // No destination. Points stay where they fell and breathe. Used wherever
    // the page's job is to be read rather than to impress.
    drift: function (p) {
      p.hx = p.nx;
      p.hy = p.ny;
    }
  };

  /* -------------------------------------------------------------------------
     4. THE FIELD
     ------------------------------------------------------------------------- */
  function initField(el, host, mode, hue, tier) {
    var ctx = el.getContext && el.getContext('2d');
    if (!ctx) return;

    var shape = TOPOLOGY[mode] || TOPOLOGY.lattice;
    var w = 0, h = 0, pts = [], raf = 0;
    var t0 = 0, running = false, visible = true;
    var px = -9999, py = -9999, sx = -9999, sy = -9999;
    var DETECT = tier.detect;
    var LINK = Math.round(tier.detect * 0.45);

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
      // Tier by page, then by area, then again for touch devices — which have
      // no cursor to drive the detector and no active cooling.
      var per = coarsePointer ? tier.per * 1.9 : tier.per;
      var n = Math.round(w * h / per);
      n = Math.max(60, Math.min(coarsePointer ? 300 : 900, n));

      pts = [];
      for (var i = 0; i < n; i++) {
        var p = {
          nx: Math.random() * w,
          ny: Math.random() * h,
          hx: 0, hy: 0, x: 0, y: 0, a: 0, r: 0, b: 0,
          ph: Math.random() * Math.PI * 2,
          sp: 0.00016 + Math.random() * 0.00034,
          am: 1.6 + Math.random() * 3.4,
          hub: Math.random() < 0.024
        };
        shape(p, i, n, w, h);
        pts.push(p);
      }
    }

    function hueAt(x) { return hue[0] + (hue[1] - hue[0]) * (x / w); }

    function draw(now) {
      if (!t0) t0 = now;
      var age = now - t0;

      // Scatter to topology, easeOutCubic over 2.4s. Then it holds.
      var settle = tier.resolve ? Math.min(age / 2400, 1) : 1;
      settle = 1 - Math.pow(1 - settle, 3);

      sx += (px - sx) * 0.14;
      sy += (py - sy) * 0.14;

      var sweep = tier.sweep ? ((((age % 9000) / 9000) * (w * 1.35)) - w * 0.18) : -99999;
      var near = [];
      var i, j, p;

      ctx.clearRect(0, 0, w, h);

      for (i = 0; i < pts.length; i++) {
        p = pts[i];
        p.x = p.nx + (p.hx - p.nx) * settle + Math.cos(age * p.sp + p.ph) * p.am;
        p.y = p.ny + (p.hy - p.ny) * settle + Math.sin(age * p.sp * 1.3 + p.ph) * p.am;

        var alpha = (p.hub ? tier.base + 0.26 : tier.base) + tier.lift * settle;
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

      /* Linking every point to every other is O(n^2) on ~900 points. Linking
         only what the detector has already selected is O(k^2) on k of about 50
         — and it reads better, because a connection then means "what the
         instrument is currently resolving" rather than "everything, always". */
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
            ctx.strokeStyle = 'rgba(' + spectrum(hueAt((a.x + b.x) / 2)) + ',' + la.toFixed(3) + ')';
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      for (i = 0; i < pts.length; i++) {
        p = pts[i];
        ctx.fillStyle = 'rgba(' + spectrum(hueAt(p.x)) + ',' + p.a.toFixed(3) + ')';
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

    /* Reduced motion gets the resolved topology as a single still frame: the
       composition the design intends, with no rAF loop ever scheduled. */
    function drawStill() {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        var a = tier.base + tier.lift + (p.hub ? 0.26 : 0);
        ctx.fillStyle = 'rgba(' + spectrum(hueAt(p.hx)) + ',' + a.toFixed(3) + ')';
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

  /* -------------------------------------------------------------------------
     5. MOUNT

     The canvas is created here rather than written into 39 body files. It is
     decorative and aria-hidden, carries no content, has no semantics and no SEO
     value, and without scripting there would be nothing to put in it — so the
     markup is better off not mentioning it at all. Sitting after .ax-grid-bg
     puts the field above the engineering grid and below the copy.
     ------------------------------------------------------------------------- */
  var hero = doc.querySelector('.ax-hero');
  var canvas = null;
  var prof = profile();

  if (hero && prof) {
    canvas = doc.createElement('canvas');
    canvas.className = 'ax-field';
    canvas.setAttribute('aria-hidden', 'true');

    var grid = hero.querySelector('.ax-grid-bg');
    if (grid && grid.nextSibling) hero.insertBefore(canvas, grid.nextSibling);
    else if (grid) hero.appendChild(canvas);
    else hero.insertBefore(canvas, hero.firstChild);

    initField(canvas, hero, prof[0], HUE[prof[1]] || HUE.full, TIER[prof[2]] || TIER.sparse);
  }

  /* -------------------------------------------------------------------------
     6. THE GOVERNED RUN

     Five pages carry a terminal holding a real trace of one of these systems
     working. Playing it on a timeline turns a still image into a demonstration.

     Every one of those traces halts somewhere — at a write gate, a validator
     repair, a pending approval — and that halt is the argument the page is
     making. So the pause is not configured per page: a row is given a long beat
     ahead of it when it contains something painted in the warn colour, which is
     already how this codebase marks "stopped, waiting for a human". The markup
     says where the interesting moment is, and the timing follows it.

     Rows reveal nodes that already exist rather than typing characters, so the
     bilingual engine in axio.css is untouched and both trees play identically.
     ------------------------------------------------------------------------- */
  var HERO_CUES = [200, 820, 1240, 1680, 2120, 3400, 4700, 5300];

  function rowsOf(run) {
    // Hand-tuned markup wins: the homepage hero is timed frame by frame.
    var explicit = run.querySelectorAll('.ax-run-row');
    if (explicit.length) return { rows: explicit, tuned: true };

    /* Otherwise take the terminal's body — the block after the title bar — and
       treat its element children as the trace. Discovering rows here is what
       lets a page opt in by adding one class instead of tagging every line. */
    var bar = run.querySelector('.ax-terminal-bar');
    var body = bar && bar.nextElementSibling;
    if (!body) return { rows: [], tuned: false };

    var kids = [];
    for (var i = 0; i < body.children.length; i++) {
      var kid = body.children[i];
      kid.classList.add('ax-run-row');
      kids.push(kid);
    }
    return { rows: kids, tuned: false };
  }

  function cuesFor(rows) {
    var out = [];
    var t = 260;
    for (var i = 0; i < rows.length; i++) {
      out.push(t);
      var next = rows[i + 1];
      // A warn-coloured row is where this trace stops and asks a person.
      var halts = next && next.querySelector('[class*="ax-warn"]');
      t += halts ? 1300 : 430;
    }
    return out;
  }

  if (!reduceMotion) {
    Array.prototype.forEach.call(doc.querySelectorAll('.ax-run'), function (run) {
      var found = rowsOf(run);
      var rows = found.rows;
      if (!rows.length) return;

      var cues = found.tuned ? HERO_CUES : cuesFor(rows);

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
          }, cues[t] || t * 430);
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
    });
  }

  /* -------------------------------------------------------------------------
     7. PLANE PARALLAX

     Depth without 3D: the grid sits furthest back, the field mid, the copy
     fixed in front. Only the two background planes move, by at most 7px. The
     copy deliberately does not — promoting a headline to its own compositor
     layer to shift it 3px costs memory and risks text rasterisation for an
     effect nobody consciously registers. Relative motion against static type
     reads as depth just as well.

     The loop writes transform and reads nothing, so it never triggers layout,
     and it exits once the planes have caught up rather than idling at 60fps.
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
