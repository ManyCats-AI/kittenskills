# Component geometry

Standard specs for common components. Every value is expressed in tokens or as a formula over tokens, so the same spec works for any input set. The numeric examples use the defaults: `u = 4`, controls `32 / 40 / 48`, `crisp` shape (control radius 4 / 6 / 8), surface radius 12, surface padding 16.

Notation: `h` = control height, `r(x)` = radius of x, `d` = inset between two nested edges.

## Controls

### Button

| Property | Formula | sm / md / lg |
|---|---|---|
| height | control scale | 32 / 40 / 48 |
| padding-x | 0.4 × h, snapped to u | 12 / 16 / 20 |
| font / line-height | sm, sm, base | 13–14/20, 13–14/20, 16/24 |
| icon | 16 if h ≤ 40 else 20 | 16 / 16 / 20 |
| icon ↔ label gap | 1.5u / 2u / 2u | 6 / 8 / 8 |
| padding-x on the icon side | padding-x − 2 (optical: icons have built-in whitespace) | 10 / 14 / 18 |
| radius | shape ratio × h | 4 / 6 / 8 |
| icon-only | width = h | 32 / 40 / 48 squares |
| focus ring | 2px at 2px offset, radius = r + 2 | 6 / 8 / 10 |
| min-width | 2 × h for text buttons (stops "OK" being a tiny square) | 64 / 80 / 96 |

Variants differ in color only (primary, secondary, ghost, danger). Never in size, padding, or radius. Hover/press changes background and border; it must not move or resize the button. A disabled button keeps its size and uses reduced contrast plus `cursor: not-allowed`; it also needs a reason the user can discover.

### Text input, select, textarea

| Property | Formula |
|---|---|
| height | same as the button of the same size (so they align in a row) |
| padding-x | 0.3 × h, snapped to u (12 for md); slightly less than buttons since text is left-aligned |
| border | 1px `--color-border-strong` (≥3:1 vs background, since the border is the only cue) |
| radius | same as button of the same size |
| leading/trailing icon | icon size from the control table, inset = padding-x, text padding = padding-x + icon + gap |
| label ↔ input | 2u (8) |
| input ↔ helper/error text | 1.5u (6) |
| field ↔ next field | 4u–6u (16–24) |
| textarea | min-height = 3 lines + 2 × padding-y; same radius |
| select chevron | 16px icon, trailing, inset = padding-x |

States: focus (ring as for buttons, border switches to accent), invalid (danger border + message with icon, never color alone), disabled, read-only (visibly different from disabled).

### Input with attached button (input group)

Outer container has radius `R` and a padding `d` around the inner button. Inner button radius = `max(0, R − d)`.

Example: md input `R = 6`, inset `d = 4`, so inner button radius = 2 and inner button height = 40 − 2 × 4 = 32 (sm). If 2 looks too sharp, raise the outer radius rather than breaking the concentric rule: R = 8 gives inner 4, the crisp sm radius, which is the ideal match.

### Checkbox, radio, switch

| Element | Size | Radius |
|---|---|---|
| checkbox | 16 (md), 20 (lg) | half the control radius, min 2 (→ 3–4) |
| radio | 16 / 20 | full |
| switch track | width = 2 × height − 4; height 20 (md) | full |
| switch thumb | track height − 2 × 2 (2px inset) | full (concentric with track) |
| label gap | 2u (8) | |
| hit area | whole row including label, ≥44px tall on touch | |

### Segmented control / tabs with a track

Track: height `h`, padding `d = 2–4`, radius `R`. Segments: height `h − 2d`, radius `R − d`. With crisp md: track h 40, R 8 (use the lg radius so the inner segments land on a scale value), d 4 → segments 32 tall with radius 4.

### Underline tabs

Height = control height; label padding-x = 0.4 × h; active indicator 2px tall, flush with the bottom border, width = label width (not the full tab), radius 0 or 1. Gap between tabs is 0; padding does the spacing so hit areas touch.

## Surfaces

### Card / panel

| Property | Formula | Default |
|---|---|---|
| padding | 4u (dense 3u, roomy 6u) | 16 |
| radius | min(2 × r(control md), padding) | 12 |
| border | 1px `--color-border` | |
| shadow | none (in a grid of cards), level 1 only if the card is interactive/draggable | |
| header ↔ body | 3u–4u | 12–16 |
| full-bleed media | top corners = card radius, bottom corners 0; or `overflow: hidden` | |
| media inset by `d` | media radius = card radius − d | e.g. 12 − 8 = 4 |
| nested card inside card | don't. Use a divider or a subtle background tint instead | |

### Popover, dropdown menu, combobox list

| Property | Formula | Default |
|---|---|---|
| inset (padding around items) | u | 4 |
| item height | control sm (32), md for touch (40) | 32 |
| item padding-x | 2u | 8 |
| item radius | r(control sm) | 4 |
| menu radius | item radius + inset (concentric) | 8 |
| min-width | max(trigger width, 8 × h) | |
| offset from trigger | 1u–2u | 4–8 |
| shadow | overlay level (2–3) + 1px border | |
| separator | 1px, margin-y = inset, full-bleed to the menu's inner edge | |

### Modal / dialog

| Property | Formula | Default |
|---|---|---|
| width | from content: 400 (confirm), 560 (form), 720+ (complex) | |
| padding | 6u | 24 |
| radius | r(surface) + 4, or equal to surface; never smaller than a card | 12–16 |
| title ↔ body | 2u | 8 |
| body ↔ actions | 6u | 24 |
| actions | right-aligned, primary last (rightmost), gap 2u | |
| backdrop | neutral-950 at 40–60% opacity; no blur by default | |
| max-height | 100dvh − 2 × 6u, body scrolls, header/actions stay | |

### Toast / banner

Height ≥ control md; padding 3u–4u; radius = r(surface) for floating toasts, 0 for full-width banners; icon 16–20 aligned to the first line's cap height; close button is an icon-only sm button whose top/right inset equals the toast padding.

## Data display

### Table

| Property | Formula |
|---|---|
| row height | control scale: 32 compact, 40 regular, 48 comfortable |
| cell padding-x | 3u (12); first/last cell padding-x = the container padding so the table aligns with surrounding text |
| header | same height, `--text-sm`, weight 500–600, muted color, sticky if long |
| dividers | 1px horizontal only; no vertical rules unless columns are dense numbers |
| numbers | right-aligned, `tabular-nums`; headers aligned with their data |
| row hover | background tint, not a border or shadow |
| inside a card | table's outer radius = card radius (clip with `overflow: hidden`) |

### List item

Height from the control scale; leading avatar/icon size = line-height of the primary text or 2 × line-height for two-line items; gap 3u; trailing meta right-aligned, muted.

### Badge / tag / status

Height = 20–24 (half-step allowed); padding-x 1.5u–2u; font xs/sm, weight 500; radius = half the control radius (min 2), or full if the shape personality is pill. Status dots 6–8px, fully round, always paired with a text label.

### Avatar

Sizes from the scale (24 / 32 / 40 / 48 / 64). Round, or `r = 0.25 × size` for a squircle-ish product look, chosen once. Avatar stacks overlap by 25% with a 2px ring in the background color.

### Stat / KPI

Number in a large type step with `tabular-nums` and tight tracking; label above or below in `--text-sm` muted; delta with icon + sign + color (never color alone). Units smaller than the number and baseline-aligned.

## Layout

### Page frame

- Header height = control lg (48) + 2 × 2u = 64, or 56 for dense apps (always a multiple of u).
- Sidebar width from content: 240–280 typical; collapsed = control md + 2 × 2u (56).
- Content padding: 16 (mobile), 24 (tablet), 32 (desktop).
- Sections separated by 16u–24u (64–96) on marketing pages, 8u–12u (32–48) in apps.

### Forms

- Single column. Labels above inputs (fastest to scan); left labels only for dense settings pages, with a fixed label column width.
- Inputs sized to expected content (a ZIP code field isn't full width), but aligned to the grid.
- Primary action aligned with the inputs' left edge (or right, for dialogs), not centered.

## Optical adjustments (the last 5%)

Math gets you consistent; these get you right. Apply them deliberately and sparingly:

- **Icons beside text:** align to cap height, not to the line box. Usually means a 1px nudge.
- **Play/arrow triangles** in circles: shift right by ~8% of the icon size so they look centered.
- **Round shapes look smaller** than squares of the same size; a circular icon may need +1–2px to match.
- **Uppercase labels** need +0.04–0.08em tracking and look visually larger; drop one size step.
- **Large headings** look misaligned at the left edge because of side bearing; a −1 to −2px margin-left can fix it at display sizes.
- **Padding next to icons** is 2px less than next to text, because icons include internal whitespace.
