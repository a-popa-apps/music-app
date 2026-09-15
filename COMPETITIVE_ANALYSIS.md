# CratePrep vs. Quickie and adjacent tools — Competitive Analysis

*Prepared 2026-09-07, refreshed 2026-09-13, re-verified live 2026-09-14,
extended 2026-09-15 with a pricing/catalog-source pass (Mixed In Key,
GreenGo, One Tagger, and genre-source expansion feasibility -- see the
new sections below; this pass is web-search-derived, not a live HTML
fetch like the Quickie/SetFlow sections).
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

**2026-09-15 update:** price alone still isn't where CratePrep wins --
a fresh pass found GreenGo pricing at almost exactly the same point as
CratePrep Pro while bundling more (stem separation), and One Tagger
undercuts the renaming/tagging half of the Pro pitch for free. See
"Direct competitors: BPM/key/tagging tools" below.

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
| Pro (monthly) | $8/month | Not scraped directly, but their own "save 20%" annual framing implies ~$5/month at the monthly rate (12 × $4 = 0.8 × 12 × monthly ⇒ monthly ≈ $5) |
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
11. **Real audio-based BPM/key/energy detection + AI cleanup + AI set-ordering, in one no-install web tool** — confirmed 2026-09-15 against Mixed In Key, GreenGo, and One Tagger too (see below): nobody found in either pass offers this exact combination in one product.

## Where we're behind or exposed

1. ~~Sign-in wall on Free~~ — **resolved.** A no-signup trial (up to 5 tracks, no account) already shipped (`a418c65`), closing most of this gap.
2. **Price** — reframed by the live re-fetch, not resolved: $5/mo vs. their $4/mo annual (~$5/mo at their monthly rate, inferred from their own "save 20%" annual framing) is close enough that it's arguably not really a premium once you factor in that our $5/mo comes with a genuinely recurring free tier and theirs doesn't. Still worth making legible on the pricing page (see recommendation below) — the raw numbers alone still read as "we cost more" to a skimming visitor. **2026-09-15: also true against GreenGo** — its ~$5-6/mo lands right on top of CratePrep Pro while adding stem separation, so "same price, does more" is a live objection there too, not just a Quickie framing question.
3. ~~No genre-based folder/playlist splitting~~ — **decided against, not just left open.** Confirmed real and live on Quickie's side ("Split by genre, sort by folders, build playlists"), but Pro-only there too — not building it for CratePrep. Not worth the scope for a niche organizational preference relative to everything else on the roadmap.
4. ~~No processing-time engagement~~ — **resolved.** A rotating status line during processing already shipped (`c791156`), explicitly built against this recommendation.
5. ~~Re-verify the free-tier session vs. monthly framing~~ — **resolved by live re-fetch (2026-09-14).** Quickie's free tier is not a recurring allowance at all — it's a one-time trial before their single paid plan is required. CratePrep's recurring 10/month is a real, confirmed advantage in kind (indefinite vs. one-shot), not a wash — though not larger in raw volume for a single month.
6. **Filename templating + genre tagging, for free, elsewhere** — One Tagger (free, open source) already does template-based renaming and catalog-based genre tagging from more sources than CratePrep uses. It doesn't do audio analysis or AI cleanup, but for someone who just wants "rename + tag from catalogs," it's a $0 substitute for half of the Pro pitch. See below.

## Direct competitors: BPM/key/tagging tools (Mixed In Key, GreenGo, One Tagger)

Added 2026-09-15, prompted by a "how does our price/feature mix compare"
question. Web-search-derived (not a live HTML fetch like the Quickie/
SetFlow sections) — verify exact current pricing before quoting it
publicly, since promos/pricing pages change.

- **Mixed In Key** ([mixedinkey.com](https://blog.dubspot.com/plugins/mixed-in-key)) — **$58, one-time purchase**, confirmed via [Dubspot](https://blog.dubspot.com/plugins/mixed-in-key) and [DJ Tech Reviews](https://djtechreviews.com/guides/resources/best-bpm-and-key-finder) (2026). The long-established "gold standard" for BPM/key detection plus an Energy Level score (1-10) — CratePrep's own Energy scale is the same concept. Local desktop app (Mac/Windows) only: no cloud, no genre/catalog lookup, no AI cleanup, no filename templating. **Actually the weakest direct threat of the three** despite being the best-known name — it only does audio analysis, none of the tagging/renaming/AI work CratePrep also does.
- **GreenGo** ([greengomusic.com](https://greengomusic.com/)) — **$5.99/mo, or $60/year (~$5/mo)** — a Chromium-based browser built for DJs/musicians: automatic BPM/key analysis, metadata tagging, audio format conversion, **and stem separation** (a feature CratePrep doesn't have at all). 7-day free trial. **This is the closest-priced real competitor** — same price point as CratePrep Pro, cloud-based like CratePrep, and it bundles more. "Same price, does more" is a real, current objection, not a hypothetical one.
- **One Tagger** ([onetagger.github.io](https://onetagger.github.io/)) — **$0, open source** (Rust backend, Vue.js frontend). Automatically tags local files from **Beatport, Traxsource, Juno Download, Discogs, iTunes, MusicBrainz, Beatsource, and Spotify** — more catalog sources than CratePrep's current Spotify + Discogs. Does template-based file renaming (the same mechanic as CratePrep's Pro-gated custom filename templates) and quick-tag energy/mood/genre presets. Desktop-only, no audio-based BPM/key detection of its own (relies on existing tags + catalog matches), no AI cleanup or set-ordering. **Undercuts half of the Pro pitch for free** for anyone who just wants rename + catalog-tag, though it can't do what CratePrep's actual audio analysis and AI features do.

**Net read:** none of the three replicates the *combination* CratePrep offers — real audio-based BPM/key/energy detection + AI-driven artist/title cleanup + AI harmonic set-ordering, from raw untagged files, with no install. That combination, not price, is the thing to keep leading with. Price positioning specifically needs updating, though: GreenGo already sits at parity on price while offering more, so "we're competitively priced" isn't really true anymore without qualifying it against GreenGo by name (internally, not necessarily on the public pricing page).

## Catalog-source expansion research (genre lookup)

Prompted by One Tagger's broader catalog list above — checked actual
API access for each source before assuming this is buildable, since
"just add more catalog lookups" isn't free if the API itself is
gated. `backend/app/detect_genre.py` currently chains Spotify → Discogs
in `lookup_track()`.

| Source | Status | Notes |
|---|---|---|
| **Spotify** | ✅ Already integrated | Client Credentials flow, already the primary lookup. |
| **Discogs** | ✅ Already integrated | Fallback lookup, optional token raises the rate limit. |
| **MusicBrainz** | 🟢 Feasible, free | Public API, non-commercial use is free. Rate limit ~1 req/sec average (up to 300/sec system-wide), requires a real identifying User-Agent string. [Docs](https://musicbrainz.org/doc/MusicBrainz_API), [rate limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting). Genre tags are community-tagged, not always as clean as Spotify/Discogs. |
| **iTunes Search API** | 🟢 Feasible, free | Public, no API key needed at all, returns genre alongside artist/title/artwork. [Apple's docs](https://developer.apple.com/library/content/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html). |
| **Deezer** | 🟢 Feasible, free | No API key or auth needed at all for public search (`api.deezer.com/search/track`) — the easiest of everything checked. Rate limit ~50 req/5sec. |
| **Last.fm** | 🟢 Feasible, free | Free API key (no OAuth). `track.getTopTags` returns crowd-sourced tags, not a strict genre field, so noisier than Spotify/Discogs but usable. Rate limit ~2 req/sec. [API docs](https://www.last.fm/api/show/track.getTopTags). |
| **TheAudioDB** | 🟢 Feasible, free | Community database, returns genre/style/mood. Shared public key (`"123"`) works with no signup; some methods have been rate-limited over the years due to abuse, but core lookups are still free. [Docs](https://www.theaudiodb.com/free_music_api). |
| **Beatport** | 🔴 Blocked | v4 OAuth API exists but is partner-gated — no public self-serve signup, brokered case-by-case through their Partner Portal + biz-dev team. [api-evangelist writeup](https://github.com/api-evangelist/beatport), [partner portal](https://partnerportal.beatport.com/hc/en-us). |
| **Beatsource** | 🔴 Blocked | Same parent company as Beatport, same partner-gated model — commercial use needs pre-approval in writing. |
| **Traxsource** | 🔴 Blocked | API keys are invite-only, aimed at label partners/content providers reporting on their own catalog, not general third-party search access. |
| **SoundCloud** | 🔴 Blocked | New third-party API key registration is currently closed; SoundCloud says they're "exploring" reopening it but isn't issuing new keys right now. |
| **Volumo** | 🔴 No API at all | Newer (2022) curated underground-electronic DJ music store, pay-per-track (no subscription), ~417K artists/36K labels. No public or partner API found anywhere -- unlike Beatport/Traxsource, there isn't even a gated one to request access to. Worth rechecking if they ever launch one. |
| **Juno Download** | ⚫ Defunct | Site shut down June 2026 — the API (which existed, XML-based) is gone with it. |
| **Cyanite.ai** | 🟡 Open, but not a fit | AI *audio* analysis (genre/mood classifier on the raw track, not catalog matching) rather than a lookup source — technically accessible, but real API usage starts at €290/month, which dwarfs CratePrep's entire $5-8/mo price point. 5 free analyses/month otherwise. Not worth it at this scale. |

**Recommendation**: add MusicBrainz, iTunes, Deezer, Last.fm, and
TheAudioDB as more fallback lookups in `lookup_track()` (same pattern as
the existing Spotify → Discogs chain) — all five are free, public, and
need no partnership. Beatport/Beatsource/Traxsource/SoundCloud would
need an actual business relationship or a reopened registration window
(worth revisiting later — Beatport/Beatsource/Traxsource's genre/style
data is the most DJ-relevant of anything on this list), Juno isn't an
option since it no longer exists, and Cyanite.ai's pricing doesn't fit
CratePrep's own price point.

## Adjacent competitors: AI/harmonic set-building tools

Three tools that don't compete on Quickie's turf (raw file cleanup/
tagging) but compete directly with CratePrep's newer **Suggest Set
Order** feature and the "vibe playlist" idea we discussed and haven't
built. SetFlow is now confirmed via live fetch (2026-09-14); BPMDex
remains search-snippet-derived. (Mixed In Key's own entry has moved to
the "Direct competitors: BPM/key/tagging tools" section above, now with
confirmed pricing.)

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
8. **Add MusicBrainz + iTunes as extra genre-lookup fallbacks** (2026-09-15) — cheap, free, no partnership needed; closes some of the "One Tagger has more catalog sources" gap without chasing the partner-gated ones.
9. **Don't lean on "competitively priced" without qualification** (2026-09-15) — GreenGo matches CratePrep Pro's price while adding stem separation. The differentiator to lead with is the audio-analysis + AI-cleanup + AI-set-ordering combination, not the price point itself.

## Caveats

- The 2026-09-14 pass fetched quickiemusic.com and setflow.app's raw HTML directly (both server-render their pricing/feature copy into the initial page load, no JS execution needed to read it) once this session's network access was widened -- this is a real, direct read of their current live pages, not a summary or a search snippet. Quoted copy and prices above are taken verbatim from that HTML.
- bpmdex.app's homepage was fetched the same way and is equally direct, but its other routes (/pricing, /build, /features) all return an identical client-rendered SPA shell with no extra static content -- their AI-set-builder details and pricing remain from web-search snippets (lower confidence than the Quickie/SetFlow sections).
- The 2026-09-15 Mixed In Key/GreenGo/One Tagger/catalog-source pass is web-search-derived (search result snippets and summaries), not a live HTML fetch like the Quickie/SetFlow sections -- treat exact prices as "recently reported," not independently scraped, and re-verify before quoting publicly.
- Everything sourced from `quickie_prd.md` is explicitly a third-party's *inference* about Quickie from studying their site at some earlier point, not their own internal documentation -- superseded by the live fetch wherever the two disagree (the free-tier structure being the main example).
- Quickie's FAQ answers (e.g. "do you store my music?", "what formats work?") are hidden behind a click-to-expand accordion that isn't populated in the raw HTML -- only the questions themselves were readable, not the answers.
- This is still a point-in-time snapshot (four passes across a week and a half); competitor pricing/features can change without notice. The inferred Quickie monthly (non-annual) price (~$5/mo) is a calculation from their own "save 20%" framing, not a directly scraped number -- worth a quick sanity check if it ever matters for a specific claim.
