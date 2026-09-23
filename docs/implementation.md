# Data Acquisition & Evidence Layer — Execution Plan
**Prepared from:** ContractorOps "Autonomous Customer Acquisition" research brief (Sept 22, 2026)
**Scope:** The web research / data acquisition / evidence subsystem only. The orchestration engine, LLM reasoning, qualification strategy, outreach execution, and UI are being built by another developer and are out of scope except where this layer must interface with them.

**Labeling key used throughout:**
`SOURCE-DERIVED` = stated in the brief · `WEB-RESEARCHED` = verified via live search this session · `INFERENCE` = reasonable extrapolation, not stated · `PROPOSED DECISION` = an implementation choice you still need to make/confirm · `OPEN` = not specified in the source, requires validation with Johnson.

---

## Part 1 — Project Context (why this layer exists)

**`SOURCE-DERIVED`** The product is not "an AI SDR." The thesis is *goal-driven delegation*: a user states a commercial outcome ("find Bay Area remodeling companies that fit ContractorOps and produce qualified demo opportunities"), and the system decides *who* to pursue, *why now*, *what to learn*, *which channel/action*, *when to stop*, and hands back a qualified opportunity — then learns from the commercial outcome, not just email/meeting metrics.

Key concepts, in plain terms:

- **Goal contract** — a structured object (business, acquisition job, vertical, geography, qualification definition, required evidence, allowed sources/channels, budget, stop conditions, handoff SLA) that every run starts from. It's the thing that keeps a general-purpose agent from becoming an unbounded prompt runner.
- **Vertical pack** — versioned data + code (ontology, source adapters, evidence schema, qualification gates, channel policy, message claims, objection taxonomy, definition of "qualified") that plugs into a **shared horizontal acquisition loop**. Contractors and freight are the two packs in scope; the loop (planner → candidate generator → entity resolver → research workers → evidence store → qualification engine → channel planner → executor → conversation agent → outcome learner → human control plane) stays the same across packs.
- **Evidence/provenance system** — the discipline of never storing "this is a good lead" as a bare conclusion. Every fact is stored as: what was observed, where it came from, when, whether it's observed or inferred, confidence, extractor version, and expiry.
- **Qualification system** — hard gates (deterministic) followed by an inspectable, reason-coded score. The LLM may extract/explain; deterministic code enforces gates, budgets, and compliance.
- **Outcome/learning loop** — joins every action back to accepted/rejected/booked/won/lost and revenue, so the system (and Johnson) can see which evidence and decisions actually produced value — not just replies or meetings.
- **Why contractors first** — Johnson already has a SERP pipeline and can personally judge fit; it's the fastest path to a real evidence loop.
- **Why freight second** — deliberately different data, cadence, and economics. It's a generalization *test*, not a second product to perfect. Success is measured by how much of the core loop is reused unchanged vs. forked.
- **Role of APIs / browser automation / computer use** — strict preference order: official API → licensed export → authorized integration → polite public-page fetch → browser automation only when necessary and permitted. Computer use is an *enabling capability* for read-heavy gaps in fragmented contractor/freight software — it is explicitly **not** the product's moat, and it does not make otherwise-prohibited scraping acceptable.

**Where your work fits:** you are not building the orchestrator, the qualification LLM logic, the outreach engine, or the UI. You are building the layer that turns messy public/authorized sources into entities with evidence, signals, and contacts that the qualification engine can trust — the "TRUSTWORTHY STRUCTURED DATA" box between external sources and the main AI system.

---

## Part 2 — Your Responsibility (system boundary)

### In scope
| Area | What it means here |
|---|---|
| Discovery | Finding candidate entities for a given goal contract (search APIs, registries, permit feeds) |
| Public/gov/open-data research | Investigating and integrating the sources in Part 4 |
| API research | Verifying real endpoints, auth, quotas, terms before any connector is built |
| Web research & scraping/crawling | Company sites, sitemaps, public pages — API-first, browser-automation last |
| Data extraction & normalization | Turning raw HTML/JSON/PDF into structured fields (name, address, phone, domain, classification) |
| Entity resolution & deduplication | Merging records from multiple sources into one canonical entity, with confidence and review states |
| Evidence & provenance | Attaching source, timestamp, confidence, observed/inferred to every claim |
| Freshness | TTL/expiry per field, refresh scheduling |
| Signal detection | Converting raw facts into timing ("why now") events |
| Contact discovery (where appropriate) | Finding a plausible decision-maker + channel, **not** verifying deliverability at scale (see below) |
| Data quality | Precision/duplicate/staleness measurement on your own output |
| Delivery to the main system | A stable, documented contract (Part 17) that the orchestrator calls or subscribes to |

### Explicitly NOT your responsibility
| Area | Who owns it |
|---|---|
| Agent orchestration / planner / state machine for a prospect | Main AI system |
| LLM reasoning about qualification, scoring weights, message strategy | Main AI system |
| Outreach execution (email/SMS/voice sends, sequencing, warmup) | Main AI system / outreach infra |
| CRM workflow, meeting booking | Main AI system |
| Business/product strategy, pricing, ICP definition | Johnson |
| UI/agent console | Main AI system |
| General multi-agent framework | Main AI system |

`PROPOSED DECISION`: treat contact **verification** (deliverability, mailbox pings) as a bought capability the main system calls, while contact **discovery** (finding a name/role/likely email pattern from your evidence) stays in your layer, because it depends on the same entity/page evidence you already hold. Confirm this split with the other developer before building anything contact-related.

---

## Part 3 — The Exact First Objective

`SOURCE-DERIVED` The brief's own worked example ("Recommended product boundary for the first build") is: **"Find Bay Area remodeling companies that fit ContractorOps and produce qualified demo opportunities."** This is the narrowest objective actually specified in the source, and it aligns with Day 1–2 of the seven-day plan (reuse Johnson's existing SERP pipeline). Use this as the target unless Johnson redirects you.

| Dimension | Definition for v0 | Status |
|---|---|---|
| Target entity type | Licensed general/remodeling contractors (CSLB classifications B – General Building, and adjacent trade classes commonly involved in remodels: C-6, C-10, C-27, C-36 etc.) | `PROPOSED DECISION` — exact classification list needs Johnson's input |
| Geography | Bay Area counties (Alameda, Contra Costa, San Francisco, San Mateo, Santa Clara, Marin, Sonoma) | `SOURCE-DERIVED` (Bay Area named), county list is `PROPOSED DECISION` |
| Minimum info required | Legal/DBA business name, license status + classification, business address, phone, website/domain, county | `INFERENCE` from CSLB fields available (Part 4) |
| Useful evidence | Active license in good standing; business age/registration date; company site describing remodeling services; recent permit activity in the entity's service area | `INFERENCE` |
| Timing signal candidates | New/renewed license, new business registration, new building permit filed by or naming the contractor, hiring signal on the company's own careers page | `INFERENCE`, not validated against real data yet |
| Fit signal | "Fits ContractorOps" — **`OPEN`**. The brief never defines what ContractorOps sells or its ICP (crew size? revenue band? license type? current software?). This is the single most important open question — see Part 23. |
| Contact identification | Business phone/general email from CSLB record or company site; named decision-maker (owner/operator) only if published on the company's own site — no purchased contact database in v0 | `PROPOSED DECISION` |
| Explicitly unnecessary for v0 | National coverage, multi-state licensing, freight/real-estate/insurance data, verified personal emails, scraped review sites, browser-automation connectors | `PROPOSED DECISION` |

**Validation process for the ambiguity** `PROPOSED DECISION`: don't guess "fit." Day 1 of the seven-day plan already calls for 20 positive / 20 negative gold examples labeled by Johnson — make "what does a fit company look like" the first thing you extract from that labeling exercise, then encode it as a set of CSLB-classification + firmographic filters you can test against, rather than as an LLM judgment call.

---

## Part 4 — US Public Data Landscape

Sources are grouped by category. Every row states access method, cost, and MVP relevance. Entries verified live this session are marked `WEB-RESEARCHED`; entries taken directly from the brief are `SOURCE-DERIVED`; anything else is flagged.

### 4.1 Contractor identity & licensing (core to MVP)

| Source | Coverage | Official API? | Bulk/export? | Cost | Freshness | Fields | Category | MVP? |
|---|---|---|---|---|---|---|---|---|
| **CSLB Public Data Portal** (cslb.ca.gov) | CA-licensed contractors, all 58 counties, ~74 classifications | **No REST API.** Only web-based downloads: "by classification+county," "by classification," full master list, "by city/zip," and an instant single-license lookup. `WEB-RESEARCHED` | Yes — a paid Data Services Unit bulk order ($245 flat, non-refundable, mailed/emailed file, up to 30 business days turnaround). `WEB-RESEARCHED` | Free (portal downloads) / $245 (bulk custom order) | Portal reflects live registry; bulk order is a snapshot at order time | License #, business name, status, classification(s), issue/expiry date, address, county, phone, bond, workers' comp. **No owner/personnel names or emails.** `WEB-RESEARCHED` | Identity, Fit | **Yes** |
| Secretary of State business registration (CA example cited in brief) | Entity status, formation date, registered address, agent | Yes, per brief — CA has a public business-entity API | Varies by state | Free/low-cost typically | Registration-event cadence | Legal name, entity status, formation date, address | Identity, weak Timing (new registration) | Yes |
| SAM.gov **Entity Management API** (`api.sam.gov/entity-information/v3/entities`) | Federal-registered entities (UEI/CAGE, NAICS, status, POCs) | Yes, official, free key via api.sam.gov/Login.gov | No separate bulk file needed for entity lookups | Free; **rate-limited: 40 calls/day on a new non-federal account, up to 1,000/day after approval** `WEB-RESEARCHED` | Near real-time | UEI, legal name, NAICS, status, POCs | Identity, weak Fit | Low priority unless the target contractor does federal work |
| SAM.gov **Get Opportunities API** (`/opportunities/v2/search`) | Federal contract solicitations/awards | Yes, same key, same quota; 1-year query-window cap `WEB-RESEARCHED` | N/A | Free (rate-limited as above) | Daily | Solicitation, NAICS, agency, dates, set-aside type | Timing (procurement signal), not identity | Tier 2 |

### 4.2 Construction & property signals

| Source | Coverage | API? | Cost | Fields | Category | MVP? |
|---|---|---|---|---|---|---|
| Census **Building Permits Survey (BPS)** | Federal, aggregate permit counts | Yes, public data API `SOURCE-DERIVED` | Free | Permit counts by place/type/month | Market-level only — not lead-level | Tier 3 (context, not leads) |
| County assessor/recorder portals, often on **Socrata** | County-level, parcel/ownership/permit data | Varies — Socrata gives a common API shape where used, but field definitions/cadence differ per county `SOURCE-DERIVED` | Usually free | Parcel, owner, sale date, sometimes permits | Timing, corroboration | Tier 2 (jurisdiction-by-jurisdiction effort) |
| City/county building/planning permit portals | City-specific | Case-by-case; some have APIs, most require a per-jurisdiction adapter `SOURCE-DERIVED` | Free | Permit type, address, contractor of record, date, value | Strong Timing signal, weak Identity | Tier 2 — highest signal value but highest integration cost; pick 2–3 Bay Area cities to pilot, not all |
| **RESO Web API** | MLS listing data, standardized transport | Yes, but requires MLS/broker/vendor agreement — RESO standardizes the API, it does not itself grant data rights `SOURCE-DERIVED` | Licensing cost varies, not public | Listing, property, agent data | Real estate vertical only | Out of scope for contractor MVP |
| ATTOM property API | Ownership, valuation, transaction, mortgage | Yes, commercial | Paid, commercial terms `SOURCE-DERIVED` | Property/owner/transaction | Real estate & property-change signals | Tier 3 for contractor MVP |

### 4.3 Business discovery / general B2B

| Source | Coverage | API? | Cost | Critical constraint | Category | MVP? |
|---|---|---|---|---|---|---|
| **Google Places API (New)** | Business listings, phone, address, hours, rating | Yes, official | Paid per call | **`WEB-RESEARCHED`, important:** Google's Maps Platform ToS permits caching *only the Place ID indefinitely* and lat/lng for up to 30 days. Display name, formatted address, rating, phone have **no storage exception** — every use of those fields is effectively a live call, not a stored database field. This has direct architectural consequences (Part 6, "Legal/Compliance"). | Identity/discovery, not a persistent store | Tier 1 for *discovery*, but design around the no-store constraint |
| Yelp Fusion API | Business listings | Yes, per brief; not independently re-verified this session | Free tier + paid | Use official API and its display/storage rules rather than scraping result pages `SOURCE-DERIVED` | Identity/discovery | Tier 2, needs its own ToS re-check before use |
| Company websites & sitemaps | First-party description, services, contact, careers | N/A — direct polite fetch | Free (respect robots/rate limits) | Retain source URL + date `SOURCE-DERIVED` | Fit evidence, some Timing (careers page) | **Yes** — this is the backbone of contractor MVP evidence |
| Job postings | Hiring signal | No single official API; varies by job board `INFERENCE` | Varies | Timing signal only, distinguish company-authored claim from verified fact `SOURCE-DERIVED` | Timing | Tier 2 |
| EPA **ECHO** web services | Regulated facilities, compliance/environmental records | Yes, per brief | Free `SOURCE-DERIVED` (not independently re-verified this session) | Facility identity + compliance history | Fit (for facility-heavy B2B), weak Identity | Tier 3 for contractor MVP; more relevant to a facilities-adjacent vertical |

### 4.4 Freight & insurance (secondary verticals — documented for Day 6 pilot, not built now)

| Source | Coverage | API? | Cost | Notes |
|---|---|---|---|---|
| **FMCSA QCMobile API** (`mobile.fmcsa.dot.gov/qc/services`) | Motor carrier registration, safety, authority, insurance-on-file status | Yes, official, free — requires Login.gov account + API "webkey" `WEB-RESEARCHED` | Free | Confirms carrier *identity/authority*, **not shipper demand**. Weekly-cadence data and per-query result caps reported by third parties — validate limits before relying on it operationally. `WEB-RESEARCHED` |
| BTS Freight Analysis Framework | Aggregate freight flows by lane/commodity | Yes `SOURCE-DERIVED` | Free | Market-sizing only, not lead-level |
| SEC EDGAR APIs | Public-company facts, filings, facilities | Yes, official `SOURCE-DERIVED` | Free | Useful for public-company shippers only |
| NAIC / NIPR (Producer DB) | Insurance producer/carrier licensing | Yes, access varies by product/state `SOURCE-DERIVED` | Varies, some restricted | Insurance vertical only; `LEGAL REVIEW REQUIRED` before any use |

### What was intentionally left out
Consumer listing/scraping of MLS sites, any source requiring bypassing a login/CAPTCHA, and any "people-search"/contact-database vendor were excluded from this table — the brief explicitly rules the first two out, and the third is a "buy for coverage, not truth" decision that belongs to the main system integration, not your v0 build.

---

## Part 5 — Source Prioritization Framework

**Methodology** `PROPOSED DECISION`: rather than a numeric score (which invites false precision on sources we haven't tested yet), use a qualitative pass/fail against four questions, in this order, because each one gates the next:

1. **Does it produce lead-level (not just market-level) data for the contractor MVP geography?** Fails → not Tier 1, regardless of anything else.
2. **Is there a legal, documented access path (API, bulk export, or polite public fetch under stated terms)?** Unclear or restrictive → `LEGAL REVIEW REQUIRED`, drop to Tier 2/3 until resolved.
3. **Is the engineering cost to integrate proportionate to one Bay Area contractor pilot** (days, not weeks)?
4. **Does it add identity, fit, or timing evidence that CSLB + company websites don't already give you?**

### Tier 1 — must build for MVP
- **CSLB Public Data Portal** (manual/downloadable, + optional $245 bulk order later) — the only source that gives identity + classification + license status for the exact target entity type.
- **Company websites & sitemaps** — the only source of first-party fit evidence and Timing (careers pages, project pages).
- **California Secretary of State registration lookup** — corroborates identity/legal status.

### Tier 2 — useful after MVP works
- Google Places / Yelp APIs for discovery breadth (once the no-store constraint has an architectural answer).
- 2–3 pilot city/county building-permit portals for Timing signal depth.
- Job-posting monitoring for hiring signal.
- SAM.gov (only if Johnson wants to target contractors doing government work).

### Tier 3 — interesting, not needed now
- ATTOM/RESO (real estate vertical, out of scope until that vertical is chosen).
- EPA ECHO, Census BPS (market-level, not lead-level for this MVP).
- FMCSA, BTS FAF, NAIC/NIPR (freight/insurance — revisit at Day 6 pilot, and only the minimum needed for that interview-driven pack).

---

## Part 6 — Data Acquisition Architecture (summary)

Full component-level architecture, file layout, and interfaces are in the companion document **`02-data-acquisition-architecture-spec.md`**. Summary flow:

```
SOURCE → DISCOVERY → FETCH → RAW SNAPSHOT → PARSE → EXTRACT → NORMALIZE
→ ENTITY RESOLUTION → VALIDATE → EVIDENCE/CLAIM → SIGNAL → QUALITY/FRESHNESS → PUBLISH
```

Two architectural facts from Part 4 already constrain this: (1) CSLB has no API, so the **Fetch** layer must support scheduled downloads of static export pages as a first-class source type, not just HTTP/JSON polling; (2) Google Places' storage restriction means **Raw Snapshot** for that source can only persist the Place ID long-term — everything else must be treated as ephemeral/re-fetchable, which changes how "freshness" applies to that specific connector.

---

## Part 7 — Data Model (MVP)

| Entity | Purpose | Key fields | Observed vs. inferred | Notes |
|---|---|---|---|---|
| `Entity` (Organization) | Canonical company record | stable_id, canonical_name, type, primary_address, domain | Canonical name is a resolution *output*, not raw | One row per real-world company, after resolution |
| `SourceRecord` / `RawSnapshot` | Immutable copy of exactly what a source returned | source, source_record_id, retrieved_at, content_hash, license_policy, raw_payload_ref | Always observed | Never overwritten; new fetch = new row |
| `Claim` | One normalized fact about an entity | entity_id, field, value, observed_or_inferred, confidence, valid_from, observed_at, expires_at, source_snapshot_id, extractor_version | Explicit flag required | This is the evidence-first unit (Part 8) |
| `IdentityEdge` | Link between two records believed to be the same entity | entity_a, entity_b, match_features, confidence, review_state | N/A | Drives entity resolution (Part 9) |
| `ContactPoint` | A phone/email/person tied to an entity | entity_id, channel, value, verification_state, verified_at, source, consent/suppression_state | Observed (as published) | No purchased/inferred personal emails in v0 |
| `Signal` | A timing event derived from claims | entity_id, signal_type, evidence_ref, observed_at, expires_at, confidence | Distinguish observed event vs. inferred meaning (Part 12) | e.g., "new license issued" is observed; "this implies expansion" is inferred |

**MVP schema** = the six tables above only. **Future schema** (not now): multi-vertical ontology tables, contact-verification-vendor result tables, cross-source contradiction-resolution tables, ML-derived quality scores.

---

## Part 8 — Evidence-First Model

`SOURCE-DERIVED` structure, directly from the brief:

```
COMPANY → FACT → SOURCE → TIMESTAMP → CONFIDENCE → EVIDENCE → EXPIRATION
```

**Example 1 (observed, high confidence):**
```
entity: "Bayview Remodeling Inc."
field: license_status
value: "ACTIVE"
observed_or_inferred: observed
confidence: 0.95
source: CSLB Public Data Portal (classification+county export, B classification, Alameda)
observed_at: 2026-09-20T00:00:00Z
expires_at: 2026-10-20T00:00:00Z   # re-check monthly; license status can change
extractor_version: cslb_export_parser@0.1
```

**Example 2 (observed low-confidence + separate inference):**
```
Claim A (observed):
  field: careers_page_text
  value: "Now hiring: project manager, 2 carpenters"
  observed_or_inferred: observed
  confidence: 0.9
  source: company website /careers page
  observed_at: 2026-09-18T00:00:00Z
  expires_at: 2026-10-18T00:00:00Z

Signal (inferred, separately stored, references Claim A):
  signal_type: possible_expansion
  evidence_ref: Claim A
  observed_or_inferred: inferred
  confidence: 0.4
```
The two never collapse into one row. The qualification engine (owned by the main system) can choose to weight or ignore the inference, but it can always see the underlying observed fact.

**Consumption by the main AI system:** claims and signals are exposed read-only via the integration contract (Part 17); the main system's qualification/ranking engine reads confidence + freshness + observed/inferred flags directly rather than receiving a single pre-baked "lead score" from your layer.

---

## Part 9 — Entity Resolution (MVP approach)

**Deterministic matching first** (in priority order):
1. Exact CSLB license number match.
2. Normalized domain match (company website).
3. Normalized phone match + normalized business-name similarity above a fixed threshold.

**Fuzzy matching**: only as a fallback, using normalized business name (strip suffixes like "Inc/LLC," lowercase, remove punctuation) + address proximity. Any fuzzy match below a confidence threshold goes to a `review_state = pending_review` `IdentityEdge` rather than being auto-merged — do not build a scored ML matcher for v0.

**Duplicate handling**: keep all `SourceRecord`s; merge only at the `Entity`/`Claim` layer via `IdentityEdge`s, so a bad merge can be undone without re-fetching anything.

This is deliberately the least sophisticated version that works for a single-state, single-vertical MVP — expand to library-based fuzzy matching (e.g., token-set + Jaro-Winkler) only once false-merge/false-split rates are actually measured against Johnson's gold set (Part 18).

---

## Part 10 — Web Crawling / Scraping Strategy

**Source hierarchy** `SOURCE-DERIVED`: official API → licensed export → customer-authorized integration → polite public-page fetch → browser automation only when permitted and necessary.

Applied to the contractor MVP specifically:
- CSLB → polite public-page fetch of the portal's static export pages (no API exists), on a **scheduled, low-frequency** basis (e.g., weekly per target county+classification) — not per-request.
- Company websites → polite fetch, respecting robots.txt, of a small fixed page set (home, about, services, careers, contact) — no full-site crawl.
- Google/Yelp → official API only, never scraped result pages.
- **No browser automation in v0.** Nothing in the contractor MVP source list requires it.

**Request management**: per-source rate limits and TTL-based conditional fetching (don't re-fetch a CSLB export or a company homepage more than once every N days unless a signal suggests it changed). Retries with backoff on 5xx/timeout; do not retry on 403/robots-disallow — that's a policy failure, not a transient one, and should be logged for human review, not silently retried.

**Dead-letter handling**: any fetch/parse that fails 3x goes to a dead-letter state with the raw error, not silently dropped — this is what makes "why do we have fewer contractors than expected" debuggable later.

---

## Part 11 — Legal / Compliance / Data-Use Boundaries

| Source | Access method | Key restriction | Status |
|---|---|---|---|
| CSLB Public Data Portal | Public web pages, public records under CA Business & Professions Code | Portal downloads are explicitly public disclosure; the $245 custom order is CSLB's own licensed distribution channel. No PII (personnel names/emails) is provided by CSLB itself. | Low risk, `WEB-RESEARCHED` |
| Google Places API | Official API, commercial ToS | **Cannot store most fields beyond 30 days (coordinates) or indefinitely (place ID only).** Any product feature that shows a cached business name/address/phone from Places must either re-fetch live or hold a separate license. | `LEGAL REVIEW REQUIRED` before building persistent storage on top of Places data — confirmed via ToS text this session |
| Yelp Fusion API | Official API | Has its own display/storage rules per the brief; not independently re-verified this session | `LEGAL REVIEW REQUIRED` before integration |
| Company websites | Public pages | Respect robots.txt and rate limits; retain source URL/date; do not republish/redistribute scraped page content wholesale — extract facts, don't mirror pages | Standard practice, low risk if polite |
| SAM.gov APIs | Official, free key | Rate-limited (40–1,000 calls/day); federal-procurement data is generally public-domain | Low risk |
| Secretary of State registrations | Official public record | Varies by state; CA's is a public API per the brief | Low risk for CA |
| Any future contact-verification/enrichment vendor | Commercial | Redistribution rights, personal-data handling, deletion obligations all vary | `LEGAL REVIEW REQUIRED` at time of selection — not needed for v0 |

General principle applied throughout: "publicly accessible" (you can view it in a browser) is **not** the same as "publicly reusable/redistributable" (you can store and republish it). CSLB and Secretary-of-State records are public records intended for this kind of reuse; API-gated commercial data (Places, any paid vendor) is accessible but licensed, and storage rights must be read from the ToS, not assumed.

---

## Part 12 — Signal Extraction (design)

| Signal type | Source | Evidence | Observed or inferred |
|---|---|---|---|
| New/renewed license | CSLB | License issue/renewal date field | Observed |
| New business registration | Secretary of State | Formation date | Observed |
| Careers-page hiring post | Company website | Page text/date | Observed (the posting); "implies growth" is a separate inferred signal |
| New building permit naming the contractor | City/county permit portal (Tier 2) | Permit record | Observed |
| License in a lapsed/expired window recently renewed | CSLB (derived from two snapshots over time) | Comparison of two `Claim`s | Observed (the state change), computed by your layer |

Every `Signal` carries its own `entity_relationship`, `evidence_ref` (pointing at the underlying `Claim`), `confidence`, and `expires_at`. The qualification engine (main system) decides how much weight a signal deserves — your layer's job stops at "this observed thing happened, here's the proof."

---

## Part 13 — Contractor MVP (concrete spec)

- **Target:** CA-licensed general/remodeling contractors (classification set `PROPOSED DECISION`, pending CSLB classification list confirmation)
- **Geography:** Bay Area counties (list above)
- **Discovery:** CSLB portal export by classification+county, county-by-county
- **Required sources:** CSLB (identity/license), company website (fit evidence, contact), CA SOS (corroboration)
- **Required fields:** business name, license #, classification, status, address, county, phone, domain, one fit-evidence snippet, one timing signal (if any)
- **Qualification inputs handed to main system:** the `Entity` + its `Claim`s + any `Signal`s — **not** a pre-computed score
- **Evidence requirements:** every claim traceable to a `SourceRecord` with URL/portal query and retrieval date
- **Contact requirements:** published business phone/email/contact form from the company's own site; no purchased personal-contact data in v0
- **Output format:** the `ResearchResult` JSON contract (Part 17)
- **Example lead / evidence card:** see Appendix A below.

### Appendix A — Example evidence card (illustrative, not real data)
```json
{
  "entity": {
    "stable_id": "ent_01HXYZ",
    "canonical_name": "Bayview Remodeling Inc.",
    "domain": "bayviewremodeling.com",
    "address": {"city": "Oakland", "county": "Alameda", "state": "CA"}
  },
  "claims": [
    {"field": "license_status", "value": "ACTIVE", "confidence": 0.95,
     "observed_or_inferred": "observed", "source": "CSLB portal export",
     "observed_at": "2026-09-20", "expires_at": "2026-10-20"},
    {"field": "license_classification", "value": "B - General Building",
     "confidence": 0.95, "observed_or_inferred": "observed", "source": "CSLB portal export"}
  ],
  "signals": [
    {"signal_type": "careers_hiring_post", "confidence": 0.6,
     "observed_or_inferred": "observed", "evidence_ref": "claim_00219",
     "observed_at": "2026-09-18"}
  ],
  "contacts": [
    {"channel": "phone", "value": "(510) 555-0134", "source": "CSLB record",
     "verification_state": "unverified"}
  ],
  "sources": ["cslb_portal_export_2026-09-20", "company_site_fetch_2026-09-18"]
}
```

---

## Part 14 — Do Not Overbuild

| Don't build now | Why not | Build instead | When it becomes justified |
|---|---|---|---|
| Universal US company database | Massively out of scope for one vertical, one state | Entities discovered per goal-contract run, resolved incrementally | Only if the main system asks for cross-run entity reuse at real scale |
| Universal scraper framework | You have 3 sources, not 300 | A `SourceConnector` interface with 3 concrete implementations | When onboarding source #6–8 makes duplication visible |
| Browser-automation pipeline | No MVP source needs it | Nothing — revisit only if a Tier 2 source (e.g., a permit portal) has no API/export | When a specific Tier 2 source is chosen and confirmed to require it |
| ML-based entity resolution | Deterministic rules cover CSLB+domain+phone matching for one state | Rule-based matcher + review queue | When false-merge/split rate on real data is actually measured and too high |
| Multi-vertical abstraction | Only one vertical pack exists (contractors); freight is a Day 6 test, not a build target now | A single, slightly-too-specific pipeline; refactor after the freight pilot shows what's actually shared | After the Day 6/7 generalization result is in |
| Full CRM/contact-vendor integrations | Not your layer's job (Part 2) | Hand off `ContactPoint`s to the main system via the contract | Main system decides |

---

## Part 15 — Tech Stack

| Need | Recommendation | Why | Needed in MVP? | Build/Buy/Wrap |
|---|---|---|---|---|
| HTTP client | `httpx` (async) | Modern, async-native, good timeout/retry ergonomics | Yes | Buy (library) |
| HTML parsing | `selectolax` or `BeautifulSoup4` | Fast, well-understood; no need for anything heavier without browser rendering | Yes | Buy |
| Browser automation | *(not included in v0)* | No MVP source requires it | No | Defer |
| Data validation/schema | `pydantic` | Matches the `Claim`/`Entity` data model directly, validates at every pipeline boundary | Yes | Buy |
| Queue | Start with a simple DB-backed job table (e.g., a `jobs` table with status) rather than standing up Celery/Redis for 3 sources | A real queue is over-engineering at this scale; revisit if concurrency/volume grows | Yes (simple version) | Build (minimal) |
| Database | PostgreSQL | Relational fit for entities/claims/edges; JSONB for raw payload refs if needed | Yes | Buy (managed Postgres) |
| Object/raw storage | Local disk or S3-compatible bucket for raw snapshots | Raw preservation principle (Part 6) needs somewhere durable and cheap | Yes | Buy |
| Caching | Simple TTL columns in Postgres (`expires_at`) rather than a separate cache layer | One more piece of infra you don't need yet | Yes (in-DB) | Build (minimal) |
| Scheduling | `cron` / a lightweight scheduler (e.g., APScheduler) for weekly CSLB pulls | Matches the actual cadence needed | Yes | Buy |
| Observability | Structured logging (`structlog`) + basic counters; defer full tracing stack | Enough to debug a 3-source pipeline | Yes (basic) | Buy (library) |
| LLM extraction | Only for company-website fit-evidence extraction (free text → structured claim); deterministic parsing for CSLB/SOS structured data | Matches "deterministic first, LLM where semantic extraction adds value" principle | Yes, narrowly | Wrap (call main system's model access or a direct API key — confirm with Johnson) |
| Embeddings/vector DB | Not needed | No semantic search requirement in v0 | No | Defer |

---

## Part 16 — Repository Structure (summary)

Full file-by-file specification is in the architecture document. Top-level shape:

```
src/
  sources/        # one module per connector: cslb, ca_sos, company_site, google_places(tier2)
  fetch/           # http fetcher, scheduling, rate limiting
  raw/             # raw snapshot storage interface
  parse/           # per-source parsers (CSLB export table, SOS API JSON, HTML)
  extract/         # deterministic + LLM extraction into Claims
  normalize/       # name/address/phone/domain canonicalization
  entities/        # entity resolution
  evidence/        # claim/evidence store + freshness logic
  signals/         # signal detection rules
  publish/         # the ResearchResult contract + delivery to main system
  config/          # source policies, credentials wiring
tests/
  unit/ integration/ fixtures/
scripts/           # one-off backfills, CSLB re-pull triggers
docs/
```

---

## Part 17 — Interface With the Main AI System

`PROPOSED DECISION` (needs confirmation with the other developer): expose a small **synchronous request/response API** for on-demand entity research, plus a **published event/table** the main system can poll or subscribe to for newly discovered candidates. A full queue/event bus is over-engineering for two developers and three sources.

**Research request:**
```json
{
  "request_id": "req_01HXYZ",
  "entity_hint": {"name": "Bayview Remodeling Inc.", "domain": null},
  "questions": ["license_status", "classification", "fit_evidence", "contact"]
}
```

**Research result (`ResearchResult`):** the same shape as Appendix A above — `entity`, `claims[]`, `signals[]`, `contacts[]`, `sources[]`. This is the canonical contract; the full schema with types/versioning lives in the architecture document (Part 34 there).

---

## Part 18 — Testing and Data Quality

- **Gold dataset**: reuse Johnson's Day 1 labeled 20-positive/20-negative set as the entity-resolution and fit-evidence ground truth, not a separately invented one.
- **Metrics to track from day one**: duplicate rate (multiple `Entity` rows for one real company), stale-field rate (`Claim`s past `expires_at` still being served), contact-field-present rate, unsupported-claim rate (a `Claim` with no `source_snapshot_id`), and human minutes per accepted lead once the main system's team starts reviewing output.
- **Regression/contract tests**: for CSLB specifically, since it's a scraped static page rather than an API, add a schema/structure test that fails loudly if the portal's export page layout changes — this is your single highest-risk breakage point.
- **Source-ablation**: once more than one source contributes to a given field, periodically check whether removing a source actually changes output quality, per the brief's own recommendation.

---

## Part 19 — Execution Roadmap

**Phase 0 — Research & source mapping** (this document + companion architecture doc). *Definition of done:* Tier 1 sources confirmed accessible with real test pulls, not just documentation.
**Phase 1 — MVP acquisition pipeline**: CSLB connector → raw snapshot → parse → normalize → publish. *DoD:* first real `Entity` + `Claim` records for one county+classification.
**Phase 2 — Evidence + entity resolution**: company-site fetch/extract, CA SOS corroboration, deterministic entity resolution. *DoD:* deduplicated entity list with evidence cards matching Appendix A's shape.
**Phase 3 — Signal extraction**: careers-page and license-renewal signals. *DoD:* at least one working signal type end-to-end.
**Phase 4 — Integration**: `ResearchResult` contract implemented and handed to the main system for a real test run. *DoD:* main system can request/receive one full research result.
**Phase 5 — Evaluation**: run the Part 18 metrics against Johnson's gold set. *DoD:* precision/duplicate/staleness numbers exist and are reviewed with Johnson.
**Phase 6 — Freight generalization test (Day 6–7 of the seven-day plan)**: implement only a freight vertical pack on the same core; measure what's reused vs. forked. *DoD:* a documented generalization result, not a working freight product.

### Day-by-day (first 7 days)
| Day | Focus |
|---|---|
| 1 | Confirm classification list + Bay Area counties with Johnson; write/verify CSLB export field mapping against a real downloaded file; stand up `RawSnapshot` + `Claim` tables |
| 2 | Build CSLB connector (fetch → parse → normalize → `Claim`); produce first real entity list for one county+classification |
| 3 | Company-site fetcher + deterministic HTML extraction (contact block); basic fit-evidence extraction (LLM-assisted, narrowly scoped) |
| 4 | Entity resolution (deterministic rules) across CSLB + company-site records; dedupe first real batch |
| 5 | Signal extraction v0 (careers-page hiring post); freshness/expiry wiring |
| 6 | `ResearchResult` contract + a manual/scripted handoff test with the main system's developer |
| 7 | Run Part 18 metrics against Johnson's gold set; write up what's missing before scale |

---

## Part 20 — First 48 Hours

1. Get CSLB classification list + county priority confirmed with Johnson (don't guess — this blocks everything downstream).
2. Manually download one real CSLB "by classification and county" export and inspect the actual columns/format (`WEB-RESEARCHED` confirms this download path exists; you haven't seen the real file structure yet).
3. Stand up Postgres locally with the `Entity`/`SourceRecord`/`Claim` tables from Part 7 (minimal columns only).
4. Write the CSLB parser against the real downloaded file, not assumed field names.
5. Load one county+classification into `Claim` rows; confirm you can reconstruct a readable evidence card from the database.
6. Fetch one real target company's website and manually note what "fit evidence" actually looks like in the wild, before writing an extraction prompt/rule.
7. Write down (in `docs/`) any place where the real CSLB file differs from what this plan assumed — this becomes your first "assumption vs. reality" log entry.

---

## Part 21 — Research Outputs to Produce (minimum useful set)

1. This execution plan (living document, update as assumptions resolve)
2. `02-data-acquisition-architecture-spec.md` (companion document, file-level detail)
3. Source Evaluation Matrix (Part 4/5 tables, kept current as sources are actually tested)
4. `ResearchResult` / evidence schema (Part 7–8, versioned)
5. Sample dataset (a handful of real, redacted evidence cards) to share with Johnson and the other developer
6. A short data-quality readout after Phase 5 (Part 18 metrics)

Skip: a separate "signal taxonomy" doc (fold into this plan, Part 12) and a separate technical README (the architecture doc's file inventory serves that purpose) — for a two-developer, one-vertical MVP, more documents than this creates maintenance overhead without adding clarity.

---

## Part 22 — Risks and Failure Modes

| Risk | Probability | Impact | Detection | Mitigation | Fallback |
|---|---|---|---|---|---|
| CSLB portal page structure changes (no API, so no versioned contract) | Medium | High — breaks the only identity source | Structure/schema test fails on next scheduled pull | Keep the parser isolated behind the `SourceConnector` interface; alert on parse failure rather than silently returning empty | Fall back to the $245 bulk order as a manual refresh while the parser is fixed |
| "Fit" criteria stay undefined too long | Medium | High — blocks meaningful qualification | Gold-set labeling produces no clear pattern | Push Johnson for firmographic ICP answers before Phase 2 finishes | Ship v0 with classification+geography only, flag fit as `needs_human` |
| Google/Yelp storage terms block a planned feature | Medium | Medium | Caught in Part 11 review | Treat those sources as live-lookup-only, never persisted beyond place ID | Drop to CSLB+website-only discovery if needed |
| Entity resolution false-merges two different companies | Low–Medium | Medium | Gold-set mismatch, Johnson spot-check | Deterministic-only matching in v0; low-confidence matches go to review, not auto-merge | Manual review queue |
| Over-scoping into a general scraping platform | Medium (natural pull given the brief's own ambition) | High — burns the 7-day window | Compare actual Day-N output to Day-N plan | Part 14's "do not build" list, reviewed daily against actual work | Cut scope back to Tier 1 sources only |
| LLM fit-evidence extraction hallucinates a claim not actually on the page | Medium | Medium–High (false evidence undermines the whole evidence-first premise) | Spot-check extracted claims against source page manually | Require every LLM-derived claim to carry a snippet/quote reference back to the raw page, not just a summary | Disable LLM extraction for that field, fall back to storing raw text only |

---

## Part 23 — Questions for the Project Owner (Johnson)

**PRODUCT**
- What does ContractorOps actually sell, and what's the ICP (crew size, revenue band, current tools/pain point)? This directly defines "fit" in Part 3/13.
- Is "qualified demo opportunity" defined anywhere beyond "booked a demo," or does it require a follow-on qualification step?

**DATA**
- Confirm the CSLB classification list that counts as "remodeler" for this pack.
- Confirm the Bay Area county list (all 7, or a narrower starting set?).
- Any existing SERP pipeline output/schema Johnson already has, so this layer complements rather than duplicates it (the brief references "the existing SERP pipeline" as something Johnson already runs).

**TECHNICAL**
- Where does the main AI system expect to receive `ResearchResult`s — sync API call, polling table, or something else already decided with the other developer?
- Is there an existing database/infra Johnson wants this layer to share, or should it be a standalone service?

**LEGAL**
- Any existing legal guidance on Google/Yelp API usage ContractorOps has already obtained, before this layer assumes the storage restrictions found this session are the full picture.

**OPERATIONS**
- Who reviews the Day 3 blind-scored 50–100 candidates — Johnson alone, or someone else at ContractorOps?
- Budget/appetite for the $245 CSLB bulk order, or is the free portal-download path sufficient for the pilot?

**INTEGRATION**
- What's the other developer's current state — is there anything to integrate against yet, or should Phase 4 assume a stub/mock contract for now?

---

## Part 24 — SINGLE SOURCE OF TRUTH (condensed)

1. **Objective**: build the data acquisition/evidence layer that supplies the ContractorOps acquisition system with trustworthy, fresh, provenance-backed contractor leads, starting with one vertical (contractors) and one geography (Bay Area).
2. **Responsibility**: discovery, fetch, parse, extract, normalize, resolve, evidence, freshness, signals, and a documented handoff contract. Not orchestration, qualification logic, outreach, CRM, or UI.
3. **Boundary**: this layer stops at `ResearchResult`; the main AI system decides what to do with it.
4. **Initial use case**: "find Bay Area remodeling companies that fit ContractorOps" (Part 3).
5. **Data requirements**: license identity + classification (CSLB), corroborating registration (CA SOS), fit + contact evidence (company site).
6. **Source strategy**: API-first; CSLB has no API so it's a scheduled polite-fetch source; no browser automation in v0.
7. **Source priority**: Tier 1 = CSLB, company sites, CA SOS. Tier 2 = Places/Yelp, permit portals, job postings. Tier 3 = everything freight/real-estate/insurance-specific.
8. **Architecture**: source → fetch → raw snapshot → parse → extract → normalize → entity resolution → validate → evidence → signal → publish (full detail in companion doc).
9. **Data model**: `Entity`, `SourceRecord`, `Claim`, `IdentityEdge`, `ContactPoint`, `Signal` (Part 7).
10. **Evidence model**: fact/source/timestamp/confidence/observed-or-inferred/expiry, never collapsed into a bare conclusion (Part 8).
11. **Signal model**: observed event stored separately from any inferred meaning (Part 12).
12. **Scraping strategy**: polite, rate-limited, scheduled; dead-letter on repeated failure; no bypassing of technical/legal controls (Part 10–11).
13. **Tech stack**: Python, httpx, pydantic, Postgres, simple DB-backed job queue, structured logging — no browser automation, no vector DB, no heavyweight queue infra in v0 (Part 15).
14. **Repository structure**: sources/fetch/raw/parse/extract/normalize/entities/evidence/signals/publish (Part 16, full detail in companion doc).
15. **Main-system integration**: sync `ResearchResult` contract, event/table for new candidates (Part 17, to be confirmed with the other developer).
16. **Testing strategy**: gold-set precision, duplicate/staleness/unsupported-claim rates, CSLB structure regression test (Part 18).
17. **MVP scope**: CSLB + company sites + CA SOS, Bay Area, contractor classifications, no purchased contact data, no browser automation.
18. **Out of scope**: universal scraper, ML entity resolution, multi-vertical abstraction, CRM integration, freight/real-estate/insurance builds (only a Day-6 freight *pilot*, not a build).
19. **Seven-day plan**: see Part 19.
20. **Definition of done (MVP)**: a real, evidence-backed, deduplicated list of Bay Area remodeling contractors with at least one signal type, delivered through the `ResearchResult` contract, measured against Johnson's gold set.
21. **Open questions**: see Part 23 — "fit" definition is the single biggest blocker.
22. **Risks**: CSLB structural fragility, undefined "fit," Places/Yelp storage constraints, over-scoping (Part 22).