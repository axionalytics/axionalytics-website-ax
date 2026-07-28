# -*- coding: utf-8 -*-
"""
Add LocalBusiness schema to the homepage and contact page.

WHY
---
Axionalytics is a firm with a real address in Davenport, Iowa, and the site
carried no local signal at all — no LocalBusiness markup, no geographic service
area, no coordinates. That makes it invisible to "AI consultant near me",
"data consulting Iowa", and the map pack, which is a whole channel forgone.

It also matters beyond local search: a verifiable physical presence is a trust
signal for a firm asking enterprises to let it inside their perimeter.

WHAT IS DEDUCED vs SUPPLIED
---------------------------
Locality, region, country, email, phone, and languages are already established
elsewhere on the site, so they are reused. Street address and geo coordinates
are NOT invented — Google tolerates a business without a public street address
(many consultancies do not publish one), and a fabricated one would fail
verification against a Google Business Profile later. Fill STREET and GEO below
if and when you want them public.

Idempotent: skips any page that already declares LocalBusiness.

Usage: python _build/scripts/add-local-business.py
"""
import io
import os

BASE = "https://www.axionalytics.com"
PAGES = "_build/pages"

# --- supply these only if you want them publicly listed ---------------------
STREET = ""          # e.g. "123 Main St, Suite 400"
POSTAL = ""          # e.g. "52801"
GEO_LAT = ""         # e.g. "41.5236"
GEO_LON = ""         # e.g. "-90.5776"
# ---------------------------------------------------------------------------

TARGETS = ["index", "contact"]


def block():
    parts = [
        '      "@type": ["ProfessionalService", "LocalBusiness"],',
        '      "@id": "%s/#localbusiness",' % BASE,
        '      "name": "Axionalytics",',
        '      "url": "%s/",' % BASE,
        '      "image": "%s/assets/og-card.png",' % BASE,
        '      "logo": "%s/assets/favicon-512.png",' % BASE,
        '      "email": "info@axionalytics.com",',
        '      "telephone": "+1-956-207-9368",',
        '      "priceRange": "$$$$",',
        ('      "description": "Axionalytics designs and ships production agentic '
         'AI systems for enterprise engineering, data, and revenue organizations. '
         'Deployed inside the customer perimeter, governed by human approval, '
         'delivered with full source transfer.",'),
    ]

    addr = ['      "address": {',
            '        "@type": "PostalAddress",']
    if STREET:
        addr.append('        "streetAddress": "%s",' % STREET)
    addr += ['        "addressLocality": "Davenport",',
             '        "addressRegion": "IA",']
    if POSTAL:
        addr.append('        "postalCode": "%s",' % POSTAL)
    addr += ['        "addressCountry": "US"',
             '      },']
    parts += addr

    if GEO_LAT and GEO_LON:
        parts += ['      "geo": {',
                  '        "@type": "GeoCoordinates",',
                  '        "latitude": "%s",' % GEO_LAT,
                  '        "longitude": "%s"' % GEO_LON,
                  '      },']

    parts += [
        '      "areaServed": [',
        '        { "@type": "Country", "name": "United States" },',
        '        { "@type": "Place", "name": "Worldwide (remote delivery)" }',
        '      ],',
        '      "knowsLanguage": ["en", "es"],',
        '      "sameAs": [',
        '        "https://www.linkedin.com/company/axionalytics",',
        '        "https://www.instagram.com/axionalytics"',
        '      ],',
        # Consulting engagements are booked, not walked into. Advertising
        # business hours a caller cannot rely on is worse than omitting them;
        # the booking link is the real availability signal.
        '      "hasOfferCatalog": {',
        '        "@type": "OfferCatalog",',
        '        "name": "Enterprise Agentic AI Solutions",',
        '        "itemListElement": [',
        '          { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Agentic Test Engineering" } },',
        '          { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Enterprise Agentic AI" } },',
        '          { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Agentic Business Intelligence" } },',
        '          { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Agentic Revenue Development" } },',
        '          { "@type": "Offer", "itemOffered": { "@type": "Service", "name": "Zero-Trust AI Governance" } }',
        '        ]',
        '      }',
    ]

    return ('\n  <script type="application/ld+json">\n  {\n'
            '    "@context": "https://schema.org",\n'
            '    "@graph": [\n    {\n'
            + "\n".join(parts) +
            '\n    }\n    ]\n  }\n  </script>\n')


def main():
    added = skipped = 0
    for slug in TARGETS:
        path = os.path.join(PAGES, slug + ".meta.html")
        if not os.path.exists(path):
            print("  missing %s" % path)
            continue
        s = io.open(path, encoding="utf-8").read()
        if "LocalBusiness" in s:
            print("  skip     %-12s already present" % slug)
            skipped += 1
            continue
        io.open(path, "w", encoding="utf-8").write(s.rstrip("\n") + "\n" + block())
        print("  added    %-12s LocalBusiness + ProfessionalService" % slug)
        added += 1

    if not (STREET and GEO_LAT):
        print("\n  note: street address and coordinates omitted (not supplied).")
        print("        Google accepts a service business without them. Fill STREET")
        print("        and GEO_* in this file only if you want them public, and")
        print("        make them match your Google Business Profile exactly.")

    print("\n  %d added, %d skipped" % (added, skipped))


if __name__ == "__main__":
    main()
