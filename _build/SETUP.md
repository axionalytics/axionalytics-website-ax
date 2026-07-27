# What is left for you to do

Everything in this list needs a human: an account, a credential, a decision, or
a name. None of it can be automated or guessed.

This file lives in `_build/`, so it is version-controlled but never published to
the website.

**Verified against the current project on 2026-07-26.** Every path, line number,
and count below was checked, not remembered.

---

## First, the thing that matters most

There are two kinds of files in this project, and they behave differently:

| Kind | Example | After editing |
|---|---|---|
| **Asset files** — served directly | `assets/axio-analytics.js`, `assets/axio-roi.js` | Just save. Done. |
| **Build sources** — templates | `_build/src/partials/head-open.html`, `_build/scripts/author.py` | Save, **then rebuild** |

To rebuild, open a terminal in the project folder and run:

```bash
bash _build/scripts/all.sh
```

**Never edit a file at the top level of the project directly** — `index.html`,
`pricing.html`, anything in `es/`. Those are generated. Your edit gets wiped the
next time anyone rebuilds. Edit the source in `_build/` instead.

### Corrections to the older instructions

If you are working from notes written earlier, three things have moved and two
numbers have changed. Using the old ones will fail:

| Old (wrong now) | Correct |
|---|---|
| `bash _build/all.sh` | `bash _build/scripts/all.sh` |
| `_build/partials/head-open.html` | `_build/src/partials/head-open.html` |
| "74 pages" | **82 files** (43 English + 39 Spanish), of which **78 are real pages** — see Step 6b |
| "70 URLs" in the sitemap | **78 URLs** (39 pages × 2 languages) |
| 3 config values to fill in | **4** — an author name was added |

---

## Step 0 — Hosting: resolved ✅

This was an open question. It is now answered, and verified against the live
DNS and the GitHub API on 2026-07-26.

| Question | Answer |
|---|---|
| How is the site hosted today? | **GitHub Pages.** `Server: GitHub.com` |
| From which repository? | **`axionalytics/axionalytics-website`** — public, Pages enabled, last pushed 2026-02-10. This is the OLD site. |
| Is DNS already correct? | **Yes.** `www` → `axionalytics.github.io`; apex has all four GitHub Pages A records. **No DNS changes are needed.** |
| Is `axionalytics` an org? | No — it is a **user** account. |
| Were the source documents ever exposed? | **No.** The public repo has 14 files and 11 commits, all old-site HTML. No `.md`, no `media/`. `https://www.axionalytics.com/example.md` returns 404. |

**Decision taken:** retire `axionalytics-website` and serve the site from
`axionalytics-website-ax` instead.

---

## Step 1 — Version control and the public/private split: done ✅

Completed on 2026-07-26. Nothing for you to do here except understand it, and
the one thing at the bottom that only you can do.

| | |
|---|---|
| Repository | `https://github.com/axionalytics/axionalytics-website-ax` |
| Visibility | **Public** |
| Branch | `main` |
| Working tree | clean |

### Why public

GitHub Pages will not serve a site from a private repository on the Free plan.
That is an account-level rule, so retiring the old repo did not change it — the
only ways around it were to pay $4/month for Pro, or to make the repository
public.

Public was chosen, and it is safe, because a scan proved that **only two things
in the entire project were sensitive**, and both were dealt with:

| Was sensitive | What happened |
|---|---|
| `_private/` — client source documents, strategy notes, original artwork | Removed from version control entirely. Local only. |
| `_build/scripts/sanitize-sources.py` — held the 38 client terms verbatim | The terms moved to `_private/terms.py`. The script now loads them at runtime and is clean. |

All 245 other tracked files scanned clean against every term. That check is now
automated and runs on every commit and every build.

### The three guards

Losing a customer's engineering documents to a public repository is
irreversible, so one safeguard is not enough:

1. **`.gitignore`** — `_private/` never enters `git add`
2. **`.git/hooks/pre-commit`** — refuses the commit even if a path is force-added,
   *and* refuses any staged content containing a client term, wherever it sits
3. **`check-leaks.py`** — step 14 of the build fails if git can see `_private/`
   at all

Guards 1 and 3 are committed. **Guard 2 is not**, because git hooks live in
`.git/hooks/` and are never cloned. If you set this project up on another
machine, reinstall it:

```bash
bash _build/scripts/install-hooks.sh
```

Both guards were tested by deliberately trying to commit a `_private/` file and
a pasted client term. Both commits were refused.

### Supporting files added

- **`.gitignore`** — the `_private/` rule, plus ordinary clutter
- **`.gitattributes`** — forces LF line endings. Without it, Windows checks
  generated files out as CRLF and git reports all 82 pages as modified after
  every build, burying real changes in noise.
- **`CNAME`** — `www.axionalytics.com`, ready for the cutover

**From now on, after any change you are happy with:**

```bash
git add -A && git commit -m "what you changed" && git push
```

> ### ⚠️ The one thing only you can do: back up `_private/`
>
> `_private/` is no longer in git. **That means it is no longer backed up.** It
> exists on this laptop and nowhere else, and it contains:
>
> - the client source documents (`source-docs/`)
> - **`terms.py` — the sanitisation rules**, without which the confidentiality
>   checks silently stop protecting you
> - the original logo artwork, at full resolution
> - the strategy notes and the ROI spreadsheet
>
> Copy the whole folder to Google Drive, or an external disk, or anywhere that
> is not this machine. Do it today. This is the single largest risk the project
> now carries, and it takes two minutes to remove.
>
> If `terms.py` ever goes missing, `check-leaks.py` will tell you loudly rather
> than passing quietly — but it cannot reconstruct the rules.

---

## Step 2 — Analytics (about 10 minutes)

**What this is:** right now you have no idea how many people visit the site or
which pages they read. This fixes that.

I chose Cloudflare because it is free, needs no cookie-consent banner, and does
not track people individually — which matters, because the entire site argues
for privacy. Using a tracker that contradicts your own sales pitch is a real
credibility problem, not a technicality.

### 2a. Make a Cloudflare account

1. Go to [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
2. Sign up with your email. Free — no card needed.
3. Confirm the email they send you.

**You do not need to move your domain to Cloudflare.** Ignore any prompt asking
you to. You are only using their analytics.

### 2b. Add your site

1. In the left sidebar, find **Analytics & Logs**, then click **Web Analytics**
2. Click **Add a site**
3. In the hostname box, type: `www.axionalytics.com`
4. Click **Done**

### 2c. Get your token

Cloudflare shows you a snippet of code, roughly like this:

```html
<script defer src='https://static.cloudflareinsights.com/beacon.min.js'
  data-cf-beacon='{"token": "abc123def456ghi789"}'></script>
```

You need **only the token** — the long string between the quotes after
`"token":`. In the example that is `abc123def456ghi789`. Yours will differ.

Copy just that string. Do not copy the whole snippet.

### 2d. Paste it in

1. Open `assets/axio-analytics.js`
2. Go to **line 36**. It reads:

   ```js
       cloudflareToken: '',      // e.g. 'a1b2c3d4e5f6...'
   ```

3. Put your token between the two single quotes:

   ```js
       cloudflareToken: 'abc123def456ghi789',      // e.g. 'a1b2c3d4e5f6...'
   ```

4. Save.

**Watch out:** keep the quotes `'` and the trailing comma `,`. Delete either one
and analytics silently stops working across the whole site — no error, just no
data.

**No rebuild needed.** This is an asset file.

### 2e. Check it worked

After you deploy (Step 6), visit your own site, then return to Cloudflare's Web
Analytics page. Your visit appears within a few minutes. If nothing shows after
an hour, the token is wrong — recopy it.

---

## Step 3 — The ROI form (about 5 minutes)

**What this is:** the ROI calculator asks for an email before showing the full
breakdown. Right now that email goes nowhere — someone types it and it vanishes.
This makes it arrive in your inbox.

### 3a. Make a Formspree account

1. Go to [formspree.io](https://formspree.io)
2. Click **Sign up**. The free plan allows 50 submissions a month, which is
   plenty to start.
3. Confirm your email.

### 3b. Create a form

1. Click **+ New Form**
2. Name it something recognisable: `ROI Calculator`
3. Set the notification email to `axionalytics@gmail.com`, or wherever you want
   leads to land
4. Click **Create Form**

### 3c. Get the endpoint

Formspree shows a URL like:

```
https://formspree.io/f/xyzabcde
```

Copy the whole URL, including the `https://`.

### 3d. Paste it in

1. Open `assets/axio-roi.js`
2. Go to **line 240**:

   ```js
     var LEAD_ENDPOINT = '';
   ```

3. Put your URL between the quotes:

   ```js
     var LEAD_ENDPOINT = 'https://formspree.io/f/xyzabcde';
   ```

4. Save.

**No rebuild needed.** This is an asset file.

### 3e. What you will receive

The payload was reformatted so it arrives readable rather than as raw JSON. A
submission email looks like:

```
Subject: ROI calculator — Test Engineering — $961,185/yr

email:                someone@bigco.com
scenario:             Test Engineering
reclaimed_hours:      11,904 hrs/yr
fte_equivalent:       5.7 FTE
net_annual_recovery:  $961,185
payback:              3.6 months
three_year_net:       $2,883,555
input_volume:         2,400
input_people:         40 FTE
input_loaded_cost:    $145,000
source:               roi-calculator
page:                 https://www.axionalytics.com/roi-calculator.html
```

You see exactly what they modelled before you reply — team size, loaded cost,
and how big the number they talked themselves into is. That tells you how
serious the lead is and gives you an opening line.

### 3f. Check it worked

After deploying, open your own ROI calculator, enter your email, and click
**Unlock the breakdown**. Check your inbox.

Formspree makes you confirm the very first submission — click the link in that
email. Every one after that arrives directly.

**One design note so it does not surprise you:** the breakdown unlocks
immediately, before the email is transmitted, and it unlocks even if the send
fails. A visitor who gave you an address should not stare at a spinner because
a form provider is slow. The email is a courtesy, not a paywall.

---

## Step 4 — Google Search Console (about 10 minutes + a wait)

**What this is:** this is how you find out what people typed into Google to find
you, which pages Google has actually indexed, and whether anything is broken.
Without it you are blind to your own search traffic.

> ⚠️ **This one has an order dependency.** Google must be able to see the
> verification tag on the live site. So: get the token → paste it → rebuild →
> deploy → *then* click Verify. You cannot verify before deploying.

### 4a. Open Search Console

1. Go to [search.google.com/search-console](https://search.google.com/search-console)
2. Sign in with a Google account

### 4b. Add your site

1. You see two boxes: **Domain** and **URL prefix**. Choose **URL prefix** — it
   is the simpler one and does not require DNS changes.
2. Type: `https://www.axionalytics.com`
3. Click **Continue**

### 4c. Get the token

1. A list of verification methods appears. Expand **HTML tag**.
2. You see something like:

   ```html
   <meta name="google-site-verification" content="AbC123_dEf456-GhI789jkl" />
   ```

3. Copy **only the content value** — the string between the quotes after
   `content=`. In the example that is `AbC123_dEf456-GhI789jkl`.

**Leave this browser tab open.** You come back to it in Step 7.

### 4d. Paste it in

1. Open `_build/src/partials/head-open.html`

   *(Note the `src/` — this moved during the reorganisation. `_build/partials/`
   no longer exists.)*

2. Go to **line 23**:

   ```html
     <!-- <meta name="google-site-verification" content="PASTE_TOKEN_HERE"> -->
   ```

3. Replace that whole line with your tag, **removing the `<!--` and `-->`**:

   ```html
     <meta name="google-site-verification" content="AbC123_dEf456-GhI789jkl">
   ```

   `<!--` and `-->` mean "ignore this line" in HTML. While they are there, the
   tag does nothing at all. Removing them is what switches it on.

4. Save.

**This is a build source — it needs a rebuild (Step 6).**

---

## Step 5 — The author name (2 minutes, optional but high value)

**What this is:** every article on the site is currently signed "Axionalytics".
Google's quality guidance weights content written by a named, identifiable
person above content from a faceless company — and for technical B2B writing,
this is one of the cheapest ranking improvements available.

The machinery is fully built, wired into the pipeline, and tested. It is
switched **off**, because it needs one thing that must not be invented: a real
person's name.

### 5a. Decide whether you want a byline

The name will be publicly attached to 24 pages, with a bio page listing
everything you have written. That is the point — it is a trust signal, and it
only works if a reader can look the person up and find a real professional.

If you do not want your name on it, skip this step. The site works fine with
company attribution. **Do not put a made-up name here.** A fabricated byline is
worse than no byline: it is the exact kind of thin-authority signal Google's
guidance is designed to catch, and if a buyer discovers it, everything else on
the site becomes suspect.

### 5b. Fill it in

1. Open `_build/scripts/author.py`
2. Go to **line 35**:

   ```python
   NAME = ""            # e.g. "Jorge Carbajal"
   ```

3. Put your name in the quotes:

   ```python
   NAME = "Your Real Name"
   ```

4. While you are there, check the two lines below it — `ROLE_EN` and `ROLE_ES`
   currently say "Founder & Principal Engineer" / "Fundador e Ingeniero
   Principal". Change them if that is not right.
5. Read `BIO_EN` and `BIO_ES` further down. They are written to be accurate and
   concrete, but they are **my words about you**. Rewrite them in your own voice
   before they go public.
6. If you have a personal LinkedIn (not the company page) or a GitHub profile,
   put them in `LINKEDIN` and `GITHUB`. Anything left empty is omitted cleanly
   rather than published as a dead link.

### 5c. What happens on the next rebuild

That one line switches on all of this:

- all 24 article and glossary pages change from company to person attribution
  in their search-engine data
- a visible "By ⟨name⟩" byline appears under each article title, in both
  languages
- `author.html` is created — a bio page listing your areas of work and every
  article you have written
- every byline links to it

Leave `NAME` empty and none of it happens, and no half-built page is published.

**This is a build source — it needs a rebuild (Step 6).**

---

## Step 6 — Rebuild and deploy

### 6a. Rebuild

```bash
bash _build/scripts/all.sh
```

This runs 14 steps and takes under a minute. The final line should read:

```
done.  43 pages en  ·  39 pages es
```

If step 14 fails with a confidentiality error, **stop** — something
client-identifying reached the output. Do not deploy. That check exists
precisely to catch this.

### 6b. Confirm the Search Console tag landed everywhere

Do **not** use `grep -l "google-site-verification"` to check this. That phrase
already appears on every page inside the commented-out placeholder, so it
returns a healthy-looking number whether or not you actually switched the tag
on. It is a false positive waiting to happen.

Check for your actual token instead, and check that the placeholder is gone:

```bash
grep -l "AbC123_dEf456-GhI789jkl" *.html es/*.html | wc -l   # use YOUR token
grep -rl "PASTE_TOKEN_HERE" *.html es/*.html | wc -l
```

The first should print **78**. The second must print **0**.

**Why 78 and not 82?** The four `*.html` files at the top level that are *not*
part of the site — `aitransformation.html`, `datatransformation.html`,
`training.html`, `successstories.html` — are redirect stubs for retired URLs.
They are deliberately marked noindex and carry no shared `<head>`, so they have
no verification tag and should not have one. 78 is the correct, complete number.

If the first command prints `0`, you left the `<!--` and `-->` in place. Go back
to Step 4d.

*(Older notes say 74 — that predates the Spanish tree and the newer articles.)*

### 6c. Commit and push

```bash
git add -A
git commit -m "Configure analytics, lead capture, Search Console, and author"
git push
```

Pushing does **not** make it live on its own — not until the cutover in Step 6d
is done. After the cutover, this three-line sequence is the entire deploy
process forever.

### 6d. The cutover — one-time, about 10 minutes

Right now `www.axionalytics.com` is served by the **old** repo,
`axionalytics/axionalytics-website`. This moves it to the new one.

Total cost: **$0**. No GitHub plan upgrade is involved.

> #### ⚠️ Step 1 below is not optional, and the order is not cosmetic
>
> The repository currently on GitHub is **private**, and its history contains
> `_private/` — the client documents were committed before the decision to go
> public was made.
>
> **Flipping that repository's visibility to public would expose them.** Deleting
> the files in a new commit does not help: git keeps every old object, and on a
> public repo they remain reachable.
>
> So the repository is deleted and recreated, and a fresh single-commit history
> is pushed. There is no shortcut here, and no way to verify afterwards that you
> got it right — the only safe move is to start clean.

**Order matters** for a second reason too: GitHub will not let two repositories
claim the same custom domain, so the old site has to release it before the new
one can take it.

**1. Delete and recreate the repository — public this time**

1. Go to `github.com/axionalytics/axionalytics-website-ax` → **Settings**
2. Scroll to the very bottom → **Delete this repository**, and confirm
3. Go to [github.com/new](https://github.com/new)
4. Repository name: **`axionalytics-website-ax`** (exactly the same)
5. Select **Public**
6. Do **not** tick "Add a README" or add a `.gitignore` — you have both
7. **Create repository**

Then tell me, and I push the clean history. Or do it yourself:

```bash
git push -u origin main --force
```

**2. Release the domain from the old repo**

1. Go to `github.com/axionalytics/axionalytics-website` → **Settings** → **Pages**
2. Under **Custom domain**, clear the box and click **Save**
3. Under **Build and deployment** → **Source**, select **None** if offered

The site is now down. This is the only downtime, and it is a few minutes.

**3. Turn on Pages for the new repo**

1. Go to `github.com/axionalytics/axionalytics-website-ax` → **Settings** → **Pages**
2. **Source:** Deploy from a branch
3. **Branch:** `main`, folder `/ (root)` → **Save**
4. Wait for the first build — 1–2 minutes. The Actions tab shows progress.

**4. Attach the domain**

1. Same page, **Custom domain**: type `www.axionalytics.com` → **Save**
2. GitHub runs a DNS check. It should pass immediately, because the DNS records
   already point at GitHub and never changed.
3. Wait for **"DNS check successful"**, then tick **Enforce HTTPS**

Enforce HTTPS may be greyed out for up to an hour while a certificate is
issued. That is normal. Come back and tick it.

**5. Retire the old repo**

Once the new site is confirmed live (Step 6e), go to
`axionalytics-website` → **Settings** → scroll to the bottom → **Archive this
repository**.

Archiving makes it read-only but keeps the history. **Prefer this to deleting.**
Deletion is irreversible, and the old repo is your last independent copy of the
pre-2026 site outside `_legacy/`.

### 6e. Check the live site

Hard-refresh with `Ctrl+Shift+R` to bypass your browser cache — the old site
will be cached and you will think nothing happened.

Confirm each of these loads:

- `https://www.axionalytics.com/` — should show the **new** homepage. The
  headline mentions surviving enterprise security review. If you still see
  "Turn Data Into Decisions", you are looking at cache.
- `https://www.axionalytics.com/es/` — Spanish homepage
- `https://www.axionalytics.com/roi-calculator.html` — calculator runs
- `https://www.axionalytics.com/sitemap.xml` — a list of URLs
- `https://axionalytics.com/` — apex should redirect to `www`

And confirm these return **404**:

- `https://www.axionalytics.com/_build/SETUP.md`
- `https://www.axionalytics.com/_build/scripts/sanitize-sources.py`
- `https://www.axionalytics.com/_legacy/index.html`

Those confirm Jekyll's underscore exclusion is active. If any downloads a file,
tell me — it means `_config.yml` is not being applied, and while nothing there
is confidential any more, it should not be on the website either.

**Also check the repository itself**, now that it is public — this is the check
that actually matters:

- `https://github.com/axionalytics/axionalytics-website-ax/tree/main/_private`
  → must be **404**
- Search the repo for `_private` → should return only `.gitignore`, the build
  scripts that reference the path, and documentation. No files *inside* it.

### 6d. Check the live site

Open these in a browser and confirm each one loads:

- `https://www.axionalytics.com/` — homepage
- `https://www.axionalytics.com/es/` — Spanish homepage
- `https://www.axionalytics.com/roi-calculator.html` — calculator runs
- `https://www.axionalytics.com/sitemap.xml` — shows a list of URLs

And confirm this one does **not** load — it should return 404:

- `https://www.axionalytics.com/_private/source-docs/example.md`

That last one is the confidentiality check. If it downloads a file, stop
everything and tell me immediately.

---

## Step 7 — Verify with Google and submit the sitemap (5 minutes)

Only possible once the site is live.

### 7a. Verify

1. Return to the Search Console tab you left open in Step 4c
2. Click **Verify**
3. It should confirm within a few seconds

If it fails: check `https://www.axionalytics.com/` in a browser, right-click →
**View Page Source**, and search for `google-site-verification`. If it is not
there, the deploy has not finished — wait two minutes and try again.

### 7b. Submit the sitemap

Do this immediately after verifying. This is the part people forget, and it is
what tells Google that all 78 of your URLs exist.

1. In Search Console's left sidebar, click **Sitemaps**
2. In the box, type just: `sitemap.xml`
3. Click **Submit**

Status will say "Couldn't fetch" for a few hours. **That is normal.** It becomes
"Success" once Google processes it.

---

## Step 8 — Google Business Profile (about 20 minutes + postcard wait)

**What this is:** the site now publishes `LocalBusiness` data — that is the half
of local search that lives on your website. The other half lives at Google, and
without it you cannot appear in the map pack or in "AI consultant near me"
searches. That is a whole channel currently forgone.

It also matters beyond local search: a verifiable physical presence is a trust
signal for a firm asking enterprises to let it inside their network perimeter.

### 8a. Create the profile

1. Go to [business.google.com](https://business.google.com)
2. Click **Manage now** and sign in
3. Business name: **Axionalytics**
4. Category: search for and choose **Software company** or **Business
   management consultant**. You can add more categories later.
5. When asked "Do you want to add a location customers can visit?" — you can
   answer **No**. Consulting firms routinely operate as service-area businesses
   without a walk-in address.
6. Service area: **Davenport, Iowa**, plus anywhere else you want to be found.
7. Phone: **+1-956-207-9368**
8. Website: `https://www.axionalytics.com`

### 8b. Verify

Google will ask you to verify by postcard, phone, or email depending on what it
offers you. A postcard takes 5–14 days. Nothing appears in search until
verification completes.

### 8c. Keep the two halves in agreement — this is the part that matters

Google cross-checks what your website says against what your profile says. If
they disagree, it discounts both.

The website's version lives in `_build/scripts/add-local-business.py`. It
currently publishes:

| Field | Value |
|---|---|
| Name | Axionalytics |
| Phone | +1-956-207-9368 |
| Email | axionalytics@gmail.com |
| City / Region / Country | Davenport / IA / US |
| Street address | *deliberately blank* |
| Coordinates | *deliberately blank* |

Use exactly these in the profile. The street address and coordinates are blank
on purpose — a fabricated address would fail Google's verification later, and I
was not going to invent one. If you decide to publish a real street address,
put it in that file's `STREET` field, rebuild, and make it match the Business
Profile character for character.

---

## Your checklist at a glance

| # | Task | Rebuild? | Needs site live? | Status |
|---|---|---|---|---|
| 0 | Identify the host | — | — | ✅ done — GitHub Pages |
| 1 | git repo, public/private split, guards installed | — | — | ✅ done |
| 1b | **Back up `_private/` off this laptop** | No | No | ☐ **you — nothing else protects it** |
| 2 | Cloudflare token → `assets/axio-analytics.js` line 36 | No | No | ☐ you |
| 3 | Formspree URL → `assets/axio-roi.js` line 240 | No | No | ☐ you |
| 4 | Google token → `_build/src/partials/head-open.html` line 23 | **Yes** | No | ☐ you |
| 5 | Author name → `_build/scripts/author.py` line 35 | **Yes** | No | ☐ optional |
| 6a–c | Rebuild, commit, push | — | — | ☐ you |
| 6d | **Cutover: delete+recreate repo as public → release domain → enable Pages → attach domain** | — | — | ☐ **you — this is what makes it live** |
| 6e | Verify the live site, archive the old repo | — | **Yes** | ☐ you |
| 7 | Click Verify in Search Console, submit `sitemap.xml` | — | **Yes** | ☐ you |
| 8 | Google Business Profile | No | No | ☐ you |

Steps 2, 3, 4, and 5 can all be done in one sitting, followed by a single
rebuild, a single push, and the one-time cutover.

**If you want to go live right now and configure the rest later:** skip to
6d. The site is already committed and pushed — the cutover alone puts the new
site on the domain. Steps 2–5 can follow at any time; each is just an edit,
a rebuild, and a push.

---

## What to expect afterwards

**Same day.** Cloudflare starts showing visits. Formspree starts catching
emails. Search Console shows nothing yet.

**Days 1–3.** Search Console's Coverage report starts listing pages as
discovered. Expect some to sit in "Discovered — currently not indexed". That is
normal for a new site and not a defect.

**Weeks 1–2.** Search Console begins showing which queries you appear for.
Expect it to look nearly empty. This is a brand-new URL structure and Google has
to crawl all 78 URLs across two languages.

**Months 1–3.** The glossary pages — "what is agentic AI", "what is BYOC",
"what is prompt injection" — typically move first, because definitional queries
are far less competitive than commercial ones. The pillar and pricing pages take
longer, and will not move at all without the backlinks discussed below.

**Do not judge anything before week three.** Early Search Console data on a new
structure is noise, and reacting to it usually means undoing work that was
correct.

---

## Beyond the setup: what the site still lacks

These are real gaps, not busywork. Listed in the order I would tackle them.

### 1. Backlinks — the single biggest constraint

The site currently has **zero** inbound links from other domains. This is the
largest remaining limit on how well anything ranks, and no amount of on-page
work substitutes for it. Everything built so far makes the site *rankable*;
links are what make it *rank*.

Realistic starting points, cheapest first:

- Your own LinkedIn company page and personal profile
- Any professional directory or association you already belong to
- Local: Quad Cities chamber of commerce, Iowa tech directories
- Writing a guest piece for a publication your buyers actually read
- The open-source strategy below

### 2. Open-source inbound

`_private/strategy/nash.md` calls for sanitised public repositories with
search-optimised READMEs, driving referral traffic back here. **Not started.**
This is the highest-leverage backlink source available to you, because it is
entirely within your control and the audience is exactly right.

**Remember: those go in new, separate repositories.** Never this one.

### 3. A native-speaker pass on the Spanish

The `/es/` tree is machine-generated. The technical vocabulary is defensible,
but the commercial copy — the pillar pages and pricing especially — should get a
native-speaker review before you promote it to Spanish-speaking buyers. Selling
to enterprises in slightly-off Spanish costs more credibility than it gains.

### 4. Publishing cadence

All 15 articles are dated in the past and nothing is scheduled forward. A site
that publishes nothing for six months reads as abandoned, to both readers and
crawlers. One well-made piece a month beats a burst followed by silence.

### 5. Smaller gaps

- The revenue pillar has 2 supporting articles; the others have 3–4
- Only one comparison page — comparison queries are high-intent and under-served
- No "industries" or "integrations" pages
- No case-study PDFs or gated long-form assets beyond the calculator
- No customer testimonials or named references *(deliberate — but worth
  revisiting if a client ever grants permission)*

---

## If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `bash: _build/all.sh: No such file` | Old path | Use `bash _build/scripts/all.sh` |
| `refusing to run: N pages carry no data-lang spans` | You ran `make-i18n.py` alone, twice | The guard is working correctly. Run `all.sh` instead. |
| Build fails at step 14 | A client term reached the output | **Do not deploy.** Read what it names and tell me. |
| Analytics shows nothing after an hour | Wrong token, or a deleted quote/comma | Recheck line 36 of `axio-analytics.js` |
| Form submits but no email arrives | First submission unconfirmed | Check inbox for Formspree's confirmation link |
| Search Console verify fails | Deploy not finished, or comment markers left in | View page source, search `google-site-verification` |
| Your edit to a page disappeared | You edited a generated top-level file | Edit the source in `_build/` and rebuild |

The full troubleshooting section is in `README.md` section 12.
