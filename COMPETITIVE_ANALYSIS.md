# CratePrep vs. Quickie and adjacent tools — Competitive Analysis

*Prepared 2026-09-07, refreshed 2026-09-13, re-verified live 2026-09-14.
Quickie and SetFlow sections are now based on a real fetch of their raw
HTML (quickiemusic.com and setflow.app, both server-render enough
content in the initial page load to read directly) once this session's
network access was widened -- pricing, feature bullets, and exact copy
below are quoted from their live marketing pages, not inferred. BPMDex
remains snippet-derived beyond its homepage: bpmdex.app's other routes
(/pricing, /build, /features) are a client-rendered SPA shell with no
extra content in the raw HTML, so its AI-set-builder and pricing
specifics are still from web-search results, not a direct read.
`files/quickie_prd.md` — a reverse-engineered spec of Quickie written at
this project's inception, used as CratePrep's original inspiration --
is superseded by the live fetch wherever the two disagree.*

## The short version

Biggest correction from the live re-fetch: **Quickie has no ongoing
free plan at all.** Their pricing page is literally headlined "One
plan. Everything unlocked" -- what looked like a comparable free tier
in the original pass is actually just "try it free (up to 25 tracks)"
before you must buy Pro; there's no recurring free allowance, and
genre-based folder/playlist splitting turns out to be bundled *inside*
their one paid plan, not a free-tier feature. CratePrep's Free plan (10
tracks *every month*, forever, no card, lowered from 25 on 2026-09-14)
is a *recurring* free offer Quickie has no equivalent to at any price --
a real advantage in kind, even though Quickie's one-time 25-track trial
is now larger than a single month of CratePrep's allowance in raw
volume. The two aren't directly comparable any more: ours compounds
every month forever, theirs is a one-shot ceiling before you must pay.

We're close to parity on the core mechanic (drop files → get BPM/key/
genre → export), genuinely ahead on a growing list of real features
(several of them AI-powered, shipped since the original pass), and the
account/trust gap from the original pass is closed: CratePrep now
offers a no-signup trial (up to 5 tracks, once, ever) matching
Quickie's zero-friction first try. Genre-based folder/playlist
splitting -- confirmed real and Pro-gated on Quickie's side too -- was
deliberately decided against for CratePrep rather than left as an open
gap (see below). What's left is the price gap itself ($5/mo vs. their
$4/mo annual), now better understood: we're not "$1 more for a
comparable free tier," we're "$1 more, but our free tier is actually
recurring and theirs isn't."

## Feature-by-feature

| | **CratePrep** | **Quickie** |
|---|---|---|
| Account required to process files | **No** for a 5-track trial (once, ever); sign-in required beyond that for the recurring Free plan | **No** — "no accounts, no waiting" (confirmed live copy) — but there's no recurring free plan to sign in *for*; Pro requires signup |
| Ongoing free plan | **Yes** — 10 tracks **every month**, recurring, forever, no card (lowered from 25, 2026-09-14) | **No.** Confirmed live: "One plan. Everything unlocked" — only a one-time-reading "try it free (up to 25 tracks)" trial exists, then Pro is required. Not a recurring allowance. |
| Filename cleanup | Yes — strips junk phrases, watermarks, catalog codes | Yes — confirmed live copy: "AI cleanup" |
| BPM detection | Yes (essentia) | Yes — confirmed live copy: "BPM & key detection" |
| Key detection | Yes (essentia, Camelot + standard notation) | Yes (see above) |
| Genre detection | Yes — real catalog lookup (Spotify + Discogs APIs), not guessed | Confirmed live, but only as part of "Split by genre" (below) — no separate genre-tagging claim independent of the folder-splitting feature |
| Energy rating | **Yes** — 1-10 loudness-derived score | Not mentioned anywhere on the live site |
| Drag-to-reorder results before export | **Yes** | Not mentioned (their "drag" language refers to dragging files *in*, not reordering results) |
| Genre-based folder/playlist splitting | No — deliberately decided against (see below) | **Confirmed real and live**, exact copy: "Split by genre, sort by folders, build playlists" — but it's a **Pro-only** perk bundled in their one paid plan, not available on the free trial |
| Custom "vibe"/mood playlist requests | No | Still unconfirmed as a *working* feature: "ask for the vibe you want" and "play a mini-game" both appear only in a social-share meta tag (SEO/tagline copy), not in the actual pricing-card feature bullets on the live page, which list nothing like this. Weaker evidence than the PRD, if anything -- may be aspirational or stale tagline copy rather than a shipped feature. |
| Playlist export | `.m3u8`, Rekordbox-compatible | `.m3u8`, Rekordbox-compatible |
| DJ software breadth | Tags read correctly by **Rekordbox, Serato, and Traktor** (standard BPM/key/genre tags) | Only Rekordbox mentioned anywhere |
| Embedded key tag correctness | Standard notation (`Am`, `F#`) — matches what all three apps expect | Unknown/unverified |
| Custom filename templates | Yes (Pro) | Not mentioned |
| History of processed tracks | Yes — searchable/sortable, per account | Not mentioned (consistent with no-account model) |
| Processing-time engagement | Rotating status line showing real pipeline steps (shipped) | Claimed as a mini-game in tagline/meta copy only -- not found in the actual live page content; status unconfirmed |
| Audio formats | MP3, WAV, AIFF, FLAC (explicit, enforced allow-list) | "Multiple formats," never itemized publicly |
| Mobile support | Yes, explicitly documented (not recommended, but works) | Not mentioned either way |
| Legal pages | Privacy Policy, Terms, Cookie Policy — all real, if still draft-flagged | Not observed on the fetched page |
| No-file-retention claim | Yes, explicit | Yes, explicit ("don't store your music," originals untouched) |

## Pricing

| | **CratePrep** | **Quickie** |
|---|---|---|
| Ongoing free plan | **Yes** — 10 tracks/month, recurring, no card (lowered from 25, 2026-09-14) | **No.** Confirmed live: a one-time-reading "try it free (up to 25 tracks)" trial, no account -- but no recurring plan behind it. Their pricing section header is literally "One plan. Everything unlocked." |
| Pro (annual) | $5/month billed annually ("Save 38%") | Confirmed live: **$4/month**, "Best value — save 20%" |
| Pro (monthly) | Not shown standalone on pricing card | Not scraped directly, but their own "save 20%" annual framing implies ~$5/month at the monthly rate (12 × $4 = 0.8 × 12 × monthly ⇒ monthly ≈ $5) |
| Pro batch cap | 50 tracks/batch | Unlimited -- confirmed live: "Unlimited track uploads," "Unlimited ZIP exports" |
| Genre-based folder/playlist splitting | Not included (decided against) | Confirmed live, but **Pro-only** — not part of the free trial either |

**The framing changes completely with the confirmed pricing.** The
original analysis read this as "$5/mo vs $4/mo for a comparable free
tier" -- a small, defensible premium. It's now "$5/mo (with a genuinely
recurring 10/month free plan) vs. effectively-$5/mo-at-the-monthly-rate
(with no recurring free plan at all, just a one-time 25-track trial)."
On price alone we're not really more expensive once you account for
what each plan actually includes below the top-line number -- but
worth being honest that Quickie's one-time trial is now more generous
in raw volume than a single month of CratePrep's Free plan (25 vs. 10);
the CratePrep advantage is that it recurs indefinitely and Quickie's
doesn't, not that it's bigger on day one.

## Positioning & tone

Quickie's whole brand is built around zero friction and a playful,
almost throwaway tone ("one quickie before my live set," no account at
all for the initial trial). It reads as a scrappy, single-purpose
utility you use once and forget -- and the pricing structure backs
that up: there's no free plan to stick around for, just a trial that
funnels you toward the single $4/mo Pro plan.

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
10. **A genuinely recurring free plan** (confirmed via live re-fetch, 2026-09-14) — Quickie has no ongoing free tier at any price point, only a one-time trial before Pro is required. CratePrep's 10/month, forever, no-card plan has no Quickie equivalent to compare against at all, even though Quickie's one-time trial ceiling (25) is larger in a single shot.

## Where we're behind or exposed

1. ~~Sign-in wall on Free~~ — **resolved.** A no-signup trial (up to 5 tracks, no account) already shipped (`a418c65`), closing most of this gap.
2. **Price** — reframed by the live re-fetch, not resolved: $5/mo vs. their $4/mo annual (~$5/mo at their monthly rate, inferred from their own "save 20%" annual framing) is close enough that it's arguably not really a premium once you factor in that our $5/mo comes with a genuinely recurring free tier and theirs doesn't. Still worth making legible on the pricing page (see recommendation below) — the raw numbers alone still read as "we cost more" to a skimming visitor.
3. ~~No genre-based folder/playlist splitting~~ — **decided against, not just left open.** Confirmed real and live on Quickie's side ("Split by genre, sort by folders, build playlists"), but Pro-only there too — not building it for CratePrep. Not worth the scope for a niche organizational preference relative to everything else on the roadmap.
4. ~~No processing-time engagement~~ — **resolved.** A rotating status line during processing already shipped (`c791156`), explicitly built against this recommendation.
5. ~~Re-verify the free-tier session vs. monthly framing~~ — **resolved by live re-fetch (2026-09-14).** Quickie's free tier is not a recurring allowance at all — it's a one-time trial before their single paid plan is required. CratePrep's recurring 10/month is a real, confirmed advantage in kind (indefinite vs. one-shot), not a wash — though not larger in raw volume for a single month.

## Adjacent competitors: AI/harmonic set-building tools

Three tools that don't compete on Quickie's turf (raw file cleanup/
tagging) but compete directly with CratePrep's newer **Suggest Set
Order** feature and the "vibe playlist" idea we discussed and haven't
built. SetFlow is now confirmed via live fetch (2026-09-14); BPMDex and
Mixed In Key remain search-snippet-derived:

- **SetFlow** (setflow.app) — confirmed live: generates harmonically-
  mixed DJ sets using the Camelot wheel, BPM matching, and "energy
  curves" ("the energy curves actually understand how a set should
  flow," per their own testimonial quote) -- functionally the same
  three signals our Suggest Set Order uses, plus their own copy also
  invites you to "pick a vibe" / "dial a vibe" as an input, not purely
  mechanical sorting. The key difference stays the same: SetFlow
  requires an *already-tagged* library import (Rekordbox XML, Traktor
  NML, or a Serato folder) -- "One-Click Import... crates and metadata
  land in seconds" -- it orders tracks you've already organized
  elsewhere; no raw-file analysis at all. Exports to Rekordbox, Traktor,
  Serato, PDF, and even TribeXR (VR DJing). CratePrep does the tagging
  *and* the set-ordering in one drop, starting from raw messy files.
  **Confirmed pricing:** Free Trial £0/7 days (up to 500 tracks
  imported, 3 sets to generate); Hobby £2.99/mo or £1.49/mo billed
  annually (save 50%) -- up to 500 tracks, 10 sets/month; Pro £4.99/mo
  or £2.49/mo billed annually (save 50%) -- unlimited tracks/sets, sets
  up to 3 hours, smart crates + planning canvas. A one-time £2.99
  "Weekend Pass" also exists (72hr full Pro access, no subscription).
  After the 7-day trial, your data is kept but "access is locked until
  you subscribe."
- **BPMDex** (bpmdex.app) — homepage confirmed live: "Import your
  Rekordbox collection, build curated playlists, browse and search
  everything" -- same category as SetFlow (existing-library import,
  not raw-file analysis), builds playlists "completely independent of
  your original Rekordbox folder layout," exports as M3U or CSV. Its
  other pages (/pricing, /build, /features) are a client-rendered SPA
  shell with no extra content in the raw HTML, so the specific
  AI-set-builder claim (type a request like *"a 90-minute techno set at
  128-132 BPM in 8A"* with a Claude/ChatGPT-connected assistant mode)
  and its pricing remain search-snippet-derived, not independently
  verified this pass.
- **Mixed In Key** (mixedinkey.com) — not fetched this pass, still
  search-snippet-derived. The long-established incumbent for this whole
  category: desktop software doing key/energy detection, energy-in-
  filename renaming, and ID3 tagging. Not a direct competitor in UX
  (desktop app, not a web drag-and-drop), but it's the accuracy
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
3. ~~Decide, deliberately, on genre-based folder/playlist splitting.~~ **Decided: not building it.** Deliberately choosing not to close this gap rather than leaving it ambiguous — don't let it drift into an implied/claimed feature on the landing page or pricing copy, since it genuinely isn't there.
4. ~~Consider a lightweight processing-time delight moment.~~ **Done.**
5. ~~Re-verify the free-tier session vs. monthly framing.~~ **Confirmed, and it's better than hoped:** Quickie has no recurring free plan at all, just a one-time trial. **New recommendation:** say this explicitly on the pricing page ("the only DJ track-prep tool with a free plan you can actually come back to every month" or similar) -- this is now a confirmed fact, not a hedge.
6. **Say the "one tool, not two" thing out loud.** Now that CratePrep also does what SetFlow does (harmonic+BPM+energy set ordering), but starting from raw files instead of an already-organized library, that combination is worth a line on the landing page -- it's not a claim any of the three tools reviewed here can make.
7. ~~Consider re-pricing the "we cost more" narrative entirely.~~ **Done.** The Free plan card's subtitle now reads "A real monthly plan — not a one-time trial" instead of "Perfect for one-off gig prep" -- states the advantage positively without naming a competitor.

## Caveats

- The 2026-09-14 pass fetched quickiemusic.com and setflow.app's raw HTML directly (both server-render their pricing/feature copy into the initial page load, no JS execution needed to read it) once this session's network access was widened -- this is a real, direct read of their current live pages, not a summary or a search snippet. Quoted copy and prices above are taken verbatim from that HTML.
- bpmdex.app's homepage was fetched the same way and is equally direct, but its other routes (/pricing, /build, /features) all return an identical client-rendered SPA shell with no extra static content -- their AI-set-builder details and pricing remain from web-search snippets (lower confidence than the Quickie/SetFlow sections).
- Mixed In Key was not fetched this pass at all -- still entirely search-snippet-derived.
- Everything sourced from `quickie_prd.md` is explicitly a third-party's *inference* about Quickie from studying their site at some earlier point, not their own internal documentation -- superseded by the live fetch wherever the two disagree (the free-tier structure being the main example).
- Quickie's FAQ answers (e.g. "do you store my music?", "what formats work?") are hidden behind a click-to-expand accordion that isn't populated in the raw HTML -- only the questions themselves were readable, not the answers.
- This is still a point-in-time snapshot (three passes across a week); competitor pricing/features can change without notice. The inferred Quickie monthly (non-annual) price (~$5/mo) is a calculation from their own "save 20%" framing, not a directly scraped number -- worth a quick sanity check if it ever matters for a specific claim.
