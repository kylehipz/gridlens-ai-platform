# GitHub Issue Dependency Graph

This document captures the implementation dependency graph for the current
GitHub issue task breakdown.

## Topological Waves

### Wave 0

- `T01`: Repository Boilerplate

### Wave 1

- `T02`: Local Runtime Dependencies
- `T03`: Shared Contracts

### Wave 2

- `T04`: Shared Libraries
- `T06`: Frontend Scaffold

### Wave 3

- `T05`: Backend Service Scaffolds

### Wave 4

- `T07`: Baseline Identity and Audit Schema
- `T38`: Local Observability

### Wave 5

- `T08`: Authentication, Tenant Context, and RBAC

### Wave 6

- `T09`: Sign-In and Workspace Picker UI
- `T10`: Audit Service Foundation

### Wave 7

- `T11`: Tenant Settings and Members APIs
- `T13`: Object Storage and File Metadata

### Wave 8

- `T12`: Tenant Shell, Settings, and Role Navigation UI
- `T14`: Dataset Catalog and Current File Lineage

### Wave 9

- `T15`: Dataset UI
- `T16`: Ingestion Job Workflow

### Wave 10

- `T17`: Validation and Quality Reports

### Wave 11

- `T18`: Dataset Quality UI
- `T19`: Normalized Operational Tables
- `T30`: Assistant Document Indexing

### Wave 12

- `T20`: Synthetic Demo Data and Seeds
- `T21`: Evaluation Run Lifecycle

### Wave 13

- `T22`: First Savings Engine

### Wave 14

- `T23`: Evaluations UI
- `T24`: Dashboard APIs
- `T26`: Anomaly Detection and APIs

### Wave 15

- `T25`: Intelligence Dashboard UI
- `T27`: Anomaly Review UI
- `T28`: Reporting Service
- `T31`: Assistant Sessions, Retrieval, Answers, and Refusals

### Wave 16

- `T29`: Reports and Evidence UI
- `T32`: Assistant UI
- `T33`: Usage and Cost Rollups
- `T35`: Audit Filters and Export

### Wave 17

- `T34`: Usage and Cost UI
- `T36`: Audit Log UI
- `T37`: Platform Operations APIs
- `T40`: P2/P3 Extension Backlog

### Wave 18

- `T39`: AWS Infrastructure Skeleton

## Direct Dependencies

```text
T01 -> none
T02 -> T01
T03 -> T01
T04 -> T03
T05 -> T02, T04
T06 -> T01, T03
T07 -> T04, T05
T08 -> T03, T07
T09 -> T06, T08
T10 -> T07, T08
T11 -> T08, T10
T12 -> T09, T11
T13 -> T02, T04, T08, T10
T14 -> T07, T13
T15 -> T06, T12, T14
T16 -> T02, T13, T14
T17 -> T16
T18 -> T15, T17
T19 -> T17
T20 -> T07, T14, T17, T19
T21 -> T14, T17, T19
T22 -> T21
T23 -> T12, T21, T22
T24 -> T17, T22
T25 -> T06, T12, T24
T26 -> T17, T22
T27 -> T12, T26
T28 -> T10, T14, T17, T22, T26
T29 -> T12, T23, T28
T30 -> T13, T14, T17
T31 -> T22, T26, T30
T32 -> T12, T31
T33 -> T10, T16, T28, T31
T34 -> T12, T33
T35 -> T10, T28
T36 -> T12, T35
T37 -> T16, T33
T38 -> T04, T05
T39 -> T05, T37, T38
T40 -> T24, T31, T33
```

## Practical Critical Path

For the first full product slice, the practical critical path is:

```text
T01 -> T03 -> T04 -> T05 -> T07 -> T08 -> T10/T13 -> T14 -> T16 -> T17 -> T19 -> T21 -> T22 -> T24/T26 -> T28/T31 -> T33 -> T37 -> T39
```

## Planning Notes

- UI tasks can usually start once their scaffold, tenant shell, and backing APIs
  are available.
- `T20` seed data is not on every backend critical path, but it becomes
  important before validating dashboard, evaluation, anomaly, reporting, and
  assistant user flows end to end.
- `T30` can progress after file metadata, dataset catalog, and quality report
  foundations exist, even before the full assistant answer pipeline is complete.
- `T39` is intentionally late because it depends on service boundaries,
  observability, and platform operations APIs being concrete enough to model in
  infrastructure.
