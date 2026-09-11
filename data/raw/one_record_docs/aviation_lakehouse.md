# AviationLakehouse narrative (RecordChat)

> This document is a **RecordChat project narrative**. It is not an IATA
> specification and does not describe a product published by IATA. Use it to
> explain how ONE Record logistics objects *could* land in an analytical
> Bronze / Silver / Gold layout for portfolio and architecture Q&A.

## What AviationLakehouse is in this project

AviationLakehouse (ALH) is RecordChat's name for an **analytical landing zone**
for copies of ONE Record logistics objects. Operational systems keep serving
live API traffic; ALH stores and reshapes those objects so analysts can ask
questions about cycle times, dwell, and event timelines without burdening the
system of record.

In this narrative, ALH is a medallion-style lakehouse idea (Bronze → Silver →
Gold). RecordChat explains the mapping. It does **not** run Spark jobs, Iceberg
tables, or a warehouse cluster.

## Relationship to ONE Record and RecordChat

- **ONE Record** defines the shared data model, JSON-LD payloads, and API
  concepts for air-cargo logistics objects.
- **ONE Record Server** (out of scope for this narrative slice) would hold the
  live, addressable LogisticsObjects that parties exchange.
- **RecordChat** answers questions about those concepts and about this ALH
  mapping story, with citations.
- **AviationLakehouse** would analyse **copies** of objects (or events derived
  from them). It is not a replacement for the Server and must not become the
  place where authoritative `@id` links are minted for operational exchange.

```text
ONE Record objects (operational JSON-LD / API)
        │  copy / land (narrative only in RecordChat)
        ▼
AviationLakehouse  Bronze → Silver → Gold
```

## Bronze

Bronze holds **raw or near-raw** ONE Record JSON-LD LogisticsObjects as they
were landed from an upstream Server, file drop, or connector.

- Prefer append-only landing: keep the original payload bytes or JSON as seen.
- Preserve `@id`, `@type`, `@context`, and source-system metadata.
- Do not force business keys or aggregates yet; Bronze is the recovery and
  audit layer for "what did we receive?"
- Typical grain: one landed LogisticsObject document (or one change event that
  wraps an object snapshot).

## Silver

Silver holds **typed, validated, and linked** logistics entities at the grain
of the ONE Record object.

- Conformed identifiers (stable keys derived from `@id` where possible).
- Explicit entity types such as Piece, Shipment, Waybill, TransportMovement,
  and LogisticsEvent.
- Link fields resolved enough for joins (for example Shipment → contained
  Pieces) while staying close to the operational model.
- Quality checks: required `@type`, parseable JSON-LD, and referential
  consistency where links exist.
- Silver is still object-centric, not a KPI mart.

## Gold

Gold holds **business-ready analytical facts** built from Silver entities.

- Examples: shipment cycle time, piece dwell between events, event timelines,
  lane or party aggregates.
- Aggregations and dimensional models are welcome; Gold is for analytics and
  reporting, **not** the system of record for API exchange.
- Consumers of Gold should not write authoritative logistics state back into
  ONE Record without going through an operational Server path.

## Example landing: Shipment + Piece

Consider a Shipment that contains two Pieces, each with JSON-LD `@id` values.

1. **Bronze** — land the Shipment document and each Piece document (or a single
   bundle) exactly as received, with ingest timestamp and source Server URI.
2. **Silver** — parse `@type=Shipment` / `@type=Piece`, normalize ids, and
   materialize the containment link so analysts can join pieces to their
   shipment without re-parsing raw JSON every time.
3. **Gold** — derive facts such as "pieces per shipment", time from first piece
   event to delivery milestone, or dwell histograms — metrics that answer
   business questions rather than replaying API payloads.

The same `@id` values remain the bridge back to the operational ONE Record
world; Gold metrics cite those ids but do not replace them.

## What this project does not run

RecordChat does **not** currently:

- stand up an AviationLakehouse cluster
- run a live Bronze/Silver/Gold ingest pipeline
- write synthetic JSON-LD from RecordForge or local templates into a lake or a
  ONE Record Server

This document exists so architecture questions can be answered with a clear,
citable mapping narrative. Live lakehouse connectors stay out of scope until a
later, explicitly scheduled platform slice.
