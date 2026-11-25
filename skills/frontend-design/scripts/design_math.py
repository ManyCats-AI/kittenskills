#!/usr/bin/env python3
"""Derive and audit a UI design system from a few inputs.

Every value a UI uses should come out of a formula, not out of the air.
This tool does the arithmetic so the agent doesn't eyeball it.

Subcommands
  tokens    Print a complete, derived token set as CSS custom properties.
  type      Type scale with grid-snapped line-heights and tracking.
  controls  Geometry for buttons/inputs/selects at each size.
  radius    Concentric (nested) radius: outer = inner + inset.
  palette   Perceptual OKLCH ramp with hex values and contrast ratios.
  contrast  WCAG contrast ratio between two hex colors.
  audit     Scan source files for off-grid values, token sprawl, and AI-slop patterns.

Standard library only. Python 3.8+.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- helpers


def snap(value: float, grid: float, mode: str = "nearest") -> float:
    """Snap a value to a grid. Ties round down so we never inflate sizes."""
    q = value / grid
    if mode == "up":
        n = math.ceil(q - 1e-9)
    elif mode == "down":
        n = math.floor(q + 1e-9)
    else:
        n = math.floor(q) if q - math.floor(q) <= 0.5 else math.ceil(q)
    out = n * grid
    return int(out) if float(out).is_integer() else out


def fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- typography


def line_height_for(size: float, unit: int) -> int:
    """Body text gets ~1.5, subheads ~1.25, display ~1.15; snapped to the
    half-unit grid so text rhythm lands on the same grid as spacing."""
    if size <= 20:
        factor = 1.5
    elif size <= 32:
        factor = 1.25
    else:
        factor = 1.15
    grid = unit
    lh = snap(size * factor, grid)
    if lh < size * 1.1:  # never cramp descenders into the next line
        lh = snap(size * 1.1, grid, "up")
    return int(lh)


def tracking_for(size: float) -> str:
    if size >= 32:
        return "-0.02em"
    if size >= 24:
        return "-0.01em"
    if size <= 12:
        return "0.01em"
    return "0"


TYPE_NAMES = {-2: "xs", -1: "sm", 0: "base", 1: "lg", 2: "xl", 3: "2xl", 4: "3xl", 5: "4xl", 6: "5xl"}


def type_scale(base: int, ratio: float, lo: int, hi: int, unit: int):
    rows, prev = [], 0
    for step in range(lo, hi + 1):
        size = round(base * ratio**step)
        if size <= prev:  # small ratios can collide after rounding
            size = prev + 1
        prev = size
        rows.append(
            {
                "step": step,
                "name": TYPE_NAMES.get(step, f"s{step}"),
                "size": size,
                "lh": line_height_for(size, unit),
                "tracking": tracking_for(size),
            }
        )
    return rows


# ---------------------------------------------------------------- geometry

SHAPES = {
    # radius as a fraction of control height. Proportional radii keep the same
    # corner "curvature" at every size, so sm/md/lg read as one family.
    "sharp": 0.05,
    "crisp": 0.15,
    "soft": 0.25,
    "pill": 0.5,
}


def control_geometry(heights, unit, border, shape, scale):
    by_step = {r["step"]: r for r in scale}
    out = []
    for i, h in enumerate(heights):
        # smaller controls use smaller text; the largest uses base size
        step = -1 if i < len(heights) - 1 else 0
        t = by_step.get(step, by_step[0])
        lh = t["lh"]
        py = (h - lh - 2 * border) / 2
        px = snap(h * 0.4, unit)
        icon = 16 if h <= 40 else 20
        gap = unit * 2 if h >= 40 else unit * 1.5
        r = h / 2 if shape == "pill" else max(2, snap(h * SHAPES[shape], 2))
        out.append(
            {
                "height": h,
                "font": t["size"],
                "lh": lh,
                "py": py,
                "px": px,
                "icon": icon,
                "gap": gap,
                "radius": r,
                "icon_only": h,  # square: width == height
            }
        )
    return out


def concentric(outer=None, inner=None, inset=0.0):
    if outer is not None:
        return max(0.0, outer - inset)
    return inner + inset


# ---------------------------------------------------------------- color (OKLCH -> sRGB)


def oklch_to_linear_srgb(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def in_gamut(rgb, eps=1e-4):
    return all(-eps <= c <= 1 + eps for c in rgb)


def oklch_to_hex(L, C, h):
    """Convert, reducing chroma until the color fits in sRGB (keeps L and h)."""
    rgb = oklch_to_linear_srgb(L, C, h)
    if not in_gamut(rgb):
        lo, hi = 0.0, C
        for _ in range(30):
            mid = (lo + hi) / 2
            if in_gamut(oklch_to_linear_srgb(L, mid, h)):
                lo = mid
            else:
                hi = mid
        rgb = oklch_to_linear_srgb(L, lo, h)

    def enc(x):
        x = min(1.0, max(0.0, x))
        x = 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        return round(x * 255)

    return "#" + "".join(f"{enc(c):02x}" for c in rgb)


def hex_to_rgb(hx):
    hx = hx.strip().lstrip("#")
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", hx):
        raise ValueError(f"not a hex color: {hx}")
    return tuple(int(hx[i : i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(hx):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in hex_to_rgb(hx))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
# Perceptual lightness per step (OKLCH L). Evenly spaced in the middle,
# compressed at the ends where the eye is less sensitive.
LIGHTNESS = [0.985, 0.965, 0.925, 0.87, 0.78, 0.68, 0.585, 0.49, 0.40, 0.31, 0.22]
# Chroma envelope: saturated in the middle, calm at the extremes so tints
# and near-blacks don't look radioactive.
CHROMA_CURVE = [0.12, 0.25, 0.45, 0.7, 0.92, 1.0, 1.0, 0.92, 0.8, 0.65, 0.5]


def ramp(hue, chroma):
    rows = []
    for step, L, k in zip(STEPS, LIGHTNESS, CHROMA_CURVE):
        hx = oklch_to_hex(L, chroma * k, hue)
        rows.append(
            {
                "step": step,
                "L": L,
                "C": round(chroma * k, 4),
                "hex": hx,
                "on_white": contrast(hx, "#ffffff"),
                "on_black": contrast(hx, "#000000"),
            }
        )
    return rows


def slop_hue_warning(hue, chroma):
    if 255 <= hue % 360 <= 320 and chroma >= 0.1:
        return (
            "WARNING: hue {:.0f} at chroma {:.2f} is the indigo/violet/purple zone that "
            "most generated UIs default to. Use it only if the brand demands it, and "
            "write down why.".format(hue, chroma)
        )
    return None


# ---------------------------------------------------------------- commands


def cmd_type(a):
    rows = type_scale(a.base, a.ratio, a.lo, a.hi, a.unit)
    print(f"Type scale: base {a.base}px x ratio {a.ratio}, line-heights on a {a.unit}px grid\n")
    print(f"{'step':>4}  {'name':<5} {'size':>5} {'line-ht':>8} {'ratio':>6}  tracking")
    for r in rows:
        print(
            f"{r['step']:>4}  {r['name']:<5} {r['size']:>4}px {r['lh']:>6}px "
            f"{r['lh'] / r['size']:>6.2f}  {r['tracking']}"
        )


def cmd_controls(a):
    scale = type_scale(a.base, a.ratio, -2, 6, a.unit)
    rows = control_geometry(a.heights, a.unit, a.border, a.shape, scale)
    print(
        f"Controls: heights {a.heights}, {a.border}px border, shape '{a.shape}' "
        f"(radius = {SHAPES[a.shape]} x height)\n"
    )
    print(f"{'height':>6} {'font/lh':>8} {'pad-y':>6} {'pad-x':>6} {'icon':>5} {'gap':>4} {'radius':>7}")
    for r in rows:
        print(
            f"{r['height']:>5}px {r['font']:>3}/{r['lh']:<4} {fmt(r['py']):>5} {fmt(r['px']):>6} "
            f"{r['icon']:>5} {fmt(r['gap']):>4} {fmt(r['radius']):>7}"
        )
        if r["py"] < 0:
            print(f"        ! line-height {r['lh']} + borders don't fit in {r['height']}px; raise height")
    print(
        "\nRule: height = line-height + 2*pad-y + 2*border. Set the height explicitly and center\n"
        "the content; pad-y is shown so you can check the text has breathing room (>= 4px)."
    )


def cmd_radius(a):
    if a.outer is not None:
        r = concentric(outer=a.outer, inset=a.inset)
        print(f"inner radius = max(0, {fmt(a.outer)} - {fmt(a.inset)}) = {fmt(r)}px")
        if r == 0:
            print("inner hits 0: the inset is larger than the outer radius, so inner corners go square.")
            print("Either that's intended, or increase the outer radius / reduce the inset.")
    else:
        r = concentric(inner=a.inner, inset=a.inset)
        print(f"outer radius = {fmt(a.inner)} + {fmt(a.inset)} = {fmt(r)}px")


def cmd_palette(a):
    w = slop_hue_warning(a.hue, a.chroma)
    if w:
        print(w + "\n")
    print(f"OKLCH ramp, hue {a.hue}, peak chroma {a.chroma}\n")
    print(f"{'step':>4}  {'L':>5} {'C':>6}  {'hex':<8} {'vs #fff':>8} {'vs #000':>8}  text use")
    for r in ramp(a.hue, a.chroma):
        uses = []
        if r["on_white"] >= 4.5:
            uses.append("text on light")
        elif r["on_white"] >= 3:
            uses.append("large/UI on light")
        if r["on_black"] >= 4.5:
            uses.append("text on dark")
        elif r["on_black"] >= 3:
            uses.append("large/UI on dark")
        print(
            f"{r['step']:>4}  {r['L']:>5.3f} {r['C']:>6.4f}  {r['hex']:<8} {r['on_white']:>8.2f} "
            f"{r['on_black']:>8.2f}  {', '.join(uses) or 'surfaces/borders only'}"
        )
    print("\nNeutrals: run again with the same hue and chroma 0.005-0.02 (a whisper of the accent hue).")


def cmd_contrast(a):
    r = contrast(a.fg, a.bg)
    verdicts = [
        ("body text (AA 4.5)", r >= 4.5),
        ("large text >= 24px or 19px bold (AA 3.0)", r >= 3.0),
        ("UI components, focus rings, icons (3.0)", r >= 3.0),
        ("body text (AAA 7.0)", r >= 7.0),
    ]
    print(f"{a.fg} on {a.bg}: {r:.2f}:1")
    for label, ok in verdicts:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")


def cmd_tokens(a):
    u = a.unit
    scale = type_scale(a.base, a.ratio, -2, a.hi, u)
    ctrls = control_geometry(a.heights, u, a.border, a.shape, scale)
    sizes = ["sm", "md", "lg"][: len(ctrls)] if len(ctrls) <= 3 else [f"h{c['height']}" for c in ctrls]
    md = ctrls[min(1, len(ctrls) - 1)]
    r_ctrl = md["radius"]
    r_surface = min(snap(r_ctrl * 2, 2), a.surface_padding) if a.shape != "pill" else snap(a.surface_padding, 2)
    # Menus/popovers wrap items with a small inset; their radius is concentric.
    menu_inset = u
    r_item = ctrls[0]["radius"] if a.shape != "pill" else ctrls[0]["height"] / 2
    r_menu = concentric(inner=r_item, inset=menu_inset)
    accent = ramp(a.hue, a.chroma)
    neutral = ramp(a.neutral_hue if a.neutral_hue is not None else a.hue, a.neutral_chroma)

    warn = slop_hue_warning(a.hue, a.chroma)
    if warn:
        print(f"/* {warn} */\n")

    L = []
    p = L.append
    p("/* Generated by design_math.py tokens")
    p(f"   unit={u} base={a.base} ratio={a.ratio} shape={a.shape} heights={a.heights}")
    p(f"   accent hue={a.hue} chroma={a.chroma}; neutral chroma={a.neutral_chroma}")
    p("   Every value below is derived; change the inputs, not the outputs. */")
    p(":root {")
    p(f"  /* Spacing: multiples of the {u}px unit */")
    for n in [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24]:
        name = fmt(n).replace(".", "_")
        p(f"  --space-{name}: {fmt(n * u)}px;")
    p("")
    p(f"  /* Type: {a.base}px x {a.ratio}^n, line-heights snapped to {u}px */")
    for r in scale:
        p(f"  --text-{r['name']}: {r['size']}px;  --leading-{r['name']}: {r['lh']}px;  --tracking-{r['name']}: {r['tracking']};")
    p("")
    p(f"  /* Controls: height = line-height + 2*pad-y + 2*border; radius = {SHAPES[a.shape]} x height */")
    for name, c in zip(sizes, ctrls):
        p(
            f"  --control-{name}-h: {c['height']}px;  --control-{name}-px: {fmt(c['px'])}px;  "
            f"--control-{name}-gap: {fmt(c['gap'])}px;  --control-{name}-icon: {c['icon']}px;  "
            f"--control-{name}-font: var(--text-{'sm' if c['font'] != a.base else 'base'});  "
            f"--radius-control-{name}: {fmt(c['radius'])}px;"
        )
    p("")
    p("  /* Radius: one family. surfaces = min(2 x control radius, surface padding);")
    p(f"     menus = item radius + {menu_inset}px inset (concentric). */")
    p(f"  --radius-surface: {fmt(r_surface)}px;")
    p(f"  --radius-menu: {fmt(r_menu)}px;  --menu-inset: {menu_inset}px;")
    p(f"  --radius-badge: {fmt(max(2, snap(r_ctrl / 2, 2)) if a.shape != 'pill' else 999)}px;")
    p("  --radius-full: 9999px;")
    p("")
    p(f"  /* Borders and focus. Ring radius = element radius + offset (concentric). */")
    p(f"  --border-w: {a.border}px;  --focus-w: 2px;  --focus-offset: 2px;")
    p("")
    p("  /* Elevation: single light source above; y doubles per level, blur = 2y. */")
    for lvl in range(1, 5):
        y = 2 ** (lvl - 1)
        p(
            f"  --shadow-{lvl}: 0 {fmt(y)}px {fmt(2 * y)}px oklch(0.2 0.01 {a.hue} / 0.08), "
            f"0 {fmt(max(0.5, y / 2))}px {fmt(max(1, y))}px oklch(0.2 0.01 {a.hue} / 0.06);"
        )
    p("")
    p("  /* Motion */")
    p("  --dur-1: 100ms;  --dur-2: 150ms;  --dur-3: 200ms;  --dur-4: 300ms;")
    p("  --ease-out: cubic-bezier(0.2, 0, 0, 1);  --ease-in: cubic-bezier(0.4, 0, 1, 1);")
    p("")
    p("  /* Color ramps (OKLCH-derived; hex for compatibility) */")
    for r in accent:
        p(f"  --accent-{r['step']}: {r['hex']};")
    for r in neutral:
        p(f"  --neutral-{r['step']}: {r['hex']};")
    p("")
    look = {f"accent-{r['step']}": r["hex"] for r in accent}
    look.update({f"neutral-{r['step']}": r["hex"] for r in neutral})

    def pick(prefix, rows, bg_hexes, need, light_mode):
        """Closest step to the background that still meets the contrast target on
        every surface it can sit on (page bg and raised cards).
        Light mode walks light->dark, dark mode walks dark->light."""
        order = rows if light_mode else list(reversed(rows))
        for r in order:
            if all(contrast(r["hex"], b) >= need for b in bg_hexes):
                return f"{prefix}-{r['step']}"
        return f"{prefix}-{order[-1]['step']}"

    def roles_for(light):
        bg = "neutral-50" if light else "neutral-950"
        raised = "#ffffff" if light else "neutral-900"
        bgx = [look[bg], raised if raised.startswith("#") else look[raised]]
        accent_role = pick("accent", accent, bgx, 4.5, light)
        acc_rows = accent if light else list(reversed(accent))
        nxt = acc_rows[min(len(acc_rows) - 1, [f"accent-{r['step']}" for r in acc_rows].index(accent_role) + 1)]
        on_accent = "#ffffff" if contrast("#ffffff", look[accent_role]) >= contrast(look["neutral-950"], look[accent_role]) else "neutral-950"
        return {
            "bg": bg,
            "surface": bg,
            "surface-raised": raised,
            "border": "neutral-200" if light else "neutral-800",
            "border-strong": pick("neutral", neutral, bgx, 3.0, light),  # input borders: WCAG 1.4.11
            "text": "neutral-950" if light else "neutral-50",
            "text-muted": pick("neutral", neutral, bgx, 4.5, light),
            "accent": accent_role,
            "accent-hover": f"accent-{nxt['step']}",
            "on-accent": on_accent,
            "focus": pick("accent", accent, bgx, 3.0, light),
        }

    roles_light, roles_dark = roles_for(True), roles_for(False)
    p("  /* Semantic roles, light. Each picked as the step nearest the background that")
    p("     still meets its contrast target (text 4.5, focus/input borders 3.0). */")
    for k, v in roles_light.items():
        p(f"  --color-{k}: {v if v.startswith('#') else f'var(--{v})'};")
    p("}")
    p("")
    p("@media (prefers-color-scheme: dark) {")
    p("  :root {")
    p("    /* Dark: elevation by lighter surfaces, not shadows. */")
    for k, v in roles_dark.items():
        p(f"    --color-{k}: {v if v.startswith('#') else f'var(--{v})'};")
    p("  }")
    p("}")
    print("\n".join(L))

    # Verify the role pairs we just emitted actually meet contrast.

    def res(v):
        return v if v.startswith("#") else look[v]

    checks = []
    for mode, roles in (("light", roles_light), ("dark", roles_dark)):
        bg = res(roles["bg"])
        raised = res(roles["surface-raised"])
        checks += [
            (mode, "text on bg", res(roles["text"]), bg, 4.5),
            (mode, "muted text on bg", res(roles["text-muted"]), bg, 4.5),
            (mode, "muted text on raised surface", res(roles["text-muted"]), raised, 4.5),
            (mode, "accent (as text/link) on bg", res(roles["accent"]), bg, 4.5),
            (mode, "accent (as text/link) on raised surface", res(roles["accent"]), raised, 4.5),
            (mode, "focus ring vs raised surface", res(roles["focus"]), raised, 3.0),
            (mode, "input border vs raised surface", res(roles["border-strong"]), raised, 3.0),
            (mode, "on-accent text on accent-hover", res(roles["on-accent"]), res(roles["accent-hover"]), 4.5),
            (mode, "on-accent text on accent", res(roles["on-accent"]), res(roles["accent"]), 4.5),
            (mode, "focus ring vs bg", res(roles["focus"]), bg, 3.0),
            (mode, "input border vs bg (WCAG 1.4.11)", res(roles["border-strong"]), bg, 3.0),
        ]
    print("\n/* Contrast verification", file=sys.stderr)
    bad = 0
    for mode, label, fg, bg, need in checks:
        r = contrast(fg, bg)
        ok = r >= need
        bad += not ok
        print(f"   {'ok  ' if ok else 'FAIL'} {mode:<5} {label:<58} {r:5.2f} (need {need})", file=sys.stderr)
    print("*/", file=sys.stderr)
    if bad:
        print(
            f"\n{bad} contrast check(s) failed. Adjust --chroma/--hue or remap the role to a darker/lighter step.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------- audit

SOURCE_EXT = {".css", ".scss", ".sass", ".less", ".html", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte", ".astro"}

SLOP = [
    (r"(linear|radial|conic)-gradient\(|bg-gradient-to-|bg-linear-to-|bg-radial", "gradient: decoration or meaning? Remove unless it encodes something."),
    (r"\b(from|via|to|bg|text|border|ring|shadow)-(purple|violet|indigo|fuchsia)-\d{2,3}\b", "Tailwind purple/violet/indigo: the default AI palette."),
    (r"background-clip:\s*text|bg-clip-text|text-transparent", "gradient text: almost always slop."),
    (r"backdrop-filter|backdrop-blur", "glassmorphism: only over real imagery/content, never as default chrome."),
    (r"\bblur-(2xl|3xl)\b|filter:\s*blur\(\s*[4-9]\d", "decorative blur blobs."),
    (r"\bshadow-(xl|2xl)\b", "heavy shadows: use the elevation tokens."),
    (r"\banimate-(bounce|ping)\b", "attention animations: almost never appropriate."),
    (r"\brounded-(2xl|3xl)\b", "very large radius: check it against the radius tokens."),
    (r"#(6366f1|8b5cf6|7c3aed|a855f7|4f46e5|9333ea|c084fc|818cf8)\b", "Tailwind indigo/violet/purple hex: the default AI palette."),
    (r"[\U0001F300-\U0001FAFF✨⚡⭐]", "emoji used as UI icons/decoration."),
    (
        r"(?i)\b(unlock the power|supercharge|seamless(ly)?|revolutioni[sz]e|elevate your|"
        r"cutting[- ]edge|game[- ]chang|next[- ]gen(eration)?|lorem ipsum|welcome to our|"
        r"take .{1,20} to the next level|effortless(ly)?|harness the)",
        "generic marketing copy: write specific, real content.",
    ),
]

PX = re.compile(r"(?<![\w.#\[-])(-?\d+(?:\.\d+)?)px\b")
TW_ARBITRARY = re.compile(r"\b[a-z-]+-\[(-?\d+(?:\.\d+)?)px\]")
RADIUS = re.compile(r"border(?:-[a-z]+)*-radius\s*:\s*([^;}{]+)")
FONT_SIZE = re.compile(r"font-size\s*:\s*([^;}{]+)")
# Hex colors are 3, 4, 6, or 8 digits; skip fragment links and SVG refs (href="#feed", url(#cafe)).
HEX = re.compile(r"""(?<!href=")(?<!href=')(?<!to=")(?<!url\()(?<!url\(")#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b""")
TW_ROUNDED = re.compile(r"(?<![\w-])rounded(?:-[trbl]{1,2})?(?:-(none|xs|sm|md|lg|xl|2xl|3xl|full|\[[^\]]+\]))?(?=[\s\"'`])")
TW_TEXT = re.compile(r"(?<![\w-])text-(xs|sm|base|lg|xl|[2-9]xl|\[[^\]]+\])\b")


def is_token_file(path: Path, text: str) -> bool:
    return "tokens" in path.name.lower() or "theme" in path.name.lower() or text.count("--") > 40


def cmd_audit(a):
    files = []
    for target in a.paths:
        p = Path(target)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.suffix in SOURCE_EXT and not any(
                    part in {"node_modules", "dist", "build", ".next", ".git", "vendor", ".svelte-kit"} for part in f.parts
                ):
                    files.append(f)
    if not files:
        print("no source files found")
        return

    off_grid, slop_hits = [], []
    radii, font_sizes, colors, tw_round, tw_text = {}, {}, {}, {}, {}
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        token_file = is_token_file(f, text)
        for ln, line in enumerate(text.splitlines(), 1):
            loc = f"{f}:{ln}"
            if not token_file:
                for m in list(PX.finditer(line)) + list(TW_ARBITRARY.finditer(line)):
                    v = abs(float(m.group(1)))
                    if v in (0, 1) or v >= 1000:
                        continue
                    if v % a.unit != 0:
                        half = v % (a.unit / 2) == 0
                        off_grid.append((loc, m.group(0), "half-step (ok only inside a component)" if half else "off-grid"))
                for m in HEX.finditer(line):
                    colors.setdefault(m.group(0).lower(), []).append(loc)
            for m in RADIUS.finditer(line):
                radii.setdefault(m.group(1).strip(), []).append(loc)
            for m in FONT_SIZE.finditer(line):
                font_sizes.setdefault(m.group(1).strip(), []).append(loc)
            for m in TW_ROUNDED.finditer(line):
                tw_round.setdefault(m.group(0), []).append(loc)
            for m in TW_TEXT.finditer(line):
                tw_text.setdefault(m.group(0), []).append(loc)
            for pat, why in SLOP:
                if re.search(pat, line):
                    slop_hits.append((loc, why, line.strip()[:110]))

    def section(title):
        print(f"\n== {title}")

    print(f"Scanned {len(files)} files (unit {a.unit}px)")

    section(f"Off-grid sizes ({len([o for o in off_grid if o[2] == 'off-grid'])} off-grid, "
            f"{len([o for o in off_grid if o[2] != 'off-grid'])} half-step)")
    for loc, val, kind in off_grid[: a.limit]:
        print(f"  {loc}  {val}  [{kind}]")
    if len(off_grid) > a.limit:
        print(f"  ... {len(off_grid) - a.limit} more")

    def sprawl(name, d, budget):
        n = len(d)
        flag = "  <-- too many; consolidate into tokens" if n > budget else ""
        section(f"{name}: {n} distinct (budget {budget}){flag}")
        for k, locs in sorted(d.items(), key=lambda kv: -len(kv[1]))[: a.limit]:
            print(f"  {len(locs):>4}x  {k}   e.g. {locs[0]}")

    sprawl("Border-radius values", radii, 5)
    sprawl("Tailwind rounded-* classes", tw_round, 5)
    sprawl("Font-size declarations", font_sizes, 8)
    sprawl("Tailwind text-* sizes", tw_text, 8)
    sprawl("Raw hex colors outside token files", colors, 0)

    section(f"AI-slop patterns: {len(slop_hits)} hits")
    for loc, why, src in slop_hits[: a.limit]:
        print(f"  {loc}  {why}\n        {src}")

    problems = (
        len([o for o in off_grid if o[2] == "off-grid"])
        + len(slop_hits)
        + max(0, len(radii) - 5)
        + max(0, len(colors))
    )
    print(f"\nTotal flags: {problems}. Each one is either fixed or has a written reason to stay.")
    sys.exit(1 if problems and a.strict else 0)


# ---------------------------------------------------------------- CLI


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(s):
        s.add_argument("--unit", type=int, default=4, help="base grid unit in px (4 or 8)")
        s.add_argument("--base", type=int, default=16, help="base font size in px")
        s.add_argument("--ratio", type=float, default=1.2, help="type scale ratio (1.125, 1.2, 1.25, 1.333)")

    s = sub.add_parser("type")
    common(s)
    s.add_argument("--lo", type=int, default=-2)
    s.add_argument("--hi", type=int, default=5)
    s.set_defaults(fn=cmd_type)

    def ctrl(s):
        s.add_argument("--heights", type=lambda v: [int(x) for x in v.split(",")], default=[32, 40, 48])
        s.add_argument("--border", type=int, default=1)
        s.add_argument("--shape", choices=SHAPES, default="crisp")

    s = sub.add_parser("controls")
    common(s)
    ctrl(s)
    s.set_defaults(fn=cmd_controls)

    s = sub.add_parser("radius")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--outer", type=float)
    g.add_argument("--inner", type=float)
    s.add_argument("--inset", type=float, required=True, help="distance between the two edges")
    s.set_defaults(fn=cmd_radius)

    s = sub.add_parser("palette")
    s.add_argument("--hue", type=float, required=True, help="OKLCH hue 0-360")
    s.add_argument("--chroma", type=float, default=0.13, help="peak OKLCH chroma (0.08 calm .. 0.2 vivid)")
    s.set_defaults(fn=cmd_palette)

    s = sub.add_parser("contrast")
    s.add_argument("fg")
    s.add_argument("bg")
    s.set_defaults(fn=cmd_contrast)

    s = sub.add_parser("tokens")
    common(s)
    ctrl(s)
    s.add_argument("--hi", type=int, default=5, help="largest type step")
    s.add_argument("--hue", type=float, required=True)
    s.add_argument("--chroma", type=float, default=0.13)
    s.add_argument("--neutral-hue", type=float, default=None)
    s.add_argument("--neutral-chroma", type=float, default=0.01)
    s.add_argument("--surface-padding", type=int, default=16, help="default card/panel padding in px")
    s.set_defaults(fn=cmd_tokens)

    s = sub.add_parser("audit")
    s.add_argument("paths", nargs="+")
    s.add_argument("--unit", type=int, default=4)
    s.add_argument("--limit", type=int, default=25, help="max rows per section")
    s.add_argument("--strict", action="store_true", help="exit 1 if anything is flagged")
    s.set_defaults(fn=cmd_audit)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
