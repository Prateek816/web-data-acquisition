# Problem: Nationwide public construction opportunity data

## Who this is for

ContractorOps (contractorops.ai) is an AI back office for small service-trade contractors. Its customers chase public construction work: county, city, state and federal projects that are publicly advertised for bid. Knowing about these projects early, and knowing which small contractors bid on them, is both a lead source for ContractorOps sales and a data asset inside the product itself.

## The problem

There is no single free national database of upcoming public construction projects in the United States. The information is public by law, but it is scattered:

- **Federal** opportunities are centralized on SAM.gov and are API-accessible, but federal construction volume is modest.
- **State** departments of transportation each publish their own letting schedules (project, advertise date, estimate, spec number) on their own websites, in 50 different formats.
- **County and city** work, which is where small service-trade contractors actually live, is fragmented across roughly 19,000 municipalities. In practice their postings concentrate on about six procurement platforms, but each platform hosts hundreds of agencies and none offers a free, unified, nationwide data feed.

Commercial aggregators (Dodge Construction Network, ConstructConnect, Deltek GovWin, SOVRA/BidNet) already solve this by scraping and licensing the result, priced for end users at $129+/month per market or at enterprise rates. A startup building this as product infrastructure cannot build on per-seat market licenses.

## What happens today without this system

A ContractorOps user (or the ContractorOps sales motion) only hears about a relevant public project if they manually check their local agency's portal, attend an outreach event, or pay an aggregator. Coverage outside their home county is effectively zero. Upcoming-project lists like a county's "2026/2027 contracting opportunities" deck are often not even published online; they exist as event slides or PDFs.

## Goal

A programmatic ingestion system that continuously extracts upcoming and advertised public construction projects from every level of US government, normalizes them into one schema, deduplicates them, and stores them for querying. Near-zero marginal cost per record, built from free official sources, with a realistic path to national coverage using roughly eight extractor templates rather than thousands of per-county scrapers.

## Non-goals

- Bidding, estimating, or proposal generation. This system is data ingestion only.
- Private/commercial construction leads. Those come from paid licenses (Dodge) later.
- Redistribution of scraped data to third parties before licensing terms are settled.

## Verified source landscape (as of 25 Sep 2026)

| Level | Source | Access | Cost |
| --- | --- | --- | --- |
| Federal | SAM.gov Get Opportunities API v2 (api.sam.gov/opportunities/v2/search) | Official REST API, key from SAM.gov account | Free, daily caps |
| Federal (defense) | DLA DIBBS | Portal | Free |
| State | 50 state DOT letting schedules (e.g. Caltrans ccop.dot.ca.gov, TxDOT letting dashboard with CSV download) | Structured web pages / downloads | Free |
| Local | PlanetBids, OpenGov Procurement, Public Purchase, Bonfire, DemandStar, BidNet Direct (SOVRA) | Portal pages; OpenGov has an official developer API | Free to read |
| Aggregated bootstrap | Apify "US Government Tenders & RFP API" actor (24 portals normalized) | API | ~$0.003/record |
| Aggregated bootstrap | Bid Banana API (1.6M+ bids/awards) | REST API | Annual subscription |
| Paid, later | Dodge Construction Network API (construction.com/apis) | REST API, enterprise license | Enterprise |