# ADR 0001: Five-level status scale, front line between 3 and 4

## Status

Accepted, 2026-10-28.

## Context

A binary "curable / not curable" flag can't place diseases like HIV or type 1 diabetes, which are neither cured nor losing battles. The front line would mean nothing.

## Decision

Each disease gets one of five statuses: Eradicated, Curable, Controlled, Treatable, Untreatable. The front line is drawn between **Controlled** and **Treatable**: a disease counts as "held" once patients can live near-normal lives, even without a cure.

## Consequences

- Every status assignment needs a source, because the line between Controlled and Treatable is a judgement call.
- The bands on either side of the line give the map visual depth, not just two colours.
- Some diseases straddle levels (e.g. a cancer that is curable when caught early). They get the status of a typical patient at diagnosis, with the nuance in the info panel.
