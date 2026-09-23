# ContractorOps Data Acquisition & Evidence Layer — Codebase File Specification

**Purpose of this document:** a file-by-file build spec for the data-acquisition/evidence subsystem described in the source planning documents (`01-data-acquisition-execution-plan.md` and `02-data-acquisition-architecture-spec.md`, both derived from the Sept 22, 2026 "Autonomous customer acquisition" brief). This document does not contain code. It exists so that a developer or a coding LLM can generate each file correctly on the first pass — what it's for, what it depends on, what it exports, what its output looks like, and exactly where it sits in the pipeline.

**Conventions carried over from the source documents:**
- `SOURCE-DERIVED` — stated directly in the brief or planning docs.
- `PROPOSED ARCHITECTURAL DECISION` — an implementation choice made in the architecture spec, not dictated by the brief.
- `NOT SPECIFIED — REQUIRES DECISION` — the source material is genuinely silent; flagged rather than invented.
- Where the two execution-plan variants disagree on a name (e.g. `RawSnapshot` vs. `SourceRecord` for the same table, or exact target counties), this document uses the **architecture spec's** naming (`RawSnapshot`, file path `raw/snapshot_store.py`) as canonical, since that is the document the repository structure is actually drawn from, and notes the variant name once here rather than repeating it per file.

---

## 1. Repository Tree (canonical, from architecture spec §6)

```
data-acquisition/
├── src/
│   ├── api/
│   │   ├── contracts.py
│   │   └── research_api.py
│   ├── orchestration/
│   │   └── run_coordinator.py
│   ├── sources/
│   │   ├── base.py
│   │   ├── cslb/
│   │   │   ├── connector.py
│   │   │   ├── parser.py
│   │   │   └── fixtures/
│   │   ├── ca_sos/
│   │   │   ├── connector.py
│   │   │   └── parser.py
│   │   ├── company_site/
│   │   │   ├── connector.py
│   │   │   └── parser.py
│   │   └── google_places/          # Tier 2 / future
│   │       └── connector.py
│   ├── fetch/
│   │   ├── http_fetcher.py
│   │   ├── rate_limiter.py
│   │   └── browser_fetcher.py      # stub only, v0
│   ├── raw/
│   │   └── snapshot_store.py
│   ├── extract/
│   │   ├── deterministic.py
│   │   └── llm_extractor.py
│   ├── normalize/
│   │   ├── names.py
│   │   ├── addresses.py
│   │   ├── phones.py
│   │   └── domains.py
│   ├── entities/
│   │   ├── resolver.py
│   │   └── review_queue.py
│   ├── evidence/
│   │   ├── claim_store.py
│   │   └── freshness.py
│   ├── signals/
│   │   ├── rules.py
│   │   └── types.py
│   ├── publish/
│   │   └── result_builder.py
│   ├── storage/
│   │   └── db.py
│   ├── config/
│   │   ├── source_policies.py
│   │   └── settings.py
│   └── observability/
│       └── logging.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── e2e/
├── scripts/
│   └── backfill_cslb_county.py
└── docs/
```

No file outside this tree should be created for v0. `sources/google_places/` and `fetch/browser_fetcher.py` exist only as reserved seams (Tier 2 / future) — see their entries below for exactly what "stub" means.

---

## 2. Canonical Data Model

Every file that touches persistence references one or more of these six tables. Defined once here; do not redefine elsewhere in the codebase (architecture spec §43: "Do not invent additional top-level entities without updating [Part 7] first").

### `Entity`
The canonical business/organization record everything else attaches to.
| Field | Notes |
|---|---|
| `entity_id` (a.k.a. `stable_id`) | Stable, internal, primary key |
| `canonical_name` | Resolution *output*, not a raw field — produced by `entities/resolver.py` |
| `entity_type` | e.g. `contractor` (vertical-specific; freight pack will add `carrier`/`shipper`) |
| `primary_address`, `county`, `state` | |
| `domain` | Normalized company website domain; used as an entity-resolution join key |
| `status` | `active` / `inactive` / `unknown` |
| `created_at`, `last_seen_at` | Timestamps only — provenance lives on `Claim`, not here |

Relationships: has many `Claim`, many `ContactPoint`, many `Signal`; many `RawSnapshot` indirectly via `Claim.source_snapshot_id`; may have `IdentityEdge`s to other entities pending merge review.

### `RawSnapshot` (a.k.a. `SourceRecord` in the execution-plan variants)
Immutable, source-verbatim capture. Never overwritten, never deleted.
| Field | Notes |
|---|---|
| `snapshot_id` | Primary key |
| `source` | e.g. `cslb`, `ca_sos`, `company_site` |
| `source_record_id` | The source's own identifier for this record, if any |
| `retrieved_at` | Mandatory |
| `content_hash` | SHA-256 of the raw payload; mandatory — used for conditional re-fetch and dedup |
| `license_policy` | Which access-terms bucket this fetch falls under (Part 11 of the execution plan) |
| `raw_payload_ref` | Pointer into object storage, or inline `raw_content` for small payloads |

Every field on this table is observed-not-inferred by definition.

### `Claim`
One fact, with full provenance — the evidence-first model made literal.
| Field | Notes |
|---|---|
| `entity_id` | FK → `Entity` |
| `field`, `value` | e.g. `field="cslb_license_status", value="active"` |
| `observed_or_inferred` | Non-nullable; `"observed"` or `"inferred"` |
| `confidence` | 0.0–1.0 |
| `valid_from`, `observed_at`, `expires_at` | Freshness fields; every claim type has an expiry, no exceptions |
| `source_snapshot_id` | FK → `RawSnapshot`; mandatory, never null |
| `extractor_version` | e.g. `cslb_parser_v1`, or for LLM-derived claims, model id + prompt-version string |

**Never overwritten.** A new observation creates a new `Claim` row; the old one stays for history/drift analysis.

### `IdentityEdge`
A candidate match between two records/entities, pending or resolved.
| Field | Notes |
|---|---|
| `entity_a`, `entity_b` | The two entities/records being compared |
| `match_features` | e.g. `{name_similarity: 0.94, address_match: true, phone_match: false}` |
| `confidence` | |
| `review_state` | `auto_merged` / `pending_review` / `rejected` |

### `ContactPoint`
A channel to reach the entity.
| Field | Notes |
|---|---|
| `entity_id` (or `person_id`, future) | |
| `channel` | `phone` / `email` / `website` |
| `value` | |
| `verification_state` | Set by *discovery* only as `unverified` in v0 — never `verified` by this subsystem (verification is main-system territory, see §Contact Architecture below) |
| `verified_at`, `source`, `consent_or_suppression_state` | |

### `Signal`
A timing ("why now") event, derived from one or more `Claim`s.
| Field | Notes |
|---|---|
| `entity_id`, `signal_type` | e.g. `signal_type="cslb_license_renewed"` |
| `evidence_ref` | Points back to the observed `Claim` that justified the signal |
| `observed_at`, `expires_at`, `confidence` | |
| `observed_or_inferred` | The underlying event is usually `observed`; the *meaning* of the event (e.g. "this implies expansion") is a separate, additional inferred layer — never collapsed into one row |

**MVP note:** `Signal` may be represented as a `Claim` with a `signal_type` field instead of a separate table for the very first cut (execution-plan variant #1, Part 7) — the architecture spec treats it as its own table (`signals/types.py`). Build the dedicated table; it is the version the file inventory (§44 of the architecture spec) and the ERD are built around.

---

## 3. Main-System Integration Contracts

Two request shapes exist across the source documents, corresponding to two endpoints (`POST /research`, single entity; `POST /discover`, target-definition-driven). Both are handled by `api/contracts.py` / `api/research_api.py`.

**`ResearchRequest` — single-entity form (`POST /research`):**
```json
{
  "request_id": "req_01HXYZ",
  "entity_hint": {"name": "Bayview Remodeling Inc.", "domain": null},
  "questions": ["license_status", "classification", "fit_evidence", "contact"]
}
```

**`ResearchRequest` — discovery form (`POST /discover`):**
```json
{
  "goal_contract_id": "gc_2026_09_20_bay_area_remodel",
  "target_definition": {
    "vertical": "contractor",
    "geography": ["Alameda", "Santa Clara", "San Mateo"],
    "classifications": ["B"]
  },
  "questions": ["is_license_active", "county_match", "has_live_website", "recent_signal"]
}
```

**`ResearchResult`** (returned by both endpoints — the canonical publish contract, `schema_version` included from day one even while it's `"1"`):
```json
{
  "schema_version": "1",
  "entity": { "entity_id": "ent_9f2a", "canonical_name": "Bayview Remodeling Inc.", "county": "Alameda", "status": "active" },
  "claims": [ { "field": "cslb_license_status", "value": "active", "observed_or_inferred": "observed",
                "confidence": 0.95, "observed_at": "2026-09-20", "expires_at": "2026-10-20",
                "source_snapshot_id": "snap_1123", "extractor_version": "cslb_parser_v1" } ],
  "signals": [],
  "contacts": [ { "channel": "phone", "value": "+15105550134", "verification_state": "unverified", "source": "cslb" } ],
  "sources": [ { "source": "cslb_master_list", "retrieved_at": "2026-09-20T04:00:00Z" } ],
  "recommendation": "pursue",
  "reason_codes": ["active_license", "classification_match", "county_match"]
}
```
`recommendation`/`reason_codes` are this subsystem's *opinion*, never a qualification *decision* — the main system's qualification engine owns the actual gate/score logic. `result_builder.py` must never compute anything resembling a lead score beyond reason-coded tags.

Error responses: a structured `{error_code, message, request_id}` — never a silent empty result.

---

## 4. File-by-File Specification

### 4.1 `src/api/contracts.py`
- **Layer:** API. **MVP:** Yes.
- **Purpose:** Defines the pydantic request/response models for the two endpoints — `ResearchRequestSingle`, `ResearchRequestDiscover`, `ResearchResult`, and the error-response shape — per §3 above.
- **Responsibilities:** Schema definition and validation only; also generates the API's auto-documentation (FastAPI reads these models directly).
- **Does NOT do:** No business logic, no DB access, no parsing.
- **External dependencies:** `pydantic` v2.
- **Internal imports:** none (this is the lowest-level contract file; `models/schema.py`-equivalent fields for `Claim`/`Signal`/`ContactPoint` should be imported from wherever the six canonical tables (§2) are defined as pydantic models, so contract objects and DB objects share one definition rather than drifting).
- **Imported by:** `api/research_api.py`.
- **Inputs:** none (type definitions only).
- **Outputs / exports:** the pydantic classes listed above, including a `schema_version` constant.
- **Testing requirements:** schema validation tests — a request missing `request_id` or with an unknown field shape should fail validation, not pass through silently.
- **Connection to rest of codebase:** this is the one file whose shape both the main AI system and this subsystem must agree on; changing it after integration begins requires a versioned migration, not a silent breaking change (architecture spec §43).

### 4.2 `src/api/research_api.py`
- **Layer:** API. **MVP:** Yes.
- **Purpose:** The subsystem's entry point. Exposes `POST /research` (single-entity, synchronous) and `POST /discover` (target-definition-driven, returns a list) as a small FastAPI service; also exposes read access to the same Postgres tables for the main system's bulk/reporting use if it prefers direct SQL.
- **Responsibilities:** Accept and validate a `ResearchRequest`, hand it to `orchestration/run_coordinator.py`, return the resulting `ResearchResult`(s); implement idempotency — resubmitting the same `request_id` returns the cached result if still fresh rather than re-running the pipeline.
- **Does NOT do:** No parsing, no scoring/qualification, no orchestration logic beyond calling the coordinator.
- **External dependencies:** `FastAPI` (or equivalent ASGI framework), `pydantic`.
- **Internal imports:** `api/contracts.py`, `orchestration/run_coordinator.py`.
- **Imported by:** nothing internal — this is the boundary the main AI system calls.
- **Inputs:** HTTP `ResearchRequest` JSON body.
- **Outputs:** HTTP `ResearchResult` JSON body, or a structured `{error_code, message, request_id}` on failure — never a silent empty 200.
- **Configuration:** none directly; relies on `config/settings.py` for anything environment-specific (port, DB connection passed through to the coordinator).
- **Connection to rest of codebase:** this is the only module the main AI system talks to. Everything else in the repository is internal to this subsystem (execution plan Part 6: "Publish is the only layer that talks to the main system... this keeps the integration contract small and stable even as your internal pipeline evolves" — `research_api.py` plays that same externally-facing role at the API layer, backed by `publish/result_builder.py` internally).

### 4.3 `src/orchestration/run_coordinator.py`
- **Layer:** Orchestration. **MVP:** Yes.
- **Purpose:** The thin, deterministic sequencer for one research request — **not** an agent, not the main system's planner. Sequences: discover → fetch → raw snapshot → parse → extract → normalize → entity resolution → validate → evidence/claim → signal → publish, for one request.
- **Responsibilities:** Look up the right connector(s) via `sources/base.py`'s registry, drive each pipeline stage in order, track per-request state, hand the resolved entity + claims to `publish/result_builder.py` at the end.
- **Does NOT do:** No qualification/scoring, no source-specific logic (must never branch on `if source == "cslb"` — that belongs inside connectors), no persistence of its own beyond what each stage's own module does.
- **External dependencies:** none beyond what its called modules require.
- **Internal imports:** `sources/base.py` (registry/connector lookup), `extract/deterministic.py` and `extract/llm_extractor.py` (via connectors), `entities/resolver.py`, `evidence/claim_store.py`, `signals/rules.py`, `publish/result_builder.py`.
- **Imported by:** `api/research_api.py`.
- **Inputs:** a validated `ResearchRequest` (entity-hint or target-definition form).
- **Outputs:** triggers persistence at each stage; ultimately produces an `entity_id` that `result_builder.py` reads from to build the `ResearchResult`.
- **State:** per-request run state only (in-memory or in the job table, §4.15 `storage/db.py`); no long-lived state of its own.
- **Error handling:** propagates the error taxonomy defined in the architecture spec §24 (`SourceUnavailable`, `SchemaChanged`, `PolicyViolation`, etc.) up to the API layer as structured errors; does not swallow failures silently.
- **Connection to rest of codebase:** this is the pipeline's backbone — the box in the architecture diagram between "API layer" and every processing stage. It is what makes the pipeline "source-agnostic core" true: it never imports anything from a specific `sources/<name>/` module directly, only through the registry.

### 4.4 `src/sources/base.py`
- **Layer:** Sources. **MVP:** Yes.
- **Purpose:** Defines the `SourceConnector` protocol/interface and the source registry. Nothing source-specific lives here — it is a seam, not a framework.
- **Responsibilities:** Declare the interface every connector must implement (`discover`, `fetch`, `parse`, `source_metadata`); provide `register_connector(name, connector)` and `get_connector(name) -> SourceConnector`, backed by an in-memory dict populated at startup from `config/source_policies.py`.
- **Does NOT do:** No HTTP calls, no parsing logic, no persistence.
- **External dependencies:** `pydantic` (for metadata typing) — nothing else.
- **Internal imports:** none below it in the dependency graph.
- **Imported by:** every `sources/<name>/connector.py`, and `orchestration/run_coordinator.py` (to look up the right connector for a request).
- **Key types/interfaces exported:**
  - `SourceMetadata` — `name`, `source_type` (`api` / `bulk_export` / `page_fetch`; **no `browser` type is implemented in v0**, only reserved), `auth_required`, `rate_limit_policy`.
  - `CandidateRef` — an opaque, per-source discovery result (e.g. "the CSLB export URL for classification B, Alameda county").
  - `SourceConnector` protocol — `discover(params) -> list[CandidateRef]`, `fetch(candidate_ref) -> RawSnapshot`, `parse(raw_snapshot) -> list[ParsedRecord]`, `source_metadata` property.
- **Error handling:** `get_connector` on an unknown name raises a clear `UnknownSourceError` — never a silent `None`.
- **Testing requirements:** unit test that registration/lookup works and that an unknown source raises.
- **Implementation notes:** resist adding plugin-discovery/auto-registration machinery for three sources — a static dict is a deliberate `PROPOSED ARCHITECTURAL DECISION` (architecture spec §9), not an oversight.

### 4.5 `src/sources/cslb/connector.py`
- **Layer:** Sources. **MVP:** Yes. **Source type:** `page_fetch` (no official API exists for CSLB).
- **Purpose:** Implements `SourceConnector` for the CSLB Public Data Portal — California contractor license identity, status, classification, address, phone.
- **Responsibilities:** Build the correct portal export URL/query for a given `(classification, county)`; drive the fetch via `fetch/http_fetcher.py`; hand raw bytes to `raw/snapshot_store.py`; call `sources/cslb/parser.py`.
- **Does NOT do:** No normalization, no entity resolution, no claim generation — those happen downstream.
- **External dependencies:** none beyond the shared HTTP client used by `http_fetcher.py`.
- **Internal imports:** `fetch/http_fetcher.py`, `raw/snapshot_store.py`, `sources/cslb/parser.py`.
- **Imported by:** `orchestration/run_coordinator.py` (via the registry), `scripts/backfill_cslb_county.py`.
- **Inputs:** `(classification, county)` discovery params.
- **Outputs / exports:** `discover(classification, county) -> CandidateRef`; `fetch(candidate_ref) -> RawSnapshot` (persisted); `parse(raw_snapshot) -> list[ParsedCSLBRecord]`.
- **Key type exported:** `ParsedCSLBRecord` — `license_number, business_name, classification, status, address, county, phone, bond_info, wc_info`.
- **State:** none held in the connector; relies on `snapshot_store` for persisted state. Fetch is idempotent given the same `candidate_ref` within the freshness TTL window — returns the cached snapshot rather than re-fetching.
- **Error handling:** distinguishes `SourceUnavailable` (retryable), `SchemaChanged` (not retryable, immediate alert — the highest-priority alert in the system), `PolicyViolation` (robots disallow — stop the connector, alert).
- **Observability:** logs classification/county on every call; emits fetch-success/failure counters tagged `source=cslb`.
- **Configuration:** portal base URL, per-classification/county page-path templates, polite request delay — from `config/source_policies.py`.
- **Security:** no credentials (portal is unauthenticated); still respects rate limits as a ToS/courtesy matter.
- **Testing requirements:** contract test against a saved real fixture page (see `sources/cslb/fixtures/`); unit test for URL-building logic; a failure-path test simulating a structure change.
- **Implementation notes:** the CSLB portal has no documented API contract — treat its page structure as fragile by construction. Do not add speculative fields beyond what a real downloaded export actually contains; verify against a real file before trusting the field list given in the planning docs.

### 4.6 `src/sources/cslb/parser.py`
- **Layer:** Sources. **MVP:** Yes.
- **Purpose:** Converts raw CSLB export HTML/CSV bytes into `ParsedCSLBRecord` rows. The single highest-maintenance file in the repository, because CSLB has no API and therefore no versioned contract to rely on.
- **Responsibilities:** Locate the data table/rows in the export format; map columns to fields; handle missing/blank fields explicitly (empty string vs. field absent, not conflated).
- **Does NOT do:** No normalization (`normalize/`), no confidence assignment (`extract/deterministic.py`).
- **External dependencies:** an HTML/CSV parsing library (e.g. an HTML table parser).
- **Internal imports:** none.
- **Imported by:** `sources/cslb/connector.py`.
- **Inputs:** raw bytes/text of one export page.
- **Outputs:** `list[ParsedCSLBRecord]`.
- **Key function:** `parse(raw_text) -> list[ParsedCSLBRecord]` — raises `SchemaChanged` if the expected table/column structure isn't found, rather than silently returning a partial/empty list.
- **State:** stateless.
- **Error handling:** any structural mismatch is a hard failure (`SchemaChanged`, no retry, immediate alert) — never a best-effort partial parse that could silently drop rows.
- **Observability:** logs row count parsed per call; a sudden drop to zero, or a large deviation from the historical average for that classification+county, is itself worth alerting on.
- **Testing requirements:** this file is the primary home of the "source contract test" category — one fixture-based test per known export variant encountered, stored in `sources/cslb/fixtures/`.
- **Implementation notes:** write defensively; grow the fixture/contract-test suite as real edge cases are found in production data.

### 4.7 `src/sources/cslb/fixtures/` (directory, not a code file)
- **Purpose:** Holds saved, real CSLB export pages (one or more per structural variant encountered) used by the contract tests in `tests/unit/sources/` and by `sources/cslb/parser.py`'s own test suite.
- **Connection to rest of codebase:** the ground truth against which `parser.py`'s structure-drift alarm is calibrated. Never synthetic data — always a real captured export.

### 4.8 `src/sources/ca_sos/connector.py`
- **Layer:** Sources. **MVP:** Yes. **Source type:** `api` (per the brief's reference to a CA business-entity public API — flagged in the execution plan as `NOT SPECIFIED — REQUIRES VALIDATION` against sos.ca.gov before building against it in earnest).
- **Purpose:** Corroborates business identity/legal status against California Secretary of State registration records.
- **Responsibilities:** Same shape as `cslb/connector.py` but for a JSON API instead of a static export page: `discover`, `fetch` (via `fetch/http_fetcher.py`), `parse` (delegates to `sources/ca_sos/parser.py`).
- **Does NOT do:** No normalization, no entity resolution, no claim generation.
- **External dependencies:** none beyond the shared HTTP client; an API key if/once the programmatic path is confirmed.
- **Internal imports:** `fetch/http_fetcher.py`, `raw/snapshot_store.py`, `sources/ca_sos/parser.py`.
- **Imported by:** `orchestration/run_coordinator.py` (via the registry).
- **Outputs:** `RawSnapshot` (persisted) + `list[ParsedSOSRecord]`.
- **Configuration:** API key (via `config/settings.py`, never hardcoded), base URL, rate limits — `config/source_policies.py`.
- **Security:** API key loaded from environment/secret store, never logged.
- **Implementation notes:** the underlying access model (free public API vs. paid/portal-only) is unconfirmed in the source material — confirm directly against `sos.ca.gov` before wiring this connector into the scheduled pipeline; do not assume the brief's "business-entity public API guide" reference is accurate without that check.

### 4.9 `src/sources/ca_sos/parser.py`
- **Layer:** Sources. **MVP:** Yes.
- **Purpose:** Field-mapping for CA SOS JSON responses into `ParsedSOSRecord` (legal name, entity number/status, filing history, registered agent, formation date, address).
- **Responsibilities:** JSON → structured record, 1:1 field mapping, no inference.
- **External dependencies:** none beyond the standard JSON handling already available in the language runtime.
- **Internal imports:** none.
- **Imported by:** `sources/ca_sos/connector.py`.
- **Error handling:** unexpected/missing JSON fields raise a parse error rather than silently defaulting.

### 4.10 `src/sources/company_site/connector.py`
- **Layer:** Sources. **MVP:** Yes. **Source type:** `page_fetch`.
- **Purpose:** Fetches a small, fixed set of pages from a candidate entity's own website (`/`, `/about`, `/services`, `/careers`, `/contact`) for a live-business check and fit/timing evidence — **not** a full-site crawl or link-following frontier crawler.
- **Responsibilities:** Try the fixed candidate paths in order; hand each fetched page to `raw/snapshot_store.py`; call `sources/company_site/parser.py` for DOM/text extraction; score fetched pages by simple keyword heuristics (e.g. "hiring," "remodel," "services") to decide which 1–2 pages get passed to `extract/llm_extractor.py`, keeping LLM calls bounded per entity.
- **Does NOT do:** No arbitrary link-following (reserved for a future, explicitly-justified crawler, per architecture spec §10); no LLM calls itself — it hands cleaned text to `extract/llm_extractor.py`.
- **External dependencies:** the shared HTTP client (`fetch/http_fetcher.py`); respects `robots.txt`.
- **Internal imports:** `fetch/http_fetcher.py`, `raw/snapshot_store.py`, `sources/company_site/parser.py`, `extract/llm_extractor.py`.
- **Imported by:** `orchestration/run_coordinator.py` (via the registry).
- **Inputs:** a candidate entity's domain (typically sourced from a CSLB or Google Places corroboration step).
- **Outputs:** `RawSnapshot`(s) for each fetched page + a small set of `ExtractionCandidate`s from the LLM extractor.
- **Configuration:** allowed page paths, polite fetch delay, User-Agent string with contact info (mirroring the SEC EDGAR "fair access" convention referenced in the execution plan) — `config/source_policies.py`.
- **Implementation notes:** per-request company-site fetch (rather than a scheduled batch) is accepted at v0 volume but flagged in the architecture spec (§38 anti-patterns) as the one place to revisit first if request volume grows — do not pre-optimize this in v0.

### 4.11 `src/sources/company_site/parser.py`
- **Layer:** Sources. **MVP:** Yes.
- **Purpose:** Converts raw company-site HTML into (a) cleaned visible text for the LLM extractor and (b) a deterministically-extracted contact block (phone/email/address patterns) that does **not** need an LLM.
- **Responsibilities:** DOM parse for visible text; opportunistically extract JSON-LD if present, but do not assume it exists; regex/pattern-based contact-block extraction.
- **External dependencies:** an HTML parsing library.
- **Internal imports:** none.
- **Imported by:** `sources/company_site/connector.py`.
- **Outputs:** cleaned page text (→ `extract/llm_extractor.py`) and a deterministic contact record (→ `extract/deterministic.py` / directly into `Claim`/`ContactPoint` candidates).

### 4.12 `src/sources/google_places/connector.py` *(Tier 2 / Future — not built in v0)*
- **Layer:** Sources. **MVP:** No (reserved seam only).
- **Purpose:** Business-identity corroboration (phone, address, active-listing status) via the official Google Places API (New).
- **Responsibilities (when built):** `discover`/`fetch` against the paid Places API; **critical constraint** from the execution plan variant that ran a live ToS check: Google's Maps Platform terms permit caching the Place ID indefinitely and lat/lng for up to 30 days, but display name, formatted address, rating, and phone have **no storage exception** — every use of those specific fields is effectively a live call, not something this subsystem may persist as a durable `Claim` value beyond a short TTL. This has direct architectural consequences for `raw/snapshot_store.py`'s freshness handling for this one connector specifically.
- **Does NOT do:** Must never scrape Google Maps pages as a ToS-violating substitute for the official API.
- **External dependencies:** Google Places API client / paid API key.
- **Internal imports (when built):** `fetch/http_fetcher.py`.
- **Implementation notes:** `LEGAL REVIEW REQUIRED` before assuming any caching pattern beyond Place ID — re-check the current Google Maps Platform ToS at integration time, not from planning-time research. Do not build this file until Tier 1 (CSLB, CA SOS, company site) is proven.

### 4.13 `src/fetch/http_fetcher.py`
- **Layer:** Fetch. **MVP:** Yes.
- **Purpose:** The only HTTP client in v0 (no browser fetcher is implemented). Issues requests with per-source headers/timeouts, respects `robots.txt` for `page_fetch` sources, applies the rate limiter, retries on 5xx/timeout with exponential backoff.
- **Responsibilities:** Retry policy (max 3 attempts, e.g. 2/4/8s backoff) on transient errors; do **not** retry on 4xx except 429; treat a repeated 403 as a `PolicyViolation` (stop the connector, alert), not a transient fault; conditional requests (`If-Modified-Since`/ETag) where a source supports them; `content_hash`-based dedup at fetch time — a byte-identical re-fetch is skipped from re-parsing.
- **External dependencies:** an async-capable HTTP client library (e.g. `httpx`).
- **Internal imports:** `fetch/rate_limiter.py`.
- **Imported by:** every source connector (`cslb`, `ca_sos`, `company_site`, and future `google_places`).
- **Inputs:** a request spec (URL, method, headers, source name for policy lookup).
- **Outputs:** raw response bytes + metadata (status, headers, retrieval timestamp) handed to `raw/snapshot_store.py`.
- **Error handling:** implements the full error taxonomy from architecture spec §24 (`SourceUnavailable`, `RateLimited`, `AuthenticationFailure`, `PolicyViolation`) and surfaces which category occurred to the calling connector.
- **Observability:** fetch success/failure counters per source per run, dead-letter counts.
- **Configuration:** timeouts, retry counts, per-source headers — `config/source_policies.py`.

### 4.14 `src/fetch/rate_limiter.py`
- **Layer:** Fetch. **MVP:** Yes.
- **Purpose:** Per-source rate limiting (e.g. a token-bucket), configured per source to respect each API's documented limits (SAM.gov's daily caps, CSLB's polite-fetch cadence, etc.).
- **Responsibilities:** Expose a check/acquire call that `http_fetcher.py` calls before every request; block or queue when a source's limit is reached.
- **External dependencies:** none beyond standard concurrency primitives.
- **Internal imports:** none.
- **Imported by:** `fetch/http_fetcher.py`.
- **Configuration:** per-source rate-limit policy from `config/source_policies.py`.

### 4.15 `src/fetch/browser_fetcher.py` *(stub only — not built in v0)*
- **Layer:** Fetch. **MVP:** No.
- **Purpose:** Reserved interface placeholder for future browser automation (Playwright preferred over Selenium if/when built, per the tech-stack discussion). **No Tier 1 source in v0 requires this**, and the execution plan explicitly frames building a robust computer-use runtime as arguably the main system's/executor's territory, not this subsystem's, per the brief's own Build/Buy split.
- **Responsibilities (when built):** would be triggered only for a specific, confirmed Tier 2 source (e.g. a county permit portal) that has no API/export and requires JS rendering — never as a default fallback, and only after legal review clears it (execution plan Part 11).
- **Implementation notes:** for v0, this file should contain only the interface shape (matching `SourceConnector`'s `fetch` signature) with no working implementation — a deliberate seam, not dead code to be filled in speculatively.

### 4.16 `src/raw/snapshot_store.py`
- **Layer:** Raw. **MVP:** Yes.
- **Purpose:** Persists immutable `RawSnapshot` rows. The layer boundary that makes re-extraction possible later without re-fetching (important once a source changes a field name and a backfill from history is needed).
- **Responsibilities:** `save_snapshot(source, source_record_id, raw_bytes, retrieved_at, license_policy) -> RawSnapshot` computing and storing `content_hash`; `get_snapshot(snapshot_id)`; support for the conditional-fetch dedup check in `http_fetcher.py` (compare a new hash against the last stored hash for the same `source_record_id`).
- **Does NOT do:** No parsing, no normalization — *Fetch never mutates data*, it only retrieves bytes and hands them to Raw Snapshot (execution plan Part 6, stated as an explicit layer boundary).
- **External dependencies:** none beyond the storage backend (local filesystem for v0, S3-compatible bucket once volume grows past local-disk comfort).
- **Internal imports:** `storage/db.py` (for the `RawSnapshot` metadata row) plus a blob-storage helper for the raw payload itself.
- **Imported by:** every source connector's `fetch()` implementation; every parser (to re-read a snapshot for re-processing).
- **Testing requirements:** round-trip test (save → get) preserves byte-identical content and correct hash.

### 4.17 `src/extract/deterministic.py`
- **Layer:** Extract. **MVP:** Yes.
- **Purpose:** Structured-source field mapping for CSLB and CA SOS: `ParsedCSLBRecord`/`ParsedSOSRecord` → `Claim` candidates, e.g. `ParsedCSLBRecord.status → Claim(field="license_status", value=..., observed_or_inferred="observed", confidence=0.95)`.
- **Responsibilities:** Direct, deterministic field mapping. Confidence is a **fixed value per field type** for structured sources — not learned, not LLM-estimated.
- **Does NOT do:** No network access, no database access — takes a `ParsedRecord` in, returns `Claim` candidates out; persistence happens later in `evidence/claim_store.py`.
- **External dependencies:** none.
- **Internal imports:** none (works purely against the `ParsedCSLBRecord`/`ParsedSOSRecord` shapes defined by the respective parsers).
- **Imported by:** `sources/cslb/connector.py` and `sources/ca_sos/connector.py` (or the coordinator, depending on where extraction is invoked in the sequence).
- **Testing requirements:** unit tests per field type verifying the correct confidence and `observed_or_inferred` value is assigned.

### 4.18 `src/extract/llm_extractor.py`
- **Layer:** Extract. **MVP:** Yes — **the only LLM-touching file in v0.**
- **Purpose:** Extracts 0–2 short, quote-anchored evidence snippets from company-site page text relevant to (a) "does this company do remodeling work" and (b) "is there a hiring/expansion signal."
- **Responsibilities:** Build the extraction prompt/schema call against an LLM; enforce the mandatory hallucination check — every returned candidate's `supporting_quote` must appear verbatim (substring match, whitespace-normalized) in the source page text, or the candidate is dropped before it ever becomes a `Claim`; attach `model_version` + `prompt_version` to every output; never call this on structured (CSLB/SOS) data.
- **Does NOT do:** No claim persistence, no confidence scoring beyond pass/fail on the quote check.
- **External dependencies:** an LLM API client (Anthropic Claude API per the tech-stack recommendation — **`NOT SPECIFIED — REQUIRES DECISION`** whether this calls a separate API key or routes through infrastructure the main system already has; confirm with whoever owns the main system before hardcoding a client).
- **Internal imports:** none (stateless per call; page text comes in from `sources/company_site/parser.py` via the connector).
- **Imported by:** `sources/company_site/connector.py`.
- **Inputs:** cleaned page text + page URL.
- **Outputs:** `list[ExtractionCandidate]` — `{claim_or_signal_type, supporting_quote, page_url, model_version, prompt_version}` — **only** entries that pass the quote-match validation.
- **Key function:** `extract(page_text, page_url) -> list[ExtractionCandidate]`.
- **Error handling:** an LLM call failure or malformed output silently drops that one candidate (logged) — never raises up to fail the whole entity's research; the page's deterministic facts (if any) still flow through.
- **Observability:** ratio of candidates-returned vs. candidates-passed-validation — a low pass rate is a prompt-quality signal to watch.
- **Configuration:** prompt template version, model identifier, max pages per entity (1–2) — from `config/settings.py`.
- **Security:** LLM API key via `config/settings.py`, never logged; page text sent is public company-website content, not sensitive data.
- **Testing requirements:** mocked-model unit tests covering: a valid quote (passes), a fabricated quote not present in source text (rejected), malformed JSON output (rejected gracefully).
- **Implementation notes:** raw pages are preserved forever (`raw/snapshot_store.py`), so re-running extraction with a new prompt/model version against old snapshots should be supported as a first-class script/replay operation, not a special pipeline mode. An LLM-derived `Claim` is marked `observed_or_inferred = "observed"` only for the literal quoted fact ("the page says X"); any semantic interpretation beyond the quote (e.g. "this suggests expansion") is a *separate* `Signal` marked `inferred` — never collapsed into one row.

### 4.19 `src/normalize/names.py`
- **Layer:** Normalize. **MVP:** Yes.
- **Purpose:** Canonicalizes business names — strip legal suffixes (`Inc`/`LLC`/`Corp`), lowercase, collapse whitespace — while retaining the original alongside the normalized form.
- **Responsibilities:** Pure function(s), no I/O.
- **External dependencies:** none beyond standard string handling.
- **Imported by:** `entities/resolver.py`.
- **Outputs:** a normalized-name string, used as a matching feature (never the sole match key on its own — see `entities/resolver.py`).

### 4.20 `src/normalize/addresses.py`
- **Layer:** Normalize. **MVP:** Yes.
- **Purpose:** Splits an address into street/city/county/state/zip components; does **not** geocode in v0.
- **Responsibilities:** Pure function(s), no I/O. If normalization can't confidently resolve a component (e.g. a missing element), store the raw value and flag `normalization_status = "partial"` rather than guessing.
- **Imported by:** `entities/resolver.py`.
- **Implementation notes:** partial-normalized fields are treated by the resolver as lower-confidence matching signals, not full matches.

### 4.21 `src/normalize/phones.py`
- **Layer:** Normalize. **MVP:** Yes.
- **Purpose:** E.164-style digits-only normalized phone form, keeping the original formatting alongside it.
- **Imported by:** `entities/resolver.py`.

### 4.22 `src/normalize/domains.py`
- **Layer:** Normalize. **MVP:** Yes.
- **Purpose:** Lowercases, strips `www.`/protocol from a company website URL; the resulting canonical domain is the **join key for entity resolution** (highest-priority deterministic match after license number).
- **Imported by:** `entities/resolver.py`.

### 4.23 `src/entities/resolver.py`
- **Layer:** Entities. **MVP:** Yes.
- **Purpose:** Deterministic entity resolution for one research run's candidate records — matches/merges records from multiple sources into a single canonical `Entity`.
- **Responsibilities:**
  1. **Deterministic matching, in priority order:** (a) exact CSLB license number, (b) normalized domain, (c) normalized phone + name-similarity above a fixed threshold. Any one exact match → high-confidence auto-merge candidate.
  2. **Fuzzy matching, fallback only:** name-similarity (token-set ratio) above a threshold (e.g. 0.9) **and** same county/city. Fuzzy-only matches **never** auto-merge — they create an `IdentityEdge` with `review_state = "pending_review"`.
  3. **Confidence bands:** license#/exact-phone match → 0.95+, auto-merge. Normalized-address-only match → 0.75, auto-merge but flagged for spot-check (addresses collide more than phone numbers — shared suites, strip malls). Fuzzy-name-only → 0.5–0.7, `pending_review`, never auto-merge.
  4. Duplicate handling: once merged, the "losing" record's `Claim`s are re-pointed to the canonical `entity_id`; the merge itself is logged (which two entity_ids, when, confidence, who/what approved it) so it is reversible.
- **Does NOT do:** No claim generation; no trained ML matching model; no cross-vertical identity resolution (a contractor entity and a future freight shipper entity are never the same kind of match problem — do not try to unify); no automatic conflict resolution when two merged sources disagree on a field value — surface the conflict, don't silently pick one.
- **External dependencies:** a string-similarity library (e.g. token-set ratio / Jaro-Winkler), used only for the fuzzy fallback.
- **Internal imports:** `normalize/names.py`, `normalize/addresses.py`, `normalize/phones.py`, `normalize/domains.py`; `evidence/claim_store.py` (to attach claims to the resolved entity).
- **Imported by:** `orchestration/run_coordinator.py`.
- **Inputs:** normalized candidate records from multiple sources for one run.
- **Outputs:** one `Entity` (existing or new) + `IdentityEdge` rows for any fuzzy-only matches.
- **Key function:** `resolve(candidates: list[NormalizedRecord]) -> Entity`.
- **State:** none held beyond the DB; each call is independent. Candidate generation is scoped to one research run — no persistent global cross-run entity-matching index in v0.
- **Configuration:** fuzzy-match similarity threshold — tunable via `config/settings.py` without a code change.
- **Observability:** counters for merges-by-rule-type (license#, domain, phone+name, fuzzy-review) — tells you later whether deterministic rules are catching most real matches or whether fuzzy/review volume is too high.
- **Testing requirements:** unit tests for each match-priority rule independently, plus a test that a fuzzy-name-only match produces a `pending_review` edge, never an auto-merge.
- **Implementation notes:** do not add a scored/weighted multi-feature matcher for v0 — stay simple until false-merge/false-split rates are actually measured against the labeled gold set.

### 4.24 `src/entities/review_queue.py`
- **Layer:** Entities. **MVP:** Yes.
- **Purpose:** Storage/query surface for `IdentityEdge` rows with `review_state = "pending_review"`, surfaced to whatever review UI the main system (or a simple internal script) provides.
- **Responsibilities:** `list_pending() -> list[IdentityEdge]`; `resolve(edge_id, decision: "confirm"|"reject")` — confirming merges the pair, rejecting records the decision (`review_state = "rejected"`) so the same pair doesn't get re-flagged on every run.
- **External dependencies:** none beyond the DB.
- **Internal imports:** `storage/db.py`.
- **Imported by:** `entities/resolver.py` (to write new pending edges); the human review surface — **`NOT SPECIFIED — REQUIRES DECISION`**: whether that review surface lives in the main system's UI or needs to be built here, per the architecture spec's open questions (§46).

### 4.25 `src/evidence/claim_store.py`
- **Layer:** Evidence. **MVP:** Yes.
- **Purpose:** The **only write path** into the `Claim` table. The structural guarantor of "never silently turn inference into fact" — this file is where the evidence-first principle is enforced as code, not just convention.
- **Responsibilities:** `save_claim(claim) -> ClaimId` — **rejects** any claim missing `source_snapshot_id`, `observed_or_inferred`, `observed_at`, `expires_at`, or `extractor_version` at save time (raises `IncompleteClaimError`) rather than persisting a null; `get_claims(entity_id) -> list[Claim]`; `get_stale_claims(as_of) -> list[Claim]` (feeds the freshness refresh scheduler in `evidence/freshness.py`).
- **Does NOT do:** No extraction, no normalization, no entity resolution.
- **External dependencies:** none beyond the DB driver/ORM.
- **Internal imports:** `storage/db.py`.
- **Imported by:** `entities/resolver.py` (to attach claims to a resolved entity), `signals/rules.py` (reads claims to derive signals), `publish/result_builder.py` (reads claims for the response), `evidence/freshness.py` (reads stale claims for the refresh scheduler).
- **Observability:** claims saved per source per run; count of rejected/incomplete claim attempts (should be exactly zero in steady state — any nonzero value is an upstream bug, not a quality metric).
- **Testing requirements:** unit test that an incomplete claim is rejected; integration test that a full save → `get_claims` round-trip returns all provenance fields intact.

### 4.26 `src/evidence/freshness.py`
- **Layer:** Evidence. **MVP:** Yes.
- **Purpose:** TTL/expiry logic and stale-claim sweeps. Determines when a `Claim` needs re-fetching.
- **Responsibilities:** Per-field-type TTL definitions (e.g. CSLB license status ~30 days, company-site fit-evidence ~30 days, signals ~14 days, CA SOS registration ~90 days — starting estimates, revisit after the first real evaluation round); expose `get_stale_claims(as_of)` consumption (via `claim_store.py`) to a scheduled job that triggers re-fetch of expiring fields.
- **Responsibilities note:** refresh is triggered by a **scheduled job** checking `expires_at`, not by request-time lazy refresh — this keeps request latency predictable.
- **Internal imports:** `evidence/claim_store.py`.
- **Imported by:** the scheduler (cron / APScheduler, configured in `config/settings.py`), which is not itself a separate file in the MVP inventory — it is a process invocation of this module's sweep function.
- **Implementation notes:** TTL values are a `PROPOSED ARCHITECTURAL DECISION`, not measured — store them as configuration (not hardcoded constants) so they can be revised after the Phase 5 evaluation without a code change.

### 4.27 `src/signals/rules.py`
- **Layer:** Signals. **MVP:** Yes.
- **Purpose:** A small, deterministic rule engine that pattern-matches recent `Claim`s to produce `Signal` rows — e.g. "a `license_status` claim transitioned from non-active to active within the last N days" → `Signal(type="license_renewed")`.
- **Responsibilities:** Rule definitions, each unit-testable against fixture claim sequences. No ML ranking of signals in v0.
- **Does NOT do:** No claim generation (reads claims, doesn't write them).
- **Internal imports:** `evidence/claim_store.py` (read path); `signals/types.py` (signal type definitions/enum).
- **Imported by:** `publish/result_builder.py` (reads generated signals for the response); invoked by `orchestration/run_coordinator.py` after claims are persisted for a run.
- **Signal types covered in v0:** new/renewed CSLB license (weekly diff of two snapshots), new federal solicitation/award match (if SAM.gov is wired in), careers-page hiring post (observed posting; "implies growth" is a *separate* inferred signal, never merged into the same row), new permit naming the business (Tier 2, deferred).
- **Testing requirements:** unit tests against fixture claim sequences, verifying correct signal type, `evidence_ref`, and `observed_or_inferred` split are produced.

### 4.28 `src/signals/types.py`
- **Layer:** Signals. **MVP:** Yes.
- **Purpose:** Defines the `Signal` type enum/constants (e.g. `"cslb_license_renewed"`, `"sam_gov_award_match"`, `"careers_hiring_post"`) and the `Signal` pydantic shape referenced in §2.
- **Internal imports:** none.
- **Imported by:** `signals/rules.py`.

### 4.29 `src/publish/result_builder.py`
- **Layer:** Publish. **MVP:** Yes.
- **Purpose:** Assembles a `ResearchResult` from a resolved entity's claims/signals/contacts for return via the API. This is the "Publish" layer boundary from the execution plan's pipeline diagram — the only layer that talks to the main system, kept deliberately thin so the integration contract stays stable even as the internal pipeline evolves.
- **Responsibilities:** Query `evidence/claim_store.py`, `signals/rules.py` (read path), and a contact store for one `entity_id`; shape the output per §3's `ResearchResult` contract; attach `schema_version`.
- **Does NOT do:** No fetching, and — stated as a hard rule — **must never compute a "lead score."** `recommendation`/`reason_codes` are this subsystem's read, not a qualification verdict; the actual qualification decision stays the main system's job.
- **External dependencies:** `pydantic` (shares the `ResearchResult` contract model with `api/contracts.py`).
- **Internal imports:** `evidence/claim_store.py`, `signals/rules.py`, a `ContactPoint` read path (see implementation note below).
- **Imported by:** `api/research_api.py`.
- **Inputs:** `entity_id`, `request_id`.
- **Outputs:** a validated `ResearchResult` object.
- **Key function:** `build_result(entity_id, request_id) -> ResearchResult`.
- **Error handling:** an entity with zero claims (e.g. a source came back empty) still produces a **valid** `ResearchResult` with empty arrays, not an error — the caller decides what "no evidence found" means.
- **Observability:** logs result size (claim/signal/contact counts) per request — useful for spotting a source silently returning nothing.
- **Testing requirements:** unit test against a fixture entity with known claims/signals, asserting the output shape matches §3's documented contract exactly.
- **Implementation note (gap in the source material, flagged rather than resolved):** the architecture spec lists "a contact store" as a dependency of this file but **no dedicated `ContactPoint` persistence file appears in the canonical file inventory.** `NOT SPECIFIED — REQUIRES DECISION`: either (a) add `ContactPoint` writes/reads to `evidence/claim_store.py` (treating it as a sibling table under the same provenance-enforcement rules), or (b) add a small dedicated `evidence/contact_store.py` following the same pattern as `claim_store.py`. Confirm with whoever owns the schema before implementing; do not silently invent a third option.

### 4.30 `src/storage/db.py`
- **Layer:** Storage. **MVP:** Yes.
- **Purpose:** The DB engine/session layer — PostgreSQL connection setup, session management, and the underlying table definitions for `Entity`, `RawSnapshot`, `Claim`, `IdentityEdge`, `ContactPoint`, `Signal`, plus the simple job table (§4.32 note below).
- **Responsibilities:** Connection/session factory used by every other persistence-touching module; owns migrations in conjunction with `alembic`.
- **External dependencies:** `PostgreSQL` driver, an ORM or query layer (SQLAlchemy or raw `psycopg`), `alembic` for schema migrations.
- **Internal imports:** none (lowest-level storage file).
- **Imported by:** `raw/snapshot_store.py`, `evidence/claim_store.py`, `entities/review_queue.py`, and effectively most modules that persist or query data.
- **Configuration:** DB connection string — via `config/settings.py`, never hardcoded.
- **Implementation notes:** for the very first days of local development, SQLite is an acceptable stand-in per the tech-stack recommendation, but migrate to Postgres before any multi-source concurrent-write phase — JSONB columns are needed for flexible fields like `match_features` on `IdentityEdge` and the raw-content-pointer field on `RawSnapshot`.

### 4.31 `src/config/source_policies.py`
- **Layer:** Config. **MVP:** Yes.
- **Purpose:** Per-source policy configuration: rate limit, auth requirement, TTL per field type, allowed page paths (for `company_site`), retry policy — literally the "per-source checklist" from the scraping-strategy section of the execution plan (official API/export available? auth needed? ToS on automation/caching/redistribution? robots directives? personal data involved? update cadence? corroboration available elsewhere?), captured as config rather than tribal knowledge.
- **Responsibilities:** One entry per registered source, consumed at startup by `sources/base.py`'s registry and by `fetch/rate_limiter.py`/`fetch/http_fetcher.py`.
- **External dependencies:** none (plain config, possibly YAML-backed per source — the architecture spec suggests a literal `sources/<name>/policy.yaml` per connector as an alternative/complementary location for this data).
- **Internal imports:** none.
- **Imported by:** `sources/base.py`, every connector, `fetch/http_fetcher.py`, `fetch/rate_limiter.py`.

### 4.32 `src/config/settings.py`
- **Layer:** Config. **MVP:** Yes.
- **Purpose:** Environment-level configuration and secrets: DB connection URL, object-storage bucket location, LLM API access, per-vertical target definitions (geography/classification list from the goal contract) as data, not hardcoded logic.
- **Responsibilities:** Single source of truth for anything environment-specific; credentials are **never** hardcoded in connector modules — always read from environment variables / a secret manager via this file.
- **External dependencies:** an environment-variable/secret-loading library as needed.
- **Imported by:** most modules (`storage/db.py`, `extract/llm_extractor.py`, `sources/*/connector.py`, `api/research_api.py`).
- **Security:** CA SOS API key and LLM API key are the only secrets in v0; both loaded here, never committed, never logged.

### 4.33 `src/observability/logging.py`
- **Layer:** Observability. **MVP:** Yes.
- **Purpose:** Structured logging setup (e.g. `structlog`), shared across the codebase — no separate monitoring dashboard/stack is built for v0.
- **Responsibilities:** One log line per pipeline stage transition, including `job_id` and `source` for correlation; counters for fetch success/failure per source per run, claims generated, signals generated, entities created vs. merged, dead-letter count, job queue depth, LLM calls + approximate cost per run.
- **External dependencies:** `structlog` or equivalent.
- **Imported by:** most modules that need to log a stage transition or emit a counter.
- **Implementation notes:** enough to catch a source silently breaking without building a full tracing/APM stack — that is explicitly deferred (architecture spec §27: "three sources and low volume don't justify it").

### 4.34 `src/config/` — the job/queue table (no dedicated file listed, lives in `storage/db.py`)
- **Note:** the architecture spec's queue design (§22) is a **DB-backed job table** (not Celery/Redis) with columns `job_id, job_type, payload, status, attempts, last_error, created_at, updated_at`, scheduled via `cron`/APScheduler. This table is defined alongside the other tables in `storage/db.py` rather than as a separate file — flagged here so it isn't missed when building the schema. Idempotency is enforced via a deterministic key in the payload (e.g. `cslb:county:classification:week`) so re-enqueueing the same logical job doesn't duplicate work; `status = "dead_letter"` after 3 failed attempts, requiring human action, never silently retried forever.

### 4.35 `scripts/backfill_cslb_county.py`
- **Layer:** Scripts. **MVP:** Yes.
- **Purpose:** CLI entrypoint / one-off manual pull for a given county+classification, bypassing the scheduled weekly job — used for initial backfill and for manual recovery after a CSLB format-change fix.
- **Responsibilities:** Calls `sources/cslb/connector.py`'s `discover`/`fetch`/`parse` directly, then runs the same downstream pipeline the coordinator would (or invokes the coordinator with a synthetic request) for one target.
- **Internal imports:** `sources/cslb/connector.py`, and either `orchestration/run_coordinator.py` or the same stage modules it calls.
- **Used by:** the operator, run manually — not invoked by any other code in the repository.

### 4.36 `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `tests/e2e/` (directories)
- **`tests/unit/`** — pure-function tests: normalizers, entity-matching rules, signal rules. No network access.
- **`tests/integration/`** — connector → parser tests against saved fixtures (not live network calls in CI).
- **`tests/fixtures/`** — shared fixture files including per-source saved responses (mirrors `sources/cslb/fixtures/` but at the test-suite level for cross-module fixtures).
- **`tests/e2e/`** — one full pipeline run against recorded fixtures, asserting on output shape end-to-end; plus, run manually or on a slow (e.g. weekly) schedule rather than per-commit, one real rate-limit-respecting live pull per source to catch drift the fixture tests can't (source contract testing, the single most important test category given CSLB's lack of a formal API).

### 4.37 `docs/` (directory)
- **Purpose:** Holds the living execution plan and this architecture/file specification themselves, plus any per-source `policy.yaml` documentation and the technical README (how to run the pipeline, what each source needs, how to add a new county/classification) once the pipeline is stable enough that instructions won't go stale within days.

---

## 5. File Dependency Graph (restated as a build-order-safe list)

No circular dependencies: `sources/*` never imports from `entities/`, `evidence/`, or `publish/`. `extract/*` never imports from `entities/`. `entities/*` never imports from `sources/*` or `fetch/*`. Source-specific parsing logic must never appear in `entities/`, `evidence/`, `signals/`, or `publish/`. Vertical-specific logic (contractor vs. future freight) must never appear in `fetch/`, `raw/`, or `orchestration/run_coordinator.py`.

```
api/contracts.py
  → api/research_api.py
      → orchestration/run_coordinator.py
          → sources/base.py
              → sources/cslb/connector.py    → fetch/http_fetcher.py → fetch/rate_limiter.py
                                              → raw/snapshot_store.py → storage/db.py
                                              → sources/cslb/parser.py
              → sources/ca_sos/connector.py  → (same fetch/raw pattern) → sources/ca_sos/parser.py
              → sources/company_site/connector.py → (same fetch/raw pattern)
                                                   → sources/company_site/parser.py
                                                   → extract/llm_extractor.py
          → extract/deterministic.py
          → normalize/{names,addresses,phones,domains}.py
              → entities/resolver.py → entities/review_queue.py
          → evidence/claim_store.py → evidence/freshness.py
          → signals/rules.py → signals/types.py
          → publish/result_builder.py
      ← (ResearchResult back to caller)
```

All modules read secrets/config through `config/settings.py` and `config/source_policies.py`; all modules that log or emit counters use `observability/logging.py`. `scripts/backfill_cslb_county.py` is a side entrypoint that calls into the `sources/cslb/` and `orchestration/` layers directly, outside the API.

---

## 6. Build Order (from architecture spec §36 — do not skip ahead)

| Phase | Files | Definition of done |
|---|---|---|
| 1 — Foundation | `storage/db.py`, `config/*`, all six data-model tables | Schema migrated, empty tables exist |
| 2 — Connector framework | `sources/base.py` | Protocol defined, one fake/test connector passes |
| 3 — First source (CSLB) | `sources/cslb/*`, `fetch/*`, `raw/snapshot_store.py` | Real CSLB fixture parses correctly |
| 4 — Extraction/normalization | `extract/deterministic.py`, `normalize/*` | CSLB record → normalized `Claim` candidates |
| 5 — Evidence storage | `evidence/claim_store.py`, `evidence/freshness.py` | Claims persisted with provenance/TTL |
| 6 — Entity resolution | `entities/*` | Deterministic matching correct on fixture data |
| 7 — Second/third source | `sources/ca_sos/*`, `sources/company_site/*`, `extract/llm_extractor.py` | Multi-source claims attach to the same entity |
| 8 — Signals | `signals/*` | At least one signal type fires on fixture data |
| 9 — Publish/API | `publish/result_builder.py`, `api/*` | Real `ResearchResult` returned for a test request |
| 10 — Observability/quality | `observability/logging.py`, quality metrics | Metrics visible; source-contract test running |

Do not build `sources/google_places/connector.py` or `fetch/browser_fetcher.py` beyond their reserved stubs until a Tier 2 source is specifically chosen and justified — this is stated explicitly, not an oversight.

---

## 7. Open Points That Affect Code Generation (carried over, not resolved here)

- **`ContactPoint` persistence** has no dedicated file in the canonical inventory (see §4.29's implementation note) — decide before writing `publish/result_builder.py`'s contact-read path.
- **Contact verification** (deliverability pinging) is explicitly **not** built in this codebase at all — `ContactPoint.verification_state` should only ever be set to `"unverified"` by this subsystem's own writes.
- **LLM provider wiring** for `extract/llm_extractor.py` (separate API key vs. routed through the main system's model access) is unresolved — do not hardcode a specific client without confirming.
- **Pull vs. push** integration with the main system (`api/research_api.py`'s sync endpoints vs. a shared table/queue the main system polls) is an open architectural choice for whoever owns the main system, not something this file set should assume either way.
- **Google Places' no-store constraint** (§4.12) should be resolved architecturally before that connector is built, not discovered after data is already cached in violation of the ToS.