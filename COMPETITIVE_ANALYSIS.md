# Competitive analysis — pricing & catalog sources

Research pass from 2026-09-15, prompted by "how does our price/feature mix compare to the competition." Captured here to reference later rather than re-research from scratch. Sources linked inline; verify before quoting exact prices publicly, since promos/pricing pages change.

## CratePrep's current pricing

- **Free**: 10 tracks/month, standard BPM & key detection, FLAC/AIFF/WAV 24-bit, Rekordbox-ready `.m3u8` export, AI batch summary.
- **Pro**: $5/mo billed annually ($60/yr) or $8/mo billed monthly — unlimited tracks, up to 50/batch, custom filename templating, enhanced BPM/key detection, AI filename cleanup, AI harmonic set-order suggestion, automatic energy sorting.

(`frontend/src/components/Pricing.tsx`)

## Competitors

### Mixed In Key — the "gold standard," but the weakest direct threat
- **$58, one-time purchase** (confirmed via [Dubspot](https://blog.dubspot.com/plugins/mixed-in-key) and [DJ Tech Reviews](https://djtechreviews.com/guides/resources/best-bpm-and-key-finder), 2026).
- BPM/key detection + an Energy Level score (1-10) — CratePrep's own Energy scale is the same concept.
- Local desktop app (Mac/Windows) — no cloud, no genre lookup/catalog matching, no AI cleanup, no filename templating/renaming.
- **Why it's not the real threat**: it only does audio analysis. Everything else CratePrep does (genre lookup, renaming, AI cleanup) is out of scope for it entirely.

### GreenGo — closest priced competitor, and it does more
- **$5.99/mo, or $60/year ($5/mo equivalent)** — effectively identical to CratePrep Pro's price. 7-day free trial. ([greengomusic.com](https://greengomusic.com/), [pricing/ranked blog post](https://greengomusic.com/blog/best-mp3-tag-editors-2026-free-paid-ranked.html))
- A full Chromium-based browser built for DJs: automatic BPM/key analysis, metadata tagging, audio format conversion, **and stem separation** — a feature CratePrep doesn't have at all.
- **Why it matters**: this is the one competitor landing on almost the exact same price point as CratePrep Pro while bundling more (stem separation, a whole browser). "Same price, does more" is a real objection.

### One Tagger — free, open source, undercuts the Pro renaming/tagging pitch
- **$0**, open source (Rust backend, Vue.js frontend). ([onetagger.github.io](https://onetagger.github.io/))
- Automatically tags local files from **Beatport, Traxsource, Juno Download, Discogs, iTunes, MusicBrainz, Beatsource, and Spotify** — more catalog sources than CratePrep's current Spotify + Discogs.
- Template-based file renaming — the exact feature CratePrep gates behind Pro.
- Quick-tag energy/mood/genre presets.
- Desktop-only, no audio-based BPM/key detection of its own (relies on existing tags + catalog matches), no AI cleanup or AI set-ordering.
- **Why it matters**: for someone who just wants "rename files + pull genre from catalogs," this is a free substitute for half of CratePrep's Pro pitch.

## Take

Price alone isn't a differentiator — GreenGo matches CratePrep's price and adds a feature CratePrep lacks (stem separation); One Tagger undercuts the renaming/tagging half of the Pro pitch for free. The one combination nobody else offers in one product: **real audio-based BPM/key/energy detection + AI-driven artist/title cleanup + AI harmonic set-ordering**, in a no-install web upload. That's the positioning to lean on, not "cheaper" or "we do tagging too."

## Catalog-source expansion research (Beatport, Traxsource, Juno, Beatsource, MusicBrainz, iTunes)

Prompted by One Tagger's broader catalog list above. Checked actual API access for each before assuming this is buildable:

| Source | Status | Notes |
|---|---|---|
| **Spotify** | ✅ Already integrated | `detect_genre.py` — Client Credentials flow, already the primary lookup. |
| **Discogs** | ✅ Already integrated | `detect_genre.py` — fallback lookup, optional token raises rate limit. |
| **MusicBrainz** | 🟢 Feasible, free | Public API, non-commercial use is free. Rate limit ~1 req/sec average (up to 300/sec system-wide), requires a real identifying User-Agent string. [Docs](https://musicbrainz.org/doc/MusicBrainz_API), [rate limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting). Genre tags are community-tagged, not always as clean as Spotify/Discogs. |
| **iTunes Search API** | 🟢 Feasible, free | Public, no API key needed at all, returns genre alongside artist/title/artwork. [Apple's docs](https://developer.apple.com/library/content/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html). |
| **Beatport** | 🔴 Blocked | v4 OAuth API exists but is partner-gated — no public self-serve signup, brokered case-by-case through their Partner Portal + biz-dev team. [api-evangelist writeup](https://github.com/api-evangelist/beatport), [partner portal](https://partnerportal.beatport.com/hc/en-us). |
| **Beatsource** | 🔴 Blocked | Same parent company as Beatport, same partner-gated model — commercial use needs pre-approval in writing. |
| **Traxsource** | 🔴 Blocked | API keys are invite-only, aimed at label partners/content providers reporting on their own catalog, not general third-party search access. |
| **Juno Download** | ⚫ Defunct | Site shut down June 2026 — the API (which existed, XML-based) is gone with it. |

**Recommendation**: add MusicBrainz and iTunes as two more fallback lookups in `lookup_track()` (same pattern as the existing Spotify → Discogs chain) — both are free, public, and need no partnership. Beatport/Beatsource/Traxsource would need an actual business relationship (worth revisiting if CratePrep grows enough to justify reaching out to their biz-dev teams — their genre/style data is the most DJ-relevant of anything on this list), and Juno isn't an option since it no longer exists.
