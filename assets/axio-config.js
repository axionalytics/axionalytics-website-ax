/* ============================================================================
   AXIONALYTICS — SHARED TAILWIND CONFIGURATION
   ----------------------------------------------------------------------------
   Load order (required):
     1. https://cdn.tailwindcss.com
     2. assets/axio-config.js   <-- this file
     3. assets/axio.css

   PALETTE RATIONALE
   Colors are sampled from logo_fixed.png: a node-graph mark rendered in a
   teal -> cyan -> blue -> violet spectrum on deep navy. The pre-2026 site used
   an orange accent (#F97316) that appears nowhere in the mark. This config
   retires the orange and rebuilds the system on the logo's own spectrum.
   ============================================================================ */

tailwind.config = {
  theme: {
    extend: {
      colors: {
        ax: {
          /* --- Surfaces (darkest -> lightest) --- */
          void:    '#05080F', // page base, hero wells
          ink:     '#0A101C', // primary dark background
          navy:    '#111C30', // raised dark surface / logo plate
          slate:   '#1B2942', // cards on dark, borders
          steel:   '#2C3E5C', // hairlines, dividers on dark
          mist:    '#F6F8FC', // light section background
          cloud:   '#EDF1F8', // light surface alt

          /* --- Brand spectrum (sampled from the mark) --- */
          teal:    '#0EA5A5', // outer teal nodes
          cyan:    '#22D3EE', // connector highlight — primary accent
          blue:    '#3B82F6', // lower-center node
          indigo:  '#4F46E5', // spine gradient midpoint
          violet:  '#A855F7', // upper/lower right nodes
          magenta: '#C026D3', // node core highlight

          /* --- Semantic --- */
          go:      '#10B981', // verified / passing
          warn:    '#F59E0B', // attention, HITL pending
          stop:    '#F43F5E', // blocked / denied
        },
      },
      fontFamily: {
        heading: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
        mono:    ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
      },
      maxWidth: {
        prose: '68ch',
      },
      animation: {
        'fade-in':   'axFadeIn 0.5s ease-out forwards',
        'slide-up':  'axSlideUp 0.6s cubic-bezier(0.16,1,0.3,1) forwards',
        'float':     'axFloat 7s ease-in-out infinite',
        'pulse-ring':'axPulseRing 2.6s cubic-bezier(0.4,0,0.6,1) infinite',
        'dash':      'axDash 3s linear infinite',
        'marquee':   'axMarquee 38s linear infinite',
      },
      keyframes: {
        axFadeIn:   { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        axSlideUp:  { '0%': { opacity: '0', transform: 'translateY(26px)' },
                      '100%': { opacity: '1', transform: 'translateY(0)' } },
        axFloat:    { '0%,100%': { transform: 'translateY(0)' },
                      '50%': { transform: 'translateY(-12px)' } },
        axPulseRing:{ '0%':   { transform: 'scale(0.92)', opacity: '0.7' },
                      '70%':  { transform: 'scale(1.25)', opacity: '0' },
                      '100%': { transform: 'scale(1.25)', opacity: '0' } },
        axDash:     { '0%': { strokeDashoffset: '200' }, '100%': { strokeDashoffset: '0' } },
        axMarquee:  { '0%': { transform: 'translateX(0)' },
                      '100%': { transform: 'translateX(-50%)' } },
      },
      boxShadow: {
        'ax-card':  '0 1px 2px rgba(10,16,28,.04), 0 12px 32px -12px rgba(10,16,28,.18)',
        'ax-lift':  '0 24px 60px -20px rgba(10,16,28,.35)',
        'ax-glow':  '0 0 0 1px rgba(34,211,238,.28), 0 18px 50px -18px rgba(34,211,238,.45)',
      },
      backgroundImage: {
        'ax-spectrum': 'linear-gradient(100deg,#0EA5A5 0%,#22D3EE 22%,#3B82F6 52%,#4F46E5 74%,#A855F7 100%)',
        'ax-grid':     'linear-gradient(rgba(44,62,92,.35) 1px,transparent 1px),linear-gradient(90deg,rgba(44,62,92,.35) 1px,transparent 1px)',
      },
    },
  },
};
