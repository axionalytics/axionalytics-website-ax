# -*- coding: utf-8 -*-
"""
AXIONALYTICS — PILLAR -> CLUSTER BACK-LINKS

Every article links up to its pillar; make-articles.py renders that link from
the manifest. Nothing linked back down. The five commercial pages were receiving
seven to fifteen in-body inbound links each and returning three to five, so all
but ten of the cluster relationships on the site were one-way.

That asymmetry costs retrieval. A pillar and its cluster read as one topic to a
retrieval model only when the relationship is expressed in both directions;
linked in one direction they are a page and a page that happens to mention it.

This step closes it from the same manifest that opens it. The pillar never has
to be told which articles belong to it, so publishing an article is still a
one-line manifest change and the block below cannot fall out of date.

Runs on built output rather than on the page sources, which makes it idempotent
by construction — the same reason add-contextual-links.py runs where it does.
The pages are still bilingual at this point, so the block carries both trees and
make-i18n splits it along with everything else.

Usage: python _build/scripts/add-pillar-clusters.py
"""
import io
import os
import re
import importlib.util

MARK_OPEN = "<!-- pillar-cluster:start -->"
MARK_CLOSE = "<!-- pillar-cluster:end -->"


def load_manifest():
    """ARTICLES and PILLARS, from the generator that already owns them."""
    spec = importlib.util.spec_from_file_location(
        "mkarts", os.path.join("_build", "scripts", "make-articles.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.ARTICLES, m.PILLARS


CARD = u"""        <a href="{slug}.html" class="rounded-xl border border-ax-ink/10 bg-white p-5 hover:border-ax-blue/40 hover:shadow-ax-card transition-all">
          <p class="text-2xs font-bold uppercase tracking-wider text-ax-blue mb-2">
            <span data-lang-en>{cat_en}</span><span data-lang-es>{cat_es}</span>
          </p>
          <p class="font-heading font-bold leading-snug mb-1.5">
            <span data-lang-en>{title_en}</span><span data-lang-es>{title_es}</span>
          </p>
          <p class="text-sm text-ax-ink/55 leading-relaxed">
            <span data-lang-en>{desc_en}</span><span data-lang-es>{desc_es}</span>
          </p>
        </a>"""

BLOCK = u"""{open}
<section class="py-20 lg:py-24 bg-ax-mist border-t border-ax-ink/[0.07]">
  <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
    <p class="ax-eyebrow text-ax-blue mb-3">
      <span data-lang-en>Written on this</span><span data-lang-es>Escrito sobre esto</span>
    </p>
    <h2 class="font-heading font-extrabold text-2xl lg:text-3xl mb-9">
      <span data-lang-en>{head_en}</span><span data-lang-es>{head_es}</span>
    </h2>
    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
{cards}
    </div>
  </div>
</section>
{close}
"""

HEAD_EN = "The engineering behind it, in detail"
HEAD_ES = "La ingeniería detrás, en detalle"


def strip_existing(html):
    """Remove a previously injected block so a rebuild replaces rather than stacks."""
    pattern = re.escape(MARK_OPEN) + r".*?" + re.escape(MARK_CLOSE) + r"\n?"
    return re.sub(pattern, "", html, flags=re.S)


def main():
    articles, pillars = load_manifest()

    # pillar key -> its articles, in manifest order (newest first).
    by_pillar = {}
    for art in articles:
        by_pillar.setdefault(art["pillar"], []).append(art)

    injected = 0
    for key, pillar in pillars.items():
        page = pillar["url"]
        if not os.path.exists(page):
            print("  skip  %-42s (not built)" % page)
            continue

        cluster = by_pillar.get(key, [])
        if not cluster:
            print("  skip  %-42s (no cluster articles)" % page)
            continue

        html = strip_existing(io.open(page, encoding="utf-8").read())

        if "</main>" not in html:
            print("  skip  %-42s (no </main> anchor)" % page)
            continue

        cards = "\n".join(CARD.format(**a) for a in cluster)
        block = BLOCK.format(open=MARK_OPEN, close=MARK_CLOSE, cards=cards,
                             head_en=HEAD_EN, head_es=HEAD_ES)

        html = html.replace("</main>", block + "</main>", 1)
        io.open(page, "w", encoding="utf-8").write(html)

        print("  %-42s %d cluster links" % (page, len(cluster)))
        injected += len(cluster)

    print("\n  %d pillar -> cluster links injected" % injected)


if __name__ == "__main__":
    main()
