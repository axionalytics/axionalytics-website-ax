# -*- coding: utf-8 -*-
"""
AXIONALYTICS — AI CITATION MONITOR

Asks generative engines the questions our buyers ask, and records who gets cited.

WHY
---
The old scoreboard was "what position do we rank on Google". That scoreboard is
broken: most searches in this category end with the person reading a synthesised
answer and never clicking. The replacement metric is AI Citation Frequency —
when a CTO asks an engine a question in our category, how often are we named?

Nobody keeps that score for us. There is no rank tracker for it. So we ask the
engines ourselves, on a schedule, and write down what they said.

This is also the first agent this company runs on its own marketing, which is
the point: we sell autonomous workflows, and until now every step of our demand
generation was a human typing a command.

WHAT IT IS NOT
--------------
Not part of the default build. Nobody wants fifty API calls because they fixed a
typo. Run it from the weekly workflow, or by hand when you want a reading.

READING THE OUTPUT
------------------
One run is noise. Engines are non-deterministic: the same prompt returns
different citations on different days, and a single week's dip is usually
sampling rather than a regression. Report the four-week rolling average, and
state the variance alongside it. The `page` field is the one that earns its
keep — it tells you which asset did the work, which is how you decide what to
write next.

Usage:
  python _build/scripts/check-citations.py                 # all configured engines
  python _build/scripts/check-citations.py --engine claude # one engine
  python _build/scripts/check-citations.py --limit 5       # smoke test
  python _build/scripts/check-citations.py --dry-run       # no API calls
"""
import io
import json
import os
import re
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPTS = os.path.join(ROOT, "_build", "data", "prompts.json")
OUTDIR = os.path.join(ROOT, "_build", "data", "aicf")

# Opus 5 is the current flagship and what a buyer asking Claude actually gets.
# Measuring on a cheaper model would measure a different product than the one
# the buyer is using, which defeats the purpose.
MODEL = "claude-opus-5"

# Latest web search variant — dynamic filtering, supported on Opus 5. Do NOT
# also declare code_execution: dynamic filtering runs it under the hood, and a
# second execution environment confuses the model.
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search"}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score(answer_text, sources, domain, brand):
    """
    One prompt's result, from one engine.

    `cited` and `named` are deliberately separate. An engine can describe our
    architecture accurately without linking us — that is brand presence without
    citation, and it moves on a different timeline. Collapsing them into one
    number hides which of the two is improving.
    """
    ours = [s for s in sources if domain in (s.get("url") or "")]
    others = []
    for s in sources:
        url = s.get("url") or ""
        m = re.match(r"https?://([^/]+)", url)
        if not m:
            continue
        host = m.group(1).lower().replace("www.", "")
        if domain not in url and host not in others:
            others.append(host)

    rank = None
    for i, s in enumerate(sources, 1):
        if domain in (s.get("url") or ""):
            rank = i
            break

    return {
        "cited": bool(ours),
        "named": brand.lower() in (answer_text or "").lower(),
        "rank": rank,
        "pages": [s.get("url") for s in ours],
        "competitors": others,
        "source_count": len(sources),
    }


# ---------------------------------------------------------------------------
# Engines
#
# Each adapter takes a prompt and returns (answer_text, sources), where sources
# is a list of {"url": ..., "title": ...}. An engine whose key is absent is
# skipped rather than failing the run — a partial reading beats no reading.
# ---------------------------------------------------------------------------

def ask_claude(prompt):
    """
    Anthropic, via the official SDK with the server-side web search tool.

    Search runs on Anthropic's infrastructure: we declare the tool and read the
    results back out of the response. There is no client-side execution loop.
    """
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "the anthropic package is not installed.\n"
            "  This repo has no dependencies by design, so this script does not\n"
            "  assume one. Install it only where the monitor runs:\n"
            "      pip install anthropic")

    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": prompt}]
    text, sources = [], []

    # A server-tool turn can stop with pause_turn when the search loop hits its
    # iteration limit. Re-send the assistant turn to resume; the server picks up
    # where it left off. Do not append a "continue" message — it detects the
    # trailing tool block on its own.
    for _ in range(4):
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            # A factual retrieval question does not need deep reasoning, and this
            # runs 50 times a week. Medium keeps the bill sane without changing
            # what gets cited.
            output_config={"effort": "medium"},
            tools=[WEB_SEARCH],
            messages=messages,
        )

        for block in response.content:
            if block.type == "text":
                text.append(block.text)
            elif block.type == "web_search_tool_result":
                # Success gives a list of results; an error gives a single object
                # carrying error_code. Indexing without checking turns a rate
                # limit into a crash.
                content = block.content
                if isinstance(content, list):
                    for r in content:
                        url = getattr(r, "url", None)
                        if url:
                            sources.append(
                                {"url": url, "title": getattr(r, "title", "")})
                else:
                    code = getattr(content, "error_code", "unknown")
                    print("      search error: %s" % code)

        if response.stop_reason != "pause_turn":
            break
        messages = [{"role": "user", "content": prompt},
                    {"role": "assistant", "content": response.content}]

    return "\n".join(text), sources


def ask_unconfigured(name):
    def _ask(prompt):
        raise RuntimeError(
            "%s adapter is not implemented.\n"
            "  Each engine has its own SDK and its own response shape, and\n"
            "  guessing at them would produce a monitor that reports confident\n"
            "  nonsense. Implement against that provider's current docs, return\n"
            "  (answer_text, [{'url', 'title'}, ...]), and register it below." % name)
    return _ask


ENGINES = {
    "claude": {"fn": ask_claude, "key": "ANTHROPIC_API_KEY"},
    "openai": {"fn": ask_unconfigured("openai"), "key": "OPENAI_API_KEY"},
    "perplexity": {"fn": ask_unconfigured("perplexity"), "key": "PERPLEXITY_API_KEY"},
    "gemini": {"fn": ask_unconfigured("gemini"), "key": "GEMINI_API_KEY"},
}

# Google AI Overviews is deliberately absent. It has no API, scraping the SERP
# breaks Google's terms and the markup shifts constantly, so a scraper would be
# both a liability and a maintenance sink. Spot-check it by hand monthly on ten
# prompts and record that separately; the four API engines are the tracked number.


# ---------------------------------------------------------------------------

def load_prompts():
    with io.open(PROMPTS, encoding="utf-8") as fh:
        return json.load(fh)


def available(name):
    """An engine is usable when its adapter exists and its key is present."""
    spec = ENGINES[name]
    return bool(os.environ.get(spec["key"]))


def run(engines, limit=None, dry_run=False):
    cfg = load_prompts()
    prompts = cfg["prompts"][:limit] if limit else cfg["prompts"]
    domain, brand = cfg["domain"], cfg["brand"]

    now = datetime.datetime.now(datetime.timezone.utc)
    run_id = "%d-W%02d" % now.isocalendar()[:2]

    results, failures = [], 0
    for engine in engines:
        print("\n  %s — %d prompts" % (engine, len(prompts)))
        consecutive = 0
        for p in prompts:
            if dry_run:
                print("    [dry] %-10s %s" % (p["id"], p["text"][:60]))
                continue
            try:
                text, sources = ENGINES[engine]["fn"](p["text"])
                consecutive = 0
            except Exception as exc:
                failures += 1
                consecutive += 1
                # A missing package or a bad key fails identically fifty times.
                # Print the whole message once, then stop asking — repeating it
                # buries the cause and, on an auth error, burns the rate limit.
                if consecutive == 1:
                    lines = str(exc).split("\n")
                    print("    FAIL  %-10s %s" % (p["id"], lines[0]))
                    for line in lines[1:]:
                        print("                     %s" % line)
                if consecutive >= 3:
                    print("    giving up on %s after 3 consecutive failures"
                          % engine)
                    break
                continue

            s = score(text, sources, domain, brand)
            s.update({"engine": engine, "prompt_id": p["id"], "group": p["group"]})
            results.append(s)
            print("    %-5s %-10s rank=%-4s sources=%d"
                  % ("CITED" if s["cited"] else ("named" if s["named"] else "-"),
                     p["id"], s["rank"] if s["rank"] else "-", s["source_count"]))

    if dry_run:
        print("\n  dry run — %d prompts x %d engines, no calls made"
              % (len(prompts), len(engines)))
        return 0

    if not results:
        print("\n  no results recorded")
        return 1

    # AICF per engine, plus blended. Reported per run; the number that matters is
    # the four-week rolling average across these files.
    summary = {}
    for engine in engines:
        rows = [r for r in results if r["engine"] == engine]
        if rows:
            summary[engine] = {
                "asked": len(rows),
                "cited": sum(1 for r in rows if r["cited"]),
                "named": sum(1 for r in rows if r["named"]),
                "aicf": round(sum(1 for r in rows if r["cited"]) / len(rows), 4),
            }

    payload = {
        "run": run_id,
        "captured_at": now.isoformat(),
        "prompt_set_version": cfg["version"],
        "model": MODEL,
        "engines": sorted(summary),
        "summary": summary,
        "results": results,
    }

    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    dest = os.path.join(OUTDIR, run_id + ".json")
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, indent=2, ensure_ascii=False))

    print("\n  AICF this run")
    for engine, s in sorted(summary.items()):
        print("    %-12s %5.1f%%   (%d/%d cited, %d named)"
              % (engine, s["aicf"] * 100, s["cited"], s["asked"], s["named"]))
    print("\n  wrote %s" % os.path.relpath(dest, ROOT).replace(os.sep, "/"))
    if failures:
        print("  %d prompt(s) failed" % failures)
    return 0


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    limit = None
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])

    if "--engine" in args:
        want = [args[args.index("--engine") + 1]]
        if want[0] not in ENGINES:
            print("  unknown engine: %s (have: %s)"
                  % (want[0], ", ".join(sorted(ENGINES))))
            return 2
    else:
        want = sorted(ENGINES)

    if not dry_run:
        want = [e for e in want if available(e)]
        if not want:
            print("  no engine is configured. Set at least one of:")
            for name in sorted(ENGINES):
                print("    %s   (%s)" % (ENGINES[name]["key"], name))
            return 1

    return run(want, limit=limit, dry_run=dry_run)


if __name__ == "__main__":
    sys.exit(main())
