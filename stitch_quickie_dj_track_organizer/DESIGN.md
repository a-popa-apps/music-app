---
name: Quickie Design System
colors:
  surface: '#faf9f7'
  surface-dim: '#dadad8'
  surface-bright: '#faf9f7'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f1'
  surface-container: '#efeeec'
  surface-container-high: '#e9e8e6'
  surface-container-highest: '#e3e2e0'
  on-surface: '#1a1c1b'
  on-surface-variant: '#444748'
  inverse-surface: '#2f3130'
  inverse-on-surface: '#f1f1ef'
  outline: '#747878'
  outline-variant: '#c4c7c7'
  surface-tint: '#5f5e5e'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1c1b1b'
  on-primary-container: '#858383'
  inverse-primary: '#c9c6c5'
  secondary: '#ab3500'
  on-secondary: '#ffffff'
  secondary-container: '#fe6a34'
  on-secondary-container: '#5d1900'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1d1b1a'
  on-tertiary-container: '#868381'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e5e2e1'
  primary-fixed-dim: '#c9c6c5'
  on-primary-fixed: '#1c1b1b'
  on-primary-fixed-variant: '#474646'
  secondary-fixed: '#ffdbd0'
  secondary-fixed-dim: '#ffb59d'
  on-secondary-fixed: '#390c00'
  on-secondary-fixed-variant: '#832600'
  tertiary-fixed: '#e6e1df'
  tertiary-fixed-dim: '#cac6c3'
  on-tertiary-fixed: '#1d1b1a'
  on-tertiary-fixed-variant: '#484645'
  background: '#faf9f7'
  on-background: '#1a1c1b'
  surface-variant: '#e3e2e0'
typography:
  display-hero:
    fontFamily: Inter
    fontSize: 72px
    fontWeight: '800'
    lineHeight: 76px
    letterSpacing: -0.04em
  display-hero-mobile:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 44px
    letterSpacing: -0.03em
  headline-xl:
    fontFamily: Inter
    fontSize: 44px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.03em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.025em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.015em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.005em
  meta-numeric:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: -0.02em
  meta-badge:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  hairline: 1px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  4xl: 96px
  container-margin-mobile: 16px
  container-margin-desktop: 48px
  tracklist-row-height: 48px
  player-bar-height: 72px
---

## Brand & Style

This design system targets working club and bedroom DJs, crate-diggers, and electronic music producers who demand ruthless efficiency, ultra-fast cognitive processing, and pristine aesthetic restraint. The emotional response is immediate confidence, surgical precision, and professional credibility.

The aesthetic synthesizes four distinct influences:
- **Apple**: Imposing typographic scale, generous negative space, deliberate lack of visual clutter, and strict grid discipline.
- **Beatport**: High-density functional utility, technical metadata priority (BPM, Key, Energy), and club-grade dark contrast.
- **SoundCloud**: Dynamic, warm orange (#FF6B35) focal energy, pill-shaped taxonomy tags, and responsive waveform visualization.
- **Volumio**: Razor-thin 1px architectural hairline dividers, zero skeuomorphism, absolute focus on core media data.

The overall style is **Minimal Technical Precision**—a hybrid of editorial minimalism and industrial audio hardware UI.

## Colors

The palette operates on high-contrast bipolarity: sterile, pristine daytime light surfaces coupled with immersive carbon performance surfaces.

### Core Swatches
- **Accent Primary**: `#FF6B35` (Active player heads, hot cues, selected chips, waveform playback progression)
- **Accent Muted/Glow**: `rgba(255, 107, 53, 0.12)` (Focus rings, hover fills on technical tags)
- **Light Surfaces**:
  - Base: `#FFFFFF`
  - Subtle Inset / Striping: `#F8F7F5`
  - Hairline Border: `#E5E5E5`
- **Dark & Performance Surfaces**:
  - Pitch Canvas: `#000000`
  - Carbon Deck: `#111111`
  - Hairline Border: `#262626`
- **Text & Metadata Hierarchy**:
  - Jet Black (High-emphasis light): `#0D0D0D`
  - Charcoal (Muted metadata light): `#555555`
  - Light Silver (High-emphasis dark): `#E5E5E5`
  - Medium Grey (Secondary metadata dark): `#888888`
  - Ghost Hairline (Disabled/inactive): `#CCCCCC` (Light), `#333333` (Dark)

### Application Rules
- Use `#FF6B35` with surgical restraint. It indicates state change, active audio stream, or hot tags. Never use it as a decorative wash or large background.
- Contrast boundaries are demarcated by 1px borders (`#E5E5E5` or `#262626`) rather than elevation drop-shadows.

## Typography

The typography strategy leverages **Inter** for massive, confident editorial headlines and pure neutral body content, juxtaposed with **JetBrains Mono** for all performance data (BPM, Musical Key, Camelot notations, Track Durations, Bitrates).

- **Headlines**: Tight letter spacing (-0.03em to -0.04em), heavy weights (700/800), zero decoration. Line heights hug the text tightly for an architectural poster feel.
- **Body**: Neutral, open, high legibility with generous breathing room.
- **Data & Metadata**: Fixed-pitch tabular figures eliminate horizontal layout shifts when values update dynamically or scrub during playback. All BPMs and Key indicators render in JetBrains Mono.

## Layout & Spacing

Layouts follow an ultra-disciplined 12-column fluid grid system pinned to generous max containers (1440px wide) with edge-to-edge full-bleed hairline sectioning.

### Form Factors & Breakpoints
- **Desktop (1024px+)**: 12 columns, 24px gutters, 48px margins. Full track view exposes title, artist, key, BPM, energy grade, date added, duration, and full inline waveform.
- **Tablet (768px - 1023px)**: 8 columns, 16px gutters, 32px margins. Condensed waveforms, secondary metadata moves to sheet drawers.
- **Mobile (< 768px)**: 4 columns, 12px gutters, 16px margins. High-density vertical track list. Primary metadata (Key + BPM) remains permanently anchored to the right edge for instant scanning.

### Spacing Principles
- Vertical rhythm follows an explicit 8px baseline matrix.
- Interactive audio components rely on rigid heights: `tracklist-row-height` (48px) ensures touch accuracy while allowing high information density on 13-inch DJ laptop displays.
- Section boundaries switch dramatically between pure white (#FFFFFF) containers and pure black (#000000) performance surfaces.

## Elevation & Depth

This system intentionally eliminates blurred shadows, volumetric gradients, and skeuomorphic drop-shadows. Depth is articulated exclusively through **1px Razor Borders**, **Flat Surface Contrast**, and **Monochrome Overlays**.

- **Level 0 (Base Canvas)**: Flat `#FFFFFF` or `#000000`.
- **Level 1 (Structural Containers & Cards)**: Inset `#F8F7F5` (light) or `#111111` (dark) bounded by a crisp 1px stroke (`#E5E5E5` or `#262626`).
- **Level 2 (Persistent Bars & Floating Decks)**: Glass-less solid carbon (`#111111`) or solid pure white (`#FFFFFF`) with a top/bottom 1px border. No drop shadows.
- **Level 3 (Modals, Overlays, Dropdowns)**: Solid high-contrast background with a sharp 1px border (`#262626` in dark mode, `#0D0D0D` in light mode). Scrims use `#000000` at 60% opacity with zero backdrop blur.

## Shapes

The design system employs an intentional visual tension: **razor-sharp architectural envelopes (0px to 4px)** housing **fluid, human pill elements (9999px)**.

- **Containers, Table Rows, Cards, Panels**: 0px border radius. Clean, hardware-inspired edges that tile without dead gap space.
- **Chips, Badges, Tags, Control Pills**: Pill-shaped (`rounded-full` / 9999px). Softens technical data and signals interactive tags, genre markers, and quick-filter buttons.
- **Buttons**:
  - Primary Action: Hard pill (`9999px`) or structural block (`2px`).
  - Cue Points & Transport controls: Pure circular or hairline pill shapes.

## Components

### 1. Buttons
- **Primary Action (Brand)**: Background `#FF6B35`, text `#FFFFFF`, rounded pill (`9999px`), no border. On hover: `#E85A26`. Active: scale(0.98).
- **Secondary (High Contrast)**: Dark mode: background `#FFFFFF`, text `#000000`. Light mode: background `#0D0D0D`, text `#FFFFFF`. 0px or 4px radius. 
- **Ghost/Outline**: 1px border in `#E5E5E5` (light) or `#262626` (dark). Text matching surface contrast. Hover: background tinted with 5% contrast color.

### 2. Chips & Pill Badges
- **Technical Metadata Chip (Key / BPM)**: JetBrains Mono font, 11px uppercase. 1px border `#E5E5E5` (light) / `#262626` (dark). Solid background `#F8F7F5` / `#161616`. Pill-radius.
- **Active State / Hot Cue Chip**: Border `#FF6B35`, background `rgba(255, 107, 53, 0.1)`, text `#FF6B35`.
- **Genre Pill**: Small body font, text `#555555`, 1px border `#E5E5E5`. Hover fill: `#0D0D0D` with `#FFFFFF` text.

### 3. Tracklist & Table Rows
- Flat 48px height, 1px bottom border `#E5E5E5` / `#262626`.
- Layout columns: `[Play/Index (32px)] [Title + Artist (Flex)] [BPM (64px)] [Key (48px)] [Waveform Preview (180px)] [Time (48px)]`.
- Hover state: Background switches instantly to `#F8F7F5` (light mode) or `#171717` (dark mode).
- Playing state: Row background solid `#111111`, Left 3px inset vertical indicator `#FF6B35`.

### 4. Waveform Visualization Motif
- High-density vertical bar representation (2px bar, 1px gap).
- Inactive/Unplayed: `#E5E5E5` in light mode, `#262626` in dark mode.
- Played / Playhead scrubbed: Solid `#FF6B35`.
- Playhead marker: 1px `#FFFFFF` or `#000000` vertical hairline with top pin indicator.

### 5. Input Fields
- Single-line border: 1px bottom border only or enclosed 1px box with 0px radius.
- Background: `#FFFFFF` or `#111111`.
- Placeholder: `#888888`, Inter 14px.
- Focus: Border color turns `#FF6B35` with no diffuse outline glow.

### 6. Cards & Panels
- 0px border radius, 1px hairline stroke wrapping the perimeter.
- Header sections divided by internal 1px horizontal hairline.
- Card padding strictly set to 24px (`md`) or 32px (`lg`).