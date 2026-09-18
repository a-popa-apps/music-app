---
name: crate-carousel
description: Generate a CratePrep Instagram/TikTok tip carousel (a Design-canvas Artifact with one Hook slide, N tip slides, and a frozen Follow-CTA closer) in the established black/orange/pink brand style. Trigger this whenever the user asks for a new carousel, tip cards, or Instagram/TikTok post set for CratePrep -- e.g. "make a carousel about X", "generate tip cards for Y", "new IG post on Z" -- not just when they type the slash command explicitly.
---

# CratePrep tip carousel generator

Produces a ready-to-post multi-slide Design-canvas Artifact matching the
carousel format established in the "CratePrep Tip Card Generator" canvas
(https://claude.ai/artifact/QJ9ZE5RgQn6bDnB5xV4uh1). Read that canvas first
if it still exists and you need a live reference for exact current values --
this file is the frozen spec so future sessions don't have to.

## When invoked

1. If the user gave a topic but no specific tips/copy, brainstorm 2-4 short,
   punchy tips yourself (same voice as existing posts: direct, DJ-to-DJ,
   a little irreverent -- see the "CratePrep Social Content Plan" doc if it
   exists for tone/pillar guidance). Confirm the copy with the user only if
   it's ambiguous; otherwise just generate a sensible draft -- they can ask
   for edits.
2. Decide the number of middle "tip" slides (default 3 unless the user
   says otherwise). Total slide count = 1 hook + N tips + 1 closer.
3. Build the canvas per the layout and card specs below, using the Design
   (canvas) Artifact type (`type_url`: search `list, type: "Design System"`
   is NOT needed here -- no design system is attached; build with this
   spec directly). Read `artifact-type/reference/format.md` from the new
   canvas before writing the first artboard if you haven't in this session.
4. One line back to the user with the link -- don't narrate the mechanism.

## Fixed brand tokens (never vary these)

- Background: `#000000`
- Orange accent: `#ff6b35`
- Pink accent: `#ff3d78`
- Bottom accent bar on every slide: `height: 10px; background: linear-gradient(90deg, #ff6b35, #ff3d78);`
- Headline font: **Bungee** (Google Fonts) -- `font-family: 'Bungee', 'Inter', system-ui, sans-serif; font-weight: 400; text-transform: uppercase;`
- Body/caption font: **Inter** -- `font-family: 'Inter', system-ui, sans-serif; font-weight: 600;`
- Handle/kicker/meta font: **JetBrains Mono**
- Google Fonts link (put in every artboard's `<helmet>`):
  `<link href="https://fonts.googleapis.com/css2?family=Bungee&family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@600;700&display=swap" rel="stylesheet">`
- Handle everywhere: `@crateprep`, white, JetBrains Mono, 30px, weight 700, `letter-spacing: -0.02em`.
- Orange titles ALWAYS carry this exact hard drop shadow, no blur:
  `text-shadow: 6px 6px 0 rgba(0,0,0,0.4);`
- Every artboard is 1080x1350 (IG portrait 4:5).

## Effect layers (every artboard, in this exact stacking order, bottom to top)

1. **Photo texture** (optional, only if a suitable light-leak/grain photo
   asset is available in the target canvas -- see "Reusing the texture
   photo" below). `position:absolute; inset:-Npx (40-60, vary per card);
   width/height: calc(100% + 2*N px); object-fit:cover; object-position:
   <random %,%>; transform: rotate(<random -20..20deg>); opacity:0.2;
   pointer-events:none;` -- vary N/position/rotation per card so no two
   look identical. If no photo asset is available, skip this layer
   entirely (do not fabricate one, do not block on it).
2. **Grain** -- one inline SVG filter per artboard (unique `id` per file to
   avoid collisions), then a full-bleed div using it:
   ```html
   <filter id="crateGrainXXX">
     <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch" result="noise"></feTurbulence>
     <feColorMatrix in="noise" type="saturate" values="0"></feColorMatrix>
   </filter>
   ```
   Applied via `filter: url(#crateGrainXXX); mix-blend-mode: overlay; opacity: 0.30;` on a `position:absolute; inset:0;` div. This grayscale-noise-plus-overlay combo is deliberate -- a naive white-noise-plus-overlay looks INVISIBLE on pure black (overlay is a no-op on the darkest possible base), so always use saturate(0) turbulence, never colored noise.
3. **Two corner glow blobs** -- soft radial gradients, one orange one pink,
   opposite corners, e.g. `position:absolute; top:-220px; right:-220px;
   width:620px; height:620px; border-radius:9999px; background:
   radial-gradient(circle, rgba(255,107,53,0.30) 0%, rgba(255,107,53,0) 70%);
   filter: blur(10px);` -- vary corner placement per card.
4. **Light-leak streak** -- oversized rotated linear+radial gradient combo,
   `mix-blend-mode: screen` (screen only adds brightness, correct for a
   light leak on ANY background color), `opacity: 0.25`, random angle and
   warm-cream/teal color placement per card, e.g.:
   ```html
   <div style="position:absolute; inset:-120px; transform: rotate(<deg>);
     background: linear-gradient(<angle>deg, rgba(255,255,255,0) 20%, rgba(255,246,225,0.9) 40%, rgba(140,225,215,0.55) 55%, rgba(255,255,255,0) 70%),
       radial-gradient(circle at <x%> <y%>, rgba(255,246,225,0.8), transparent 44%),
       radial-gradient(circle at <x%> <y%>, rgba(140,225,215,0.55), transparent 44%);
     filter: blur(36px); mix-blend-mode: screen; opacity: 0.25; pointer-events: none;"></div>
   ```

## Card types

### 1. Hook slide (always exactly one, always first)

No kicker pill, no drop-shadow-body-copy constraints beyond what's below.
Left-aligned, vertically centered as a block:

- `<h1>`: ONE short title (1-3 words, e.g. "3 Things"), orange `#ff6b35`,
  `font-size: 108px; line-height: 1.05;`, the standard drop shadow.
- `<h2>` directly below: ONE white subtitle continuing the sentence (e.g.
  "Ruining Your Rekordbox Library Right Now"), white `#ffffff`,
  `font-size: 60px; line-height: 1.15;`, same drop-shadow treatment
  (`text-shadow: 5px 5px 0 rgba(0,0,0,0.4);`), wrap across as many lines
  as it naturally needs (no hard line-count cap here -- there's no caption
  competing for space).
- Handle row + accent bar as usual, no kicker pill.

### 2. Middle tip slides (N of them, between hook and closer)

Same structure as the existing "Crate Tip 0N" cards:

- Kicker pill, top-left: `Crate Tip 0N` (sequential, orange text, orange
  8%-opacity pill bg, orange 35%-opacity border), JetBrains Mono 20px.
- `<h1>` title: orange `#ff6b35`, Bungee, `font-size: 72px; line-height:
  1.18;`, the standard drop shadow. **MUST fit in exactly 2 lines** --
  rephrase/shorten the copy if needed rather than letting it wrap to 3+ or
  shrinking the font. Manually insert the `<br>` at the natural break.
- `<p>` caption: white `#ffffff`, Inter, `font-size: 40px; line-height:
  1.45; font-weight: 600; max-width: 800px;`. **MUST fit in 4 lines or
  fewer** at that size/width -- shorten the copy if it would run longer,
  don't shrink the font to force a fit.
- Handle row (`@crateprep`, white) + accent bar as usual.
- Content padding on every card: `padding: 88px;` uniform (not asymmetric
  top/bottom -- that was a real bug once: asymmetric padding visibly
  skews the vertically-centered block off-center).

### 3. Closer slide (always exactly one, always last, text never changes)

Reuse verbatim -- this is frozen copy, do not reword it even if asked to
"vary" the carousel, unless the user explicitly asks to change the closer
itself:

```html
<h1 style="...">Follow<br><span style="color: #ff6b35;">@crateprep</span></h1>
<p style="...">DJ tips, before/afters, and feature drops every week.</p>
```

Centered layout (`align-items:center; justify-content:center; text-align:
center;`), no kicker pill. Handle row below still shows `@crateprep` white.

## Canvas layout mechanics

Artboards sit left to right, 80px gutter, all `y:0`, all `w:1080 h:1350`:
hook at `x:0`, then each tip slide at `x: 1160, 2320, 3320+...` (each +1160
from the last), closer at the final `+1160` slot. `order` array = same
left-to-right sequence (z-order doesn't matter here, nothing overlaps).
Name files descriptively (`Hook.dc.html`, `Tip1.dc.html`, `Tip2.dc.html`,
..., `Closer.dc.html`) -- don't reuse the old `Main.dc.html`/`Card2.dc.html`
naming from the original canvas, that was incidental.

## Reusing the texture photo

The light-leak photo texture (a real analog-film light-leak shot the user
supplied) lives as an uploaded asset on the original canvas,
`https://claude.ai/artifact/QJ9ZE5RgQn6bDnB5xV4uh1`, asset id
`b0b560b406b78d5835989eea1c6e467f`. To reuse it in a NEW canvas without
asking the user to re-share the file: `Artifact({action:"publish", url:
<new canvas url>, asset:true, from_url:
"https://claude.ai/artifact/QJ9ZE5RgQn6bDnB5xV4uh1", asset_ids:
["b0b560b406b78d5835989eea1c6e467f"]})` -- this copies it server-side, no
download/re-upload, and returns the new canvas's own `/_blob/<id>` to
reference. If that source canvas is ever deleted or inaccessible, fall back
to the CSS-only light-leak (step 4 above works with zero external assets)
and mention to the user that the photo-texture layer was skipped.

## Triggering this in future sessions

Two ways, both work:
- Explicit: the user types `/crate-carousel` (optionally with a topic,
  e.g. `/crate-carousel <args>topic: energy auto-sort feature</args>`).
- Implicit: the user just asks in plain language ("make a carousel about
  X", "new IG post for Y", "generate tip cards on Z") -- Claude Code
  matches this skill's `description` against that intent automatically;
  no slash command required.
