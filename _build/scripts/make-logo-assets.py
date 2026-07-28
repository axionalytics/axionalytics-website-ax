# -*- coding: utf-8 -*-
"""
Produce the site's logo assets from the supplied source art.

SOURCE SELECTION
----------------
media/ holds four candidates. All four carry the mark at the same effective
resolution (~519x598 px of actual artwork), so none is higher quality than the
others in detail — they differ only in canvas padding and background tint:

    Company_Logo_White.png                 2048x2080  full lockup, bg #F7F7F6
    Company_Logo_White_Logo_only.png       1135x864   mark only,   bg #FFFFFF
    Company_Logo_White_Logo_Small_only.png  582x656   mark only,   bg #FEFEFE
    axionalytics.png                        490x211   full lockup, bg #FEFDFE

`Company_Logo_White_Logo_only.png` is chosen: it is mark-only (the site renders
the "axionalytics" wordmark as live text beside it, so the lockup's baked-in
black wordmark is unusable on a dark header) and its background is pure white,
which keys with the least residue.

None of the four contains any transparency — the two RGBA files are RGBA in
name only, with a fully opaque alpha channel.

BACKGROUND REMOVAL
------------------
Trimap matting rather than a binary threshold. The source has a clean ~2px
anti-aliased edge ramp; a hard threshold would either leave a white halo or eat
the edge. Pixels are classified core / unknown / background by distance from
white, alpha ramps across the unknown band, and partial pixels are un-matted
(the white the artwork was composited over is divided back out) so no light
fringe survives on a dark header.

THE HUB
-------
The central node is pure black. On the near-black site header (#05080F) it
disappears, and the mark stops reading as hub-and-spoke. Two variants are
emitted so each background gets a legible mark.

Usage: python _build/scripts/make-logo-assets.py
"""
from PIL import Image
import os

# The source art is local working material and lives outside version control.
# It was under media/ when this script was written and now sits in _private/;
# both are tried so the script runs from either layout rather than failing with
# a path that looks like a typo.
SRC_CANDIDATES = (
    "_private/media/Company_Logo_White_Logo_only.png",
    "media/Company_Logo_White_Logo_only.png",
)
OUT = "assets"

# Favicon plate. The mark is placed on the site's own dark surface rather than
# left transparent — see the favicon note in main().
PLATE = (10, 16, 28, 255)   # #0A101C, the header and footer background
PLATE_FILL = 0.82           # mark width as a fraction of the plate

# Trimap thresholds, in "distance from white" units (0-255).
CORE_D = 50   # at or above -> fully opaque
BG_D = 12     # at or below  -> fully transparent

PAD_RATIO = 0.04   # breathing room around the mark, as a fraction of its size


def distance_from_white(p):
    r, g, b = p[0], p[1], p[2]
    return max(255 - r, 255 - g, 255 - b)


def key_out_white(im):
    """White background -> alpha, with un-matting on the anti-aliased band."""
    im = im.convert("RGB")
    w, h = im.size
    src = im.load()

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()

    span = float(CORE_D - BG_D)

    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            d = max(255 - r, 255 - g, 255 - b)

            if d <= BG_D:
                continue                      # background
            if d >= CORE_D:
                dst[x, y] = (r, g, b, 255)    # solid artwork
                continue

            # Unknown band: estimate coverage, then divide the white back out.
            a = (d - BG_D) / span
            inv = 1.0 - a
            ur = (r - 255.0 * inv) / a
            ug = (g - 255.0 * inv) / a
            ub = (b - 255.0 * inv) / a
            dst[x, y] = (
                max(0, min(255, int(round(ur)))),
                max(0, min(255, int(round(ug)))),
                max(0, min(255, int(round(ub)))),
                int(round(a * 255)),
            )
    return out


def keep_largest_component(im, min_alpha=8):
    """Discard everything except the largest connected blob.

    The source background carries low-level compression noise — scattered
    pixels at rgb(250,250,248) and similar, spread across the whole canvas,
    far from the artwork. Their intensity overlaps the faint end of the mark's
    own anti-aliased edge, so no threshold separates the two.

    Geometry does separate them: the mark is a single connected shape (every
    spoke meets the hub), while the noise is isolated specks. Keeping only the
    largest component removes all of it without eroding a real edge.
    """
    w, h = im.size
    px = im.load()

    labels = [0] * (w * h)
    best_label, best_size, current = 0, 0, 0

    for sy in range(h):
        for sx in range(w):
            i = sy * w + sx
            if labels[i] or px[sx, sy][3] < min_alpha:
                continue

            current += 1
            size = 0
            stack = [(sx, sy)]
            labels[i] = current

            while stack:
                x, y = stack.pop()
                size += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        j = ny * w + nx
                        if not labels[j] and px[nx, ny][3] >= min_alpha:
                            labels[j] = current
                            stack.append((nx, ny))

            if size > best_size:
                best_size, best_label = size, current

    removed = 0
    for y in range(h):
        for x in range(w):
            if labels[y * w + x] != best_label and px[x, y][3]:
                px[x, y] = (0, 0, 0, 0)
                removed += 1

    print("  kept largest component (%d px), discarded %d noise px in %d specks"
          % (best_size, removed, current - 1))
    return im


def trim_to_content(im, pad_ratio=PAD_RATIO):
    box = im.getbbox()          # alpha-aware once keyed
    if not box:
        raise SystemExit("empty image after keying")
    im = im.crop(box)
    w, h = im.size
    pad = int(round(max(w, h) * pad_ratio))
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    canvas.paste(im, (pad, pad), im)
    return canvas


def square(im):
    """Centre on a transparent square so every downstream size is predictable."""
    w, h = im.size
    s = max(w, h)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.paste(im, ((s - w) // 2, (s - h) // 2), im)
    return canvas


def _luma(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def find_hub(im, max_luma=70, max_chroma=26):
    """Locate the central hub as a connected achromatic-dark region.

    Darkness alone does not identify it: the blue and violet spokes darken
    toward the centre (rgb(16,40,160) sits at luma 44), so a luma-only flood
    fill escapes down the spokes and swallows most of the mark. Chroma is the
    discriminator — the hub is neutral (max-min channel ~0) while every spoke
    and node is heavily saturated.
    """
    w, h = im.size
    px = im.load()

    def is_hub(p):
        r, g, b, a = p
        return (a > 8 and _luma(r, g, b) < max_luma
                and (max(r, g, b) - min(r, g, b)) < max_chroma)

    start = (w // 2, h // 2)
    if not is_hub(px[start]):
        raise SystemExit("expected the hub at the centre of the mark; found %s"
                         % (px[start],))

    seen = set()
    stack = [start]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        if not is_hub(px[x, y]):
            continue
        seen.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen


def recolour_hub(im, hub, target=(232, 240, 252)):
    """Lift the hub to a light neutral so it stays legible on a dark surface.

    Each pixel keeps its own alpha, so the hub's anti-aliased rim survives and
    the disc does not gain a hard edge.
    """
    im = im.copy()
    px = im.load()
    for (x, y) in hub:
        r, g, b, a = px[x, y]
        # Preserve the rim's shading by scaling toward the target rather than
        # flat-filling, so the disc keeps a little dimension.
        t = 1.0 - (_luma(r, g, b) / 70.0) * 0.18
        px[x, y] = (int(target[0] * t), int(target[1] * t), int(target[2] * t), a)
    return im, len(hub)


def lift_shadows(im, skip, floor=78):
    """Raise very dark artwork so it does not disappear on a near-black page.

    About a tenth of the mark — the shaded side of the teal nodes and the inner
    ends of the blue and violet spokes — sits below luma 55. Against the site
    header at #05080F that is almost no contrast, and those areas read as bites
    taken out of the shape. Value is raised in HSV so hue and saturation, and
    therefore the brand colour, are unchanged.
    """
    im = im.copy()
    px = im.load()
    w, h = im.size
    lifted = 0

    for y in range(h):
        for x in range(w):
            if (x, y) in skip:
                continue
            r, g, b, a = px[x, y]
            if a < 8:
                continue

            mx, mn = max(r, g, b), min(r, g, b)
            if mx >= floor or mx == 0:
                continue

            scale = floor / float(mx)
            px[x, y] = (min(255, int(r * scale)),
                        min(255, int(g * scale)),
                        min(255, int(b * scale)), a)
            lifted += 1

    return im, lifted


def resize(im, height):
    w, h = im.size
    return im.resize((max(1, int(round(w * height / float(h)))), height), Image.LANCZOS)


def save(im, name, **kw):
    path = os.path.join(OUT, name)
    im.save(path, "PNG", optimize=True, **kw)
    print("    %-30s %4dx%-4d  %6.1f KB" % (name, im.size[0], im.size[1],
                                            os.path.getsize(path) / 1024.0))


def plate(mark, size):
    """The mark centred on an opaque brand-navy square."""
    tile = Image.new("RGBA", (size, size), PLATE)
    m = resize(square(mark), int(round(size * PLATE_FILL)))
    tile.paste(m, ((size - m.size[0]) // 2, (size - m.size[1]) // 2), m)
    return tile


def main():
    src = next((p for p in SRC_CANDIDATES if os.path.exists(p)), None)
    if src is None:
        raise SystemExit("missing source art; looked for:\n  " +
                         "\n  ".join(SRC_CANDIDATES))
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    print("  source: %s" % src)
    raw = Image.open(src)
    keyed = key_out_white(raw)
    keyed = keep_largest_component(keyed)
    mark = trim_to_content(keyed)
    print("  keyed and trimmed to %dx%d" % mark.size)

    hub = find_hub(mark)
    print("  hub located: %d px" % len(hub))

    dark_mark, moved = recolour_hub(mark, hub)
    dark_mark, lifted = lift_shadows(dark_mark, skip=hub)
    print("  dark variant: hub lifted (%d px), shadows lifted (%d px)\n"
          % (moved, lifted))

    # Serving size. The header renders the mark at 2.5rem (40 px) and the
    # article author block at 48 px, so 160 px covers 4x displays with room to
    # spare. A 512 px file would be ~104 KB to show 40 px of logo; 160 px is
    # 15 KB for the same rendered result.
    print("  light-background variant (black hub) — for white surfaces:")
    save(resize(mark, 160), "logo-mark.png")

    print("\n  dark-background variant (lifted hub) — for the header and footer:")
    save(resize(dark_mark, 160), "logo-mark-dark.png")

    # Full-resolution masters, for print, decks, or any future asset that needs
    # to be re-derived without re-running the keying.
    print("\n  masters:")
    save(resize(mark, 512), "logo-mark-512.png")
    save(resize(dark_mark, 512), "logo-mark-dark-512.png")

    # Favicons.
    #
    # These used to be the black-hub variant on transparency, on the reasoning
    # that tab strips render on a light chrome. That is no longer safe to assume:
    # in a dark-themed browser the black hub sits on a near-black tab and
    # disappears, so the mark stops reading as hub-and-spoke and becomes a ring
    # of unconnected dots — the exact failure the dark header variant was created
    # to avoid.
    #
    # So the favicon now carries its own ground: the lifted-hub variant on
    # #0A101C, which is the mark exactly as it appears in the site header. It is
    # legible on any tab colour, it matches what a visitor already associates
    # with the site, and it follows the same reasoning as the social card below —
    # a transparent icon is at the mercy of a background you do not control.
    #
    # The plate also buys legibility at 32px. The spokes are thin; against an
    # unknown background they smear, and against a known one they do not.
    print("\n  favicons (mark on the header's own navy, for legibility on any tab):")
    for size in (32, 180, 512):
        name = "favicon-%d.png" % size if size != 180 else "apple-touch-icon.png"
        save(plate(dark_mark, size), name)

    # Browsers and crawlers request /favicon.ico from the site root whether or
    # not any page links to it. Without this the site answers 404 on every one
    # of those requests. It ships the small sizes only: the .ico is a fallback
    # for clients too old to take the PNGs above, and they are the clients least
    # able to spare the bytes.
    print("\n  root favicon.ico (16/32/48, for clients that ignore the PNGs):")
    ico = plate(dark_mark, 48)
    ico.save("favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("    %-30s %6.1f KB" % ("favicon.ico", os.path.getsize("favicon.ico") / 1024.0))

    # A social card needs an opaque background: transparent PNGs render
    # unpredictably (black on some clients, white on others) in link previews.
    print("\n  social share card:")
    card = Image.new("RGBA", (1200, 630), (10, 16, 28, 255))
    m = resize(dark_mark, 300)
    card.paste(m, ((1200 - m.size[0]) // 2, (630 - m.size[1]) // 2 - 20), m)
    save(card.convert("RGB"), "og-card.png")

    print("\n  done.")


if __name__ == "__main__":
    main()
