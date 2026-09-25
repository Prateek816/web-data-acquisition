# Product: Public construction opportunity ingestion pipeline

## Summary

A scheduled ingestion system that pulls upcoming and advertised public construction projects from three layers of free official sources, normalizes every record into one schema, deduplicates, and stores results in Postgres for querying by the ContractorOps app and sales motion.

## Sources to implement, in build order

### 1. SAM.gov (federal)

- API: Get Opportunities Public API v2, `https://api.sam.gov/opportunities/v2/search`
- Auth: free API key, generated in the SAM.gov account details page. Store in env var.
- Query: notice types `p` (pre-solicitation), `o` (solicitation), `k` (combined synopsis/solicitation); NAICS 236, 237, 238 (construction); paginate; respect per-day request caps by caching aggressively.
- Reference: https://open.gsa.gov/api/get-opportunities-public-api/

### 2. State DOT letting schedules (50 states, start with California)

- Caltrans Contracting Opportunities Portal: https://ccop.dot.ca.gov/ (advertised projects by district) plus the statewide upcoming-work list.
- TxDOT Projects Scheduled for Letting dashboard: hourly refresh, next two fiscal years, Excel/CSV download. Prefer the download over scraping.
- Pattern per state: one extractor module implementing a common interface (`fetch() -> RawProject[]`). Clone state by state after the interface is proven on California and Texas.

### 3. Local platforms (six extractor templates)

One extractor per platform covers every agency hosted on that platform; do not write per-county scrapers.

| # | Platform | Notes |
| --- | --- | --- |
| 1 | PlanetBids | Dominant in California cities/counties. Portal pages only. Build first for local CA coverage. |
| 2 | OpenGov Procurement | Formerly ProcureNow. Official developer API: https://developer.opengov.com/catalog . Cleanest path. |
| 3 | Public Purchase | Claims ~72,000 agencies. Portal pages only. |
| 4 | Bonfire | Agencies, school boards, hospitals. |
| 5 | DemandStar | 1,000+ local governments. |
| 6 | BidNet Direct (SOVRA) | State/county/city purchasing networks; Alameda County agencies post here. Public search pages. |

### 4. Bootstrap feed (temporary, parallel)

Run the Apify "US Government Tenders & RFP API" actor (https://apify.com/magebase/us-government-tenders-rfp-api/api) on a schedule while own extractors are built. It normalizes 24 portals (SAM.gov, DIBBS, DemandStar, BidNet Direct, BidSync, Bonfire, OpenGov, Public Purchase) into one deduplicated feed at roughly $0.003 per record. Drop it once own coverage matches.

## Data model

One table, one schema, every source:

- `id` (internal UUID)
- `source` (sam_gov | state_dot:<state> | planetbids | opengov | public_purchase | bonfire | demandstar | bidnet | apify_bootstrap)
- `source_id` (notice ID / spec number / solicitation ID as published)
- `project_name`
- `agency` (awarding body, e.g. "Alameda County Public Works Agency")
- `level` (federal | state | county | city | district)
- `location` (city, county, state; normalized)
- `advertise_date`
- `bid_due_date`
- `estimated_value` (nullable; many locals do not publish estimates)
- `naics` / trade categories where available
- `description` (raw text)
- `source_url` (canonical link back to the posting)
- `raw` (JSONB of the original payload)
- `first_seen_at`, `last_seen_at`, `status` (upcoming | open | closed | awarded, where derivable)

## Processing rules

1. Store the raw payload before any normalization. Never lose the original.
2. Normalize into the schema above. Missing estimates or dates stay null; do not invent them.
3. Deduplicate across sources on (normalized project name + agency + location) and on matching source IDs. The same project is routinely cross-posted on BidNet and the agency's own site.
4. Update `last_seen_at` on re-encounter; transition status when a posting closes or an award notice appears.
5. Every extractor runs on a schedule (daily is enough for letting schedules; SAM.gov within its daily cap) and is idempotent.

## Build order

1. SAM.gov extractor + storage + schema. This is the day-one win.
2. Caltrans extractor (home market), then TxDOT (CSV download), then the remaining states one at a time.
3. PlanetBids extractor, then OpenGov (official API), then Public Purchase, Bonfire, DemandStar, BidNet Direct.
4. Dedupe layer across all sources.
5. Apify bootstrap running in parallel from step 1; retired when own coverage matches.

## Constraints and watch-outs

- Terms of use differ per portal. OpenGov has an official API; PlanetBids and Public Purchase do not publish open APIs. Reading public postings for internal use is what every aggregator does; redistributing the data inside a paid product at scale should move to a licensed feed (Dodge Construction Network API, enterprise) when that becomes load-bearing.
- Scrape politely: low request rates, cached pages, daily cadence. Faster polling risks blocks and, on logged-in portals, account flags.
- Some "upcoming projects" lists (e.g. county flood-control forecast decks) are event-only and not published online. The system covers what is published; event decks stay a manual, relationship-driven channel.
- Prices and access terms verified 25 Sep 2026: SAM.gov API free; ConstructConnect $129-199/mo per market per seat (poor fit for powering a SaaS backend); Dodge and GovWin enterprise-only; Apify actor ~$0.003/record.