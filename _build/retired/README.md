# Retired build scripts

## extract-articles.py

One-time migration that lifted four articles out of the pre-2026 accordion blog
(`_legacy/blog.html`) into standalone pages.

**Superseded by `_build/scripts/make-articles.py`.** Do not run it again — all
four of those articles have since been rewritten, and this script would
overwrite the rewrites with the superseded copy.

Kept for reference because it documents the malformed-attribute repair
(28 spans written `<span data-lang-es">`, which no selector matched, so Spanish
leaked into the English view) in case similar markup surfaces elsewhere.
