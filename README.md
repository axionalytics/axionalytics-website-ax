# Axionalytics Website

The complete guide to this website: what it is, how it is built, what every file
does, and what is left to do.

**This document assumes no prior knowledge.** If a term looks unfamiliar, it is
explained the first time it appears. If you only read one section, read
[Rule #1](#rule-1-never-edit-files-at-the-top-level).

---

## Table of contents

1. [What this project is](#1-what-this-project-is)
2. [Rule #1: never edit files at the top level](#rule-1-never-edit-files-at-the-top-level)
3. [Folder structure — what lives where](#3-folder-structure--what-lives-where)
4. [How the build works](#4-how-the-build-works)
5. [Every build script explained](#5-every-build-script-explained)
   - [5.1 The author system](#51-the-author-system)
   - [5.2 Contextual linking](#52-contextual-linking)
6. [The design system](#6-the-design-system)
7. [How the site is organised for search](#7-how-the-site-is-organised-for-search)
8. [The two languages](#8-the-two-languages)
9. [Common tasks, step by step](#9-common-tasks-step-by-step)
10. [Decisions we made, and why](#10-decisions-we-made-and-why)
11. [What is left to do](#11-what-is-left-to-do)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. What this project is

A marketing website for Axionalytics, a firm that builds production agentic AI
systems for large enterprises. It sells five solutions and is written for a
technical buyer — a CTO, a VP of Engineering, a security architect.

**It is a static site.** There is no server, no database, no login. It is a
folder of HTML files that a web host serves exactly as they are. That makes it
fast, cheap, and almost impossible to hack, because there is nothing running to
attack.

**It is hosted on GitHub Pages**, a free service that publishes files from a
code repository straight to the web.

### The numbers

| | |
|---|---|
| English pages | 43 (39 real pages + 4 redirect stubs) |
| Spanish pages | 39 |
| Articles | 15 |
| Glossary definitions | 7 + hub |
| Words of published English | ~11,200 in articles alone |
| Total CSS + JS shipped | ~80 KB |

---

## Rule #1: never edit files at the top level

This is the single most important thing in this document.

The `.html` files in the top folder — `index.html`, `pricing.html`,
`glossary.html`, and the rest — are **generated**. They are the *output* of a
build process, like a printed document is the output of a word processor.

If you edit `pricing.html` directly, your change works until the next time
anyone runs the build. Then it is silently erased.

### Where to edit instead

| You want to change… | Edit this |
|---|---|
| Words on a normal page | `_build/pages/<name>.body.html` |
| Page title / description / schema | `_build/pages/<name>.meta.html` |
| An article's text | `_build/src/articles/<name>.html` |
| A glossary definition's text | `_build/src/glossary/<name>.html` |
| The top navigation bar | `_build/src/partials/header.html` |
| The footer | `_build/src/partials/footer.html` |
| Colours, spacing, visual style | `assets/axio.css` |
| Interactive behaviour | `assets/axio.js` |

Then run:

```bash
bash _build/scripts/all.sh
```

**How to tell if a file is generated:** open it and look at the top. Generated
files say so in a comment within the first few lines.

---

## 3. Folder structure — what lives where

```
axionalytics-website-ax/
│
├── *.html                 ← THE LIVE ENGLISH SITE (generated — do not edit)
├── es/                    ← THE LIVE SPANISH SITE (generated — do not edit)
├── assets/                ← stylesheets, scripts, images (edit these directly)
│
├── sitemap.xml            ← generated: list of every page, for search engines
├── robots.txt             ← tells crawlers what to skip
├── rss.xml                ← generated: article feed
├── llms.txt               ← generated: site map for AI crawlers
├── _config.yml            ← tells GitHub Pages what NOT to publish
├── README.md              ← this file
│
├── _build/                ← IN GIT, not on the website. The machinery.
│   ├── scripts/           ← the 21 programs that build the site
│   ├── src/               ← handwritten content
│   │   ├── articles/      ← blog article text
│   │   ├── glossary/      ← glossary definition text
│   │   └── partials/      ← header, footer, shared <head>
│   ├── pages/             ← assembly staging area
│   ├── retired/           ← old scripts, kept for reference
│   └── SETUP.md           ← the click-by-click setup runbook
│
├── _legacy/               ← IN GIT, not on the website. The pre-2026 site.
│
└── _private/              ← NOT IN GIT AT ALL. Confidential. Local only.
    ├── terms.py           ← the client term list the sanitiser reads
    ├── source-docs/       ← internal platform docs the site was written from
    ├── strategy/          ← strategy notes
    ├── media/             ← original logo artwork
    └── reference/         ← spreadsheets and misc
```

### Two different kinds of "not public", and why the difference matters

**This repository is public.** Anyone can read every file in it. That is fine,
and it is what lets GitHub Pages serve the site for free — but it means there
are now two separate questions about any file, not one:

| | On the website? | In the public repo? |
|---|---|---|
| `index.html`, `assets/`, `es/` | **yes** | yes |
| `_build/`, `_legacy/` | no | **yes** |
| `_private/` | no | **no** |

**Kept off the website by `_config.yml`.** GitHub Pages runs Jekyll, and Jekyll
ignores folders whose names begin with `_`. `_config.yml` also lists them
explicitly, so the protection does not rely on a convention someone might not
know. This is what keeps `_build/` and `_legacy/` out of the published site —
they are perfectly readable in the repository, they just are not web pages.

**Kept out of the repository by `.gitignore`.** `_private/` is different in kind.
It contains a customer's internal engineering documents and the term list that
keeps them unidentifiable. It is not committed, not pushed, and not backed up —
it exists on one laptop.

> **Both of these were real problems, not hypotheticals.**
>
> The internal platform documents once sat at the *top level* and were publicly
> downloadable — 548 KB naming a client 67 times. Moving them to `_private/`
> fixed the website exposure.
>
> Then going public created a second, different exposure: `_private/` would have
> been readable in the repo even though it was invisible on the site. That is
> why it is now untracked, guarded by a pre-commit hook, and verified on every
> build.

**The rule now has two halves:**

1. If a stranger should not see it **on the website**, it goes in a folder
   starting with an underscore. Never add a `.nojekyll` file — that switch turns
   off the underscore protection and would republish everything.
2. If a stranger should not see it **at all**, it goes in `_private/`, and it is
   never committed. See [section 10](#confidentiality).

---

## 4. How the build works

Think of it like a factory line. Raw text goes in one end; finished web pages
come out the other.

```
   _build/src/articles/*.html          (you write the words)
   _build/src/glossary/*.html
   _build/pages/*.body.html
                  │
                  ▼
   [ generator scripts ]               steps 1–6: turn text into page pieces
                  │
                  ▼
   _build/pages/*.{meta,body}.html     (staging: head + body for every page)
                  │
                  ▼
   [ build.sh ]                        step 7: glue on header + footer
                  │
                  ▼
   bilingual pages at the top level    (every page contains BOTH languages)
                  │
                  ▼
   [ add-contextual-links.py ]         step 8: link key phrases inside prose
                  │
                  ▼
   [ make-i18n.py ]                    step 10: split into two language trees
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
   /*.html (English)    /es/*.html (Spanish)
```

### Running it

```bash
bash _build/scripts/all.sh
```

That runs all 14 steps in the correct order. **Always use this** rather than
running individual scripts, because several steps depend on the output of
earlier ones.

The most important ordering rule: `make-i18n.py` **must** run after `build.sh`.
`build.sh` produces pages containing both languages; `make-i18n.py` splits them
apart and overwrites the originals. Run it twice in a row without rebuilding and
it would have no Spanish left to extract — so it now refuses to run in that
situation and tells you what to do.

---

## 5. Every build script explained

All in `_build/scripts/`. Run from the project's top folder.

### The 14 steps of `all.sh`

| # | Script | What it does |
|---|---|---|
| 1 | `make-articles.py` | Wraps article text in the shared article layout. Also generates the blog index page. Reads the `ARTICLES` list inside the file, which holds every article's title, date, description, and which solution it supports. |
| 2 | `make-glossary.py` | Same for glossary definitions. Reads the `TERMS` list. Also builds the glossary hub. |
| 3 | `extract-legal.py` | Pulls the privacy policy, terms, and accessibility text out of the old site in `_legacy/` and rewraps it in the new design. **The legal wording is copied unchanged** — restyling should never silently reword terms someone agreed to. |
| 4 | `add-breadcrumbs.py` | Adds "Home › Solutions › This Page" data for search results on the 10 handwritten pages. Skips any page that already has it. |
| 4b | `add-local-business.py` | Adds `LocalBusiness` data to the homepage and contact page, so the firm can appear in "AI consultant near me" style searches and the map pack. See [section 5.1](#51-the-author-system). Skips a page that already has it. |
| 5 | `make-author-page.py` | Generates `author.html` — but **only if a name has been filled in** in `author.py`. Otherwise it does nothing at all. See [section 5.1](#51-the-author-system). |
| 6 | `sanitize-sources.py` | Removes client-identifying details. See [section 10](#confidentiality). Safe to run repeatedly. |
| 7 | `build.sh` | The assembler. For each page: shared `<head>` + that page's meta + header + that page's body + footer → one finished file. |
| 8 | `add-contextual-links.py` | Turns key phrases inside article paragraphs into links to the relevant page — "BI backlog" becomes a link to the business-intelligence page. See [section 5.2](#52-contextual-linking). |
| 9 | `build-tailwind.py` | Compiles the stylesheet. See [section 6](#6-the-design-system). |
| 10 | `make-i18n.py` | Splits every bilingual page into an English version and a Spanish version. |
| 11 | `make-feeds.py` | Generates `rss.xml` and `llms.txt`. |
| 12 | `make-sitemap.py` | Generates `sitemap.xml` covering both languages. |
| 13 | `make-redirects.sh` | Creates the 4 "this page moved" stubs for retired URLs. |
| 14 | `check-leaks.py` | The safety net. Reads every published file and **fails the build** if any client-identifying term made it through. See [section 10](#confidentiality). |

`author.py` is not a step — it is a settings file that step 5 and step 1 both read.

### 5.1 The author system

Search engines weight content written by a named, identifiable person above
content attributed to a faceless company. Every article on this site is
currently signed "Axionalytics", which forfeits that.

The machinery to fix it is built and wired in, but **switched off**, because
turning it on requires one thing that must not be made up: a real person's name.

**To turn it on:** open `_build/scripts/author.py`, put a name in the `NAME`
line near the top, and run `bash _build/scripts/all.sh`. That one change:

* switches all 24 article and glossary pages from company attribution to
  person attribution in the search-engine data
* adds a visible "By ⟨name⟩" byline under each article title
* creates `author.html` — a bio page listing areas of work and every article
* points every byline at that page

Leave `NAME` empty and none of it happens. No half-built page reaches the
public, so the file is safe to ship unfilled — which is how it currently ships.

> **Do not invent a name.** The whole value of the signal is that it is a real
> person a reader could look up. A fabricated byline is worse than no byline.

`add-local-business.py` follows the same principle: it publishes the city,
region, country, email, and phone that were already public, and deliberately
leaves street address and map coordinates blank rather than guessing them.
A made-up address would fail verification against a Google Business Profile
later. Fill `STREET` and `GEO_LAT` / `GEO_LON` in that file only if you want
them public, and make them match the Business Profile exactly.

### 5.2 Contextual linking

Before this step, every internal link on the site lived in the navigation bar,
the related-articles grid, or the footer — furniture that repeats on every page.
Search engines weight a link inside a sentence far above a link in a template,
because the first is an editorial judgement and the second is boilerplate.

`add-contextual-links.py` reads a table of ~30 phrases and the page each one
should point to, then links the first occurrence of each inside article prose.
It currently inserts **21 links across 13 pages in each language tree** — 42 in
total, since it runs before the site is split into English and Spanish.

It is deliberately conservative, because over-linking reads as spam:

* only inside article body text, never in a heading or an existing link
* first occurrence of a term only, and never a page linking to itself
* a hard cap of 6 links per page
* English phrases match English text; Spanish phrases match Spanish text,
  tracked separately so the Spanish tree gets equal coverage

It runs on the finished pages rather than on the source text, which makes it
safe to run repeatedly: each build regenerates the pages from scratch, so links
are inserted once per build instead of piling up.

**Adding a phrase:** edit the `TARGETS` table in the script. The one rule that
matters — every phrase must be unambiguous on its own. "outbound" was removed
from the table because on the security pages it means outbound network traffic,
and linking that to a sales page misleads both the reader and the crawler.

### Scripts not in the pipeline

Run these by hand, only when needed.

| Script | When to run it |
|---|---|
| `make-logo-assets.py` | Only if the logo artwork changes. Turns the original file in `_private/media/` into transparent PNGs and favicons. |
| `retarget-legacy-nav.py` | One-time historical fix. You will not need it. |
| `install-hooks.sh` | Once per machine, after cloning. Installs the pre-commit guard that refuses to commit confidential material. Hooks are not cloned with a repository, so this cannot happen automatically. |
| `scan-staged.py` | Not run by hand — the pre-commit hook calls it. Scans staged content for client terms. |

### `_build/retired/`

`extract-articles.py` lives here. It was a one-time migration and would now
overwrite rewritten articles with old content. **Do not run it.** It is kept
because it documents a markup bug found in the old site.

---

## 6. The design system

### Two stylesheets

**`assets/tailwind.css` (29 KB) — generated, do not edit.**

Tailwind is a library of small styling shortcuts. Instead of writing a rule
saying "this box has 16px of padding", you write `p-4` on the element.

Originally this site loaded Tailwind from the internet as a 400 KB JavaScript
file that **compiled the stylesheet inside the visitor's browser on every single
page load.** That is slow, and page speed affects search ranking.

There is no Node.js on this machine, so the official Tailwind compiler is
unavailable. Instead `build-tailwind.py` does something more reliable than
re-implementing it: it collects every styling shortcut used anywhere on the
site, loads the real Tailwind library once in a headless browser, and captures
the stylesheet it produces. The result is exactly what the library would have
generated, minus the compiler. 400 KB of JavaScript became 29 KB of CSS.

> Run `build-tailwind.py` after introducing new Tailwind shortcuts. `all.sh`
> does it automatically.

**`assets/axio.css` (22 KB) — handwritten, edit freely.**

Everything custom: the colour palette, buttons, cards, the article typography.
Classes are prefixed `ax-` so you can always tell ours from Tailwind's.

### The colours

Sampled from the logo itself — a node graph in teal → cyan → blue → violet. The
old site used an orange accent that appears nowhere in the logo. Defined in
`assets/axio-config.js`.

| Name | Use |
|---|---|
| `ax-void` / `ax-ink` / `ax-navy` | dark backgrounds |
| `ax-cyan` | primary accent |
| `ax-blue` / `ax-indigo` / `ax-violet` | the spectrum |
| `ax-go` / `ax-warn` / `ax-stop` | success / caution / danger |

### The JavaScript

| File | Purpose |
|---|---|
| `assets/axio.js` | Menu, scroll animations, accordions, animated counters. Every part checks whether its markup exists first, so one shared file works on every page. |
| `assets/axio-roi.js` | The ROI calculator. All arithmetic runs in the visitor's browser; nothing is transmitted while they use it. |
| `assets/axio-analytics.js` | Visitor measurement. Currently inert — needs a token. |

### The logo

| File | Where used |
|---|---|
| `assets/logo-mark-dark.png` | header and footer (dark backgrounds) |
| `assets/logo-mark.png` | article author box (white backgrounds) |
| `assets/logo-mark-512.png` | full-resolution master, for print |
| `assets/favicon-32.png`, `favicon-512.png`, `apple-touch-icon.png` | browser tab and bookmarks |
| `assets/og-card.png` | preview image when the site is shared on social media |

Two versions exist because the logo's centre hub is pure black. At the 40px size
used in the header, a black hub is invisible against the near-black background
and the mark reads as a broken starburst. The dark-background version lifts the
hub to a light neutral and raises the darkest shading, **keeping every hue and
saturation unchanged** — the brand colours are not altered, they simply do not
fall below the page.

---

## 7. How the site is organised for search

### Pillar and cluster

Five **pillar** pages are what the business sells:

| Pillar | Page |
|---|---|
| Agentic Test Engineering | `agentic-test-engineering.html` |
| Enterprise Agentic AI | `enterprise-agentic-ai.html` |
| Agentic Business Intelligence | `agentic-business-intelligence.html` |
| Agentic Revenue Development | `agentic-revenue-development.html` |
| Zero-Trust AI Governance | `enterprise-ai-security.html` |

Every article and glossary page is a **cluster** page that supports exactly one
pillar, links up to it prominently, and names it in its structured data.

Why: search engines weigh a page partly by what links to it. Twenty-two supporting
pages all pointing at five commercial pages concentrates that weight where it
earns money, instead of spreading it evenly across a blog.

The link is not manual — each article declares its pillar in the manifest, and
the generator renders the link. It cannot drift.

### Structured data

212 blocks of machine-readable page description across the site, in a format
called JSON-LD. This is what produces rich search results — the FAQ dropdowns,
the breadcrumb trail, the article date.

Counts below are for the English tree; the Spanish tree mirrors them.

| Type | Count | Effect |
|---|---|---|
| BreadcrumbList | 35 | breadcrumb trail instead of a bare URL |
| FAQPage | 30 | question-and-answer dropdowns in results |
| Article / BlogPosting | 15 | article cards with dates |
| DefinedTerm | 14 | glossary definitions |
| LocalBusiness | 2 | eligibility for map-pack and "near me" results |
| Service, Organization, others | rest | describes the business |

`author.py` adds a `Person` type to every article and a `ProfilePage` on
`author.html` — but only once a name is filled in. See
[section 5.1](#51-the-author-system).

FAQ answers are written **BLUF** — bottom line up front. The direct answer is
the first sentence, because AI answer engines quote the opening and discard the
build-up.

### Files search engines read

| File | Purpose |
|---|---|
| `sitemap.xml` | All 78 URLs (39 pages × 2 languages), each declaring its translations |
| `robots.txt` | What to skip |
| `rss.xml` | Article feed for readers and aggregators |
| `llms.txt` | Plain-text site summary for AI crawlers |

---

## 8. The two languages

### How it works now

Two separate sets of pages:

- `https://www.axionalytics.com/pricing.html` — English only
- `https://www.axionalytics.com/es/pricing.html` — Spanish only

Each page contains **one** language. Each declares itself as that language,
points to itself as the authoritative version, and declares where its
translation lives. The language switcher in the header is a **link** to the
other URL.

### Why it was rebuilt this way

Originally every page contained both languages, with Spanish hidden by styling
and revealed by a toggle button. That works for a person clicking the switch and
is worthless for search:

- one address can only have one official language, so Spanish could never appear in Spanish search results;
- the tag that declares translations requires separate addresses, so none could be declared;
- hidden text is discounted by search engines anyway;
- every page carried roughly twice the content it needed.

Roughly ten thousand words of Spanish were returning nothing.

### Editing translations

Edit the source in `_build/`, where both languages sit side by side:

```html
<span data-lang-en>Book a Technical Briefing</span>
<span data-lang-es>Agendar Sesión Técnica</span>
```

Then rebuild. Step 8 separates them automatically.

> **Both spans must always exist.** The generator counts them and stops the
> build if they do not match, because a missing translation would produce a
> Spanish page with an English gap in it.

Page titles and descriptions have no spans to draw from, so their Spanish
versions live in the `ES_META` list at the top of `make-i18n.py`.

---

## 9. Common tasks, step by step

### Add a new article

**1.** Create `_build/src/articles/my-new-article.html`. Body text only — no
`<html>` or `<head>`. Every piece of text needs both languages:

```html
<p>
  <span data-lang-en><strong>Your opening answer goes here.</strong></span>
  <span data-lang-es><strong>Su respuesta inicial va aquí.</strong></span>
</p>

<h2>
  <span data-lang-en>A section heading</span>
  <span data-lang-es>Un encabezado de sección</span>
</h2>
```

Optionally add FAQ entries at the very top — these become search-result
dropdowns:

```html
<!--FAQ The question? | The answer, 40 to 60 words, direct.-->
```

**2.** Register it. Open `_build/scripts/make-articles.py` and add an entry to
the `ARTICLES` list, newest first:

```python
{
    "slug": "my-new-article",
    "pillar": "security",          # security | agentic | testing | bi | revenue
    "date": "2026-08-01",
    "date_en": "August 2026", "date_es": "Agosto 2026",
    "cat_en": "Security", "cat_es": "Seguridad",
    "title_en": "...", "title_es": "...",
    "desc_en": "...", "desc_es": "...",
},
```

**3.** Add the slug to the `PAGES` list in `_build/scripts/build.sh`, under the
right pillar comment.

**4.** Run `bash _build/scripts/all.sh`.

The blog index, sitemap, RSS feed, and related-article links all update
automatically.

### Add a glossary term

Same pattern: create `_build/src/glossary/what-is-thing.html`, add an entry to
`TERMS` in `make-glossary.py` (including the `answer_en` / `answer_es`
definition, which appears in three places), add the slug to `build.sh`, rebuild.

### Change wording on a normal page

Edit `_build/pages/<name>.body.html`, rebuild.

### Change the navigation or footer

Edit `_build/src/partials/header.html` or `footer.html`, rebuild. The change
appears on all 82 pages.

### Change a colour

Edit `assets/axio-config.js`, then run `bash _build/scripts/all.sh` — the
stylesheet has to be recompiled for a palette change to take effect.

### Publish

```bash
bash _build/scripts/all.sh
git add -A
git commit -m "Describe what changed"
git push
```

GitHub Pages updates in 1–2 minutes.

> **This folder is not yet a git repository.** If `git add` reports "not a git
> repository", that setup has not been done yet — see
> [section 11](#11-what-is-left-to-do).

---

## 10. Decisions we made, and why

### Positioning

The old site sold to small businesses — "enterprise-grade without the enterprise
price tag". The new one sells to Fortune 500 buyers. Those cannot coexist: SMB
language actively repels an enterprise buyer.

The organising argument is that **enterprise AI dies in the security
questionnaire, not the demo**. Every page answers an objection a security
architect raises.

### Confidentiality

The site was written from internal platform documentation for real client work.
Three categories were removed:

1. **Client identifiers.** A real requirement ID and three real signal names appeared verbatim in an illustrative screenshot. Replaced with synthetic equivalents.
2. **Exact metrics.** Unrounded counts — index sizes, test-suite totals — fingerprint one specific deployment: search the exact figure and you find the customer. Rounded to the nearest thousand. Same honest claim, nothing to match on. *(The real figures are deliberately not repeated here — quoting one in the document that explains the rule would defeat it.)*
3. **Named vendor components.** Replaced with category terms. This also covers the
   fourteen third-party services named in the revenue-development source: publishing
   that list would be a procurement recipe for a competitor and would tell prospects
   which vendors hold their contact record.

#### Where the rules live, and why not here

`sanitize-sources.py` enforces this on every build. It does **not** contain the
terms it removes.

That separation is the whole design. A sanitiser has to name what it is
deleting, which would make the sanitiser itself the most sensitive file in the
project — and this repository is public. So the 38 literal strings live in
`_private/terms.py`, which is never committed, and the script loads them at
runtime. Without that file the script degrades to a clearly-announced no-op,
which is the correct behaviour for anyone who clones this repo: the committed
sources are already clean, so there is nothing to remove and nothing to leak.

The same file feeds `check-leaks.py`, so the check can never drift from the
sanitiser — add a rule in one place and both are covered.

#### Three guards, because the mistake is irreversible

Losing a customer's documents to a public repo cannot be undone — deleting them
in a later commit leaves every earlier object reachable.

| Guard | Where | Catches |
|---|---|---|
| `.gitignore` | committed | `_private/` entering `git add` |
| `.git/hooks/pre-commit` | **not committed** | a force-added path, *and* a client term pasted into any staged file anywhere |
| `check-leaks.py` | build step 14 | git being able to see `_private/` at all |

The hook is the one that catches the leak that actually happens in practice —
not someone committing the source documents, but someone pasting a real
requirement ID into an article. That has already occurred once here: an earlier
README explained the exact-metrics rule *by quoting a real metric*.

Git hooks are never cloned, so on any new machine run:

```bash
bash _build/scripts/install-hooks.sh
```

#### `_private/` is not backed up

It is deliberately outside version control, which means git will not save you if
the disk fails. Copy it somewhere off this machine. `terms.py` especially — the
checks announce loudly if it goes missing, but they cannot rebuild it.

### Case studies name no clients

Deliberate. The work touches proprietary architecture and revenue data. A vendor
who leaks one client's name will eventually leak yours — the page says so.

### Published pricing

Most firms in this category will not publish a number. Ranges are published here
because withholding them wastes a month before either side learns whether the
budget is in the same order of magnitude.

### Honest numbers

Several claims were corrected during the build rather than carried forward:

- The old blog labelled 183-word articles as "12 min read". Read times are now computed from actual word count.
- The homepage ROI teaser showed different figures from the calculator itself. Both now derive from the same model.
- 28 styling shortcuts silently produced no output, so those borders had been falling back to defaults on the live site. Fixed.

### Cookieless analytics

Deliberate. This site sells zero-egress, privacy-preserving AI to security
architects. Loading a cookie-based tracker that requires a consent banner
undercuts the argument on the page — and cookieless needs no banner, which
removes the biggest conversion tax on a B2B site.

---

## 11. What is left to do

> **A click-by-click version of everything below lives in
> `_build/SETUP.md`** — every account to create, every button to press, every
> line number, in the order they have to happen. This section is the summary;
> that file is the walkthrough.

### Blocking — needs your credentials

These are the only things standing between the site and a working measurement,
lead-capture, and authorship loop. Each is a one-line paste.

| # | Task | File | Line |
|---|---|---|---|
| 1 | Cloudflare Web Analytics token | `assets/axio-analytics.js` | 36 |
| 2 | Formspree endpoint for the ROI form | `assets/axio-roi.js` | 240 |
| 3 | Google Search Console verification | `_build/src/partials/head-open.html` | 23 |
| 4 | Author name — turns on bylines and `author.html` | `_build/scripts/author.py` | 35 |

Items 1 and 2 take effect on save. **Items 3 and 4 require a rebuild** (they are
build sources). Item 3 can only be verified after the site is live.

Item 4 is described in full in [section 5.1](#51-the-author-system). The
machinery is built and tested; it stays dormant until a real name is supplied,
and a name must not be invented.

After verifying in Search Console, submit `sitemap.xml` — that is what tells
Google all 78 URLs exist.

### Google Business Profile

The site now publishes `LocalBusiness` data (step 4b), which is the half of
local search that lives on the website. The other half lives at Google: create
a free Business Profile at [business.google.com](https://business.google.com)
for Axionalytics in Davenport, Iowa.

The two halves have to agree. Use the same business name, phone number, and
city that appear in `_build/scripts/add-local-business.py`, or Google discounts
both. Service-area businesses can hide the street address; if you later choose
to publish one, put it in that script's `STREET` field so the two match exactly.

### Set up version control

This folder is **not a git repository**, which means there is no undo and no
history. `_legacy/` is currently the only rollback path. Setting up git should
happen before the next significant change.

### Spanish review

The `/es/` tree is machine-generated from translations written during the build.
The technical vocabulary is defensible, but commercial copy — the pillar pages
and pricing especially — should get a native-speaker pass before it is promoted
to Spanish-speaking buyers.

### Open-source inbound

The strategy notes in `_private/strategy/nash.md` call for sanitised public
repositories with search-optimised READMEs, driving referral traffic back here.
**Not started.**

### Content gaps

- No customer testimonials or named references (deliberate, but worth revisiting if a client ever grants permission)
- No case study PDFs or gated long-form assets beyond the calculator
- Only one comparison page; comparison queries are high-intent and under-served
- No "integrations" or "industries" pages

### Nice to have

- WebP versions of the logos (~7 KB saving; low priority since they are cached)
- Self-hosted fonts to remove the last third-party request
- A test that checks all internal links after every build, rather than manually

---

## 12. Troubleshooting

### "refusing to run: N pages carry no data-lang spans"

You ran `make-i18n.py` on its own after a previous run already split the pages.
This is the safety guard working as designed — it stops before doing damage.

**Fix:** run `bash _build/scripts/all.sh` instead.

### My change disappeared

You edited a generated file at the top level. See
[Rule #1](#rule-1-never-edit-files-at-the-top-level). Re-apply the change in
`_build/` and rebuild.

### "bilingual parity broken — N EN spans vs M ES spans"

An article has a `data-lang-en` without a matching `data-lang-es`, or the
reverse. The build stops rather than publish a page with a language gap.

**Fix:** the error names the file. Find the unpaired span and add its partner.

### A colour change did nothing

Palette changes live in `assets/axio-config.js`, which is the *source* the
stylesheet is compiled from — it is not loaded by the browser. Run
`bash _build/scripts/all.sh` to recompile.

### A style is missing after adding new markup

You used a Tailwind shortcut not previously used anywhere. Run
`bash _build/scripts/all.sh`, which recompiles the stylesheet to include it.

### The build fails on `build-tailwind.py`

It needs Chrome or Edge to capture the compiled stylesheet. If neither is
installed at a standard location, this step fails. The rest of the site still
builds; the stylesheet simply is not refreshed.

### I want to see the old site

Open any file in `_legacy/`. It is a complete snapshot of the pre-2026 site,
including its logo. It is not published.

---

## Quick reference

```bash
# Build everything (the command you will use 95% of the time)
bash _build/scripts/all.sh

# Preview locally, then open http://localhost:8000
python -m http.server 8000

# Check for broken internal links
for f in *.html; do
  grep -o 'href="[a-zA-Z0-9._-]*\.html"' "$f" | sed 's/href="//;s/"//' | sort -u |
  while read t; do [ -f "$t" ] || echo "$f -> $t"; done
done

# Confirm nothing confidential reached the published output.
# Reads the sensitive terms from the sanitiser so this command never has to
# name a client, and can never drift from the rules it is checking.
python _build/scripts/check-leaks.py
```
