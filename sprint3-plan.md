# Sprint 3 Plan — RCA Quality v2 + Operator Feedback Loop

> **Sprint window:** 2026-04-23 → 2026-05-07 (2 weeks)
> **Status:** Day 7 of 14 — Epic 1 mostly Done, Epics 2–3 starting week 2
> **Repos in scope:** `monitoring-triage-service` · `monitoring-docs` · `monitoring-mcp-servers` · `provisioning-monitoring-infra`
> **Capacity:** ~70 SP total (49 SP shipped under Epic 1 close-out + ~20 SP new work in Epics 2–3)

---

## Sprint goal

1. **Close out the RCA-quality work** that started inside Sprint 2 ("Epic 5") under a clean Sprint 3 epic — the historical record matches when the work actually shipped.
2. **Ship the operator feedback loop + curated RAG** on top of the existing US-5.3 feedback infrastructure, so the model learns from operator thumbs-up/down + corrections.
3. **Wire up the Drain3 baseline lifecycle** — S3 plumbing already exists in `drain_analyzer.py` (built in Sprint 2, never invoked). Add scheduling, boot-time restore, and three operator-facing endpoints.

## Why this framing

~10 working days of substantive work happened between Sprint 2's official close (2026-04-23) and today (2026-04-29). It doesn't fit Sprint 2's Epic 5 scope (UEBA-flavored) and is too coherent to attribute to nothing. Sprint 3 absorbs it as **Epic 1 — RCA Quality v2**, alongside two forward-looking epics (2 and 3) for the remaining week.

---

## Out of scope (explicitly deferred to Sprint 4)

| Item | Reason |
|---|---|
| **US-5.2 Incident correlator** | 1–2 days; was Tier-1 but would crowd out feedback-loop work. Pull in next sprint. |
| **GPU migration to us-west-2 + qwen2.5:14b** | Laptop @ 32 GB still serves qwen2.5:7b adequately; defer until tool-calling rewrite needs it. |
| **MCP native tool-calling rewrite** (backlog #5) | 5 SP rewrite, gates on GPU. |
| **Planner → Executor → Writer** (backlog #2c) | Gates on tool-calling. |
| **Trace-ID linkage from log anomalies** (backlog #2a) | 2 SP, attractive but additive — no sprint capacity. |
| **RCA playbook templates** (backlog #2b) | Complements Epic 2 but additive. |
| **US-5.7 Labeled corpus + F1 tracking** | 2-day estimate is optimistic; plan separately. |
| **O-9 webhook auth, O-10 nightly RCA-history S3 backup, O-11 ansible-vault** | Friday-slot hardening or Sprint 4. |
| **`monitoring-project/CLAUDE.md` + PNG diagram refresh** | Single doc-debt commit, anytime. |

---

## Epic 1 — RCA Quality v2 (close-out)

**Goal:** Backfill Sprint 3's epic record with RCA-quality work shipped between 2026-04-23 and 2026-04-29. **All "Done" stories already have commits in their respective repos.**

**Net effort:** 49 SP shipped + 1 SP cleanup remaining.

| ID | Story | SP | Status |
|---|---|---|---|
| US-3-CO1 | US-5.1 Phase A — Per-service Drain3 (`dict[service → TemplateMiner]`) | 3 | Done |
| US-3-CO2 | US-5.1 Phase B — Entity baselines (code complete, real-RCA verification pending) | 3 | In Progress |
| US-3-CO3 | US-5.3 — Closed-loop feedback override/confirm + precision/recall metrics | 5 | Done |
| US-3-CO4 | US-5.4 — Adaptive thresholds on 3 flappiest rules | 3 | Done |
| US-3-CO5 | US-5.8 — Recurrence gates (pre-LLM + post-LLM, MediumCpu/Mem opt-in) | 5 | Done |
| US-3-CO6 | RCA quality hardening F-1..F-5 (Drain3 webhook enrichment, hallucination blocklist, confidence clamp, surface-only LEDE validator, retry-on-violations) | 8 | Done |
| US-3-CO7 | Exemplar library (D17, 11 archetypes) + RCA prose philosophy (D18 + D19) | 5 | Done |
| US-3-CO8 | Dashboard redesign + `/dashboard/guide` operator manual | 3 | Done |
| US-3-CO9 | Pod-level alert rules `PodHighMemoryUsage` + `PodHighCpuUsage` (2 query bugs filed for Sprint 4) | 3 | Done |
| US-3-CO10 | Chaos test harness (`scripts/chaos/`, 4 test classes, RCA scorer) | 5 | Done |
| US-3-CO11 | Daily audit feeds — static (cloud /schedule routine) + live (controller cron) | 3 | Done |
| US-3-CO12 | Audit repo migrations (3 manual audits → private repo) + SESSION_HANDOFF history scrub | 2 | Done |
| US-3-CO13 | Codify `app/policy.py` + `app/bypass_llm.yaml` (extract from existing rule/LLM ordering — *cleanup only, behavior unchanged*) | 1 | To Do |

---

## Epic 2 — Operator feedback → curated RAG

**Goal:** Capture per-decision operator feedback (thumbs ↑/↓ + structured tags + free-text correction) and feed it back into the LLM prompt as similar-case examples.

**Why:** The exemplar library is a frozen seed of 11 archetypes. As real US-5.3 `feedback` accumulates (override/confirm), there's no closed loop bringing that signal into future LLM prompts. Epic 2 closes that loop without abandoning the existing schema.

**Net effort:** 14 SP.

**Dependency order:** 3.1 → (3.2 ∥ 3.3) → 3.4 → 3.5

### US-3.1 — Extend feedback schema + endpoint *(3 SP)*

**Repo:** `monitoring-triage-service`

**Approach:** Extend the existing `feedback` table — do **not** create v2. Adds operator-quality-vote alongside the existing override/confirm behavioral signal.

Schema migration (additive, in `app/rca_store.py:_init_schema`):

```sql
ALTER TABLE feedback ADD COLUMN rating TEXT
  CHECK (rating IN ('up','down') OR rating IS NULL);
ALTER TABLE feedback ADD COLUMN tags TEXT;             -- JSON array, only when rating='down'
ALTER TABLE feedback ADD COLUMN actual_root_cause TEXT;-- only when rating='down', optional
ALTER TABLE feedback ADD COLUMN comment TEXT;
ALTER TABLE feedback ADD COLUMN rater TEXT;
```

`feedback_type` (override/confirm) stays for the US-5.3 path. New rows from this story have `feedback_type=NULL` and one of `rating={up,down}` set. Either-or is enforced at the endpoint, not the table.

New endpoint: `POST /decisions/{id}/feedback`

```json
{
  "rating": "up" | "down",
  "tags": ["wrong_severity"|"wrong_root_cause"|"wrong_evidence"|"wrong_action"|"missing_context"],
  "actual_root_cause": "string",
  "comment": "string",
  "rater": "string"
}
```

Validation: `tags` and `actual_root_cause` rejected when `rating=='up'`. `tags` must be a subset of the 5 allowed enum values.

New MCP tools (read-only, on `monitoring-mcp-servers/rca_history_mcp/`):
- `get_feedback_stats` — counts by rating, top tags, rater frequency
- `get_high_rated_examples(limit, since_days)` — returns up-rated decisions for inspection

**Files:**
- `app/rca_store.py` — schema migration + `record_rating()` method
- `app/models.py` — `RatingFeedbackRequest` Pydantic schema
- `app/main.py` — new endpoint
- `tests/test_feedback_rating.py` — CRUD + validation; complement `test_feedback_us53.py`
- `monitoring-mcp-servers/rca_history_mcp/main.py` — 2 new tools

**Done when:** Migration is idempotent; endpoint rejects invalid combos; MCP tools return sane stats over a seeded test DB; existing US-5.3 endpoints unaffected.

### US-3.2 — Operator rating UI *(2 SP)*

**Repo:** `monitoring-triage-service`

Minimal vanilla-JS form (no framework) at `app/static/rate.html`:
- Decision context block (alert name, RCA prose, verdict — fetched via `GET /decisions/{id}`)
- Big ↑/↓ buttons
- On ↓: 5 tag chips (multi-select) + textarea for `actual_root_cause` + textarea for `comment`
- "Submit" → `POST /decisions/{id}/feedback`
- Success state with one-line confirmation

Email integration: `app/email_renderer.py` appends a "Rate this decision" link with `?rate=1` to the decision URL. The dashboard's decision-detail panel gets a "Rate" button that opens `rate.html?id=<decision_id>`.

**Files:** `app/static/rate.html`, `app/static/rate.css`, `app/email_renderer.py`, `app/main.py` (serve static), dashboard panel template.

**Done when:** Email link → form → submit → row in `feedback` table → confirmation. Dashboard "Rate" link works for any decision listed.

### US-3.3 — Weekly curation job *(3 SP)*

**Repo:** `monitoring-triage-service`

**Approach:** APScheduler in-process (no separate cron container). Add `apscheduler` to `requirements.txt`.

`app/exemplars/curate.py`:

```python
def curate_weekly() -> None:
    """Read SQLite feedback → emit library_curated.yaml."""
    positives = _select_positives(db)   # rating='up', age < 90 days, cap 200
    anti      = _select_anti(db)        # rating='down' + actual_root_cause non-null, age < 90 days, cap 50
    yaml_path = APP_DIR / "exemplars" / "library_curated.yaml"
    yaml_path.write_text(_render(positives, anti))
```

Scheduled in `app/main.py:lifespan()`:

```python
scheduler.add_job(curate_weekly, "cron", day_of_week="sun", hour=2, minute=0)
```

Curated YAML schema mirrors `library.yaml` with two extra fields: `source: "curated"` and `polarity: "positive" | "anti"`.

**Files:** `app/exemplars/curate.py`, `app/exemplars/__init__.py` (export), `app/main.py` (scheduler wiring), `tests/test_curate.py`.

**Done when:** Job runs against a seeded DB, produces a YAML file matching seed-format schema; cap limits enforced; no exception on empty feedback table.

### US-3.4 — RAG retrieval into prompt *(5 SP)*

**Repo:** `monitoring-triage-service`

**Approach:** **BM25 first** (lexical, no model load). Only fall back to sentence-transformers if a 2-week A/B shows BM25 underperforming.

`app/exemplars/loader.py` reads `library.yaml` + `library_curated.yaml` into a unified record set (`source`, `polarity`).

`app/exemplars/retriever.py`:
- BM25 over each record's concatenated `(alert_pattern + context_keywords + hypothesis)`
- Top-K=3 positives + top-K=2 anti-examples
- Cached on disk (`/data/retriever_index.pkl`); rebuilt when curated YAML mtime changes

In `app/llm_client.py:_build_prompt()`:

```text
## Past similar cases that were rated correct:
- {hypothesis} | {evidence} | {action}

## Past mistakes — do NOT repeat:
- Alert: {alertname}
  Previous wrong hypothesis: {text}
  Actual root cause: {actual_root_cause}
```

Conditional ST upgrade (gated, **not in this sprint unless BM25 underperforms**): if `RETRIEVER_BACKEND=sentence-transformers`, load `all-MiniLM-L6-v2` (~80 MB) and use cosine similarity over precomputed embeddings.

A/B harness: every prompt build records `rag_examples_retrieved{polarity}` metric and the chosen exemplar IDs in the decision row.

**Files:** `app/exemplars/loader.py`, `app/exemplars/retriever.py`, `app/llm_client.py` (prompt injection), `app/config.py` (`RETRIEVER_BACKEND`), `tests/test_retriever.py`.

**Done when:** Real LLM prompt for a chaos `PodHighMemoryUsage` alert includes ≥1 retrieved example; metric increments; validator-pass-rate not regressed on the chaos suite.

### US-3.5 — Feedback observability *(1 SP)*

New Prometheus metrics:
- `feedback_total{rating}`
- `feedback_tag_total{tag}`
- `rag_examples_retrieved{polarity}`
- `curate_run_total{status}` and `curate_run_duration_seconds`

New Grafana panel on `triage-service-health` dashboard: feedback volume + tag breakdown + curate-job freshness.

**Files:** `app/metrics.py`, `roles/grafana/templates/dashboards/triage-service-health.json`.

**Done when:** Panel renders with non-zero data after first 24 h post-launch.

---

## Epic 3 — Drain3 baseline lifecycle

**Goal:** Activate the dormant S3 baseline plumbing in `app/drain_analyzer.py`. Every needed function already exists — they just need a scheduler, a boot-time restore call, and three operator endpoints.

**Why:** A fresh pod has no way to catch up to the last known-good baseline. An oncall engineer who knows the system is healthy can't tell Drain3 "learn from this moment." See `monitoring-docs/sprint3-backlog.md#1` for the long version.

**Out of scope vs. backlog #1:** `sources.yaml` + topology hashing + calibration mode are **deferred**. Dynamic discovery (US-5.1 Phase A) already works; hard-coding sources would regress that. Add only if v1 surfaces a real need.

**Net effort:** 6 SP.

**Dependency order:** 3.6 → 3.7 → 3.8

### US-3.6 — Scheduled snapshots + boot-time restore *(3 SP)*

**Repo:** `monitoring-triage-service`

`app/config.py` additions:

```python
drain3_s3_bucket: str = ""           # empty = disable S3 lifecycle
drain3_s3_snapshot_interval: int = 3600   # seconds; weekly upload at minimum
drain3_s3_prefix: str = "drain3"
```

In `app/main.py:lifespan()`:
- **Boot-time:** if `drain3_s3_bucket` set AND local persistence file is missing/empty → call existing `download_baseline_from_s3()` BEFORE `seed_from_loki()`.
- **Periodic:** APScheduler job calls `upload_snapshot_to_s3()` every `drain3_s3_snapshot_interval` seconds. No-op when bucket empty.

**Files:** `app/config.py`, `app/main.py` (lifespan), `tests/test_drain3_lifecycle.py`.

**Done when:** Fresh pod on fresh PVC + bucket with a known-good baseline → pod boots with the baseline loaded; `total_clusters > 0` immediately; scheduled snapshot fires once within first interval.

### US-3.7 — Operator-facing endpoints *(2 SP)*

**Repo:** `monitoring-triage-service`

Three new endpoints on the triage service:

| Endpoint | Wraps | Purpose |
|---|---|---|
| `POST /drain3/snapshot` | `upload_snapshot_to_s3()` | Force a snapshot now |
| `POST /drain3/baseline/tag` | `tag_known_good()` | "This moment is healthy — save it" |
| `POST /drain3/baseline/restore` | `download_baseline_from_s3()` + reinit miner | Force restore to latest known-good |

`/drain3/stats` extended with: `last_snapshot_uploaded_at`, `last_baseline_restored_at`, `s3_bucket_configured`.

**Files:** `app/main.py`, `tests/test_drain3_endpoints.py`.

**Done when:** Operator runbook in `monitoring-docs/build-guide.html` shows "tag baseline" → 200 → snapshot file exists in S3 with `known-good-YYYY-MM-DD.bin` key.

### US-3.8 — IAM + Grafana visibility *(1 SP)*

**Repos:** `provisioning-monitoring-infra` (IAM) + `monitoring-project` (Grafana)

- IAM policy update on existing `cires-observability-demo-*` bucket: grant `s3:PutObject` + `s3:GetObject` + `s3:ListBucket` to the laptop's IAM principal (or static access-key IAM user used by the triage service).
- Grafana panel on `triage-service-health`: snapshot age (now − `last_snapshot_uploaded_at`) + time since last `tag_known_good`.

**Files:** `provisioning-monitoring-infra/iam.tf` (or new `s3-policies.tf`), `roles/grafana/templates/dashboards/triage-service-health.json`.

**Done when:** Grafana panel renders snapshot age post-launch.

---

## Story summary

| Story | Epic | SP | Status | Repo |
|---|---|---|---|---|
| US-3-CO1..CO12 | 1 | 48 | Done / In Progress | various |
| US-3-CO13 (policy.py cleanup) | 1 | 1 | To Do | triage-service |
| US-3.1 Feedback schema + endpoint | 2 | 3 | To Do | triage-service + mcp-servers |
| US-3.2 Rating UI | 2 | 2 | To Do | triage-service |
| US-3.3 Weekly curation job | 2 | 3 | To Do | triage-service |
| US-3.4 RAG retrieval into prompt | 2 | 5 | To Do | triage-service |
| US-3.5 Feedback observability | 2 | 1 | To Do | triage-service + monitoring-project |
| US-3.6 Scheduled snapshots + boot restore | 3 | 3 | To Do | triage-service |
| US-3.7 Operator endpoints | 3 | 2 | To Do | triage-service |
| US-3.8 IAM + Grafana panel | 3 | 1 | To Do | provisioning-infra + monitoring-project |
| **Total** |  | **69** |  |  |

**Capacity check:** 21 SP new work in 7 remaining days = ~3 SP/day. Tight but achievable at the pace of the past week. The cleanup ticket (US-3-CO13) lands first; Epic 2 in parallel; Epic 3 in week-2-end if Epic 2 wraps early.

---

## Cross-cutting decisions (apply across Epics 2–3)

- **Cron mechanism:** APScheduler in-process. One less container to manage. `apscheduler` → `requirements.txt`.
- **No new infra in Epic 2.** All work is in `monitoring-triage-service` + small additions to `monitoring-mcp-servers`.
- **Epic 3 needs Loki retention ≥ 7 days** (verify before US-3.6) and S3 IAM on the existing bucket.
- **No new metrics namespace.** Everything goes under `triage_*` to match existing conventions.

---

## Sprint 4 candidates (next-sprint backlog)

In rough priority order:

1. **US-5.2 Incident correlator** — 4-alert kill-chain RCA email (carryover from Sprint 2 Tier-1)
2. **Pod-level alert rule fixes** — memory cgroup-churn aggregation + CPU label-mismatch (~30 min each)
3. **Sentence-transformers retriever** (US-3.4 fallback) — only if BM25 underperforms in A/B
4. **O-9 webhook auth + O-10 nightly RCA-history S3 backup** — Friday-slot hardening
5. **GPU migration to us-west-2 + qwen2.5:14b** (deferred 3–5 day effort)
6. **MCP native tool-calling rewrite** (sprint3-backlog #5) — gates on GPU
7. **Trace-ID linkage from log anomalies** (sprint3-backlog #2a)
8. **RCA playbook templates** (sprint3-backlog #2b)
9. **US-5.7 Labeled corpus + F1 tracking**
10. **L2/L3 chaos scenarios** (O-12)
11. **Drain3 self-monitoring loop allowlist** (`service_name=drain3` exclusion)
12. **Pipeline duration instrumentation** per-stage
13. **Doc debt:** `monitoring-project/CLAUDE.md` + stale architecture PNGs

---

## How to import to Jira

The companion file `sprint3-jira-import.csv` is ready to import:

1. Jira → Settings → System → External System Import → CSV
2. Upload `sprint3-jira-import.csv`
3. Column mapping (Jira will guess most):
   - `Issue Type` → Issue Type
   - `Summary` → Summary
   - `Description` → Description
   - `Epic Name` → Epic Name (Epic rows only)
   - `Epic Link` → Epic Link (Story rows; references Epic Name)
   - `Status` → Status
   - `Story Points` → Story point estimate (custom field)
   - `Sprint` → Sprint (custom field — create "Sprint 3" with start 2026-04-23 / end 2026-05-07 first if it doesn't exist)
   - `Priority` → Priority
   - `Labels` → Labels
4. Run import; verify row count matches CSV (3 Epics + 13 Epic-1 stories + 5 Epic-2 + 3 Epic-3 = 24 issues)
