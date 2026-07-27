# axionalytics.com

The Axionalytics marketing site: a static, bilingual, generated site published
with GitHub Pages at [www.axionalytics.com](https://www.axionalytics.com).

No server, no database, no runtime dependencies. The published output is plain
HTML, one compiled stylesheet, and a little vanilla JavaScript.

| | |
|---|---|
| Pages | 39 English, 39 Spanish |
| Generated from | 15 articles, 7 glossary entries, 17 hand-written pages |
| CSS + JS shipped | ~80 KB total |
| Build | Python 3 and bash. No Node, no package manager, no lockfile. |

---

## Rule #1 — do not edit the files at the top level

`index.html`, `pricing.html`, everything in `es/` — all generated. Editing them
works until the next build, then the change is silently gone.

| To change… | Edit |
|---|---|
| Words on a page | `_build/pages/<name>.body.html` |
| Title, description, structured data | `_build/pages/<name>.meta.html` |
| An article | `_build/src/articles/<name>.html` |
| A glossary entry | `_build/src/glossary/<name>.html` |
| Navigation / footer | `_build/src/partials/` |
| Visual design | `assets/axio.css` |
| Behaviour | `assets/axio.js` |

Then rebuild.

---

## Build

```bash
bash _build/scripts/all.sh
```

Fourteen steps, under a minute, idempotent — run it as often as you like. Always
use this rather than individual scripts; several steps consume the output of
earlier ones.

```
_build/src/         ->  generators  ->  _build/pages/  ->  assembler
                                                             |
                                             bilingual pages at the root
                                                             |
                                                    language splitter
                                                    /                \
                                            *.html (en)        es/*.html
```

The ordering constraint that matters: the language splitter must run after the
assembler. The assembler emits pages containing both languages; the splitter
consumes and replaces them. Run the splitter twice without rebuilding and there
would be no second language left to extract — so it refuses, rather than
destroying the Spanish tree.

### The steps

| # | Script | Does |
|---|---|---|
| 1 | `make-articles.py` | Articles + blog index, from the `ARTICLES` manifest |
| 2 | `make-glossary.py` | Glossary entries + hub, from the `TERMS` manifest |
| 3 | `extract-legal.py` | Re-wraps the legal pages from `_legacy/`, wording unchanged |
| 4 | `add-breadcrumbs.py` | `BreadcrumbList` data for hand-written pages |
| 4b | `add-local-business.py` | `LocalBusiness` data on home and contact |
| 5 | `make-author-page.py` | `author.html`, only once a name is set in `author.py` |
| 6 | `sanitize-sources.py` | Applies the editorial substitution list |
| 7 | `build.sh` | Assembles head + meta + header + body + footer |
| 8 | `add-contextual-links.py` | In-prose internal links on matched phrases |
| 9 | `build-tailwind.py` | Compiles the utility stylesheet actually in use |
| 10 | `make-i18n.py` | Splits bilingual pages into `/` and `/es/` |
| 11 | `make-feeds.py` | `rss.xml`, `llms.txt` |
| 12 | `make-sitemap.py` | `sitemap.xml`, both languages |
| 13 | `make-redirects.sh` | Stubs for retired URLs |
| 14 | `check-leaks.py` | Verification gate; non-zero exit fails the build |

Run by hand only when needed: `make-logo-assets.py` (regenerates logo PNGs and
favicons), `install-hooks.sh` (once per clone, see below).

---

## Layout

```
├── *.html, es/, assets/     published site (generated — do not edit)
├── sitemap.xml, rss.xml, llms.txt, robots.txt, CNAME
├── _config.yml              tells GitHub Pages what to leave unpublished
│
├── _build/                  in git, not on the website
│   ├── scripts/             the generators
│   ├── src/                 hand-written source: articles, glossary, partials
│   ├── pages/               assembly staging
│   └── retired/             superseded scripts, kept for reference
│
├── _legacy/                 the previous version of the site
└── _private/                local working material — not in version control
```

GitHub Pages runs Jekyll, which ignores folders whose names begin with `_`.
`_config.yml` states the same exclusions explicitly so nothing depends on that
convention being known. **Never add a `.nojekyll` file** — it disables the
underscore rule and would publish everything.

Anything at the top level is served to the public, whether or not it looks like a
web page. Assume that by default.

---

## Two languages

Every page exists twice: `/pricing.html` and `/es/pricing.html`, each in one
language only, with reciprocal `hreflang` annotations and an `x-default`.

Source pages are written bilingually, marking each language inline, and step 10
splits them. This is deliberate — a single-language page can rank, whereas a page
containing both languages is ambiguous to a search engine and reads as duplicate
content. The language switcher in the header is a plain link between the two
URLs.

`/es/` is machine-translated with technical vocabulary reviewed by hand.

---

## Conventions worth knowing

**Structured data.** 212 JSON-LD blocks across the site: `Article`, `FAQPage`,
`BreadcrumbList`, `DefinedTerm`, `LocalBusiness`, `Service`, `Organization`.
Emitted by the generators, so they cannot drift from the content.

**Pillar and cluster.** Five commercial pages are pillars; every article and
glossary entry declares exactly one pillar in the manifest and links to it. The
link is generated, never typed.

**No CDN.** The stylesheet is compiled locally from the utility classes actually
present in the output. This replaced a 400 KB CDN dependency with roughly 29 KB
and removed a render-blocking third-party request.

**`author.py`.** Article attribution is configurable from one constant. Left
empty it attributes to the organisation; set to a name it switches every article
to person attribution and generates a profile page. It ships empty.

---

## Contributing

```bash
git clone https://github.com/axionalytics/axionalytics-website-ax.git
cd axionalytics-website-ax
bash _build/scripts/install-hooks.sh    # once per clone
bash _build/scripts/all.sh
python -m http.server 8000              # then open http://localhost:8000
```

`install-hooks.sh` installs a pre-commit hook. Git hooks are not cloned with a
repository, which is why installing it is a manual step.

Step 6 and step 14 read an editorial substitution list from `_private/`, which is
outside version control. In a fresh clone both announce that the list is absent
and do nothing — correct behaviour, since the committed sources already reflect
every substitution.

---

## Deploying

Push to `main`. GitHub Pages rebuilds within a minute or two.

```bash
bash _build/scripts/all.sh
git add -A
git commit -m "…"
git push
```

Do not push without rebuilding: the generated pages are committed, so skipping
the build publishes stale HTML alongside fresh sources.

---

## Licence

© Axionalytics. All rights reserved. The site content, copy, and visual design
are not licensed for reuse.
