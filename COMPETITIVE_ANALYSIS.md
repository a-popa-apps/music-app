# CratePrep vs. CratePrem (cratepremmusic.com) — Competitive Analysis

*Prepared 2026-09-07. Sources: live fetch of cratepremmusic.com, and
`files/crateprem_prd.md` — a reverse-engineered spec of CratePrem written at
this project's inception, used as CratePrep's original inspiration. The
PRD is unconfirmed against what CratePrem has actually shipped, so items
sourced only from it are marked accordingly.*

## The short version

We're close to parity on the core mechanic (drop files → get BPM/key/
genre → export), genuinely ahead on a few real features, and behind on
one thing that matters a lot for a tool this disposable: **CratePrem
needs no account to try it; CratePrep requires sign-in before you can
process a single file.** That's the single biggest competitive risk
below — everything else is a feature gap or a pricing gap, both of
which are cheaper to close than a trust/friction gap.

## Feature-by-feature

| | **CratePrep** | **CratePrem** |
|---|---|---|
| Account required to process files | **Yes**, sign-in required even for Free | **No** — "no accounts, no waiting" (Pro requires signup) |
| Free tier limit | 25 tracks **per month**, recurring | Up to 25 tracks **per session** (PRD; unclear if session or monthly on the live product) |
| Filename cleanup | Yes — strips junk phrases, watermarks, catalog codes | Yes — "AI cleanup" |
| BPM detection | Yes (essentia) | Yes |
| Key detection | Yes (essentia, Camelot + standard notation) | Yes |
| Genre detection | Yes — real catalog lookup (Spotify + Discogs APIs), not guessed | Yes — described as "AI-powered genre classification" (unclear if catalog-verified or inferred/guessed) |
| Energy rating | **Yes** — 1-10 loudness-derived score | Not mentioned anywhere |
| Drag-to-reorder results before export | **Yes** | Not mentioned (their "drag" language refers to dragging files *in*, not reordering results) |
| Genre-based folder/playlist splitting | No — single flat zip, one playlist | Yes (PRD) — splits into genre subfolders/playlists |
| Custom "vibe"/mood playlist requests | No | Yes (PRD) — "ask for the vibe you want" |
| Playlist export | `.m3u8`, Rekordbox-compatible | `.m3u8`, Rekordbox-compatible |
| DJ software breadth | Tags read correctly by **Rekordbox, Serato, and Traktor** (standard BPM/key/genre tags) | Only Rekordbox mentioned anywhere |
| Embedded key tag correctness | Standard notation (`Am`, `F#`) — matches what all three apps expect | Unknown/unverified |
| Custom filename templates | Yes (Pro) | Not mentioned |
| History of processed tracks | Yes — searchable/sortable, per account | Not mentioned (consistent with no-account model) |
| Processing-time engagement | Plain spinner + progress bar | Mini-game while processing (PRD) |
| Audio formats | MP3, WAV, AIFF, FLAC (explicit, enforced allow-list) | "Multiple formats," never itemized publicly |
| Mobile support | Yes, explicitly documented (not recommended, but works) | Not mentioned either way |
| Legal pages | Privacy Policy, Terms, Cookie Policy — all real, if still draft-flagged | Not observed on the fetched page |
| No-file-retention claim | Yes, explicit | Yes, explicit ("don't store your music," originals untouched) |

## Pricing

| | **CratePrep** | **CratePrem** |
|---|---|---|
| Free | 25 tracks/month, no card | Up to 25 tracks, no account at all |
| Pro (monthly) | Not shown standalone on pricing card | $4/month |
| Pro (annual) | $5/month billed annually ("Save 38%") | $48/year = **$4/month**, "20% off" |
| Pro batch cap | 50 tracks/batch | Unlimited (PRD claims no feature gating at all between tiers beyond volume) |

**We're priced ~25% higher on the annual plan** ($5/mo vs. $4/mo) for
a product with a comparable core feature set plus a few real
extras (energy rating, reorder, wider DJ-software tag compatibility,
history). That's a defensible premium *if* those extras are visible
to a prospective buyer — right now the pricing page doesn't make the
case for why we cost more, it just lists the extras alongside "25
tracks/month" without contrasting against the competitor's laxer free
tier.

## Positioning & tone

CratePrem's whole brand is built around zero friction and a playful,
almost throwaway tone ("one crateprem before my live set," a mini-game
during processing, no account at all for the free tier). It reads as
a scrappy, single-purpose utility you use once and forget.

CratePrep (after this session's rebrand away from the "CratePrem"-
adjacent name and copy) reads more like a considered, slightly more
"pro tool" product — precision/selector language, a persistent
account with history, Pro-tier depth (custom templates, batch size).
That's a legitimate different position, not automatically worse, but
it raises the bar for trust before first use: a DJ has to sign up
before they see any value, where CratePrem lets them just try it.

## Where CratePrep is genuinely ahead

1. **Energy rating** — real, shipped, nothing comparable found on CratePrem.
2. **Drag-to-reorder before download** — shipped; CratePrem's UI has no equivalent.
3. **Catalog-verified genre** (Spotify/Discogs lookup) vs. what reads as inferred/AI-guessed genre on CratePrem — likely more accurate, though this is an assumption about their internals we can't verify.
4. **Wider, verified DJ-software compatibility** — Rekordbox *and* Serato *and* Traktor via correct standard-notation tags, vs. only Rekordbox ever mentioned by CratePrem.
5. **Persistent history** — lets a returning user see what they've already processed; CratePrem's no-account model can't offer this at all.
6. **Custom filename templates** — real Pro feature with no CratePrem equivalent found.

## Where we're behind or exposed

1. **Sign-in wall on Free** — the single biggest gap. A DJ comparing both tools in two browser tabs gets instant results from CratePrem and a signup form from us. This is worth treating as the top priority.
2. **Price** — $5/mo vs. their $4/mo annual, with no on-page argument for the premium.
3. **No genre-based folder/playlist splitting** — if CratePrem has actually shipped this (PRD-only claim, unconfirmed), it's a real organizational feature we don't have. (Worth noting: we deliberately walked back a similar "Genre-Sorted Playlists" claim of our own earlier this session for being unbuilt — so if we ever build this for real, it becomes a genuine advantage rather than another aspirational bullet.)
3. **No "try before you sign up" path at all** — even a heavily-limited anonymous trial (e.g. 1-3 tracks, no account) would close most of the friction gap without giving away the product.
4. **No processing-time engagement** — minor, but CratePrem's mini-game (PRD) is a real point of delight/virality we have nothing to answer with beyond a progress bar.

## Recommendations, roughly in priority order

1. **Ship a no-signup trial tier.** Doesn't have to be the full 25/month Free tier — even "process up to 3 tracks with no account, sign up for more" removes the single biggest conversion-killer on the landing page. This is the highest-leverage fix available.
2. **Make the Pro price premium legible on the pricing page itself.** A one-line comparison callout or just tighter copy connecting the price to the differentiators (energy rating, 3-app compatibility, history, templates) turns "we cost more" into "here's why."
3. **Decide, deliberately, on genre-based folder/playlist splitting.** Either build it for real (there's already a `genre` field on every track — grouping into per-genre playlists is a contained addition, not a rebuild) or don't claim it; don't let it become another "Genre-Sorted Playlists" situation like the one already caught and fixed this session.
4. **Consider a lightweight processing-time delight moment.** Not necessarily a literal mini-game, but the current plain spinner is the least differentiated part of the whole flow — even a rotating fun-fact ticker about the tracks being analyzed would cost little and add personality back, without going full playful-brand like CratePrem.
5. **Re-verify the free-tier session vs. monthly framing.** If CratePrem's real (not PRD-inferred) free tier is genuinely "25 tracks, once, ever" rather than a recurring monthly allowance, our recurring 25/month is a stronger offer and worth saying so explicitly rather than leaving it implicit.

## Caveats

- CratePrem's live site was fetched once, via a markdown-conversion tool, not browsed interactively — anything behind a login, a modal, or JS-only rendering may be missed (e.g. we could not find or load an actual pricing sub-page; the $4/mo figure comes from the homepage).
- Everything sourced from `crateprem_prd.md` is explicitly a third-party's *inference* about CratePrem from studying their site at some earlier point, not their own internal documentation — treat those rows as "plausible, unconfirmed" rather than fact.
- This is a one-time snapshot; competitor pricing/features can change without notice.
