# CratePrep vs. Quickie and adjacent tools — Competitive Analysis

*Prepared 2026-09-07, refreshed 2026-09-13. Quickie section: live fetch
of quickiemusic.com from the original 2026-09-07 pass, plus
`files/quickie_prd.md` — a reverse-engineered spec of Quickie written at
this project's inception, used as CratePrep's original inspiration. The
PRD is unconfirmed against what Quickie has actually shipped, so items
sourced only from it are marked accordingly. This refresh could NOT
re-fetch quickiemusic.com, bpmdex.app, or setflow.app live -- this
session's network egress is restricted to an allowlist that doesn't
include them, so the Quickie section below is unchanged from the
original snapshot (could be stale), and the two new adjacent-tool
sections are built from search-result snippets only, not a full page
read. Treat all of it as directionally useful, not verified fact.*

## The short version

We're close to parity on the core mechanic (drop files → get BPM/key/
genre → export), genuinely ahead on a growing list of real features
(several of them AI-powered, shipped since the original pass), and the
account/trust gap identified in the original pass has already been
closed: CratePrep now offers a no-signup trial (up to 5 tracks, once,
ever) matching Quickie's zero-friction first try. What's left is a
smaller price gap ($5/mo vs. their $4/mo) and one real unclaimed
feature (genre-based folder/playlist splitting) — both cheaper to close
than the trust/friction gap already was.

## Feature-by-feature

| | **CratePrep** | **Quickie** |
|---|---|---|
| Account required to process files | **No** for a 5-track trial (once, ever); sign-in required beyond that for the recurring Free plan | **No** — "no accounts, no waiting" (Pro requires signup) |
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

| | **CratePrep** | **Quickie** |
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

Quickie's whole brand is built around zero friction and a playful,
almost throwaway tone ("one quickie before my live set," a mini-game
during processing, no account at all for the free tier). It reads as
a scrappy, single-purpose utility you use once and forget.

CratePrep reads more like a considered, slightly more "pro tool"
product — precision/selector language, a persistent account with
history, Pro-tier depth (custom templates, batch size, and now several
AI-assisted features). That's a legitimate different position, not
automatically worse, and the no-signup trial now closes most of the
practical trust gap even if the tone stays more "pro tool" than
Quickie's throwaway one.

## Where CratePrep is genuinely ahead

1. **Energy rating** — real, shipped, nothing comparable found on Quickie.
2. **Drag-to-reorder before download** — shipped; Quickie's UI has no equivalent.
3. **Catalog-verified genre** (Spotify/Discogs lookup) vs. what reads as inferred/AI-guessed genre on Quickie — likely more accurate, though this is an assumption about their internals we can't verify.
4. **Wider, verified DJ-software compatibility** — Rekordbox *and* Serato *and* Traktor via correct standard-notation tags, vs. only Rekordbox ever mentioned by Quickie.
5. **Persistent history** — lets a returning user see what they've already processed; Quickie's no-account model can't offer this at all.
6. **Custom filename templates** — real Pro feature with no Quickie equivalent found.
7. **AI-assisted filename cleanup** (shipped since the original snapshot) — an LLM fallback split for filenames regex and catalog lookup can't crack, vs. Quickie's unverified "AI cleanup" claim.
8. **AI batch summary** (shipped since the original snapshot) — free for every user, a plain-language read on the batch's genre/BPM/energy shape after processing. No equivalent found on Quickie.
9. **Suggest Set Order + auto-sort-by-energy** (shipped since the original snapshot, Pro) — see the new "Adjacent competitors" section below; this moves CratePrep into a second competitive category, not just a like-for-like Quickie feature.

## Where we're behind or exposed

1. ~~Sign-in wall on Free~~ — **resolved.** A no-signup trial (up to 5 tracks, no account) already shipped (`a418c65`), closing most of this gap.
2. **Price** — still $5/mo vs. their $4/mo annual; the on-page argument for the premium has been improved (`fa71747` tied price copy to differentiators) but the raw number is still higher, and the differentiator list is now longer than what that copy pass covered (see recommendation below).
3. **No genre-based folder/playlist splitting** — if Quickie has actually shipped this (PRD-only claim, unconfirmed), it's a real organizational feature we still don't have. Still open.
4. ~~No processing-time engagement~~ — **resolved.** A rotating status line during processing already shipped (`c791156`), explicitly built against this recommendation.
5. **Re-verify the free-tier session vs. monthly framing** — still open; unconfirmed whether Quickie's real free tier is "25 tracks once" vs. a recurring allowance.

## Adjacent competitors: AI/harmonic set-building tools

Two tools found via search (not fetchable this session — network egress
blocked, so this is snippet-derived only) don't compete on Quickie's
turf (raw file cleanup/tagging) but compete directly with CratePrep's
newer **Suggest Set Order** feature and the "vibe playlist" idea we
discussed and haven't built:

- **SetFlow** (setflow.app) — generates harmonically-mixed DJ sets using
  the Camelot wheel, BPM matching, and "intelligent energy curves" --
  functionally the same three signals our Suggest Set Order uses. The
  key difference: SetFlow requires an *already-tagged* library imported
  from Rekordbox/Traktor/Serato: it orders tracks you've already
  organized elsewhere. CratePrep does the tagging *and* the set-ordering
  in one drop, starting from raw messy files. Pricing found: a £2.99
  one-time "Weekend Pass" (72hr full Pro access, no subscription) plus
  Hobby/Pro subscriptions (annual saves 33%); free trial covers up to
  500 tracks / 7 days / 3 generated sets.
- **BPMDex** (bpmdex.app) — a DJ library platform with an AI set-builder:
  type a request like *"a 90-minute techno set at 128-132 BPM in 8A,
  nothing played in the last month"* and it builds the playlist, with a
  Claude/ChatGPT-connected assistant mode. This is close to the
  never-built "ask for the vibe you want" idea from CratePrep's own
  original PRD -- someone else has already shipped a version of it, on
  top of an existing organized library rather than raw files. Specific
  pricing wasn't found; AI features are gated behind an upgrade.
- **Mixed In Key** (mixedinkey.com) — the long-established incumbent for
  this whole category: desktop software doing key/energy detection,
  energy-in-filename renaming, and ID3 tagging. Not a direct competitor
  in UX (desktop app, not a web drag-and-drop), but it's the accuracy
  benchmark this project's own tech-stack doc already references, and
  likely what any DJ evaluating "is this tool's key detection any good"
  mentally compares against.

**The upshot:** CratePrep's Suggest Set Order + tagging pipeline
straddles two competitive categories at once -- Quickie's category
(raw file cleanup) and SetFlow's category (smart set-building from an
existing library) -- which nobody found in this pass does in a single
tool. That's a real, sayable differentiator ("skip the library-import
step every set-builder assumes you've already done") once the pricing
page actually says it.

## Recommendations, roughly in priority order

1. ~~Ship a no-signup trial tier.~~ **Done.**
2. ~~Make the Pro price premium legible on the pricing page itself.~~ **Done, but incomplete** — the copy pass predates AI filename cleanup, AI batch summary, and Suggest Set Order. Worth another pass now that the differentiator list is longer (see the landing-page update alongside this doc refresh).
3. **Decide, deliberately, on genre-based folder/playlist splitting.** Either build it for real (there's already a `genre` field on every track — grouping into per-genre playlists is a contained addition, not a rebuild) or don't claim it; don't let it become another "Genre-Sorted Playlists" situation like the one already caught and fixed this session. Still the single largest unclaimed feature gap against Quickie specifically.
4. ~~Consider a lightweight processing-time delight moment.~~ **Done.**
5. **Re-verify the free-tier session vs. monthly framing.** If Quickie's real (not PRD-inferred) free tier is genuinely "25 tracks, once, ever" rather than a recurring monthly allowance, our recurring 25/month is a stronger offer and worth saying so explicitly rather than leaving it implicit.
6. **Say the "one tool, not two" thing out loud.** Now that CratePrep also does what SetFlow does (harmonic+BPM+energy set ordering), but starting from raw files instead of an already-organized library, that combination is worth a line on the landing page -- it's not a claim any of the three tools reviewed here can make.

## Caveats

- Quickie's live site was fetched once (2026-09-07), via a markdown-conversion tool, not browsed interactively — anything behind a login, a modal, or JS-only rendering may be missed (e.g. we could not find or load an actual pricing sub-page; the $4/mo figure comes from the homepage).
- Everything sourced from `quickie_prd.md` is explicitly a third-party's *inference* about Quickie from studying their site at some earlier point, not their own internal documentation — treat those rows as "plausible, unconfirmed" rather than fact.
- The 2026-09-13 refresh could not re-fetch quickiemusic.com, bpmdex.app, or setflow.app -- this session's network egress is restricted to an allowlist that doesn't cover them. The SetFlow/BPMDex/Mixed In Key section is built entirely from web-search result snippets, not a full page read; pricing and feature claims there are lower-confidence than the original Quickie fetch.
- Web search results are only available for the US region in this session, which may skew what surfaced.
- This is a point-in-time snapshot with two passes six days apart; competitor pricing/features can change without notice, and a full live re-fetch (from an environment without this network restriction) would be worth doing before making any claim on the landing page that depends on a competitor's *current* feature set rather than what's documented here.
