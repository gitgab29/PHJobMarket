# Build Instructions

This folder stores **actionable, stage-by-stage build instructions** — the "here's exactly
what to build next and why" documents we approve before writing code.

## How this differs from the other docs folders

| Folder | Purpose | Audience / lifespan |
|---|---|---|
| `docs/plan/` | The **reference spec** for the whole system (architecture, schema, every model's SQL). Stable, rarely changes. | "How is X supposed to work?" — look it up. |
| `docs/instructions/` (this folder) | **Approved work orders** for one stage at a time. Each file = one chunk of work, with the *why* explained for a junior engineer. | "What are we building right now, and in what order?" |
| `handoff.md` (repo root) | The **running log** of project state — what exists, what's next, session history. | Read first every session. |

Think of it as: `plan/` = the blueprint, `instructions/` = the work orders cut from that
blueprint, `handoff.md` = the site diary.

## Naming convention
`NN-short-topic.md` (e.g. `01-dbt-warehouse-layer.md`), numbered in the order they were
tackled. Each file starts with a **stage banner** (status, prerequisites, what it unblocks).

## Status values
- `PLANNED` — approved, not started
- `IN PROGRESS` — actively being built
- `DONE` — built and verified (note the commit/date)
- `SUPERSEDED` — replaced by a later instruction (link to it)
