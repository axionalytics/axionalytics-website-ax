/* ============================================================================
   AXIONALYTICS — ROI CALCULATOR
   ----------------------------------------------------------------------------
   Runs entirely client-side. No input is transmitted while the user models.
   The email gate unlocks the detailed breakdown immediately and, if
   LEAD_ENDPOINT is configured below, posts a JSON summary in the background.
   Unconfigured, it captures nothing and says so in the comment there.

   Model
   -----
   Three scenarios, each reducing to the same shape: hours currently spent on
   mechanical work, the share of that work the platform absorbs, and the loaded
   hourly cost of the people doing it.

     reclaimed_hours = volume × hours_per_unit × automation_share
     gross_recovery  = reclaimed_hours × loaded_hourly_cost
     net_recovery    = gross_recovery − run_rate
     payback_months  = build_investment ÷ (net_recovery ÷ 12)

   Automation share is deliberately conservative and capped below 1.0 — review,
   judgment, and exception handling do not go away, and a calculator that claims
   they do is one a CFO discards. Defaults are documented inline so a buyer can
   argue with the assumptions rather than the arithmetic.
   ============================================================================ */
(function () {
  'use strict';

  var form = document.getElementById('roi-form');
  if (!form) return;

  /* -------------------------------------------------------------------------
     Scenario presets
     hoursPerUnit  — engineer-hours the mechanical task consumes per unit
     autoShare     — fraction of those hours the platform absorbs (capped)
     unitLabel     — what "volume" counts, per scenario
     ------------------------------------------------------------------------- */
  var SCENARIOS = {
    test: {
      hoursPerUnit: 3.2,   // hours to hand-author one reviewed test case
      autoShare: 0.62,     // transcription absorbed; review and judgment remain
      runRateShare: 0.08,  // annual platform run cost as a share of gross recovery
      buildInvestment: 285000
    },
    bi: {
      hoursPerUnit: 21,    // analyst-hours per dashboard request, first draft to publish
      autoShare: 0.68,
      runRateShare: 0.07,
      buildInvestment: 240000
    },
    agent: {
      hoursPerUnit: 1.4,   // hours per manual research-and-update workflow
      autoShare: 0.55,
      runRateShare: 0.10,
      buildInvestment: 320000
    }
  };

  var state = { scenario: 'test' };

  /* ---------------------------------------------------------------------- */
  function $(id) { return document.getElementById(id); }

  function num(id) {
    var el = $(id);
    if (!el) return 0;
    var v = parseFloat(el.value);
    return isFinite(v) ? v : 0;
  }

  function money(v) {
    return '$' + Math.round(v).toLocaleString('en-US');
  }

  function moneyCompact(v) {
    if (Math.abs(v) >= 1000000) return '$' + (v / 1000000).toFixed(1) + 'M';
    if (Math.abs(v) >= 1000) return '$' + Math.round(v / 1000) + 'K';
    return '$' + Math.round(v);
  }

  function hours(v) {
    return Math.round(v).toLocaleString('en-US');
  }

  /* ----------------------------------------------------------------------
     Core model
     ---------------------------------------------------------------------- */
  function compute() {
    var s = SCENARIOS[state.scenario];

    var volume = num('roi-volume');        // units per year
    var people = num('roi-people');        // FTE doing the work
    var salary = num('roi-salary');        // loaded annual cost per FTE

    // Loaded hourly cost: 1,880 productive hours/year is the conventional
    // planning figure once PTO, holidays, and non-project time are removed.
    var hourlyCost = salary / 1880;

    var currentHours = volume * s.hoursPerUnit;
    var reclaimedHours = currentHours * s.autoShare;

    // Capacity is bounded by the team that actually exists — you cannot
    // reclaim more hours than the group works in a year.
    var teamCapacity = people * 1880;
    if (reclaimedHours > teamCapacity) reclaimedHours = teamCapacity;

    var grossRecovery = reclaimedHours * hourlyCost;
    var runRate = grossRecovery * s.runRateShare;
    var netRecovery = grossRecovery - runRate;

    var paybackMonths = netRecovery > 0
      ? (s.buildInvestment / (netRecovery / 12))
      : Infinity;

    var threeYearNet = (netRecovery * 3) - s.buildInvestment;
    var roiPct = s.buildInvestment > 0
      ? (threeYearNet / s.buildInvestment) * 100
      : 0;

    return {
      hourlyCost: hourlyCost,
      currentHours: currentHours,
      reclaimedHours: reclaimedHours,
      fteEquivalent: reclaimedHours / 1880,
      grossRecovery: grossRecovery,
      runRate: runRate,
      netRecovery: netRecovery,
      paybackMonths: paybackMonths,
      threeYearNet: threeYearNet,
      roiPct: roiPct,
      buildInvestment: s.buildInvestment,
      autoShare: s.autoShare,
      hoursPerUnit: s.hoursPerUnit,
      capped: (volume * s.hoursPerUnit * s.autoShare) > teamCapacity
    };
  }

  /* ----------------------------------------------------------------------
     Render
     ---------------------------------------------------------------------- */
  function render() {
    var r = compute();

    setText('out-hours', hours(r.reclaimedHours));
    setText('out-fte', r.fteEquivalent.toFixed(1));
    setText('out-net', moneyCompact(r.netRecovery));
    setText('out-payback', isFinite(r.paybackMonths) ? r.paybackMonths.toFixed(1) : '—');

    // Detailed breakdown (revealed after the gate)
    setText('det-hourly', money(r.hourlyCost) + '/hr');
    setText('det-current', hours(r.currentHours) + ' hrs');
    setText('det-share', Math.round(r.autoShare * 100) + '%');
    setText('det-reclaimed', hours(r.reclaimedHours) + ' hrs');
    setText('det-gross', money(r.grossRecovery));
    setText('det-runrate', '−' + money(r.runRate));
    setText('det-net', money(r.netRecovery));
    setText('det-invest', money(r.buildInvestment));
    setText('det-3yr', money(r.threeYearNet));
    setText('det-roi', Math.round(r.roiPct) + '%');
    setText('det-perunit', r.hoursPerUnit.toFixed(1) + ' hrs');

    var capNote = $('roi-cap-note');
    if (capNote) capNote.hidden = !r.capped;

    // Live echo of slider values
    setText('echo-volume', num('roi-volume').toLocaleString('en-US'));
    setText('echo-people', num('roi-people').toLocaleString('en-US'));
    setText('echo-salary', money(num('roi-salary')));

    // The submitted payload is assembled from compute() at submit time rather
    // than mirrored into hidden inputs, so it cannot drift from what is on
    // screen.
  }

  function setText(id, value) {
    var el = $(id);
    if (el) el.textContent = value;
  }

  /* ----------------------------------------------------------------------
     Scenario tabs
     ---------------------------------------------------------------------- */
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-scenario]'),
    function (btn) {
      btn.addEventListener('click', function () {
        state.scenario = btn.getAttribute('data-scenario');

        Array.prototype.forEach.call(
          document.querySelectorAll('[data-scenario]'),
          function (b) {
            var on = b === btn;
            b.setAttribute('aria-selected', on ? 'true' : 'false');
            b.classList.toggle('bg-ax-cyan', on);
            b.classList.toggle('text-ax-void', on);
            b.classList.toggle('text-white/60', !on);
          }
        );

        Array.prototype.forEach.call(
          document.querySelectorAll('[data-scenario-label]'),
          function (el) {
            el.hidden = el.getAttribute('data-scenario-label') !== state.scenario;
          }
        );

        render();
      });
    }
  );

  /* ----------------------------------------------------------------------
     Inputs
     ---------------------------------------------------------------------- */
  Array.prototype.forEach.call(
    form.querySelectorAll('input[type="range"], input[type="number"]'),
    function (input) { input.addEventListener('input', render); }
  );

  /* ----------------------------------------------------------------------
     Email gate
     ----------------------------------------------------------------------
     CONFIGURE ME — set LEAD_ENDPOINT to start capturing.

       Formspree (works on GitHub Pages):
         https://formspree.io/f/xxxxxxxx      <- create a form, paste its URL

       Netlify Forms (only if hosted on Netlify):
         '/' plus a hidden form-name field; see Netlify's docs

       Any endpoint accepting a JSON POST also works.

     Left empty, the gate still unlocks the breakdown client-side and captures
     nothing. That is deliberate: a dead form that silently swallows an address
     is worse than an honest one that does not ask.

     The unlock never waits on the network. A visitor who gave you an address
     should not stare at a spinner because your form provider is slow, and the
     breakdown is not secret — the email is a courtesy, not a paywall.
     ---------------------------------------------------------------------- */
  var LEAD_ENDPOINT = 'https://formspree.io/f/xwvgabdz';

  var gate = $('roi-gate');
  var detail = $('roi-detail');
  var gateBtn = $('roi-gate-submit');
  var gateNote = $('roi-gate-note');

  /* The gate is NOT a <form>, and must never become one again.
     ------------------------------------------------------------------------
     The whole calculator is wrapped in #roi-form, and HTML forbids nesting one
     form inside another: the parser silently discards the inner start tag. An
     earlier version had <form id="roi-gate-form"> here, so that element never
     existed in the DOM, getElementById returned null, no submit listener was
     ever attached, and the button — now owned by the outer form, which carries
     onsubmit="return false" — did nothing at all when clicked. No console
     error, no visible failure. The gate simply never worked in production.

     So: a plain button with a click handler, plus Enter on the email field to
     keep the keyboard behaviour a form would have given for free. */
  if (gateBtn) {
    gateBtn.addEventListener('click', submitGate);
  }

  var emailField = $('field-email');
  if (emailField) {
    emailField.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.keyCode === 13) {
        e.preventDefault();
        submitGate();
      }
    });
  }

  function submitGate() {
    var email = $('field-email');
    if (!email || !email.checkValidity()) {
      if (email) email.reportValidity();
      return;
    }

    // Flat, human-readable keys. Form services (Formspree, Netlify) render
    // each key as a row in the notification email; a nested object would
    // arrive as "[object Object]" or raw JSON, which is unreadable in an
    // inbox. Values are pre-formatted for the same reason.
    var r = compute();
    var scenarioLabel = {
      test:  'Test Engineering',
      bi:    'Business Intelligence',
      agent: 'Autonomous Workflows'
    }[state.scenario] || state.scenario;

    var payload = {
      email: email.value.trim(),
      _subject: 'ROI calculator — ' + scenarioLabel + ' — ' + money(r.netRecovery) + '/yr',

      scenario: scenarioLabel,
      reclaimed_hours: hours(r.reclaimedHours) + ' hrs/yr',
      fte_equivalent: r.fteEquivalent.toFixed(1) + ' FTE',
      net_annual_recovery: money(r.netRecovery),
      payback: isFinite(r.paybackMonths) ? r.paybackMonths.toFixed(1) + ' months' : 'n/a',
      three_year_net: money(r.threeYearNet),

      input_volume: num('roi-volume').toLocaleString('en-US'),
      input_people: num('roi-people') + ' FTE',
      input_loaded_cost: money(num('roi-salary')),

      source: 'roi-calculator',
      page: window.location.href
    };

    if (window.axioTrack) {
      window.axioTrack('roi_unlock', {
        scenario: state.scenario,
        captured: LEAD_ENDPOINT ? 'yes' : 'no'
      });
    }

    // Reveal first, transmit second.
    unlock();

    if (!LEAD_ENDPOINT) return;

    send(payload);
  }

  function send(payload) {
    if (!window.fetch) return;
    fetch(LEAD_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (res) {
      note(res.ok
        ? 'Sent — the summary is on its way to your inbox.'
        : 'We could not send the summary. The breakdown below is still yours.');
    }).catch(function () {
      note('We could not send the summary. The breakdown below is still yours.');
    });
  }

  function note(msg) {
    if (!gateNote) return;
    gateNote.textContent = msg;
    gateNote.hidden = false;
  }

  function unlock() {
    if (gate) gate.hidden = true;
    if (detail) {
      detail.hidden = false;
      detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    try { sessionStorage.setItem('axio-roi-unlocked', '1'); } catch (e) {}
  }

  try {
    if (sessionStorage.getItem('axio-roi-unlocked') === '1') unlock();
  } catch (e) {}

  /* ----------------------------------------------------------------------
     Print / export
     ---------------------------------------------------------------------- */
  var printBtn = $('roi-print');
  if (printBtn) printBtn.addEventListener('click', function () { window.print(); });

  render();
})();
