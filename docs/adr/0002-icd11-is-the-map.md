# ADR 0002: ICD-11 is the map, GBD supplies the burden

## Status

Accepted, 2026-10-28. Replaces an earlier draft in which GBD causes were the provinces and the map stopped at GBD granularity.

## Context

The map needs a hierarchy to zoom through, and provinces need a burden figure to set their size. ICD-11 is the WHO's standard disease classification: deep and complete, but with no burden data. GBD reports burden for only ~370 causes.

The project's pitch is "every human disease", so the map should not stop at ~370 causes.

## Decision

ICD-11 is the map. Its chapters and blocks are territories, and its diseases are provinces, down to the deepest level.

GBD supplies the burden. GBD assigns every ICD-10 code to exactly one cause, and WHO publishes ICD-10 → ICD-11 mapping tables, so every ICD-11 disease traces back to one GBD cause. Provinces under the same GBD cause split its burden equally.

## Consequences

- Thousands of provinces. Most of the map starts as fog and is assessed in burden order.
- Sizes below GBD level are estimates and are labelled "size estimated".
- The cross-walk is many-to-one (ICD-11 disease → GBD cause), so no tie-breaking rule is needed in the common case. Majority rule, with an LLM-proposed and owner-reviewed fallback, covers any disease whose ICD-10 codes point to more than one cause.
- ICD-11 branches with no traceable GBD cause have no size. How to handle them, and ICD-11 chapters that aren't diseases, is decided separately.
