# Data Acquisition & Evidence Layer — Execution Plan
**ContractorOps Autonomous Customer Acquisition — Prateek's workstream**
Source document: *Autonomous customer acquisition* research brief, prepared for Johnson Subedi / ContractorOps, Sept 22, 2026.

Labeling used throughout: **SOURCE-DERIVED** (from the brief), **WEB-RESEARCHED** (verified via live search, dated), **INFERENCE** (reasoned from the above), **PROPOSED DECISION** (a call this plan is making that you can override), **NOT SPECIFIED — REQUIRES VALIDATION** (the brief is silent or ambiguous).

---

## PART 1 — The project, in plain terms

**SOURCE-DERIVED.** ContractorOps is building a system that takes a business-language acquisition goal ("find Bay Area remodelers that fit us and produce demo opportunities") and runs the whole funnel — decide who's worth pursuing, why now, what to learn, which channel, when to stop — instead of shipping a campaign-configuration tool. The brief calls this a **goal contract**: a structured object (target, evidence requirements, qualification bar, allowed sources/channels, spend/contact limits, stop conditions, handoff SLA) that a natural-language ask gets compiled into. Without it, an "autonomous" agent is just an unbounded prompt runner.

**Vertical packs** are the unit of specialization: each vertical (contractors, then freight, later maybe real estate/insurance) gets its own source adapters, ontology, evidence extractors, scoring rules, channel policy, and definition of "qualified opportunity" — versioned data+code, not a longer system prompt. They all sit on one **shared horizontal acquisition loop**: planner → candidate generator → entity resolver → research workers → evidence store → qualification/ranking → channel policy → executor → conversation agent → outcome tracker → human control plane, modeled as a state machine per prospect (`discovered → researched → eligible → contactable → contacted → engaged → qualified → booked → opportunity → won/lost`, with `suppressed`/`stopped`/`needs_human` reachable from anywhere).

The **evidence/provenance system** is the discipline of never storing a bare conclusion ("good lead") — every fact carries its source, retrieval time, confidence, and whether it was observed or LLM-inferred, with an expiry. The **qualification system** applies hard gates first (compliance, contactability, minimum fit), then an inspectable score with reason codes — LLMs extract/explain, deterministic code enforces gates and limits. The **outcome/learning loop** joins every action back to its evidence and forward to won/lost/revenue, so the system (and Johnson) can tell whether targeting quality is actually creating opportunities, not just activity.

Why **contractors** first: Johnson already runs ContractorOps and can personally judge whether a candidate lead is actually a fit — that's the fastest labeling loop available. Why **freight** second: it's a deliberately different market (different data, cadence, qualification, economics) chosen as a falsification test — if the shared loop only works for contractors, that's a real finding, not a failure.

**What makes this different from a standard AI SDR** (per the brief's own competitive read — this is the differentiation thesis your work needs to support, not marketing copy you should take as settled fact): goal-driven delegation instead of ICP+sequence configuration; vertical packs on shared infra instead of one generic prompt; execution through the customer's existing software (APIs first, computer use as fallback) instead of a new database; and optimization on qualified opportunities/revenue with a full evidence→decision→action→response→outcome trace, instead of opens/replies/meetings. Computer use, browser automation, and existing SaaS APIs are all **execution tools** the orchestrator/executor layer uses to act inside a contractor's or shipper's actual software — not something your data-acquisition layer builds or owns.

**INFERENCE.** Everything above is main-system scope. Your layer is the thing that feeds Part 6 of the loop (research workers → evidence store) with trustworthy inputs; you are not building the planner, the qualification engine's decision logic, the channel policy, the executor, or the conversation agent.


---

## PART 2 — What is (and isn't) your responsibility

**PROPOSED DECISION.** The brief describes the full loop but explicitly splits the work: someone else owns the main AI system and orchestration; you own the layer that supplies it trustworthy information. Based on the brief's own architecture (§B steps 2–5: candidate generator, entity resolver, research workers, evidence store) and its data-sourcing section, your scope is:

**In scope:**
- **Discovery** — turning a goal contract's target definition into a source query plan (which registries, which portals, which search patterns).
- **Public data research** — mapping what exists (Part 4) so decisions about what to integrate are informed, not guessed.
- **API research & integration** — official government/commercial APIs (SAM.gov, FMCSA, EPA ECHO, SEC EDGAR, Census, Google Places, etc.).
- **Government/open-data research** — federal/state/county/city sources, bulk files, Socrata-style portals.
- **Web research/crawling/scraping** — company sites, sitemaps, structured data, search APIs, and browser extraction only where permitted and no API/export exists.
- **Data extraction & normalization** — turning raw HTML/PDF/JSON into a consistent schema.
- **Entity resolution & deduplication** — knowing that "Acme Roofing LLC" from CSLB and "Acme Roofing" from Google Places are the same entity.
- **Evidence/provenance** — every claim traceable to a source, timestamp, and confidence.
- **Freshness** — field-level TTLs and staleness detection.
- **Signal detection** — timing/"why now" events, not just static identity.
- **Contact discovery** — where a source legitimately surfaces it (not building a contact database from scratch).
- **Data quality** — precision, duplicate rate, staleness, measured against a labeled set.
- **Delivery to the main system** — publishing structured, evidence-backed records through whatever contract Part 17 defines.

**Explicitly NOT your responsibility (PROPOSED DECISION, consistent with the brief's Build/Buy/Buy-or-Wrap split):**
- Agent orchestration, the planner, and the state machine that drives a prospect through its lifecycle.
- LLM reasoning for qualification *decisions* (you may extract/summarize with an LLM; the gate/score logic and its thresholds are the main system's).
- Channel/timing policy (email vs. call vs. wait) and outreach copy.
- Outreach execution — sending email/SMS/calls, mailbox warmup, deliverability.
- CRM workflow and calendar booking.
- Business/GTM strategy (which vertical, pricing, positioning).
- UI/dashboard for Johnson or end customers.
- The general agent framework/computer-use runtime itself (you may *specify* what a computer-use adapter needs to observe/extract for a given source, but building the isolated browser runtime, permissioning, and approval flow is main-system/executor territory per the brief's §D).

If a source needs computer-use to read (not act on) a system — e.g., pulling permit data from a county portal with no API — that read-only adapter is arguably yours to specify since it's a discovery/fetch concern feeding evidence, but the shared runtime it executes in belongs to the platform. **NOT SPECIFIED — REQUIRES VALIDATION:** confirm this boundary with whoever owns orchestration before building a bespoke browser adapter, since duplicate runtimes are a real risk (see Part 14).


---

## PART 3 — The narrowest useful first objective

**SOURCE-DERIVED**, directly from the brief's Day 1–2 plan and its Contractor pack v0 recommendation: *"find newly active/local remodelers that fit ContractorOps and book a demo"* is the named best candidate for the first seven days, specifically because Johnson can personally judge fit and the brief assumes an existing SERP pipeline is already in place.

Filling in what the brief leaves open (flagged individually):

- **Target entities:** Local remodeling/general-contracting businesses (residential remodel, not new-build, not purely commercial) — **NOT SPECIFIED — REQUIRES VALIDATION**: exact trade scope (does "remodeler" include kitchen/bath specialists, whole-home, ADU builders?) needs one line from Johnson.
- **Geographic scope:** Bay Area, per the brief's own example. **PROPOSED DECISION:** start with 2–3 counties (e.g., Alameda + Santa Clara + San Mateo) rather than the whole metro, so CSLB county filtering and city permit lookups stay tractable in a week.
- **Minimum information required (PROPOSED DECISION, MVP floor):** legal/DBA business name, CSLB license number + status + classification, city/county of record, at least one of (phone, website, Google/Yelp listing), and one freshness-bearing fact (license issue/renewal date, or a "why now" signal if available).
- **Useful evidence:** an active, non-expired CSLB license in a relevant classification (B, or a remodeling-adjacent specialty); a live business web presence; physical presence in the target counties.
- **Timing ("why now") signal:** the brief doesn't mandate one for the contractor MVP — day-1 goal is to *validate the loop*, not require a signal on day one. **PROPOSED DECISION:** treat a timing signal as a *scoring boost*, not a hard gate, for v0. Candidates: recently issued/renewed CSLB license, a new business registration, active hiring posts, or a recent permit under the business's name if the city portal is queryable. **NOT SPECIFIED — REQUIRES VALIDATION:** whether Johnson's demo pitch is time-sensitive enough to need a signal at all, or whether "actively licensed and locally operating" is a sufficient bar for v0.
- **Fit information:** license classification match, county/city match, business still active (not suspended/revoked).
- **Contact identification:** business phone from CSLB or the business's own site; a named decision-maker (owner/principal) is a stretch goal, not an MVP requirement, since CSLB does not publish emails (see Part 4).
- **Unnecessary for v0 (PROPOSED DECISION):** revenue estimates, employee counts, review sentiment analysis, multi-source corroboration beyond one primary + one corroborating source, and anything freight- or insurance-specific.

**Validation process** for anything left ambiguous above: run the Day 3 blind-scoring exercise (Part 19) with Johnson before locking these definitions — his agreement/disagreement on 50–100 candidates *is* the validation, cheaper than debating definitions in the abstract.


---

## PART 4 — US public data landscape

Every entry below marked **WEB-RESEARCHED** was checked live (queries run September 23, 2026); pricing/terms for commercial products change often — re-verify before integrating, don't trust this table past a few months.

### 4.1 Federal — entity identity & contracting

| Source | What it contains | API? | Auth | Cost | Freshness | Best for |
|---|---|---|---|---|---|---|
| **SAM.gov Entity Management API** | Registered federal vendors/contractors: legal name, UEI, CAGE code, status, NAICS, points of contact | Yes — `api.sam.gov/entity-information/v3/entities` (v4 also live) | Free public API key via SAM.gov account | Free | Near real-time on registration changes | Identity + fit for any entity that does or wants federal work |
| **SAM.gov Opportunities API** | Active/archived federal contract notices: solicitations, sources-sought, awards | Yes — `api.sam.gov/opportunities/v2/search`, filterable by NAICS/state/date | Same free API key | Free, but daily rate limits apply | Updated continuously | **Timing signal** — a fresh solicitation/award in a relevant NAICS+state is a strong "why now" for contractors and freight alike |
| **SAM.gov Exclusions API** | Debarred/excluded parties | Yes — `entity-information/v4/exclusions` | Same key | Free | — | Compliance gate, not a lead source |
| **SEC EDGAR (submissions + XBRL company facts)** | Public-company filings, facility/risk disclosures, structured financials | Yes — `data.sec.gov/submissions/CIK{n}.json`, `data.sec.gov/api/xbrl/companyfacts/CIK{n}.json` | None — keyless, but SEC requires a descriptive `User-Agent` with contact email and paced requests ("fair access") | Free | Filing-driven (quarterly/annual/8-K event-driven) | Public-company identity, facilities, and event signals (freight shipper discovery, insurance carrier-side fit) |
| **Census Bureau Building Permits Survey (BPS)** | **Aggregate** counts/valuation of new residential permits by state/county/CBSA/permit-issuing place | Yes, via `data.census.gov`/economic indicators API | None for basic access | Free | Monthly + annual | **Market-level** construction-activity context, NOT company- or address-level. Do not expect lead-level records here — see caution below. |
| **EPA ECHO Web Services** | Compliance/violation/inspection/enforcement history for 800,000+ regulated facilities (CAA, CWA, RCRA, SDWA) | Yes — public web services + bulk ZIP downloads | None — no key, no registration | Free | Rolling, per-program cadence | Facility identity + regulatory-event signals for contractor/industrial/freight verticals |

### 4.2 Freight/trucking-specific

| Source | What it contains | API? | Auth | Cost | Notes |
|---|---|---|---|---|---|
| **FMCSA QCMobile API** | Real-time carrier safety/identity data (USDOT, MC, operating status, equipment) | Yes — REST, `mobile.fmcsa.dot.gov` | Free key, requires a login.gov account | Free | This is the correct *programmatic* path — use it instead of scraping SAFER's HTML |
| **SAFER Company Snapshot** | Same underlying data, single-carrier ad-hoc lookup | No API — web form only | None for search | Free (full "company profile" report is a paid add-on) | Fine for spot-checks; not a bulk source — use QCMobile for automation |
| **BTS Freight Analysis Framework (FAF)** | Freight flows by origin/destination/commodity | Bulk data files | None | Free | Market-sizing / lane hypotheses only — no entity or contact data |

### 4.3 State/local — contractor & business identity

| Source | What it contains | API? | Auth | Cost | Notes |
|---|---|---|---|---|---|
| **CSLB Public Data Portal (California)** | ~243,000 CA contractor licenses: classification, status, bond, workers' comp, business address/phone, county | **No official REST API.** CSLB publishes a downloadable **Master List** bulk file, refreshed **weekly** | None to download the master list | Free | **Legally important:** CSLB does **not** publish contractor email addresses — California B&P Code §27 prohibits it. Any vendor claiming to sell CSLB emails is not sourcing them from CSLB. Cancelled/revoked/non-renewable-expired licenses are excluded from the master list at the source. |
| **California Secretary of State — bizfile Online** | 17M+ CA corporation/LLC/LP registration records: name, entity number, status, filing history, registered agent | **No confirmed official public developer API** — bizfile Online (`bizfileonline.sos.ca.gov`) is a free web *search portal*, not a documented REST API | N/A for the free portal | Free portal / paid document orders | The brief refers to a "business-entity public API guide" — **this needs direct validation against sos.ca.gov before you build against it.** Third-party KYB vendors (e.g., Signzy, OpenCorporates) resell programmatic access by aggregating state portals; that's a buy decision, not a free integration. Some other states (e.g., NY, TX) do publish bulk entity files — check per state, don't assume CA's pattern generalizes. |
| **City/county building permit portals** | Address-level permits: permit type, valuation, contractor of record, issue date | Varies wildly — Socrata-backed cities (e.g., data.sfgov.org, data.sacramento.gov) expose Socrata Open Data APIs; many counties have neither API nor bulk export | Varies | Usually free | Highest-value timing signal for contractors (permit names the contractor directly) but requires a **per-jurisdiction adapter** — no national standard. This is where the "generalized platform" temptation lives; resist it for v0 (Part 14). |
| **EPA ECHO** | (see 4.1) | | | | Applies here too for contractor-adjacent industrial/environmental fit signals |

### 4.4 Real estate

| Source | What it contains | API? | Access model | Notes |
|---|---|---|---|---|
| **RESO Web API** | The *transport standard* (OData 4.x profile) that ~90% of the US's 489 MLSs use to expose listing data, per RESO's own certification tracking (**WEB-RESEARCHED**, reso.org) | Yes, as a standard — but RESO itself runs no production API and holds no listing data | Each MLS/broker issues its own credentials under its own data-license agreement | **Critical distinction the brief already makes correctly:** RESO standardizes the *field names and transport*; it grants **zero** listing rights. You cannot "integrate RESO" — you integrate a specific MLS after Johnson (or ContractorOps) signs a data agreement. Treat as a Tier 3/legal-review item unless real estate becomes an active vertical. |
| **ATTOM Data API** | Property ownership, valuation, mortgage, sales/deed history — 155M+ US properties | Yes, REST, self-serve developer portal exists | Commercial, quote-based pricing (**WEB-RESEARCHED** — no public price list; "contact sales," transaction-based tiers) | Buy, not build, if/when real estate is prioritized |
| **County assessor/recorder portals, Socrata** | Parcel, ownership, transaction records | Varies per county; Socrata (`dev.socrata.com`) standardizes the *query layer* for counties that use it, not the underlying schema | Free where offered | Same per-jurisdiction adapter problem as permits |

### 4.5 Insurance

| Source | What it contains | API? | Access model | Notes |
|---|---|---|---|---|
| **NIPR Producer Database (PDB)** | Insurance producer licensing/appointment/regulatory-action records, all 50 states + territories | NIPR advertises custom APIs "to meet your unique needs" (**WEB-RESEARCHED**, nipr.com) | **Subscriber/contract-gated**, not open. Individuals get one free self-report per 12 months; commercial bulk access is a paid subscription | LEGAL REVIEW REQUIRED before any integration — this sits inside state insurance-licensing law |
| **NAIC company lookup / state DOI datasets** | Licensed carrier identity | Portal-based, varies by state | Mostly free to search | Weak on its own; combine with timing signals from elsewhere |

### 4.6 General B2B / cross-vertical

| Source | What it contains | API? | Access | Notes |
|---|---|---|---|---|
| **Google Places API (New)** | Business discovery: name, address, phone, hours, category, ratings | Yes | Per-SKU pricing since March 2025 (**WEB-RESEARCHED**, developers.google.com, verified pricing table dated 2026-07-03): Text/Nearby Search **Pro tier $32.00/1,000 calls** after 5,000 free/month; Place Details Essentials $5.00/1,000 after 10,000 free/month. Adding fields like rating/hours bumps you to Enterprise ($35–40/1,000). | Model actual MVP call volume against this before assuming "cheap" — at a few hundred candidates/day this is trivial; at scale it isn't. |
| **Yelp Fusion API** | Business discovery + reviews | Yes | **Pricing is unsettled/conflicting in current sources** (**WEB-RESEARCHED**): one set of docs shows a free tier (5,000 calls/day) plus paid usage tiers ($7.99–$14.99/1,000 calls); a separately verified source (dated July 2026) shows Yelp's Fusion/Places API now costs **$229–$643/month** with an evaluation-only trial, and a reseller-gated Leads API. **Verify directly against business.yelp.com/fusion before committing** — treat as likely-paid for planning purposes. | Use Google Places or CSLB/SOS as primary identity sources; treat Yelp as supplementary, not load-bearing, until pricing is confirmed. |
| **Company websites / sitemaps** | First-party description, services, sometimes contact/staff | No API — polite fetch | Free, subject to robots.txt and ToS | Best source for services offered and a live "is this business real and active" check |
| **Job postings** | Hiring signals (expansion, new capacity) | Varies (Indeed/LinkedIn scraping is generally against ToS; some aggregators offer licensed feeds) | Mostly paid/licensed if done at scale | Timing signal, not identity |

**Caution flagged explicitly (INFERENCE from 4.1–4.6):** several sources in the brief's text are aggregate/market-level, not lead-level (Census BPS, BTS FAF). Don't let "we have a permit dataset" quietly become "we have a per-contractor permit feed" — those are different engineering problems with very different effort.


---

## PART 5 — Source prioritization framework

**PROPOSED DECISION.** Rather than a numeric score (which invites false precision on sources you've barely tested), categorize each candidate source along four qualitative dimensions, then tier by the combination:

- **Lead-level usefulness:** does this source name a specific entity you can act on, or only describe a market?
- **Access reality:** official free API → licensed bulk/export → free portal, no API → paid/commercial API → scrape-only. (This mirrors the brief's own scraping decision rule in Part 10 — reuse it here rather than inventing a second scale.)
- **Integration effort:** hours (official API, stable schema) / days (bulk file + per-jurisdiction adapter) / weeks+ (browser automation, legal review pending).
- **Signal type:** identity, fit, timing, or contact — a source can serve more than one.

### TIER 1 — build/integrate for the contractor MVP
- **SAM.gov Entity + Opportunities APIs** — free, official, stable, gives identity and a timing signal (contract awards/solicitations) that generalizes to freight later. *Why now:* lowest integration cost of anything in Part 4, and it's the one source useful to both verticals.
- **CSLB Master List (bulk file)** — free, official, weekly refresh, directly matches the contractor MVP's identity/fit requirement. *Why now:* it's the actual backbone of the v0 target list.
- **Google Places API (Text Search Pro + Place Details)** — paid but cheap at MVP volume, gives corroborating identity (phone, address, active-business signal) and a natural entity-resolution anchor (address/phone match against CSLB). *Why now:* CSLB alone won't confirm a business is still operating day-to-day.
- **Company website fetch** — free, gives a live-business check and services-offered text for the evidence card. *Why now:* near-zero cost, high corroboration value.
- **EPA ECHO** — free, official, no key — cheap to wire in even if only used opportunistically for industrial-adjacent contractor signals. *Why now:* effort is trivial relative to potential signal value.

### TIER 2 — useful after MVP validates
- **FMCSA QCMobile API** — not needed until freight pack v0 starts (Part 19, Day 6), but integrate early in that phase since it's free and official.
- **City/county permit portals for the 2–3 target counties** — real timing-signal upside for contractors, but per-jurisdiction adapters take real engineering time; defer until the MVP loop itself is proven, then invest here specifically because it's the evidence type competitors (per the brief's "what incumbents miss") tend to skip.
- **SEC EDGAR** — low relevance to residential contractors, high relevance once freight (public shippers) or a B2B vertical needs public-company facts.
- **Bulk state-entity files where they exist** (some states publish these; CA does not appear to, per Part 4) — evaluate per state as new geographies open up.

### TIER 3 — interesting, not needed now
- **RESO/MLS access** — real legal/commercial lift (data-license agreement per MLS) for a vertical (real estate) that isn't active yet. Revisit only if real estate becomes a prioritized pack.
- **ATTOM, NIPR/NAIC, Yelp Fusion (paid tier)** — all commercial, quote-based, or legally gated; not worth the procurement/legal cycle until a specific vertical or gap in Tier 1/2 coverage justifies it.
- **Commercial contact/email enrichment vendors** — the brief is explicit: buy for coverage, benchmark on a labeled sample first, never treat as ground truth. Not a v0 need since the contractor MVP's contact requirement is a business phone, not a verified email.


---

## PART 6 — Data acquisition architecture

**PROPOSED DECISION**, adapted from the brief's own collection-architecture sketch (its `discover → fetch → preserve raw → parse/extract → normalize → resolve entity → validate → score → qualify → publish` pipeline) with layer boundaries made explicit:

```
SOURCE (SAM.gov, CSLB, Google Places, county portal, company site)
   │
   ▼
DISCOVERY            — turns a goal-contract target into a query plan per source
   │
   ▼
FETCH                — HTTP client per source-connector; respects rate limits, robots, auth
   │
   ▼
RAW SNAPSHOT         — immutable copy: bytes + retrieval time + content hash + source_record_id
   │                    (stored before any parsing — nothing is ever discarded/overwritten here)
   ▼
PARSE / EXTRACT      — source-specific: JSON field mapping, HTML/DOM extraction, or LLM extraction
   │                    for unstructured text (job postings, site copy) — versioned extractor code
   ▼
NORMALIZE            — canonical field names/units/formats (this is where CSLB's "classifications"
   │                    and Google's "types" become one internal taxonomy)
   ▼
ENTITY RESOLUTION    — dedupe/merge into a stable Entity; keeps every contributing source_record_id
   │
   ▼
VALIDATE             — schema checks, plausibility checks (license not expired, address geocodes)
   │
   ▼
EVIDENCE / CLAIMS    — raw normalized fields become Claims: source, timestamp, confidence,
   │                    observed_or_inferred, expires_at
   ▼
QUALITY / FRESHNESS  — per-field TTL check, corroboration count, completeness score
   │
   ▼
PUBLISH              — structured record + evidence bundle delivered to the main system (Part 17)
```

**Layer boundaries, stated explicitly because this is where scope creep happens:**
- *Fetch* never mutates data — it only retrieves bytes and hands them to Raw Snapshot. This is what makes re-extraction possible later without re-fetching (important once CSLB or Google changes a field name and you need to backfill from history).
- *Extract* is allowed to use an LLM (e.g., pulling a "services offered" list from unstructured site copy); *Normalize* and *Validate* should be deterministic code, per the brief's own working rule #13 ("prefer deterministic systems for validation, normalization, deduplication, gates, and policy enforcement; use LLMs where semantic extraction actually adds value").
- *Entity Resolution* sits **before** qualification scoring — you cannot score a duplicate coherently.
- *Publish* is the only layer that talks to the main system. Everything upstream of it is internal to your service; this keeps the integration contract (Part 17) small and stable even as your internal pipeline evolves.

This is not forced to be a literal microservice-per-box architecture for v0 — **PROPOSED DECISION:** for the 7-day MVP, implement this as a single Python process with clearly separated modules (Part 16), not distributed services. Split into real services only once volume or team size demands it.


---

## PART 7 — Data model

**PROPOSED DECISION**, built from the brief's own schema sketch (`RawSnapshot`, `Claim`, `Entity`, `IdentityEdge`, `ContactPoint`), split into MVP vs. future.

### MVP schema

**`Entity`**
- *Purpose:* the canonical business/organization record everything else attaches to.
- *Key fields:* `entity_id` (stable, internal), `canonical_name`, `entity_type` (contractor/carrier/shipper/…), `primary_address`, `county`, `state`, `status` (active/inactive/unknown), `created_at`.
- *Relationships:* has many `Claim`s, many `ContactPoint`s, many `RawSnapshot`s (via Claims); may have `IdentityEdge`s to other Entities pending merge review.
- *Example:* `{entity_id: "ent_9f2a", canonical_name: "Acme Roofing LLC", entity_type: "contractor", county: "Alameda", state: "CA", status: "active"}`
- Fields needing timestamps: `created_at`, `last_seen_at`. Fields needing provenance: none directly — provenance lives on the Claims, not the Entity summary row.

**`RawSnapshot`**
- *Purpose:* immutable, source-verbatim capture — the thing you can always re-derive from.
- *Key fields:* `snapshot_id`, `source`, `source_record_id`, `retrieved_at`, `content_hash`, `license_policy`, `raw_content` (or a pointer to object storage).
- *Relationships:* referenced by one or more `Claim`s via `source_snapshot_id`.
- Every field here is observed-not-inferred by definition; `retrieved_at` and `content_hash` are mandatory.

**`Claim`**
- *Purpose:* one fact, with full provenance — the brief's evidence-first model made literal.
- *Key fields:* `entity_id`, `field`, `value`, `observed_or_inferred`, `confidence`, `valid_from`, `observed_at`, `expires_at`, `source_snapshot_id`, `extractor_version`.
- *Example:* `{entity_id: "ent_9f2a", field: "cslb_license_status", value: "active", observed_or_inferred: "observed", confidence: 1.0, observed_at: "2026-09-20", expires_at: "2026-10-20", source_snapshot_id: "snap_1123", extractor_version: "cslb_parser_v1"}`
- *Which fields need expiry:* all of them — even "observed" facts decay (a license status is only as fresh as the last CSLB refresh). Set per-field-type TTLs (Part 8).
- Never overwritten: a new observation creates a **new** Claim row; the old one stays for history/drift analysis (per the brief's working rule #10 — "never let an LLM overwrite an observed value without keeping both versions").

**`IdentityEdge`**
- *Purpose:* records a candidate match between two raw records/entities before/after merge.
- *Key fields:* `entity_a`, `entity_b`, `match_features` (e.g., `{name_similarity: 0.94, address_match: true, phone_match: false}`), `confidence`, `review_state` (`auto_merged` / `pending_review` / `rejected`).
- MVP entity resolution should default new matches below a high-confidence threshold to `pending_review`, not silent auto-merge (Part 9).

**`ContactPoint`**
- *Purpose:* a channel to reach the entity or a person at it.
- *Key fields:* `entity_id` (or `person_id` — MVP can skip a separate Person table and attach contacts to Entity directly), `channel` (phone/email/website), `value`, `verification_state`, `verified_at`, `source`, `consent_or_suppression_state`.
- For the contractor MVP, expect this table to mostly hold `channel: "phone"` and `channel: "website"` rows sourced from CSLB and Google Places — **not** email, since CSLB doesn't publish it and you're not buying an enrichment vendor for v0.

### Future schema (not needed for MVP — noted so you don't accidentally build it early)
- A separate `Person` entity (decision-maker identification) — only needed once contact discovery goes beyond "business phone."
- `Signal` as a first-class table distinct from `Claim` (Part 12) — MVP can represent a signal as a Claim with a short TTL and a `signal_type` field; promote it to its own table once signal volume/variety grows.
- `Consent`/suppression as a dedicated table with jurisdiction-aware rules — needed before insurance or any regulated-channel outreach, not for CSLB-sourced contractor phone numbers.
- Multi-source corroboration scoring as a derived materialized view — v0 can compute this on read.


---

## PART 8 — The evidence-first model

**SOURCE-DERIVED**, made concrete. Instead of storing a conclusion, store the chain that produced it:

```
ENTITY → FACT (Claim) → SOURCE (RawSnapshot) → TIMESTAMP → CONFIDENCE → OBSERVED/INFERRED → EXPIRATION
```

**Example 1 — an observed fact:**
```json
{
  "entity": "Acme Roofing LLC",
  "field": "cslb_license_status",
  "value": "active",
  "observed_or_inferred": "observed",
  "confidence": 1.0,
  "source": "CSLB Master List, 2026-09-20 refresh",
  "retrieved_at": "2026-09-20T04:00:00Z",
  "expires_at": "2026-10-20T00:00:00Z",
  "extractor_version": "cslb_parser_v1"
}
```

**Example 2 — an inferred fact:**
```json
{
  "entity": "Acme Roofing LLC",
  "field": "services_offered",
  "value": ["kitchen remodel", "bathroom remodel", "ADU conversion"],
  "observed_or_inferred": "inferred",
  "confidence": 0.82,
  "source": "acmeroofing.com/services, fetched 2026-09-18",
  "retrieved_at": "2026-09-18T11:02:00Z",
  "expires_at": "2026-12-18T00:00:00Z",
  "extractor_version": "site_copy_llm_extractor_v2",
  "extraction_note": "LLM-summarized from unstructured page copy; not a structured field on the source page"
}
```

**Example 3 — a timing signal:**
```json
{
  "entity": "Acme Roofing LLC",
  "field": "signal.cslb_license_renewed",
  "value": true,
  "observed_or_inferred": "observed",
  "confidence": 1.0,
  "source": "CSLB Master List, 2026-09-20 refresh vs. 2026-08-20 refresh",
  "retrieved_at": "2026-09-20T04:00:00Z",
  "expires_at": "2026-10-04T00:00:00Z",
  "signal_type": "timing"
}
```

**Why the split matters downstream (main-system consumption):** the qualification engine's hard gates should only ever key off `observed_or_inferred: "observed"` facts with confidence above a set floor — an LLM's guess at "services offered" is useful for personalization copy, not for a compliance or fit gate. The evidence card (Part 13) shown to Johnson should visually separate observed facts from inferred ones, so he's never trusting a guess without knowing it's a guess. Expiry drives re-fetch scheduling on your side, not just display — a Claim past its `expires_at` should trigger a re-fetch of that field before it's used in a fresh qualification pass.


---

## PART 9 — Entity resolution

**PROPOSED DECISION — MVP approach, deliberately simple:**

1. **Deterministic matching first.** Normalize business name (lowercase, strip legal suffixes like "LLC"/"Inc", strip punctuation) and compare against: (a) exact CSLB license number if both records carry one, (b) normalized phone number, (c) normalized street address. Any one exact match on (a)/(b)/(c) → high-confidence auto-merge candidate.
2. **Fuzzy matching second**, only for records with no deterministic match: name similarity (token-set ratio) above a threshold (e.g., 0.9) **and** same county/city. Fuzzy-only matches never auto-merge — they create an `IdentityEdge` with `review_state: pending_review`.
3. **Confidence bands (PROPOSED DECISION):**
   - Deterministic match on license number or exact phone → confidence 0.95+, auto-merge.
   - Deterministic match on normalized address only → confidence 0.75, auto-merge but flag for spot-check (addresses collide more than phone numbers — strip malls, shared suites).
   - Fuzzy name match only → confidence 0.5–0.7, `pending_review`, never auto-merge.
4. **Review states:** `auto_merged`, `pending_review` (surfaced in whatever review UI the main system or a simple internal script provides), `rejected` (a human said "these are different businesses" — keep this decision recorded so the same pair doesn't get re-flagged every run).
5. **Duplicate handling:** once merged, the "losing" record's Claims are re-pointed to the canonical `entity_id`; the merge itself is logged (which two entity_ids, when, confidence, who/what approved it) so it's reversible.
6. **Canonical entity creation:** the first record seen for a genuinely new business becomes the canonical Entity; nothing fancier is needed for v0.

**What NOT to build yet:** a trained ML matching model, cross-vertical identity resolution (a contractor entity and a freight shipper entity are never the same kind of match problem — don't try to unify the tables), or automatic conflict resolution when two merged sources disagree on a field value (surface the conflict, don't silently pick one — this is exactly the "never overwrite an observed value" rule from Part 7 applied to merges).


---

## PART 10 — Web crawling / scraping strategy

**SOURCE-DERIVED hierarchy, adopted as-is** (the brief states this decision rule and this plan agrees with it): official API → licensed bulk/export → customer-authorized integration → polite public-page fetch → browser automation only when permitted and necessary. Computer use does not make prohibited scraping acceptable; paywalls, CAPTCHAs, and technical controls are boundaries, not puzzles to solve.

**Applied to your actual Tier 1/2 sources:**
- SAM.gov, FMCSA QCMobile, EPA ECHO, SEC EDGAR → official API. Use it.
- CSLB → licensed/official **bulk export** (the Master List file) — not the search form, not a per-license scrape.
- Google Places → official paid API. Use it; don't scrape Google Maps as a substitute (ToS-violating and unreliable).
- Company websites → polite public-page fetch: respect `robots.txt`, identify your fetcher with a real User-Agent and contact info (mirroring SEC EDGAR's own "fair access" requirement), cache aggressively, and never fetch pages behind a login.
- County permit portals → varies per jurisdiction; check for an API/export first (Socrata-backed cities have one), fall back to polite fetch of public search results only where ToS allows, browser automation only as a last resort and only after the specific portal's terms are checked.

**For every source, before writing a connector, record:**
official API/export available? auth/customer-authorization needed? terms on automation, caching, derived data, redistribution? robots directives and rate limits? personal/sensitive data involved? update cadence and deletion obligations? can the claim be corroborated elsewhere? — this is the brief's own checklist; keep it as a literal per-source YAML/config entry, not tribal knowledge (see Part 16, `sources/*/policy.yaml`).

**Request management, PROPOSED DECISION for MVP scale (low hundreds of entities/day):**
- Per-source rate limiting via a simple token-bucket, configured per source (respect each API's documented limits — SAM.gov's daily caps in particular).
- Retries with exponential backoff (e.g., 3 attempts, 2/4/8s) on transient errors (5xx, timeouts); no retry on 4xx except 429.
- Conditional requests (`If-Modified-Since`/ETag) where a source supports them, to cut refresh cost on CSLB's weekly file and city portals.
- Deduplication at fetch time using `content_hash` — if a re-fetch returns byte-identical content, skip re-parsing.
- A dead-letter table for fetches that fail repeatedly, reviewed manually rather than silently dropped.
- Basic monitoring: fetch success/failure counts per source per run, alert (even just a log line/Slack message for v0) on a source's failure rate crossing a threshold — this catches a source silently changing its HTML/schema before it corrupts your data quietly.

**When browser automation is genuinely necessary:** only for a source with no API/export and no acceptable ToS-compliant fetch path, and only after Part 11's legal check. For v0, this should be **zero** sources — everything in Tier 1 has an API or bulk export. If a Tier 2 county portal turns out to need it, treat that as a deliberate, reviewed decision, not a default.


---

## PART 11 — Legal / compliance / data-use boundaries

**Not legal advice — flagged per item where LEGAL REVIEW REQUIRED applies.**

| Concept | Meaning | Applies to |
|---|---|---|
| Publicly accessible | Anyone can view it without a login | CSLB master list, SAM.gov, EPA ECHO, most city permit portals |
| Publicly reusable | Accessible **and** the publisher's terms permit downstream use | Government data generally yes (public records); commercial sites' terms vary — check each |
| API-accessible | A documented programmatic interface exists | SAM.gov, FMCSA, EPA ECHO, SEC EDGAR, Google Places (paid), CSLB (bulk file, not API) |
| Licensed | Requires a signed agreement to access at all | RESO/MLS data, NIPR PDB, most enrichment vendors |
| Scrapable (technically) | No technical block prevents fetching it | True for many sites; **not the same as legally permitted** |
| Redistributable | You may pass the data to others (including the main system, which is fine internally, but *externally* — e.g., in a sold list — is a different question) | Government public-record data generally yes; scraped commercial-site content generally no without explicit permission |
| Commercially usable | Using it to generate revenue (which this whole project is) is permitted | Government sources generally yes; check each commercial API's ToS for "no resale"/"no lead-gen" clauses specifically |

**Per major source category:**
- **CSLB Master List:** public record, free, explicitly published for reuse (this is the point of the portal). **Do not** attempt to source contractor emails and claim they came from CSLB — B&P Code §27 prohibits CSLB from publishing them, so any such claim would be false and any such data would be from an unverified third party.
- **SAM.gov / FMCSA / EPA ECHO / SEC EDGAR:** federal public data, explicitly designed for programmatic reuse, free. SEC EDGAR specifically requires a compliant `User-Agent` header — this is a technical ToS term, not optional courtesy.
- **Google Places API:** commercial terms apply — Google's ToS historically restricts certain uses (e.g., pre-fetching/caching results beyond permitted windows, or using results to build a competing places database). **LEGAL REVIEW REQUIRED** before assuming you can cache Place Details indefinitely; check the current Google Maps Platform ToS at integration time, not from this document.
- **CA bizfile / Secretary of State data generally:** public record for the search itself; bulk/programmatic access model unconfirmed for California specifically (Part 4) — **LEGAL REVIEW REQUIRED** if you build anything beyond ad-hoc portal lookups here.
- **RESO/MLS, NIPR/NAIC, ATTOM:** all licensed/commercial. **LEGAL REVIEW REQUIRED** before any integration — these involve signed data agreements, not terms-of-use you accept by clicking through.
- **Company websites:** publicly accessible, technically scrapable; redistribution/reuse rights vary per site's terms. Extracting factual business information (services offered, address) for lead qualification is lower-risk than reproducing substantial original content; don't store or forward large verbatim chunks of a company's marketing copy — extract facts, not prose.
- **Personal/sensitive data:** none of the Tier 1 sources involve personal data in the sensitive sense (health, financial account numbers, etc.) — they're business-entity records. If contact discovery ever extends to named individuals (owners/principals), that becomes personal data subject to different handling (consent/suppression tracking, Part 7's future schema) — **LEGAL REVIEW REQUIRED** at that point, and especially before any outreach touches a personal (vs. business) contact channel.
- **Insurance vertical specifically** (per the brief, echoed here because it's the strongest warning in the source document): state producer licensing, approved product/jurisdiction, disclosure, consent, and do-not-contact rules are **not** an implementation afterthought — they gate whether you can enter the vertical at all. Do not build insurance-vertical scraping ahead of that legal review.


---

## PART 12 — Signal extraction ("why now")

**PROPOSED DECISION**, signal categories mapped to sources you actually have in Tier 1/2:

| Signal type | Source | Evidence | Confidence approach | Expiry |
|---|---|---|---|---|
| New/renewed CSLB license | CSLB weekly diff | Compare this week's master list to last week's | Observed, high confidence | ~2 weeks (recency is the whole point) |
| New federal solicitation/award in relevant NAICS+geography | SAM.gov Opportunities API | Direct API field | Observed, high confidence | Until solicitation closes / award date passes |
| New EPA ECHO enforcement/inspection event | EPA ECHO diff | Compare snapshots | Observed, high confidence | Event-dated, doesn't really "expire" but relevance decays — treat as low-priority signal after ~90 days |
| Business still actively listed/open | Google Places (`isClosed` equivalent field, active listing) | Direct field | Observed, high confidence | Re-check monthly |
| Hiring activity | Job postings (if a licensed feed is used) | Posting date + role | Observed for the posting, inferred for "this means growth" | ~30–60 days |
| New permit under business name | City/county portal (Tier 2, per-jurisdiction) | Permit record | Observed, high confidence | Permit-type dependent; a building permit stays relevant longer than a small trade permit |

**Structure for every signal (matches Part 8's evidence model exactly — a signal is a Claim with a `signal_type`):** signal type, source, evidence (the underlying Claim/snapshot), timestamp, expiry, confidence, entity relationship, observed-vs-inferred.

**How the qualification engine should consume these (main-system responsibility, noted here so your output format serves it):** signals should be additive to the score, not a replacement for fit/identity gates — a fresh permit on a business with an expired license is not a good lead. The brief's own Contractor pack v0 recommendation deliberately doesn't require a signal to define an MVP-qualified lead (an active, locally-operating, correctly-classified license is enough to test the loop); treat signals as what upgrades a "pursue" candidate to a "pursue now," not as a v0 hard requirement (see Part 3).


---

## PART 13 — Contractor MVP, concretely

**PROPOSED DECISION**, pulling together Parts 3, 4, and 12 into one buildable target.

- **Exact target:** Active, licensed general/remodeling contractors (CSLB classification B, plus C-classifications commonly used in remodel work — e.g., C33 painting, C36 plumbing, if Johnson's ICP includes trade-specific remodelers — **NOT SPECIFIED, confirm exact classification list with Johnson**).
- **Geography:** Alameda, Santa Clara, San Mateo counties (PROPOSED starting scope).
- **Candidate discovery:** pull the CSLB Master List filtered to target classifications + counties; this is your candidate seed list (deterministic, not a search-API guess).
- **Required sources for v0:** CSLB (identity, license status, classification, address, phone) + Google Places (corroboration: is this business still active/discoverable, matching address/phone) + company site fetch where a website exists (services text, live-business check).
- **Required fields:** business legal/DBA name, CSLB license number + status + classification + issue/expiry dates, county, phone, address, website (if found), Google Places match confidence.
- **Required signals (optional/boost, not gate):** license renewed within the last 60 days; SAM.gov award/solicitation match (unlikely for small residential remodelers but free to check); nothing else for v0.
- **Qualification inputs handed to the main system:** all of the above as Claims, plus an entity-resolution confidence score if CSLB and Google Places records were merged.
- **Evidence requirements:** every field above traceable to its source snapshot; no field presented without a timestamp.
- **Contact requirements:** business phone number, minimum; website if available. No email requirement for v0 (per Part 4/11 — CSLB doesn't have it, and buying an enrichment vendor is out of scope for a 7-day validation).
- **Output format:** one evidence-bearing record per candidate, in the schema from Part 7, delivered via whatever mechanism Part 17 settles on.

**Example lead:**
```json
{
  "entity_id": "ent_9f2a",
  "canonical_name": "Acme Roofing LLC",
  "county": "Alameda",
  "cslb_license_number": "1000002",
  "cslb_classification": "B",
  "cslb_status": "active",
  "phone": "+1-510-555-0134",
  "website": "https://acmeroofing.com",
  "google_places_match_confidence": 0.93,
  "recommendation": "pursue",
  "reason_codes": ["active_license", "classification_match", "county_match", "website_confirms_active"]
}
```

**Example evidence card (what Johnson should be able to see for any candidate, per the brief's own "lead evidence card" concept in its closing section):**
> **Acme Roofing LLC** — Alameda County — CSLB #1000002 (Active, Class B)
> - License status: *Active* — source: CSLB Master List, retrieved 2026-09-20. [Observed, confidence 1.0]
> - Business phone: 510-555-0134 — source: CSLB Master List. [Observed]
> - Website confirms active operation, lists kitchen/bath remodel services — source: acmeroofing.com, fetched 2026-09-18. [Observed: page exists and is live; Inferred: service list, LLM-extracted, confidence 0.82]
> - Google Places match: same address/phone, 4.3★, "open" — source: Google Places API, 2026-09-19. [Observed]
> - No timing signal detected this run.
> - **Recommendation: pursue** — reason codes: active license, classification match, county match, corroborated by two independent sources.


---

## PART 14 — What NOT to build initially

| Don't build | Why not now | Build instead | When it becomes justified |
|---|---|---|---|
| Universal US company database | Months of effort before any lead ships; the brief itself warns against a "universal contact database" | A narrow, source-specific pipeline for the exact contractor MVP target | Only if/when many verticals need the same national identity layer — not before at least two verticals are proven |
| Universal scraper / hundreds of connectors | Most named sources (Tier 1) have official APIs — a generalized scraping platform solves a problem you mostly don't have yet | Per-source connectors, each ~a day of work, added one at a time as Tiers unlock | When you're integrating your 6th+ per-jurisdiction portal with genuinely repeated structure (e.g., many Socrata-backed cities) |
| Full autonomous browser agent for data acquisition | No Tier 1 source needs it; building a robust computer-use runtime is itself a multi-week project and arguably the main system's, not yours (Part 2) | Official APIs and bulk files only, for v0 | If a specific high-value Tier 2 source (e.g., a specific county permit portal) has no API/export and is worth the legal+engineering cost |
| Complex ML ranking/scoring model | You don't have labeled outcome data yet (Part 18), and the brief explicitly puts ranking logic in the main system's qualification engine, not yours | Deterministic reason-code tagging on your side; hand raw evidence + gate results to the main system | After the Day 3 labeling exercise produces a real gold set — and even then, it's plausibly still the main system's job, not yours |
| Self-learning scraper | Massive overkill for ~5 sources at MVP scale | Versioned extractors with manual review when a source's schema drifts | If source count and change frequency genuinely make manual maintenance a bottleneck |
| Multi-vertical abstraction before one vertical works | The brief's own riskiest-assumption #6: shared LLM calls aren't shared architecture if schemas/policies are all rewritten per vertical | Build the contractor pack concretely first; only extract shared code when freight actually needs the same piece | After Day 6/7's freight pack test shows what genuinely reuses vs. forks |
| Full CRM integrations | Not your layer's job (Part 2) | Publish clean records via the integration contract (Part 17); let the main system own CRM sync | Never, for this workstream specifically |
| Massive contact database | You need business phones for ~50–100 v0 candidates, not a national contact graph | Extract what each Tier 1 source legitimately provides | Only if a specific vertical's qualification bar requires verified personal contacts at scale, and only via a benchmarked, paid vendor per the brief's own guidance |


---

## PART 15 — Tech stack

**PROPOSED DECISION**, biased toward what a strong Python backend developer can ship in a week without new operational surface area.

| Need | Recommendation | Why | Needed in MVP? | Build/Buy/Wrap |
|---|---|---|---|---|
| HTTP client | `httpx` (async-capable) | Modern, typed, handles both sync and async cleanly; better default timeouts/retries story than raw `requests` | Yes | Wrap (library) |
| HTML parsing | `selectolax` or `BeautifulSoup4` | `selectolax` is much faster for the volume of company-site fetches; BS4 if you want more forgiving parsing and don't need speed yet | Yes | Wrap |
| Retries/backoff | `tenacity` | Declarative retry decorators, avoids hand-rolled backoff bugs | Yes | Wrap |
| Browser automation | **Not needed for v0** — if a Tier 2 source forces it later, Playwright over Selenium (faster, better async support) | No Tier 1 source requires it | No | Defer |
| Search API | Google Places API (New) directly | Already the Tier 1 choice; no need for a SERP-wrapper vendor at this volume | Yes | Buy (per-call) |
| Queue | Start with none — a single sequential/async pipeline run is enough at MVP volume (hundreds of candidates); if needed, `Redis` + `RQ` or `arq` (simpler than Celery for this scale) | Avoid infra you don't need yet | No (defer) | Wrap, if/when needed |
| Database | **PostgreSQL** (or SQLite for the very first days of local development, migrate to Postgres before Day 4's email-execution phase) | Relational model (Entity/Claim/RawSnapshot/IdentityEdge) is a natural fit; JSONB columns handle the flexible `match_features`/raw-content-pointer fields | Yes | Build on top of (open source) |
| Object storage | Local filesystem for v0; S3-compatible (or a Google Cloud Storage bucket, given no strong existing-cloud constraint) once raw snapshots grow past local-disk comfort | Raw HTML/JSON snapshots are exactly the kind of blob object storage is for | Defer past Day 2 if disk suffices | Buy (cloud) when needed |
| Caching | HTTP-level: `httpx` + a simple SQLite-backed cache keyed on URL+params for conditional requests; no separate cache service for v0 | Avoids introducing Redis just for caching at this scale | Yes, lightweight | Build (simple) |
| Scheduling | `cron` (or a simple `apscheduler` in-process) for the CSLB weekly refresh and periodic re-fetch of expiring Claims | No need for Airflow-class orchestration at 5 sources | Yes, minimal | Build (simple) |
| Observability | Structured logging (`structlog`) to start; a single dashboard is unnecessary before Day 5 — count fetch success/failure per source per run and log it | Enough to catch a source silently breaking without building a monitoring stack | Yes, minimal | Build (simple) |
| Data validation / schema | `pydantic` v2 models for every schema in Part 7 | Free validation, serialization, and a self-documenting contract for the Part 17 integration boundary | Yes | Wrap (library) |
| Schema management (DB migrations) | `alembic` (pairs with SQLAlchemy or raw `psycopg`) | Standard, avoids hand-rolled migration scripts | Yes | Wrap |
| LLM extraction | Claude via the Anthropic API, used narrowly (site-copy → services-offered extraction, unstructured job-posting parsing) | Matches working rule #13 — LLM only where semantic extraction adds value, not for normalization/validation | Yes, narrowly | Buy (API) |
| Embeddings / vector DB | **Not needed for v0.** Entity resolution at this scale is deterministic/fuzzy string matching (Part 9), not semantic search | — | No | Defer entirely — don't add a vector DB "just in case" |

**Build vs. buy vs. wrap, summarized:** build the pipeline glue and schema (it's your actual differentiated work); wrap well-maintained libraries for HTTP/parsing/validation/retries (no reason to hand-roll); buy the two APIs that cost money (Google Places, Anthropic) because they're cheaper than building equivalents; defer everything with real operational weight (queues, vector DBs, distributed orchestration, browser automation) until volume or a specific source genuinely demands it.


---

## PART 16 — Repository structure

**PROPOSED DECISION**, sized to a single-developer, single-process MVP (not a distributed-services layout you'd regret maintaining alone):

```
contractorops-data-layer/
├── src/
│   ├── sources/                 # one subfolder per source, each self-contained
│   │   ├── sam_gov/
│   │   │   ├── client.py        # thin API client
│   │   │   ├── policy.yaml      # Part 10's per-source checklist, as config
│   │   │   └── mapper.py        # raw response -> normalized fields
│   │   ├── cslb/
│   │   │   ├── loader.py        # downloads + parses the weekly Master List
│   │   │   ├── policy.yaml
│   │   │   └── mapper.py
│   │   ├── google_places/
│   │   │   ├── client.py
│   │   │   ├── policy.yaml
│   │   │   └── mapper.py
│   │   └── company_site/
│   │       ├── fetcher.py       # polite fetch + robots.txt check
│   │       └── extractor.py     # LLM-assisted services-offered extraction
│   ├── pipeline/
│   │   ├── snapshot.py          # RawSnapshot persistence
│   │   ├── normalize.py
│   │   ├── entity_resolution.py # Part 9 logic
│   │   ├── evidence.py          # Claim construction (Part 8)
│   │   ├── signals.py           # Part 12 logic
│   │   ├── quality.py           # freshness/corroboration scoring
│   │   └── run.py               # orchestrates one end-to-end pipeline run
│   ├── models/                  # pydantic models: Entity, Claim, RawSnapshot,
│   │   └── schema.py            # IdentityEdge, ContactPoint — the Part 7 schema, literally
│   ├── storage/
│   │   ├── db.py                # Postgres/SQLite connection + queries
│   │   └── blob.py              # raw-content storage (local disk → S3 later)
│   ├── publish/
│   │   └── contract.py          # Part 17's boundary — the only module the main system touches
│   └── config/
│       └── settings.py          # API keys, rate limits, per-vertical target definitions
├── tests/
│   ├── sources/                 # per-connector unit tests + fixture responses (schema-drift tests)
│   ├── pipeline/                # entity resolution, evidence construction tests
│   └── e2e/                     # one full run against recorded fixtures, asserting on output shape
├── data/
│   └── gold_sets/                # Part 18's labeled evaluation sets, versioned
└── scripts/
    └── run_contractor_pack.py    # CLI entrypoint for the v0 pipeline
```

**Responsibility of each top-level directory:** `sources/` isolates everything that changes when a data provider changes its API/schema — a breaking change should touch exactly one folder. `pipeline/` is the source-agnostic logic from Part 6's architecture diagram — it never imports anything from `sources/` directly except through the normalized shape each source's `mapper.py` produces. `models/` is the single place the Part 7 schema is defined, imported everywhere else. `publish/` is deliberately thin and is the only file that should need to change if the main-system integration contract changes. `config/` holds the vertical pack's target definition (Part 3's geography/classification list) as data, not hardcoded logic, so adding a county or classification doesn't require a code change.

**PROPOSED DECISION for the freight pack (Day 6):** it becomes `sources/fmcsa/`, `sources/bts_faf/`, etc., plus a second config target definition — reusing `pipeline/`, `models/`, and `publish/` unchanged. If that reuse doesn't hold in practice, that's the generalization finding the brief's Day 7 asks you to report.


---

## PART 17 — Interface with the main AI system

**PROPOSED DECISION.** Given this is two developers (you + whoever owns the main system) at MVP stage, favor the simplest contract that's still clean: **a REST endpoint your service exposes, plus a database/table the main system can also read directly for bulk queries** — not a queue or event bus, which is unjustified operational complexity for two developers and a few hundred records a day. Revisit toward events/queue only if the main system needs push notification of new evidence rather than pull.

**Research-request / response contract:**

Request (main system → your service):
```json
{
  "goal_contract_id": "gc_2026_09_20_bay_area_remodel",
  "entity": "Acme Roofing LLC",           // optional: specific entity to research
  "target_definition": {                   // optional: used for discovery runs instead
    "vertical": "contractor",
    "geography": ["Alameda", "Santa Clara", "San Mateo"],
    "classifications": ["B"]
  },
  "questions": [
    "is_license_active", "county_match", "has_live_website", "recent_signal"
  ]
}
```

Response (your service → main system):
```json
{
  "entity": {
    "entity_id": "ent_9f2a",
    "canonical_name": "Acme Roofing LLC",
    "county": "Alameda",
    "status": "active"
  },
  "claims": [
    { "field": "cslb_license_status", "value": "active", "observed_or_inferred": "observed",
      "confidence": 1.0, "observed_at": "2026-09-20", "expires_at": "2026-10-20",
      "source_snapshot_id": "snap_1123" }
  ],
  "signals": [],
  "contacts": [
    { "channel": "phone", "value": "+15105550134", "verification_state": "unverified", "source": "cslb" }
  ],
  "sources": [
    { "source": "cslb_master_list", "retrieved_at": "2026-09-20T04:00:00Z" },
    { "source": "google_places", "retrieved_at": "2026-09-19T18:20:00Z" }
  ],
  "recommendation": "pursue",
  "reason_codes": ["active_license", "classification_match", "county_match"]
}
```

**Why this shape:** it mirrors the brief's own sketch almost exactly, because that sketch is already good — claims and contacts are separate arrays (a contact is not just another field), every claim is self-contained with its own provenance (the main system never has to join back to your internal DB to know why it should trust a fact), and `recommendation`/`reason_codes` give the main system your layer's read without pretending to make its qualification decision for it (that's still the main system's call — you're handing it inputs and an opinion, not a verdict).

**Delivery mechanism, concretely:** a small FastAPI service exposing `POST /research` (single-entity) and `POST /discover` (target-definition-driven, returns a list), plus read access to the same Postgres tables for bulk/dashboard use if the main system prefers direct SQL for reporting. `pydantic` models from `models/schema.py` double as the request/response validation and the API's auto-generated schema — one definition, not two to keep in sync.

**NOT SPECIFIED — REQUIRES VALIDATION:** confirm with whoever owns the main system whether they'd rather pull via this API or have you push completed records into a shared table/queue they poll. Either works with the schema above; the choice is about *their* architecture preferences, not yours.


---

## PART 18 — Testing and data quality

**PROPOSED DECISION**, sized to what's achievable in the 7-day window while still being real evaluation, not vibes.

**Gold dataset:** 20 positive + 20 negative CSLB-sourced candidates, hand-labeled by Johnson before he sees any model/pipeline output (per the brief's Day 1 instruction) — this is the single most important artifact of week one, because every metric below is meaningless without it.

**Metrics to track from Day 3 onward:**
- **Precision at top-K** (top 10, top 20 of ranked/gated candidates) against the gold set — the brief's own bar: don't send at scale until top-20 clears ~80% agreement with Johnson's labels.
- **Duplicate rate** — how many published entities turn out to be the same business under manual review (tests Part 9's entity resolution).
- **Stale-field rate** — % of published Claims past their `expires_at` at publish time (should be ~0 if freshness checking is wired correctly).
- **Contact match rate** — % of candidates with at least one usable contact point.
- **Unsupported-claim rate** — % of published Claims with no `source_snapshot_id` or a broken one (should be exactly 0; this is a correctness bug, not a quality metric, if it's ever above 0).
- **Extraction accuracy** — for LLM-extracted fields specifically (services-offered), spot-check a sample against the actual source page.
- **Entity resolution accuracy** — sample `IdentityEdge`s at each confidence band, manually confirm merge/no-merge was correct.
- **Human minutes per accepted lead** — how long Johnson spends reviewing before accepting/rejecting a candidate; this is the metric that most directly tells you if the loop is actually saving him time.
- **Research cost** — Google Places + Anthropic API spend per candidate researched, tracked from day one so unit economics aren't a Day 20 surprise.

**Building the labeled set before scaling:** run the pipeline against ~50–100 CSLB candidates in the target counties, generate evidence cards, have Johnson label pursue/reject/borderline blind (without seeing your pipeline's own recommendation), then compare. Where you two disagree, look at *why* before assuming the model is wrong — Johnson's judgment is the ground truth you're trying to approximate, not a benchmark to beat.

**Regression / source / extraction tests, PROPOSED DECISION for what's actually worth writing in week one:**
- **Source schema tests:** for CSLB and SAM.gov specifically, a test that fetches a small real sample and asserts the expected fields are present — this is what catches a source silently changing its schema before it corrupts data (fits the dead-letter/monitoring approach from Part 10).
- **Extraction tests:** fixture-based (recorded HTML/JSON → expected normalized output) for each `mapper.py`, so a refactor doesn't silently break parsing.
- **Integration tests:** one real (rate-limit-respecting) call per source per test run, not per commit — CI can run these nightly rather than on every push.
- **End-to-end test:** one full pipeline run against a small fixed set of known CSLB license numbers, asserting the final published record shape matches Part 17's contract.
- **Drift monitoring:** not a separate system for v0 — the per-run fetch success/failure logging from Part 10 doubles as this; revisit a dedicated drift dashboard only past MVP.


---

## PART 19 — Execution roadmap

**PROPOSED DECISION**, phases scoped to your layer specifically (the brief's own 7-day plan is whole-system; this maps your slice onto it).

### PHASE 0 — Research and source mapping
- **Goal:** know exactly which sources you're integrating and why, before writing a connector.
- **Deliverables:** Parts 4–5 of this document, validated against live source docs (not just this write-up).
- **Tasks:** confirm SAM.gov API key works, confirm CSLB Master List download URL/format, confirm Google Places API key + billing set up, confirm target counties/classifications with Johnson.
- **Dependencies:** none — this can start immediately.
- **Definition of done:** you can fetch one real record from each Tier 1 source manually (curl/notebook), not yet through your pipeline.
- **Risks:** CSLB's master-list URL or format has changed since this document's research (Sept 2026) — verify directly at cslb.ca.gov before building the loader.
- **What NOT to do:** don't start writing entity-resolution or evidence-model code before you've actually seen real data from each source — schemas always have surprises.

### PHASE 1 — MVP acquisition pipeline
- **Goal:** CSLB + Google Places + company-site candidates flowing through fetch → snapshot → normalize → publish, unranked.
- **Deliverables:** working `sources/cslb`, `sources/google_places`, `sources/company_site`, `pipeline/snapshot.py`, `pipeline/normalize.py`.
- **Definition of done:** 50–100 real candidates in Postgres with normalized fields and raw snapshots preserved.
- **Risks:** CSLB weekly file may be large (~243K statewide records per Part 4's research) — filter early (county+classification) rather than parsing everything.

### PHASE 2 — Evidence + entity resolution
- **Goal:** every field is a Claim with provenance; CSLB/Google Places duplicates are merged.
- **Deliverables:** `pipeline/evidence.py`, `pipeline/entity_resolution.py`, populated `Claim`/`IdentityEdge` tables.
- **Definition of done:** the example evidence card from Part 13 can be generated for a real candidate.

### PHASE 3 — Signal extraction
- **Goal:** at least the CSLB-renewal and SAM.gov-award signals are detected and attached.
- **Deliverables:** `pipeline/signals.py`, a second week's CSLB snapshot to diff against the first.
- **Definition of done:** at least one real candidate shows a non-empty `signals` array with correct provenance.
- **Risks:** you need two weekly CSLB snapshots to compute a "renewed" signal — this phase is naturally gated by calendar time, not just engineering effort; plan around it rather than being surprised by it.

### PHASE 4 — Integration with main acquisition system
- **Goal:** the FastAPI `/research` and `/discover` endpoints are live and match Part 17's contract.
- **Deliverables:** `publish/contract.py`, a working API, a shared Postgres schema the main system can query.
- **Definition of done:** the main-system developer can pull a real candidate record end-to-end without asking you for help.

### PHASE 5 — Evaluation
- **Goal:** the Part 18 metrics are real numbers, not projections.
- **Deliverables:** the labeled gold set, precision@K, duplicate rate, unsupported-claim rate, cost-per-candidate.
- **Definition of done:** Johnson has blind-labeled 50–100 candidates and you can report top-20 precision against his labels.

### PHASE 6 — Second vertical / generalization test
- **Goal:** freight pack v0 built on the same `pipeline/`, `models/`, `publish/` — reuse measured, not assumed.
- **Deliverables:** `sources/fmcsa/`, a freight target-definition config, a report on what had to fork vs. what reused cleanly.
- **Definition of done:** a freight candidate record, in the same schema shape as the contractor one, published through the same `/research` endpoint.

### Day-by-day plan for the first 7 days (your slice of the brief's whole-system plan)

| Day | Your tasks |
|---|---|
| **1** | Confirm target counties/classifications with Johnson (Part 3). Get API keys: SAM.gov, Google Places, Anthropic. Manually fetch one real record from CSLB and Google Places. Set up Postgres + `models/schema.py` (Part 7 schema, literally, as pydantic models). |
| **2** | Build `sources/cslb/loader.py` (download + filter Master List to target counties/classifications) and `sources/google_places/client.py`. Wire both into `pipeline/snapshot.py` + `pipeline/normalize.py`. End of day: 50–100 raw+normalized candidates in Postgres. |
| **3** | Build `pipeline/entity_resolution.py` (CSLB↔Google Places matching) and `pipeline/evidence.py` (Claims with provenance). Generate evidence cards (Part 13 format) for the full candidate set. **Hand these to Johnson for blind labeling** — this is his Day 3 task per the brief, and your job is to have real evidence cards ready for it, not placeholders. |
| **4** | Compute precision@K against Johnson's labels. Fix whatever entity-resolution or normalization bugs the labeling exposed (there will be some — this is expected, not a failure). Start `sources/company_site` fetcher for live-business corroboration. |
| **5** | Build the `pipeline/signals.py` skeleton (even if the CSLB-renewal signal can't fire yet without a second weekly snapshot). Stand up the FastAPI `/research` endpoint against real data, so the main-system developer has something to integrate against by end of week. |
| **6** | Start `sources/fmcsa/` for the freight pack, reusing `pipeline/` and `models/` unchanged where possible. Note explicitly (in a short doc, per the brief's own instruction) anywhere the shared orchestration/schema had to fork — that note is itself a deliverable. |
| **7** | Compare contractor vs. freight: % shared code/schema, precision if freight candidates were also labeled, research cost per vertical. Write up findings for the "deepen contractor / deepen freight / revise the abstraction" decision — that decision itself belongs to Johnson and the main-system owner, not to you alone, but your data should drive it. |


---

## PART 20 — First 48 hours, concretely

**PROPOSED DECISION**, sequenced by dependency, not by the brief's generic order:

1. **Confirm scope with Johnson** (15 min, async is fine): exact CSLB classifications, exact starting counties, whether a timing signal is required for v0 or optional (Part 3's open questions).
2. **Get credentials:** SAM.gov public API key (self-service via SAM.gov account), Google Places API key + billing enabled, Anthropic API key. None of these should block on anyone else.
3. **Manually pull one real record from each Tier 1 source** — a `curl`/notebook exercise, not production code. Confirm CSLB's actual current Master List download URL/format directly at cslb.ca.gov (this document's research is from Sept 2026 and formats do change).
4. **Stand up Postgres locally** (or a small managed instance) and write `models/schema.py` as pydantic models matching Part 7 exactly — `Entity`, `RawSnapshot`, `Claim`, `IdentityEdge`, `ContactPoint`.
5. **Write `sources/cslb/loader.py`:** download the Master List, filter to target counties + classifications, store one `RawSnapshot` per license record, output normalized `Entity`+`Claim` rows.
6. **Write `sources/google_places/client.py`:** for each CSLB candidate, a Text Search or Place Details call to corroborate name/address/phone/active-status; store as `RawSnapshot` + `Claim`s.
7. **Produce the first evidence-bearing records:** run the pipeline end-to-end on the filtered candidate set, generate 5–10 evidence cards by hand (Part 13's format) to sanity-check the shape before scaling to the full 50–100.
8. **Commands/artifacts checklist for end of Day 2:** a `git` repo matching Part 16's layout; a `.env.example` listing required API keys; a `scripts/run_contractor_pack.py` that runs the full pipeline for the current target definition; a Postgres dump or query output showing real candidate rows with populated Claims.

Deviate from this sequence only if Phase 0's manual source checks (step 3) turn up something the brief/this document got wrong (e.g., CSLB's download format has changed) — fix that before building on top of an assumption that's already false.


---

## PART 21 — Research outputs to produce

**PROPOSED DECISION — minimum useful set**, trimmed from the brief's full list to what actually earns its keep in week one:

1. **This document** — Public Data Source Map + Source Evaluation Matrix + Data Schema + Scraping Architecture + Signal Taxonomy combined, since splitting them into five separate files at this stage creates sync overhead with no reader benefit yet.
2. **API/Connector specification** — living `policy.yaml` per source (Part 16), which is more useful than a separate prose spec because it's the thing the code actually reads.
3. **Sample dataset** — the 50–100 real, evidence-bearing contractor candidates from Day 2–3, handed to Johnson for labeling. This is the actual proof-of-work artifact for the week.
4. **Data quality report** — the Part 18 metrics computed against Johnson's labels, written up as a short doc once real numbers exist (Day 4–5).
5. **Technical README** — how to run the pipeline, what each source needs (API keys), how to add a new county/classification to the target definition — written once the pipeline is stable enough that instructions won't be stale in two days.

**Deliberately not producing separately in week one:** a standalone "Evidence Schema" doc (it's Part 7/8 of this document and the actual pydantic code — a third copy would drift), a standalone "MVP Implementation" writeup (the code + README is the implementation), a formal "Scraping Architecture" diagram beyond Part 6's (redrawing it in a diagramming tool adds no information).


---

## PART 22 — Risks and failure modes

Qualitative levels (Low/Medium/High) — not statistical probabilities.

| Risk | Probability | Impact | Detection | Mitigation | Fallback |
|---|---|---|---|---|---|
| CSLB changes Master List format/URL | Low-Medium | High (blocks primary source) | Source schema test (Part 18) fails | Version the parser, keep a fixture of the last known-good format | Fall back to CSLB's live search form for a manual spot-check while the loader is fixed |
| Google Places pricing/ToS changes | Low-Medium | Medium (cost or legal exposure) | Billing alerts; periodic ToS re-read | Cap daily API spend; re-verify ToS before any caching decision | Reduce corroboration to company-site fetch only if Places becomes unaffordable |
| Yelp Fusion pricing genuinely at $229–643/mo (per Part 4's conflicting research) | Medium | Low (Yelp is supplementary, not load-bearing) | Direct check at business.yelp.com/fusion before integrating | Don't integrate Yelp for v0 at all | Google Places + company site already cover the identity-corroboration need |
| CA SOS has no usable programmatic path (per Part 4's flagged ambiguity) | Medium | Low for v0 (CSLB is the primary identity source, not SOS) | Direct check at bizfileonline.sos.ca.gov / sos.ca.gov developer docs | Treat SOS as manual-lookup/corroboration only, not a pipeline source, until confirmed | None needed — v0 doesn't depend on it |
| Duplicate entities inflate candidate count | Medium | Medium (wastes review time, skews precision metrics) | `IdentityEdge` review-state audit (Part 18) | Conservative auto-merge thresholds (Part 9); manual spot-check of `pending_review` edges | Slightly higher human-review load until thresholds are tuned |
| False/weak signals | Medium | Medium (erodes trust in the system) | Compare signal-flagged candidates against Johnson's blind labels specifically | Keep signals additive to score, never a hard gate, for v0 (Part 12) | Disable a specific signal type if it's shown to correlate poorly with real fit |
| Hallucinated LLM extraction (services-offered, etc.) | Medium | Medium (bad inferred Claims) | Spot-check sample against source page (Part 18) | Keep `observed_or_inferred` strict; never let inferred fields feed hard gates (Part 8) | Fall back to raw extracted text with no LLM summarization if accuracy is poor |
| Incorrect entity matching at scale | Low-Medium | High (wrong business = wasted outreach downstream) | Entity-resolution accuracy sampling (Part 18) | Deterministic-first matching, conservative fuzzy thresholds (Part 9) | Manual review queue for anything below auto-merge confidence |
| Infrastructure cost surprise | Low at MVP scale | Low-Medium | Track cost-per-candidate from Day 1 (Part 18) | Cheap defaults (SQLite→Postgres, no queue/vector DB until needed, Part 15) | Throttle Google Places / Anthropic call volume if costs spike |
| Overengineering (building Part 14's "don't build" list anyway) | Medium — this is the most likely failure mode for a strong engineer working solo | Medium (burns the 7-day window on infrastructure instead of evidence) | Explicit daily check against Part 19's day-by-day plan | Part 14's table, referenced deliberately before starting any new component | Cut scope back to the literal Day-by-day plan if behind schedule |
| Insufficient signal volume for contractors specifically | Medium | Low for v0 (per Part 3, signals are a boost, not a gate) | Compare "pursue" rate with vs. without signal boost | Design v0 to work with zero signals present, per the brief's own contractor-pack framing | None needed if v0's qualification bar doesn't require a signal |
| Poor generalization to freight | Medium — this is a deliberate test, not really a "failure" if it happens | Low (it's designed-for information, per the brief) | % shared code/schema, measured explicitly (Part 19, Day 7) | None — a fork is a valid finding | Document why, feed into the "revise the abstraction" decision |


---

## PART 23 — Questions to ask the project owner

**PRODUCT**
- Is an active, correctly-classified CSLB license in the target counties sufficient to define "qualified for outreach" for v0, or does Johnson want a timing signal required before a candidate is shown to him? (Part 3)
- Exact CSLB classification list ContractorOps actually wants (B only, or specific C-classifications for remodel-adjacent trades)?
- What does "book a demo" require as a handoff — just a phone number, or does the main system need a named contact before it will attempt outreach?

**DATA**
- Does the main system need a verified email at all for v0, or is phone-only acceptable given CSLB doesn't publish emails and buying enrichment is out of scope this week?
- Should the starting geography be exactly Alameda/Santa Clara/San Mateo, or does Johnson have a different county priority based on where ContractorOps already has traction?

**TECHNICAL**
- Pull (main system queries your API/DB) or push (you write to a shared table/queue) — see Part 17's open item?
- Where should raw snapshots live long-term — local disk is fine for a week, but who owns the object-storage decision once volume grows?

**LEGAL**
- Confirm current Google Places API ToS permit the caching/reuse pattern this plan assumes (Part 11) — worth a 15-minute read of the current terms before Day 2's build, not after.
- If contact discovery ever needs to go beyond business phone to a named individual, who signs off on the consent/suppression handling that requires (Part 7's future schema, Part 11)?

**OPERATIONS**
- Who owns API-key/credential management and billing alerts across SAM.gov, Google, and Anthropic — you, or a shared account?
- What's the actual cadence Johnson can commit to for the Day 3 blind-labeling exercise — this plan assumes he can turn around 50–100 labels within a day of receiving evidence cards; if that's not realistic, the whole week's schedule shifts.

**INTEGRATION**
- What does the main-system developer actually need from you by end of week to unblock their own Day 4–5 work (email execution, reply handling)? Confirm this doesn't silently require your `/research` endpoint earlier than Part 19's Day 5 plan assumes.
- Is the freight pack (Day 6) actually in scope for this specific week, or is it acceptable to defer if the contractor MVP itself runs long — the brief frames it as a generalization test, not a hard deadline.


---

# SINGLE SOURCE OF TRUTH

**1. Project objective.** Build a data acquisition + evidence layer that supplies ContractorOps' autonomous acquisition system with trustworthy, fresh, provenance-backed information about potential contractor (then freight) customers — proving the acquisition loop on a narrow contractor MVP before generalizing.

**2. My responsibility.** Discovery, source research, connector building, extraction, normalization, entity resolution, evidence/provenance, freshness, signal detection, contact discovery (where legitimately available), data quality, and publishing structured records to the main system.

**3. System boundary.** Not mine: orchestration/planning, qualification decision logic, channel/timing policy, outreach execution, CRM workflow, business strategy, UI, or the general computer-use runtime.

**4. Initial use case.** Active, correctly-classified CSLB-licensed remodeling contractors in Alameda/Santa Clara/San Mateo counties — identity and fit from CSLB, corroboration from Google Places and company sites, a timing signal treated as a boost, not a gate.

**5. Data requirements.** Per candidate: legal/DBA name, CSLB license number/status/classification, county, phone, website if available, entity-resolution confidence, and every field's source/timestamp/confidence.

**6. Source strategy.** Official APIs and bulk exports first (SAM.gov, FMCSA, EPA ECHO, SEC EDGAR, CSLB Master List), paid official APIs where free isn't available (Google Places), polite ToS-compliant fetch for company sites, browser automation deferred entirely for v0.

**7. Source priority.** Tier 1 (build now): SAM.gov, CSLB, Google Places, company-site fetch, EPA ECHO. Tier 2 (after MVP): FMCSA, city/county permit portals, SEC EDGAR. Tier 3 (not needed now): RESO/MLS, ATTOM, NIPR/NAIC, paid Yelp, contact-enrichment vendors.

**8. Architecture.** `source → discovery → fetch → raw snapshot → parse/extract → normalize → entity resolution → validate → evidence/claims → quality/freshness → publish`, implemented as one Python process for v0, split into services only when volume demands it.

**9. Data model.** `Entity`, `RawSnapshot`, `Claim`, `IdentityEdge`, `ContactPoint` — pydantic models backed by Postgres. Every fact is a Claim with source, timestamp, confidence, observed-or-inferred, and expiry; nothing is overwritten, only superseded.

**10. Evidence model.** `ENTITY → FACT → SOURCE → TIMESTAMP → CONFIDENCE → OBSERVED/INFERRED → EXPIRATION`, exactly as specified in Part 8, with worked examples for observed facts, inferred facts, and signals.

**11. Signal model.** CSLB license renewal (weekly diff), SAM.gov solicitation/award match, EPA ECHO enforcement events, live-website confirmation — all additive to the score, none a hard gate for v0.

**12. Scraping strategy.** Official API → licensed bulk/export → customer-authorized integration → polite public fetch → browser automation only when nothing else works and legal review clears it. Zero v0 sources require browser automation.

**13. Tech stack.** Python, `httpx`/`selectolax`/`tenacity` for fetch/parse/retry, Postgres + `alembic`, `pydantic` for schema, FastAPI for the integration endpoint, Claude API for narrow LLM extraction, structured logging for observability. No queue, no vector DB, no browser runtime for v0.

**14. Repository structure.** `src/sources/` (per-connector), `src/pipeline/` (source-agnostic logic), `src/models/` (the schema), `src/publish/` (the one module the main system touches), `src/config/` (target definitions as data), `tests/`, `data/gold_sets/`.

**15. Main-system integration contract.** A `POST /research` and `POST /discover` REST API returning `{entity, claims[], signals[], contacts[], sources[], recommendation, reason_codes[]}`, per Part 17 — with a shared Postgres schema available for direct query if preferred over the API.

**16. Testing strategy.** A 20-positive/20-negative gold set labeled blind by Johnson before Day 3; precision@K, duplicate rate, stale-field rate, unsupported-claim rate, entity-resolution accuracy, human-minutes-per-accepted-lead, and cost-per-candidate tracked from Day 1. Source-schema tests, extraction fixture tests, and one real end-to-end test per source.

**17. MVP scope.** CSLB + Google Places + company-site pipeline for the target counties/classifications, entity resolution, evidence Claims, one optional signal type, published through the `/research` API — no email, no browser automation, no ranking model, no second vertical until Day 6.

**18. Out of scope (for now).** Universal company database, universal scraper, full browser agent, ML ranking model, self-learning scraper, cross-vertical abstraction before contractor works, CRM integrations, contact-database purchasing.

**19. Seven-day execution plan.** Day 1: scope + credentials + schema. Day 2: CSLB + Google Places pipeline live, 50–100 raw candidates. Day 3: entity resolution + evidence cards, handed to Johnson for blind labeling. Day 4: precision@K measured, bugs fixed, company-site fetcher added. Day 5: signals skeleton + `/research` API live for the main-system developer. Day 6: freight pack v0 (FMCSA), reuse vs. fork noted explicitly. Day 7: contractor-vs-freight comparison written up for the deepen/deepen/revise decision.

**20. Definition of done (for this week).** 50–100 real, evidence-bearing contractor candidates in Postgres; a measured precision@K against Johnson's blind labels; a working `/research` API the main-system developer has actually queried; a documented freight-pack attempt with an explicit reuse/fork finding — not a polished platform, a validated (or invalidated) loop.

**21. Open questions.** See Part 23 in full — the two that block Day 1 specifically are the exact CSLB classification list and whether a timing signal is required for v0.

**22. Risks.** See Part 22 in full — the two most likely to actually bite in week one are CSLB format drift (verify directly before building the loader) and overengineering (the strongest pull for a solo engineer with a week and a big brief — Part 14's table exists specifically to be checked against, daily, not just read once).