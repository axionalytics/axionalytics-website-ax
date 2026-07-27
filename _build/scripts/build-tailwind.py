# -*- coding: utf-8 -*-
"""
Compile a static Tailwind stylesheet, replacing the Play CDN.

WHY
---
The Play CDN ships ~400KB of JavaScript that compiles CSS in the browser on
every page load. It is render-blocking, it defeats HTTP caching of the styles
themselves, and it makes Largest Contentful Paint a function of how fast the
visitor's device can run a CSS compiler. Core Web Vitals is a ranking signal,
so this costs search traffic on every page.

HOW
---
There is no Node toolchain on this machine, so the official CLI is unavailable.
Rather than reimplement Tailwind's utility grammar — which would be wrong in
subtle ways around arbitrary values, variants, and specificity order — this
harvests the CDN's own output:

  1. Collect every distinct class used across the built pages.
  2. Emit a harvest page that references all of them, loading the real CDN and
     the project's own tailwind.config.
  3. Render it in headless Chrome so the CDN compiles as it normally would.
  4. Extract the <style> block Tailwind injected and write it to disk.

The result is byte-for-byte what the CDN would have produced, minus the
compiler. Re-run whenever new utility classes are introduced.

Usage: python _build/scripts/build-tailwind.py
"""
import glob
import io
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "tailwind.css")
HARVEST = os.path.join(ROOT, "_build", "tw-harvest.html")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("no Chrome/Edge binary found for harvesting")


def collect_classes():
    """Every distinct class token across the published pages."""
    seen = set()
    for path in glob.glob(os.path.join(ROOT, "*.html")):
        html = io.open(path, encoding="utf-8").read()
        for attr in re.findall(r'class="([^"]*)"', html):
            for token in attr.split():
                if token:
                    seen.add(token)
    # Utilities that only ever appear from JavaScript (state toggles) would be
    # missed by static scanning, so they are named explicitly.
    seen |= {
        "is-open", "is-in", "is-scrolled", "is-active",
        "text-white", "text-white/70",          # applied by the active-nav module
        "shadow-lg",
    }
    return sorted(seen)


def write_harvest(classes, config_js):
    body = "\n".join(
        '<div class="%s"></div>' % c.replace('"', "&quot;")
        for c in classes
    )
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>tailwind harvest</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>
%s
</script>
</head>
<body>
%s
</body>
</html>
""" % (config_js, body)
    io.open(HARVEST, "w", encoding="utf-8").write(html)


def render(chrome, path):
    profile = tempfile.mkdtemp(prefix="twharvest-")
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--user-data-dir=" + profile,
        "--virtual-time-budget=15000",
        "--dump-dom",
        "file:///" + path.replace("\\", "/"),
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=180)
    return res.stdout.decode("utf-8", "replace")


def extract_css(dom):
    """Pull the largest injected <style> block — Tailwind's generated sheet."""
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", dom, re.S)
    if not blocks:
        raise SystemExit("no <style> block in rendered DOM; CDN did not run")
    return max(blocks, key=len)


def main():
    chrome = find_chrome()

    config_path = os.path.join(ROOT, "assets", "axio-config.js")
    config_js = io.open(config_path, encoding="utf-8").read()

    classes = collect_classes()
    print("  harvesting %d distinct classes" % len(classes))

    write_harvest(classes, config_js)
    dom = render(chrome, HARVEST)
    css = extract_css(dom).strip()

    header = (
        "/* ============================================================\n"
        "   AXIONALYTICS - TAILWIND (compiled)\n"
        "   GENERATED FILE - do not edit.\n"
        "   Produced by _build/scripts/build-tailwind.py from the utility classes\n"
        "   actually used across the site, using the project's own\n"
        "   assets/axio-config.js theme. Re-run after introducing new\n"
        "   utility classes.\n"
        "   Replaces the Tailwind Play CDN, which compiled CSS in the\n"
        "   browser on every page load.\n"
        "   ============================================================ */\n"
    )

    io.open(OUT, "w", encoding="utf-8").write(header + css + "\n")
    os.remove(HARVEST)

    size = os.path.getsize(OUT) / 1024.0
    print("  wrote assets/tailwind.css  %.1f KB  (CDN was ~400 KB of JS)" % size)
    print("  rules: %d" % css.count("{"))


if __name__ == "__main__":
    main()
