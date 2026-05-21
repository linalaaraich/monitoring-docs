# Sprint 3 Plan — RCA Quality v2 + Operator Feedback Loop + Hallucination Firewall

> **Sprint window:** 2026-04-23 → 2026-05-08 (16 days nominal; **extended de-facto** — sprint object still open in Jira as of 2026-05-20; closure-vs-roll decision pending per `SESSION_HANDOFF.md` §Decision 1)
> **Status (2026-05-20, Day 28):** Epic 1: 12/13 SP Done (1 SP hygiene gap on US-3-CO13). **Epic 4: 15/15 SP Done ✅** (closed 2026-05-19). Epic 2: 0/7 SP. Epic 3: 0/6 SP. **63 SP shipped, 13 SP carry.**
> **Repos in scope:** `monitoring-triage-service` · `monitoring-docs` · `monitoring-mcp-servers` · `monitoring-project` · `provisioning-monitoring-infra`
> **Capacity (retro):** Plan called for ~77 SP across 16 days × 3 engineers. Actual: Epic 1 + Epic 4 = 63 SP shipped over 2 working bursts (2026-04-23..04-29 + 2026-05-19). Epic 2 + Epic 3 blocked behind a 20-day prototyping/doc-refresh window, deferred to Sprint 4. The team was effectively 1 engineer for the working bursts (Lina solo), not 3.
> **Jira keys:** SCRUM-132..163 (32 work items: 4 epics + 28 stories). See `linalaaraich/jira/Sprint3-additions.csv` + `SPRINT3-README.md` for the import + ID mapping.

---

## Sprint goal

1. **Close out the RCA-quality work** that started inside Sprint 2 ("Epic 5") under a clean Sprint 3 epic — the historical record matches when the work actually shipped.
2. **Ship the operator feedback loop** on top of the existing US-5.3 feedback infrastructure, so the model learns from operator thumbs-up/down + corrections. (Curated RAG retrieval/curation deferred to Sprint 4.)
3. **Wire up the Drain3 baseline lifecycle** — S3 plumbing already exists in `drain_analyzer.py` (built in Sprint 2, never invoked). Add scheduling, boot-time restore, and three operator-facing endpoints.
4. **Close the hallucination-firewall gap** exposed by the 2026-04-29 HighKongP95Latency `0b215ef3` incident — enforce MCP-only data access (no direct DB / Prometheus / in-process reads anywhere the LLM sees data) and wire trace-depth drilling through the existing `get_trace` MCP tool that was never invoked.

## Why this framing

~10 working days of substantive RCA-quality work happened between Sprint 2's official close (2026-04-23) and 2026-04-29. It doesn't fit Sprint 2's Epic 5 scope (UEBA-flavored) and is too coherent to attribute to nothing. Sprint 3 absorbs it as **Epic 1 — RCA Quality v2**, alongside three forward-looking epics (2, 3, 4) for the remaining 9 days.

**Epic 4 was added on 2026-04-29** after the `0b215ef3` decision shipped templated kubectl OOMKill remediations on a Kong p95 latency alert at 0.40 confidence. Root-cause analysis surfaced two structural gaps: (a) the F-4 confidence clamp adjusted the trust signal but didn't strip the offending templated actions, and (b) the pipeline gathers trace data at the service-boundary level only — it never calls `get_trace(trace_id)` to drill into spring-boot's spans, so the LLM correctly identified "upstream is slow" but couldn't name what was slow. Three additional code paths were found violating the MCP-only invariant (entity_baselines direct Prometheus, bounded_agency direct DB + in-process exemplars). Epic 4 closes all of these.

---

## Out of scope (explicitly deferred to Sprint 4)

| Item | Reason |
|---|---|
| **US-5.2 Incident correlator** | 1–2 days; was Tier-1 but would crowd out feedback-loop + hallucination-firewall work. Pull in next sprint. |
| **GPU migration to us-west-2 + qwen2.5:14b** | Laptop @ 32 GB still serves qwen2.5:7b adequately; defer until tool-calling rewrite needs it. |
| **MCP native tool-calling rewrite** (backlog #5) | 5 SP rewrite, gates on GPU. |
| **Tier 3 — Iterative agentic gather (hypothesis-tree state)** | 3-5 day rewrite of `bounded_agency.py`; gates on Sprint 3's Tier 4 measurement scaffold (US-3.17) being green first. |
| **Planner → Executor → Writer** (backlog #2c) | Gates on tool-calling. |
| **Trace-ID linkage from log anomalies** (backlog #2a) | 2 SP, attractive but additive — no sprint capacity. |
| **RCA playbook templates** (backlog #2b) | Complements Epic 2 but additive. |
| **US-5.7 Labeled corpus expansion + F1 tracking** | Sprint 3's US-3.17 seeds the corpus + CI gate; broader F1 measurement is Sprint 4. |
| **Curated RAG retrieval + weekly curation job** (was US-3.3, US-3.4) | Deferred — depends on accumulated feedback volume; corpus needs to grow before retrieval improves outcomes. |
| **O-9 webhook auth, O-10 nightly RCA-history S3 backup, O-11 ansible-vault** | Friday-slot hardening or Sprint 4. |
| **`monitoring-project/CLAUDE.md` + PNG diagram refresh** | Single doc-debt commit, anytime. |

---

## Epic 1 — RCA Quality v2 (close-out)

**Goal:** Backfill Sprint 3's epic record with RCA-quality work shipped between 2026-04-23 and 2026-04-29. **All "Done" stories already have commits in their respective repos.**

**Net effort:** 48 SP shipped + 1 SP hygiene gap on US-3-CO13.

| Jira | ID | Story | SP | Status |
|---|---|---|---|---|
| SCRUM-136 | US-3-CO1 | US-5.1 Phase A — Per-service Drain3 (`dict[service → TemplateMiner]`) | 3 | Done |
| SCRUM-137 | US-3-CO2 | US-5.1 Phase B — Entity baselines (verification dependency US-3.12 shipped 2026-05-19) | 3 | Done |
| SCRUM-138 | US-3-CO3 | US-5.3 — Closed-loop feedback override/confirm + precision/recall metrics | 5 | Done |
| SCRUM-139 | US-3-CO4 | US-5.4 — Adaptive thresholds on 3 flappiest rules | 3 | Done |
| SCRUM-140 | US-3-CO5 | US-5.8 — Recurrence gates (pre-LLM + post-LLM, MediumCpu/Mem opt-in) | 5 | Done |
| SCRUM-141 | US-3-CO6 | RCA quality hardening F-1..F-5 (Drain3 webhook enrichment, hallucination blocklist, confidence clamp, surface-only LEDE validator, retry-on-violations) | 8 | Done |
| SCRUM-142 | US-3-CO7 | Exemplar library (D17, 14 archetypes — bumped from 11 in commit `134e811`) + RCA prose philosophy (D18 + D19) | 5 | Done |
| SCRUM-143 | US-3-CO8 | Dashboard redesign + `/dashboard/guide` operator manual | 3 | Done |
| SCRUM-144 | US-3-CO9 | Pod-level alert rules `PodHighMemoryUsage` + `PodHighCpuUsage` (2 query bugs filed for Sprint 4) | 3 | Done |
| SCRUM-145 | US-3-CO10 | Chaos test harness (`scripts/chaos/`, 4 test classes, RCA scorer) | 5 | Done |
| SCRUM-146 | US-3-CO11 | Daily audit feeds — static (cloud /schedule routine) + live (controller cron) | 3 | Done |
| SCRUM-147 | US-3-CO12 | Audit repo migrations (3 manual audits → private repo) + SESSION_HANDOFF history scrub | 2 | Done |
| SCRUM-148 | US-3-CO13 | Codify `app/policy.py` + `app/bypass_llm.yaml` — **hygiene gap**: marked Done in Jira 2026-05-19 but the two files don't exist in `monitoring-triage-service` (logic stayed inline; the extraction was deemed not worth the churn). Reopen-or-rename pending Decision 1 in `SESSION_HANDOFF.md`. | 1 | Hygiene gap |

---

## Epic 2 — Operator feedback loop

**Goal:** Capture per-decision operator feedback (thumbs ↑/↓ + structured tags + free-text correction) so future RCAs can learn from operator signal.

**Why:** The exemplar library is a frozen seed of 11 archetypes. As real US-5.3 `feedback` accumulates (override/confirm), there's no closed loop bringing operator thumbs-up/down + corrections into the system. Epic 2 captures the signal and exposes it through MCP. Curated-RAG retrieval (formerly US-3.3 + US-3.4) is deferred to Sprint 4 — it depends on accumulated feedback volume.

**Net effort:** 7 SP (was 14 SP before Sprint 4 deferral). **0/7 shipped as of 2026-05-20** — carried to Sprint 4 (Decision 1 pending: extend Sprint 3 vs roll to Sprint 4 / EPIC11).

**Dependency order:** 3.1 → 3.2 → 3.5

**Jira:** SCRUM-149 (US-3.1) · SCRUM-150 (US-3.2) · SCRUM-151 (US-3.5). Parent epic SCRUM-133 still marked "To Do" in the export despite child stories already in "In Progress"; epic should be bumped to "In Progress" or "Done" depending on Decision 1.

### US-3.1 — Extend feedback schema + endpoint *(4 SP)*

**Repo:** `monitoring-triage-service` + `monitoring-mcp-servers`

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

**4 read-only MCP tools** on `monitoring-mcp-servers/rca_history_mcp/` (combined scope with US-3.14):
- `get_feedback_stats` — counts by rating, top tags, rater frequency
- `get_high_rated_examples(limit, since_days)` — up-rated decisions for prompt injection
- `get_similar_decisions(alert_name, days, min_quality, min_confidence)` — quality-filtered lookup (replaces direct-DB call in `bounded_agency.py:rca_history.similar`)
- `get_low_rated_examples_for_alert(alert_name, days)` — anti-examples ("here's what we got wrong before")

**Files:**
- `app/rca_store.py` — schema migration + `record_rating()` method
- `app/models.py` — `RatingFeedbackRequest` Pydantic schema
- `app/main.py` — new endpoint
- `tests/test_feedback_rating.py` — CRUD + validation; complement `test_feedback_us53.py`
- `monitoring-mcp-servers/rca_history_mcp/main.py` — 4 new tools

**Done when:** Migration is idempotent; endpoint rejects invalid combos; all 4 MCP tools return sane stats over a seeded test DB; existing US-5.3 endpoints unaffected.

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

### US-3.5 — Feedback observability *(1 SP)*

New Prometheus metrics:
- `feedback_total{rating}`
- `feedback_tag_total{tag}`

New Grafana panel on `triage-service-health` dashboard: feedback volume + tag breakdown.

**Files:** `app/metrics.py`, `roles/grafana/templates/dashboards/triage-service-health.json`.

**Done when:** Panel renders with non-zero data after first 24 h post-launch.

---

## Epic 3 — Drain3 baseline lifecycle

**Goal:** Activate the dormant S3 baseline plumbing in `app/drain_analyzer.py`. Every needed function already exists — they just need a scheduler, a boot-time restore call, and three operator endpoints.

**Why:** A fresh pod has no way to catch up to the last known-good baseline. An oncall engineer who knows the system is healthy can't tell Drain3 "learn from this moment." See `monitoring-docs/sprint3-backlog.md#1` for the long version.

**Out of scope vs. backlog #1:** `sources.yaml` + topology hashing + calibration mode are **deferred**. Dynamic discovery (US-5.1 Phase A) already works; hard-coding sources would regress that. Add only if v1 surfaces a real need.

**Net effort:** 6 SP. **0/6 shipped as of 2026-05-20** — carried to Sprint 4 (Decision 1 pending; same fate as Epic 2).

**Dependency order:** 3.6 → 3.7 → 3.8

**Jira:** SCRUM-152 (US-3.6) · SCRUM-153 (US-3.7) · SCRUM-154 (US-3.8). Parent epic SCRUM-134 marked "To Do" despite child stories already "In Progress"; same status-update needed as Epic 2.

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

## Epic 4 — Hallucination firewall + trace depth

**Goal:** Close the structural gap exposed by the 2026-04-29 `0b215ef3` HighKongP95Latency incident along two dimensions: **MCP-only data access** (every data source the LLM sees must come through an MCP bridge — no direct DB / Prometheus / in-process reads) and **trace depth** (drill into per-span attributes via the existing `get_trace` MCP tool that was never wired up).

**Why:** The `0b215ef3` decision emailed `kubectl set resources --limits=memory=2Gi` + `kubectl rollout restart deploy/spring-boot` as remediation for a Kong p95 latency alert. Investigation found three structural causes: (a) the F-4 confidence clamp adjusted the trust signal but didn't strip templated kubectl actions; (b) the pipeline never called `get_trace(trace_id)` so the LLM saw only service-boundary trace summaries — it correctly identified "upstream is slow" but couldn't name what was slow inside spring-boot; (c) several code paths read data directly (entity_baselines → Prometheus, bounded_agency → SQLite, exemplars → in-process import), bypassing the MCP hallucination firewall. Epic 4 ships fixes for all three on top of a measurement scaffold (US-3.17) so Sprint 4's Tier 3 agentic loop can be built and measured cleanly.

**MCP-only invariant** (durable architectural rule, applies to all future work): every data source the LLM sees must come through an MCP bridge. Direct `httpx`/`requests`/DB calls are forbidden outside the MCP servers themselves and the sanctioned `_mcp_call` helper. Boot-time/migration code (lifespan, schema init) is exempt — it never feeds the LLM.

**Tier mapping:**
- **Tier 0** (US-3.9): F-4 clamp strips actions → ships immediately, ~45 min
- **Tier 1** (US-3.15): trace drill via `get_trace` MCP → the structural fix
- **Tier 2** (US-3.11): hypothesis-menu validator → backstop
- **Tier 4** (US-3.17): chaos scorer 5th axis + corpus seed + CI gate → measurement scaffold for Sprint 4
- **MCP integrity** (US-3.12, US-3.13, US-3.14, US-3.16): four code-path refactors + a CI lint
- **Bug** (US-3.10): wrong-archetype lookup neutralized by Tier 0 but worth fixing at the source

**Net effort:** 15 SP.

**Dependency order:** 3.9 ∥ 3.10 (both unblocking) → 3.11 ∥ 3.12 ∥ 3.13 → 3.14 → 3.15 → 3.16 → 3.17

### US-3.9 — Tier 0: Diagnostic-only actions on F-4 clamp *(1 SP, Highest)*

**Repo:** `monitoring-triage-service`

When the F-4 confidence clamp fires (`pipeline.py:650-673`), strip `decision.suggested_actions` and emit read-only diagnostic verbs in a **new** `decision.diagnostic_steps` field instead. Keeps templated/bad actions out of operator emails while clearly signaling "investigate, don't remediate."

Schema change:

```python
class LLMDecision(BaseModel):
    # ... existing fields ...
    suggested_actions: list[str]            # state-changing remediations (existing)
    diagnostic_steps: list[str] = Field(default_factory=list)   # NEW
```

Diagnostic verbs are alert-aware. For `HighP95Latency` / `HighKongP95Latency`:
- "Open Jaeger and inspect the slowest trace for service=`{service}` in the last 15 min"
- spring-boot pivots: `hikaricp_connections_active / hikaricp_connections_max`, `rate(jvm_gc_pause_seconds_sum[5m])`
- kong pivots: `kong_upstream_latency_ms` vs `kong_proxy_latency_ms` p95
- Explicit "do NOT run kubectl rollout/scale/set commands until a specific cause is named"

Email + dashboard updates: `notifier.py:_build_escalation_body` and dashboard renderer split into two cards — "Suggested actions" (suppressed when clamped) and "Diagnostic steps" (always shown when populated).

**Validation case:** replay decision `0b215ef3-74fa-4e1f-88a4-057437f04d0e` through the patched pipeline. Assert: confidence=0.40, `suggested_actions=[]`, `diagnostic_steps[0].startswith("Open Jaeger")`, no `kubectl` substring anywhere in either field.

**Files:** `app/pipeline.py` (Step 6d), `app/models.py` (LLMDecision), `app/clamp_actions.py` (new — diagnostic verb generator), `app/notifier.py` (email template), `app/main.py` (dashboard /decisions endpoint), `tests/test_pipeline_clamp.py` (new).

**Done when:** Replay test passes; no in-flight decisions email kubectl actions at confidence ≤ 0.4.

### US-3.10 — Bug: HighKongP95Latency wrong-archetype lookup *(1 SP, Highest)*

**Repo:** `monitoring-triage-service`

`HighKongP95Latency` matched the OOMKill action template (`suggested_actions.yaml:67-68`) during the `0b215ef3` incident — emitted `kubectl set resources --limits=memory=2Gi` + `kubectl rollout restart`. Investigate `app/action_templates.py` and `app/suggested_actions.yaml` to find the keying bug (likely a wildcard/fallback match firing for an alert that should have no template). Fix.

Add unit test asserting `HighKongP95Latency` (and `HighP95Latency`) do NOT return any `kubectl set resources` / `kubectl rollout restart` actions from the template lookup.

**Files:** `app/action_templates.py`, `app/suggested_actions.yaml`, `tests/test_action_templates.py`.

**Done when:** Test passes; lookup either returns latency-appropriate actions or empty (Tier 0 fills with diagnostic_steps in either case).

### US-3.11 — Tier 2: Hypothesis-menu validator + cause-evidence rule *(2 SP, High)*

**Repo:** `monitoring-triage-service`

Add `_HYPOTHESIS_MENU_PATTERNS` to `app/response_validator.py` to flag prose listing alternatives without committing — `"possibly X or Y"`, `"either A or B"`, `"may be due to (a slow query|pool saturation)"`, `"could be one of"`. Add cause-must-share-token-with-evidence rule: tokenize the RCA's first sentence (4+ char words), tokenize `decision.evidence`, fail if intersection minus stopwords is empty.

Both rules ship **aggressive behind a feature flag** `triage_hypothesis_menu_strict` (default `True`), with a new Prometheus metric `triage_validator_retries_total{reason}`. If FP rate exceeds ~5% in production, dial back via the flag without redeploying.

Hits trigger the existing retry path (`pipeline.py:444-566`); Tier 0 clamp is the safety net for retries that still fail.

**Files:** `app/response_validator.py` (patterns + 2 new check blocks), `app/config.py` (feature flag), `app/metrics.py` (counter), `tests/test_response_validator.py` (8+ new cases including FP/TP boundaries).

**Done when:** Replay `0b215ef3` RCA → `should_retry=True` due to "hypothesis-menu" hit. New unit cases cover legitimate `or`-prose that should NOT trigger.

### US-3.12 — MCP integrity: route entity_baselines through prometheus_mcp *(1 SP, High)*

**Repo:** `monitoring-triage-service` + possibly `monitoring-mcp-servers`

`app/entity_baselines.py:144` calls `httpx.AsyncClient.get(prometheus_url + "/api/v1/query")` directly — violates the MCP-only invariant. Refactor to call `prometheus_mcp` instead. Verify the existing `prometheus_mcp /tools/query` covers `quantile_over_time(...[7d])` efficiently; if not, extend the MCP tool surface with a dedicated endpoint.

Update the call site in `app/pipeline.py:360-390` to pass the MCP URL not the raw Prometheus URL.

This story also closes US-5.1 Phase B's verification dependency (US-3-CO2) — once baselines flow through observable MCP traffic, we can confirm baseline-σ claims appear in real RCAs by inspecting MCP request logs.

**Files:** `app/entity_baselines.py`, `app/pipeline.py`, `app/config.py` (URL setting), possibly `monitoring-mcp-servers/prometheus_mcp/main.py`.

**Done when:** No `httpx` calls in `entity_baselines.py`; baseline fetches show up in `prometheus_mcp` request logs; existing baseline tests still pass.

### US-3.13 — MCP integrity: route bounded_agency rca_history through MCP *(1 SP, High)*

**Repo:** `monitoring-triage-service`

`app/bounded_agency.py:222-242` does direct DB lookup for `rca_history.similar` and direct in-process import for `rca_history.list_exemplars` / `rca_history.get_exemplar`. Refactor all three to HTTP calls against `rca_history_mcp` on port 8095.

Existing `rca_history_mcp` tools cover `search_rcas` (similar shape). For `list_exemplars` / `get_exemplar`, add tools to `rca_history_mcp` exposing the curated exemplar library (move `app/exemplars/` data into a location the MCP server can load, OR expose a read-only API on the triage service that the MCP wraps — pick whichever is cleaner during implementation).

After this lands, the entire `bounded_agency.py` tool whitelist routes through MCP servers exclusively.

**Files:** `app/bounded_agency.py`, `monitoring-mcp-servers/rca_history_mcp/main.py` (new exemplar tools), tests.

**Done when:** No direct `store.*` or `from app import exemplars` calls remain in `bounded_agency.py`; existing bounded-agency tests pass against the MCP-routed paths.

### US-3.14 — Quality-rated rca_history MCP tools *(2 SP, High)*

**Repo:** `monitoring-mcp-servers`

Combined with US-3.1's planned MCP additions. Adds quality-aware tools so the LLM can prefer high-rated similar decisions and learn from low-rated ones:

- `get_similar_decisions(alert_name, days, min_quality, min_confidence)` — filter by `rca_quality` ∈ {actionable, data_starved, needs_review} and minimum `llm_confidence`. Replaces the direct-DB call in US-3.13.
- `get_low_rated_examples_for_alert(alert_name, days)` — anti-examples (rating='down' from US-3.1's feedback table) for the prompt's "Past mistakes — do NOT repeat" section.

Plus US-3.1's `get_feedback_stats` and `get_high_rated_examples`. All 4 land in one `rca_history_mcp` PR.

**Files:** `monitoring-mcp-servers/rca_history_mcp/main.py`, `tests/test_rca_history_mcp.py`.

**Done when:** All 4 tools return sane results over a seeded test DB; integration test exercises `min_quality='actionable'` filtering + low-rated-example retrieval.

### US-3.15 — Tier 1: Deeper trace gather via get_trace MCP *(3 SP, High)*

**Repo:** `monitoring-triage-service`

`app/context.py:_fetch_jaeger` (lines 274-301) currently calls `find_traces` (summary-only) and never drills. Extend to call the existing `jaeger_mcp /tools/get_trace` endpoint on top-K slowest + any error traces (default `K=3`, parallel via `asyncio.gather`).

Add new models in `app/models.py`:

```python
class TraceSpanSummary(BaseModel):
    trace_id: str
    span_id: str
    operation: str
    service: str
    duration_ms: float
    parent_operation: str | None = None
    db_statement: str | None = None    # tags["db.statement"], truncated 200 chars
    http_target: str | None = None
    http_status: str | None = None
    error: bool = False

class TraceDrillResult(BaseModel):
    trace_id: str
    total_duration_ms: float
    span_count: int
    dominant_service: str | None
    dominant_service_pct: float | None
    slowest_span: TraceSpanSummary | None
    db_call_count: int = 0
    db_total_ms: float = 0.0
    has_errors: bool = False

# GatheredContext gains: trace_drills: Optional[list[TraceDrillResult]] = None
```

New prompt section in `app/llm_client.py` rendering: dominant service + percentage + db_call_count + db_total_ms, plus the slowest span line with `operation`, `db.statement` (if present, truncated), `http.target` + status, error flag.

**Pre-implementation step (per Q5=B):** sample 10 spring-boot traces in production via `curl http://jaeger-mcp:8094/tools/get_trace?trace_id=...`, eyeball `db.statement` values to confirm JDBC parameterization. **Default assumption:** parameterized — no PII redaction needed. **If literal values appear:** add a regex redactor stripping numeric literals (`\d{3,}`), email-shaped tokens, UUIDs before the `db.statement` field lands in evidence/email.

**Files:** `app/context.py` (`_fetch_jaeger` + new helpers `_pick_drill_candidates`, `_summarize_trace`), `app/models.py` (new dataclasses), `app/llm_client.py` (prompt section), `app/config.py` (`jaeger_drill_top_k`, `jaeger_drill_min_duration_ms`), `tests/test_context_jaeger_drill.py` (new).

**Done when:** Replay `0b215ef3-…` window — prompt sent to LLM includes a "Trace span breakdown" section with `dominant=spring-boot 99%, db_calls=N, db_total=Xms, slowest span: SELECT … = Yms`. New chaos test `high_p95_latency` (deferred to Sprint 4) will be the end-to-end verifier.

### US-3.16 — MCP integrity: CI lint forbidding direct data access *(2 SP, High)*

**Repos:** all (CI rule applies repo-wide)

Add a CI check (ruff custom rule, semgrep pattern, or a grep-based pre-commit) that forbids `httpx`/`requests`/`aiosqlite`/raw-SQL calls outside the allowed boundaries:

**Allowed:** `monitoring-mcp-servers/*` (the MCP layer itself), `app/context.py:_mcp_call` (the only sanctioned bridge from triage-service to MCPs).

**Exempt boundary** (per Q3=B): lifespan/startup/migration code — `app/main.py:lifespan`, `app/rca_store.py:_init_schema`, drain3 boot restore in US-3.6's `download_baseline_from_s3()`. These are operator-tier and never feed the LLM.

**Forbidden everywhere else:** any module that runs during request handling and could reach the LLM prompt.

Document the rule in a new `monitoring-docs/architectural-invariants.md` page so it survives team turnover.

**Files:** `.github/workflows/lint.yml` (or equivalent CI config), `pyproject.toml` (ruff config), `monitoring-docs/architectural-invariants.md` (new doc), pre-commit hook.

**Done when:** CI fails the build when a PR adds a forbidden direct call; a deliberate test PR with a `httpx` call in `app/pipeline.py` is rejected.

### US-3.17 — Tier 4: Chaos scorer 5th axis + corpus seed + CI gate *(2 SP, Medium)*

**Repos:** `monitoring-project` (chaos scorer) + `monitoring-triage-service` (corpus + CI)

**Why this must land before Sprint 4's Tier 3:** Tier 3 (iterative agentic loop with hypothesis-tree state) is a high-cost, high-risk change. Without a binary "did the RCA name the actual injected cause?" metric and a corpus regression gate, you ship Tier 3 unmeasured. Tier 4 is the scoreboard.

**Chaos scorer extension** (`monitoring-project/scripts/chaos/lib/rca_scorer.py`):

```python
@dataclass
class QualityScore:
    cause_first_lede: float
    named_cause: float
    specific_evidence: float
    state_changing_action: float
    cited_injected_cause: float    # NEW — 0.0 or 1.0
    notes: list[str]
```

Add `expected_cause_tokens: list[str]` to the `ChaosTest` base class. Score 1.0 if any token appears in `decision.rca_report` or `decision.evidence`; 0.0 otherwise.

**Corpus seed:** `monitoring-triage-service/tests/corpus/labeled/bad/hypothesis_only_clamp_leak.json` — full payload from `0b215ef3-74fa-4e1f-88a4-057437f04d0e` plus expected_violations, expected_post_clamp_actions_must_not_contain (`kubectl rollout`, `kubectl set resources`), expected_post_clamp_actions_must_contain_any_of (`Open Jaeger`, `hikaricp_connections_active`, `jvm_gc_pause_seconds`).

**CI regression gate:** `tests/test_corpus_regression.py` — every JSON in `corpus/labeled/bad/*` must trigger ≥1 violation from `validate()`.

**Files:** `monitoring-project/scripts/chaos/lib/rca_scorer.py`, `monitoring-project/scripts/chaos/tests/base.py`, `monitoring-triage-service/tests/corpus/labeled/bad/hypothesis_only_clamp_leak.json` (new seed), `monitoring-triage-service/tests/test_corpus_regression.py` (new), CI config.

**Done when:** Chaos report shows new `cited_injected_cause` column with binary pass/fail per test row. A deliberate test PR weakening the validator (removing the hypothesis-menu pattern) fails the corpus regression gate.

---

## Story summary

| Story | Epic | SP | Status | Repo |
|---|---|---|---|---|
| US-3-CO1..CO12 | 1 | 48 | Done 2026-04-23..04-29 | various |
| US-3-CO13 (policy.py cleanup) | 1 | 1 | **Dropped 2026-05-20** — refactor superseded, policy logic stayed inline | triage-service |
| US-3.1 Feedback schema + 4 MCP tools | 2 | 4 | In Progress (carried into Sprint 4 2026-05-20) | triage-service + mcp-servers |
| US-3.2 Rating UI | 2 | 2 | In Progress (carried into Sprint 4 2026-05-20) | triage-service |
| US-3.5 Feedback observability | 2 | 1 | To Do (carried into Sprint 4 2026-05-20) | triage-service + monitoring-project |
| US-3.6 Scheduled snapshots + boot restore | 3 | 3 | In Progress (carried into Sprint 4 2026-05-20) | triage-service |
| US-3.7 Operator endpoints | 3 | 2 | In Progress (carried into Sprint 4 2026-05-20) | triage-service |
| US-3.8 IAM + Grafana panel | 3 | 1 | In Progress (carried into Sprint 4 2026-05-20) | provisioning-infra + monitoring-project |
| US-3.9 Tier 0 diagnostic-only on clamp | 4 | 1 | Done 2026-04-29 | triage-service |
| US-3.10 HighKongP95Latency wrong-archetype bug | 4 | 1 | Done 2026-04-29 | triage-service |
| US-3.11 Tier 2 hypothesis-menu validator | 4 | 2 | Done 2026-04-29 | triage-service |
| US-3.12 MCP integrity — entity_baselines | 4 | 1 | **Done 2026-05-19** | triage-service + mcp-servers |
| US-3.13 MCP integrity — bounded_agency rca_history | 4 | 1 | **Done 2026-05-19** | triage-service |
| US-3.14 Quality-rated rca_history MCP tools | 4 | 2 | **Done 2026-05-19** | mcp-servers |
| US-3.15 Tier 1 deeper trace gather | 4 | 3 | **Done 2026-05-19** | triage-service |
| US-3.16 MCP integrity CI lint | 4 | 2 | **Done 2026-05-19** | all repos + monitoring-docs |
| US-3.17 Tier 4 chaos scorer + corpus seed | 4 | 2 | **Done 2026-05-19** | monitoring-project + triage-service |
| **Total** |  | **77** | **63 SP Done / 1 SP Dropped / 13 SP carried to Sprint 4** |  |

**Capacity check (retro 2026-05-20):** Plan called for 28 SP new+changed work over 9 remaining days × 3-engineer team. Actual: Epic 4 (15 SP) shipped in a single focused session on 2026-05-19 by Lina solo, after a 20-day prototyping/doc-refresh window (2026-04-30 → 2026-05-18). Epic 2 + Epic 3 (13 SP) blocked behind that window — never started, carried to Sprint 4. The "3-engineer team" assumption was the planning fiction: the working team was effectively 1 engineer for the Sprint 3 work bursts. Lesson for Sprint 4 capacity planning: size against 1 engineer × ~5 SP/day burst capacity, not 3 × 3.1 SP/day.

---

## Cross-cutting decisions (apply across Epics 2–4)

- **Cron mechanism:** APScheduler in-process. One less container to manage. `apscheduler` → `requirements.txt`.
- **No new infra in Epic 2.** All work is in `monitoring-triage-service` + small additions to `monitoring-mcp-servers`.
- **Epic 3 needs Loki retention ≥ 7 days** (verify before US-3.6) and S3 IAM on the existing bucket.
- **No new metrics namespace.** Everything goes under `triage_*` to match existing conventions.
- **MCP-only data access invariant** (Epic 4, durable rule): every data source the LLM sees must come through an MCP bridge. Direct `httpx`/`requests`/DB calls are forbidden in any module that can reach an LLM prompt. Boot-time/migration code is exempt. Enforced by the US-3.16 CI lint and documented in `architectural-invariants.md`.
- **Diagnostic-action schema** (Epic 4, Q1=B): `LLMDecision` gains a new `diagnostic_steps: list[str]` field separate from `suggested_actions`. Email + dashboard render them as distinct cards. Forward-compatible with Sprint 4's per-decision diagnostic-vs-remediation routing.
- **Hypothesis-menu validator strictness** (Epic 4, Q2=C): aggressive patterns ship behind `triage_hypothesis_menu_strict=True` flag with `triage_validator_retries_total{reason}` metric. Dial back if FP rate >5%.
- **MCP-integrity lint scope** (Epic 4, Q3=B): exempt boot-time code (lifespan, schema init, drain3 boot restore). Strict everywhere else.

---

## Sprint 4 candidates (next-sprint backlog)

> **Superseded 2026-05-19.** The 16-item list previously held here has been replaced by a 24-item P-tag-integrated ranking after the 2026-05-19 real-load investigation surfaced findings P0–P11. See **`sprint-history.html` §"Sprint 4 candidates — ranked priority list"** for the authoritative ordered list with per-item evidence and gate.
>
> **GPU migration to us-west-2 + `qwen2.5:14b` was dropped on cost grounds 2026-05-19, then reversed and shipped 2026-05-21 after a Lambda-autoshutoff cost-frame rebuild** — see `decisions-log.html#d24`. The Sprint-4 P0 latency bundle ships as defensive margin now rather than as the primary latency intervention. The MCP native tool-calling rewrite (previously gated on the GPU) is Sprint 4 item #10 and can take advantage of the larger model's better function-calling reliability.
>
> The Sprint 4 import for Jira lives at **`linalaaraich/jira/Sprint4-additions.csv`** (4 themed epics EPIC9/10/11/12 + 29 stories, 100 SP — EPIC12 predictive observability + S4-HF-01 bounded-agency widening added 2026-05-20/21). See **`linalaaraich/jira/SPRINT4-README.md`** for the import + bulk-edit instructions.

---

## How to import to Jira

The Jira-import CSV lives in the dedicated Jira repo: **`linalaaraich/jira/Sprint3-additions.csv`** (matches the Sprint 2 `Jira-additions.csv` format with 13 columns including `Work item Id`, `Work type`, and `Parent` — the column shape Jira's importer requires).

1. Jira → Settings → System → External System Import → CSV
2. Upload `Sprint3-additions.csv` from the Jira repo
3. Column mapping (Jira will recognize most automatically since this matches the Sprint 2 import):
   - `Work item Id` → Work item ID
   - `Summary` → Summary
   - `Work type` → Work type (Epic / Story)
   - `Status` → Status
   - `Priority` → Priority
   - `Labels` → Labels
   - `Description` → Description
   - `Sprint` → Sprint (create "SCRUM Sprint 3" with start 2026-04-23 / end 2026-05-08 first if it doesn't exist)
   - `Story Points` → Story point estimate
   - `Parent` → Parent (links stories to their epic via `Work item Id`)
   - `Reporter` → Reporter
   - `Assignee` → Assignee
   - `Due date` → Due date
4. Run import; verify count: **32 work items** = 4 Epics (EPIC5/6/7/8) + 28 Stories (S3-CO-01..13, S3-FB-01..03, S3-DR-01..03, S3-HF-01..09).
5. Each story description carries a `Cross-reference: US-3.X` line in its metadata footer, mapping the Jira ID back to the US-3.X IDs used throughout this plan document.
