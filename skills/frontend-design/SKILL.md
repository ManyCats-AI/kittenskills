---
name: frontend-design
description: Build or restyle web interfaces (pages, components, apps, landing pages, dashboards) as a calculated design system: every size, radius, space, color, and shadow derived from a few explicit inputs, so components fit together precisely and nothing looks AI-generated (no default purple gradients, glassmorphism, or emoji icons). Use when the user asks to create, design, style, or improve UI or front-end code in HTML/CSS, React, Vue, Svelte, Tailwind, or similar, or says a UI looks generic, ugly, inconsistent, "AI-looking", or broken.
---

# Frontend Design

A designed interface is a **system**: a handful of decisions, each turned into a formula, and every pixel on screen traced back to one of them. AI slop is what you get when each value is picked locally ("this card looks nice with 14px radius and a purple glow") instead of derived globally.

The rule for this skill: **no magic numbers.** If you can't say which formula or token a value came from, it's wrong.

## Related files and skills

| What | Where |
|---|---|
| Calculator: type scale, control geometry, concentric radii, OKLCH palettes, contrast, full token set, slop audit | `scripts/design_math.py` (run with `python3`, stdlib only) |
| Exact specs for every common component (button, input, card, menu, table, modal, …) | `references/component-geometry.md` |
| Charts, dashboards, data visualization | `dataviz` if available |
| Baseline coding rules (scope, verification, security) | `engineering-practices` |

## Workflow

Do the steps in order. Steps 2–3 happen **before** any component code is written.

### 1. Write a design brief (5 lines, not more)

Answer these in writing, in the conversation or a `DESIGN.md`:

1. **Who and what task.** "Ops engineers triaging 200 alerts a shift" designs differently from "first-time buyers comparing plans."
2. **Density.** Compact (data tools, 32px controls), regular (apps, 40px), or comfortable (marketing/consumer, 48px).
3. **Tone, in three concrete adjectives**, each tied to the audience. "Calm, precise, utilitarian," not "modern and clean" (which means nothing and produces slop).
4. **Shape personality**: sharp, crisp, soft, or pill (see step 2). One, everywhere.
5. **One signature move.** The single distinctive decision the design commits to: an unusual typeface, a strong accent used sparingly, a strict editorial grid, oversized numerals, a monochrome palette with one hot color. One. Not five half-hearted flourishes.

**Check the repo first.** If there's an existing design system, Tailwind config, theme file, or brand guide, the inputs come from there. Extend it; don't fight it. If it's internally inconsistent, propose consolidating it rather than adding another layer.

### 2. Derive the system

Pick the inputs, then calculate everything else. Run `<skill-dir>/scripts/design_math.py tokens` (by full path, from the project directory) to do the arithmetic and emit CSS custom properties; the derivations it uses are below so you can apply them by hand or in another format (Tailwind theme, JS tokens, SwiftUI).

```bash
python3 <skill-dir>/scripts/design_math.py tokens --unit 4 --base 16 --ratio 1.2 \
  --heights 32,40,48 --shape crisp --hue 155 --chroma 0.13 > tokens.css
```

It refuses to finish (exit 1) if any semantic color pair fails WCAG contrast.

#### 2a. Base unit → spacing

- **Unit `u` = 4px** (8px for spacious marketing pages). Every spacing value is `n × u`.
- Scale: `4 8 12 16 20 24 32 40 48 64 80 96`. Use only these.
- **2px half-steps** are allowed *inside* a component (icon-to-label nudges, badge padding), never for layout between components.
- **Proximity rule (Gestalt):** space inside a group must be clearly smaller than space between groups. Use a ratio of at least 2×:

  | Relationship | Typical gap |
  |---|---|
  | Icon ↔ its label | 6–8 |
  | Label ↔ its input; heading ↔ its paragraph | 8 |
  | Field ↔ next field; list item ↔ list item | 16–24 |
  | Group ↔ group within a section | 32–48 |
  | Section ↔ section | 64–96 |

  If two unrelated things are as close as two related things, the layout lies about its structure.

#### 2b. Type scale

- **Modular scale:** `size(n) = base × ratio^n`, rounded to whole px. Pick the ratio by density:
  - 1.125 (major second): dense data UIs, few heading levels
  - 1.2 (minor third): most apps
  - 1.25 (major third): marketing, docs
  - 1.333 (perfect fourth): editorial, landing pages with drama
- **Line-height is snapped to the grid unit** so text lines up with spacing: body ≈ 1.5, subheads ≈ 1.25, display ≈ 1.15, then round to the nearest multiple of `u`. 16 → 24, 14 → 20, 12 → 16, 20 → 28, 32 → 40, 48 → 56.
- **Tracking:** tighten large text (−0.01em at ≥24px, −0.02em at ≥32px); loosen small caps and tiny labels (+0.02 to +0.06em).
- **Weights:** at most three (e.g. 400, 500, 600). Hierarchy comes from size and color first, weight second.
- **Families:** one, or two with a clear job split (display + text, or text + mono). Choose for the audience and the tone adjectives, not by default; say why you chose it.
- **Measure:** body text 60–75 characters (`max-width: 65ch`).
- **Numbers in tables and stats:** `font-variant-numeric: tabular-nums` so columns align.

#### 2c. Component sizes

Controls (buttons, inputs, selects, segmented controls) share **one height scale**, so a button and an input in the same row align exactly. Default `32 / 40 / 48`.

```
height  = line-height + 2 × padding-y + 2 × border        (set height explicitly; center content)
padding-x ≈ 0.4 × height, snapped to u                     (32 → 12, 40 → 16, 48 → 20)
icon    = 16 for heights ≤ 40, 20 for 48
icon gap = 6 (small) / 8 (medium, large)
icon-only button: width = height (square), same radius
```

Run `design_math.py controls` to get the table for your inputs. Everything that sits in a row with controls (table rows, list items, tabs, chips) uses a height from the same scale.

#### 2d. Radius: one family, calculated

Radius is where generated UIs fall apart: 6px buttons inside 24px cards inside 12px panels, each picked independently. Instead:

1. **Pick a shape personality** and derive control radius from height, so corners have the same curvature at every size:

   | Personality | radius / height | 32 / 40 / 48 controls |
   |---|---|---|
   | sharp | 0.05 | 2 / 2 / 2 |
   | crisp | 0.15 | 4 / 6 / 8 |
   | soft | 0.25 | 8 / 10 / 12 |
   | pill | 0.5 | 16 / 20 / 24 (fully round) |

2. **Concentric rule.** When one rounded shape sits inside another with an even inset `d` (a button inside an input group, an item inside a menu, an image inside a padded card, tabs inside a tab track, a focus ring around a button):

   ```
   outer radius = inner radius + d
   inner radius = max(0, outer radius − d)
   ```

   Same center of curvature means the gap between the two curves stays constant. Violating this is the single most visible "something is off" tell. `design_math.py radius --inner 6 --inset 4` → 10.

3. **Surfaces** (cards, panels, modals): `min(2 × control radius, surface padding)`, snapped to 2. A radius larger than the padding makes content look like it's about to fall out of the corner.
4. **Small elements** (badges, tags, checkboxes): half the control radius, minimum 2. Avatars and status dots: fully round.
5. **Nesting order:** radius never increases as you go inward. A child never has a larger radius than its parent.
6. **Things that touch an edge** (a full-bleed image at the top of a card, a table inside a card) take the parent's radius on the touching corners and 0 elsewhere, or get clipped with `overflow: hidden`.

Result: at most ~5 radius values in the whole product, each with a reason.

#### 2e. Borders, focus, elevation

- **Border:** 1px everywhere. A heavier border is a different token with a reason (selected state, emphasis).
- **Focus ring:** 2px outline at 2px offset, accent-colored, ≥3:1 against the background. Its radius is concentric: `element radius + offset`. `outline` with `outline-offset` follows `border-radius` in modern browsers; check it.
- **Elevation** comes from a single light source above the screen. Shadows are two layers (tight key shadow + soft ambient), tinted with the neutral hue, low opacity. Each level doubles the y-offset and blur = 2 × y. Use 2–3 levels total: raised (cards, if needed at all), overlay (menus, popovers), modal.
- **Prefer borders over shadows** for separating flat content. Shadows mean "this floats above" (menus, dialogs, dragged items). A card in a grid usually doesn't float.
- **Dark mode:** elevation comes from lighter surfaces, not shadows.

#### 2f. Color

Work in **OKLCH**, where equal lightness steps look equal, and convert to hex if needed. `design_math.py palette --hue H --chroma C` builds an 11-step ramp and reports contrast for every step.

- **Neutrals carry the interface** (90%+ of pixels): background, surfaces, borders, text. Give them a whisper of the accent hue (chroma 0.005–0.02) so they feel related to the brand instead of dead gray.
- **One accent**, used sparingly: primary action, links, focus, selection. If everything is accented, nothing is.
- **Semantic colors** (success, warning, danger, info) are separate ramps used only for their meaning.
- **Choose the hue for a reason:** the brand, the domain (finance, health, tooling), or the tone adjectives. Write the reason down. Hues 255–320 at high chroma (indigo, violet, purple) are the default of generated UIs; using them requires a brand reason.
- **Roles, not raw values.** Components use `--color-text-muted`, never `--neutral-600` or `#6b7280`. The role-to-step mapping is chosen by contrast: each role takes the step closest to the background that still passes (body text 4.5:1, large text and UI components 3:1). The `tokens` command does this.
- **Text on color:** compute it; don't assume white works.
- **Never encode meaning in color alone:** pair it with an icon, label, or pattern.
- **Gradients:** only when they encode something (a scale, a heatmap, a real light effect on an image). Never as a default background, never on text.

#### 2g. Layout grid

- A **12-column grid** (4 on mobile, 8 on tablet) with gutters from the spacing scale (16 mobile, 24 desktop) and outer margins of 16 / 24 / 32+.
- **Content max-width** chosen from the content: ~65ch for reading, 1200–1440px for apps and dashboards.
- **Breakpoints** where the content breaks, not at device names. Mobile-first.
- **Alignment:** every element's left edge lines up with something else's. Pick the alignment axis for a page and hold it. Text baselines in a row align; icons are optically centered on the cap height or x-height, not the line box.

#### 2h. Motion, layers, icons

- **Durations:** 100 (micro: hover, press), 150–200 (small: menus, toggles), 300 (large: modals, drawers). Enter with ease-out, exit with ease-in, exits faster than entrances. Animate only `transform` and `opacity`. Respect `prefers-reduced-motion`.
- **z-index scale** as tokens: base, dropdown, sticky, overlay, modal, toast. No `z-index: 9999`.
- **Icons:** one set, one stroke weight matched to the text weight (≈1.5px stroke at 20px for regular text), sized from the control table. Never emoji as UI icons.

### 3. Spec the components before building

For each component you'll build, write its geometry as a small table first, with every value pointing at a token. Use `references/component-geometry.md` for the standard specs. Example:

| Button (md) | Value | From |
|---|---|---|
| height | 40 | `--control-md-h` |
| padding-x | 16 | 0.4 × 40 |
| font / line-height | 14 / 20 | `--text-sm` |
| icon / gap | 16 / 8 | control table |
| radius | 6 | crisp: 0.15 × 40 |
| focus ring radius | 8 | 6 + 2 offset (concentric) |

If a component needs a value that isn't in the system, either the system is missing a token (add it, with its formula) or the component is wrong.

### 4. Build structure first

- **Semantic HTML:** `header`, `nav`, `main`, `section`, `article`, `button`, `a`, `label`, `table`. Real buttons for actions, real links for navigation.
- **Layout with Grid and Flexbox,** using `gap` from the spacing scale rather than margins on children.
- **Hierarchy** with size, then color, then weight, then space. One obvious primary action per screen; secondary actions visibly quieter.
- **Real content.** Write the actual labels, numbers, names, and copy, including the long and ugly cases. Placeholder copy hides layout problems and is itself a slop signal.
- **Tokens only.** Components reference tokens, never literal px, hex, or Tailwind default palette classes. In Tailwind, put the tokens in the theme and remove the default palette so `indigo-500` can't creep in.

### 5. Design every state

- **Interaction:** default, hover, focus-visible, active/pressed, disabled, and selected where relevant. State changes alter color/border/shadow, never size or position (no layout shift).
- **Data:** loading (skeletons shaped like the content), empty (what it is and how to fill it), error (what happened and how to recover), partial, and overflow (long names, 0 items, 1 item, 10,000 items).
- **Feedback:** every action gets visible confirmation; anything slower than ~400ms shows progress.

### 6. Accessibility (required)

- Keyboard-only use works everywhere, with a visible focus ring and logical tab order.
- Every input has a `<label>`; images have meaningful `alt` (or `alt=""` if decorative); icon-only buttons have `aria-label`.
- Contrast: 4.5:1 body text, 3:1 large text, UI components, input borders, and focus rings. Verified with `design_math.py contrast`, not estimated.
- Touch targets ≥ 44×44 (a 32px control can extend its hit area with padding or a pseudo-element).
- Native semantics first; ARIA only following the WAI-ARIA Authoring Practices.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`; text zoom to 200% doesn't break layout.

### 7. Audit the code

```bash
python3 <skill-dir>/scripts/design_math.py audit src/ --unit 4
```

It flags off-grid pixel values, too many distinct radii and font sizes, raw hex colors outside token files, and known slop patterns (purple/indigo Tailwind classes, gradients, gradient text, glassmorphism, blur blobs, heavy shadows, emoji, generic marketing copy). Fix every flag or write down why it stays. Then check by hand:

- Every radius traceable to the radius rules; concentric where nested.
- Rows of controls share one height; their text baselines align.
- Spacing follows the proximity rule; no two different gaps that are almost equal (16 next to 18 means one is wrong).
- Nothing uses a color outside the role tokens.

### 8. Look at it, critique it, fix it

Don't ship UI you haven't seen. Run it and take screenshots at 375, 768, and 1280+ wide, light and dark, and with long content. Then critique like a senior designer:

- **Squint test:** blur your eyes. Is the primary action the first thing you see? Is the hierarchy obvious?
- **Edge test:** draw imaginary vertical lines. How many distinct left edges are there? Fewer is better.
- **Corner test:** zoom to 400% on nested corners. Is the gap between inner and outer curves even?
- **Slop test:** run through the list below. Would someone glance at this and think "an AI made this"? If yes, find the cause and remove it.
- **Remove test:** what can be removed without losing meaning? Remove it.

Iterate at least once. The first render is a draft.

## AI slop: what it is and what to do instead

These patterns are the visual fingerprint of generated UIs. Avoid them unless the brief gives a specific, written reason.

| Slop | Why it reads as slop | Instead |
|---|---|---|
| Purple/indigo/violet gradients, especially as hero backgrounds | It's the default of every template and model | A hue chosen for the brand or domain; flat color; real imagery |
| Gradient text (`bg-clip-text`) | Decoration with no meaning; hurts legibility | Solid text; hierarchy through size and weight |
| Glassmorphism, `backdrop-blur` chrome | Trendy, low contrast, expensive to render | Opaque surfaces with a border |
| Blurred color blobs and glows in the background | Fills space with nothing | Whitespace, or real content |
| Neon accents on near-black ("dark mode = cyberpunk") | Generic and fatiguing | A calm dark palette from the same ramps, accent lightened just enough to pass contrast |
| Every element with a large radius and `shadow-xl` | No hierarchy; everything floats | Radius from the system; shadows only for things that actually float |
| Three identical feature cards, each with an icon in a rounded square | The template every landing page starts from | Layout driven by the actual content: a comparison table, a screenshot with annotations, a list with real detail |
| Centered hero, giant headline, two buttons, then a card grid | Same | A layout that fits the product's real first impression |
| Emoji or ✨ sparkles as icons | Unprofessional, inconsistent rendering | One icon set at a consistent stroke |
| Pill badges and chips everywhere | Visual noise | Plain text labels; badges only for status |
| Gray text on colored backgrounds | Fails contrast; looks washed out | Computed on-color text |
| Generic copy ("Unlock the power of…", "Seamless", "Elevate your workflow", "Lorem ipsum") | Says nothing; signals no one thought about the product | Specific claims, real numbers, real names |
| Fake social proof ("10k+ happy users", made-up testimonials) | Dishonest and obvious | Real data or leave it out |
| Scroll-triggered fade-ins on every section | Delays content; feels like a template | Content visible on load; motion only for state changes |
| Tailwind defaults left as the design (indigo-600 primary, gray-500 text, rounded-lg everything) | Recognizable instantly | Tokens derived from the brief |

## Output checklist

- [ ] Design brief written (audience, density, tone, shape, signature move)
- [ ] Tokens derived from explicit inputs; derivation recorded (comment at the top of the token file)
- [ ] Every component spec traces to tokens; no magic numbers
- [ ] Radii: one family, proportional to height, concentric where nested, never growing inward
- [ ] Control heights shared across buttons, inputs, and row-aligned elements
- [ ] Spacing on the grid and obeying the proximity rule
- [ ] Colors are roles, contrast-verified in light and dark
- [ ] All interaction and data states designed
- [ ] Keyboard accessible, labeled, touch-target sized
- [ ] `design_math.py audit` clean, or every remaining flag justified
- [ ] Screenshots taken at three widths, both themes; critique pass done and fixes applied
- [ ] Nothing on the slop list without a written reason
