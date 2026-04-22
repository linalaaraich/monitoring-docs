# Sprint 3 Backlog

> **Project:** CIRES AI Observability Platform
> **Sprint 3 start:** TBD (after Sprint 2 closes 2026-04-23)
> **Status:** Living document — add items here as they're surfaced during Sprint 2 work.
>
> This file is the **durable home** for Sprint 3 follow-ups. It is tracked in git (repo `linalaaraich/monitoring-docs`) so the backlog survives any individual machine being torn down.

---

## 1. Drain3 — Scheduled healthy-baseline lifecycle <!-- SPRINT-3-DRAIN3-BASELINE -->

**Priority:** High · **Estimated effort:** 3 pts · **Owner:** Lina
**Surfaced on:** 2026-04-22, during Sprint 2 demo prep (triage pipeline returning "insufficient data" verdicts — Drain3 reported `total_clusters: 0` because there's no scheduled mechanism to tag and restore a known-good baseline).

### Why this matters

Drain3 discriminates between "known log patterns" (`[KNOWN]`) and "new patterns" (`[ANOMALY]`) by comparing incoming log lines to its in-memory template tree. The quality of that tree *is* the quality of the anomaly signal:

- If the tree is **empty** (fresh pod, no persisted state, no seed), everything looks anomalous → useless output.
- If the tree **absorbs bad logs** as baseline (trained during an outage), the next real outage of the same shape won't be flagged → missed anomalies.
- If the tree **drifts** over weeks (logs evolve, versions ship), templates mined months ago bias the model toward things that no longer exist → noise.

The correct operational pattern is: **periodically snapshot a known-good state to durable storage (S3), and restore that baseline on fresh pods or after detected drift.**

### What's already implemented (don't re-do)

In `monitoring-triage-service/app/drain_analyzer.py`:

- `seed_from_loki()` — one-shot startup seed from last 1h of Loki logs. ✅
- `start_background_ingestion()` / `_ingest_loop()` — polls Loki every `drain3_poll_interval=30s`, keeps templates current with live traffic. ✅
- Local file persistence via `FilePersistence` at `/data/drain3_state/drain3_state.bin` (PVC-backed, survives pod restarts). ✅
- `save_snapshot_to_file()` — timestamped local snapshot. ✅
- `upload_snapshot_to_s3(bucket, prefix="drain3/snapshots")` — function exists. ✅
- `download_baseline_from_s3(bucket, prefix="drain3/baselines")` — function exists. ✅
- `tag_known_good(bucket)` — uploads current state as `drain3/baselines/known-good-{date}.bin`. ✅

**The S3 mechanism is built. It's just never invoked.**

### What's missing

1. **No scheduler** calls `upload_snapshot_to_s3()` — the function exists but no background task or cron triggers it.
2. **No boot-time `download_baseline_from_s3()`** — a fresh pod on a fresh PVC has no way to catch up to the last known-good baseline from S3. It only reads the local file (which doesn't exist yet on a fresh pod).
3. **No operator-facing HTTP endpoints** — there's no way to push "snapshot now," "tag this as known-good," or "restore latest baseline" without editing code. An oncall engineer who knows the system is healthy can't tell Drain3 "learn from this moment."
4. **No config for the S3 bucket** — the S3 methods accept `bucket` as a parameter, but `config.py` has no `drain3_s3_bucket` setting. Even a scheduler wouldn't know which bucket to write to.
5. **No drift-detection trigger** — nothing watches the ratio of `[ANOMALY]` lines over time to decide "we should probably re-baseline."

### Acceptance criteria

- [ ] Add `drain3_s3_bucket: str = ""` (and `drain3_s3_snapshot_interval: int = 3600`) to `app/config.py`.
- [ ] Wire these through the `ai-stack` Helm chart (`values.yaml` + `triage-deployment.yaml` env).
- [ ] On pod startup, if `drain3_s3_bucket` is set and the local persistence file is missing/empty, call `download_baseline_from_s3()` before `seed_from_loki()`.
- [ ] Add a second background task (alongside `_ingest_loop`) that calls `upload_snapshot_to_s3()` every `drain3_s3_snapshot_interval` seconds. No-op when bucket is empty.
- [ ] Expose three HTTP endpoints on the triage service:
  - `POST /drain3/snapshot` → `upload_snapshot_to_s3`
  - `POST /drain3/baseline/tag` → `tag_known_good` (the "this is healthy, save it" button)
  - `POST /drain3/baseline/restore` → `download_baseline_from_s3` + reinitialize the in-memory miner
- [ ] Update `/drain3/stats` to also return `last_snapshot_uploaded_at`, `last_baseline_restored_at`, `s3_bucket_configured`.
- [ ] Add a Grafana panel to the **triage-service-health** dashboard showing snapshot age + time since last known-good baseline.
- [ ] IAM: the k3s node (or pod via IRSA when migrated to EKS) needs `s3:PutObject` + `s3:GetObject` + `s3:ListBucket` on the configured bucket. Reuse the existing `cires-observability-demo-*` bucket (S3 already provisioned by Terraform).
- [ ] Document the operator runbook in `monitoring-docs/build-guide.html`: "when is it safe to tag a baseline," "how to force a restore after an incident," "how to read snapshot age in Grafana."
- [ ] Test: fresh pod on fresh PVC + bucket with a known-good baseline → pod boots with the baseline loaded and 0 lines marked anomalous in a subsequent healthy-traffic window.

### Non-goals for this story

- Automatic drift detection (a smarter "when should we re-baseline?" heuristic). That's a future iteration; for Sprint 3 we accept *scheduled periodic snapshots + operator-triggered known-good tagging* as sufficient.
- Cross-region baseline replication. Single-region S3 is fine until we deploy to CIRES private cloud.

### Related files (for the implementer)

- `monitoring-triage-service/app/drain_analyzer.py` — all five S3 methods already exist.
- `monitoring-triage-service/app/config.py` — add new settings here.
- `monitoring-triage-service/app/main.py` — wire boot-time restore + start the periodic-snapshot task in `lifespan()`; register the three HTTP endpoints.
- `monitoring-project/charts/ai-stack/values.yaml` + `templates/triage-deployment.yaml` — expose the config as env.
- `provisioning-monitoring-infra/s3-cloudfront.tf` — bucket already exists; add an IAM policy statement (or leave for later when we do IRSA).

---

## 2. Deeper LLM correlation — playbook templates + LLM-driven MCP tool calling <!-- SPRINT-3-LLM-DEEP-RCA -->

**Priority:** High · **Estimated effort:** 8 pts (split into 3a + 3b + 3c) · **Owner:** Lina
**Surfaced on:** 2026-04-22, evening Sprint 2 demo-prep session. Lina observed that LLM verdicts read like "insufficient evidence, please investigate" rather than the sharp root-cause narrative she expects, and asked whether the LLM can actually correlate logs ↔ traces ↔ metrics for the alert's timeframe.

### Why this matters

Current (post-Sprint-2) behaviour:

- All three pillars share the same time window and same service filter — basic correlation exists.
- Sprint 2 also landed the "anchor context to alert.startsAt" change, so the window covers the incident's timeframe, not the LLM's wake-up moment.
- Evidence bundle size raised from 5 log lines / 1 trace / 3 min to 50 / 10 / 10 min — the LLM has material to reason over.

Still missing (and this is what a "sharp RCA" really needs):

- **No trace-ID linkage.** We pull "recent traces for the service," not "the specific traces whose trace_ids appear in the anomalous log lines." An LLM reasoning about an error log in most cases can't connect it to the actual failing span — Jaeger returns whatever's most recent.
- **No LLM-driven MCP calls.** The triage service pre-fetches one bundle; the LLM can't ask for more data ("show me the spans between 10:00 and 10:02 where status=error"). Our MCP servers are a security boundary + HTTP abstraction, not a tool harness the LLM drives. This is deliberate — llama3.2:3b has weak tool-calling — but it caps how deep any single verdict can go.
- **No structured reasoning playbook.** The system prompt is "you are an SRE, check all three pillars, output JSON." No decision tree for common incident shapes (HTTP 500 surge, DB connection leak, deploy regression, noisy-neighbor latency). The model has to rediscover the SRE playbook for every alert.

### 2a — Trace-ID linkage from log anomalies (low risk, pure ADD)

**Effort:** 2 pts

When `DrainAnalyzer.annotate_lines()` tags a line `[ANOMALY]`, extract any `trace_id=<32hex>` embedded in the line body. For each unique trace_id extracted, issue a targeted Jaeger MCP call (`/tools/get_trace?trace_id=...`) and include those specific traces in `GatheredContext.traces` — **in addition to** the existing service-wide sample. The LLM then sees both "here's 10 random recent traces" and "here's the 3 traces that contain the exact log anomalies you're looking at."

Acceptance:

- [ ] Add `extract_trace_ids(lines)` helper in `drain_analyzer.py` (regex `trace_id=([a-f0-9]{32})`).
- [ ] Add `/tools/get_trace` endpoint to `jaeger_mcp` (exists in the Jaeger HTTP API as `/api/traces/<id>`).
- [ ] In `pipeline.py` between Drain3 annotation and LLM call, resolve each extracted trace_id and merge into `ctx.traces` (dedup by trace_id).
- [ ] Prompt: add a section `"Traces linked to anomalous log lines:"` so the LLM knows which ones to reason over specifically.
- [ ] Test: synthetic alert with a single malformed-JSON POST produces a decision whose `evidence` field references the specific traceID from the log, not a random one.

### 2b — RCA playbook templates (decision-tree skeletons for common shapes)

**Effort:** 3 pts

Lina's original framing: *"give it a bunch of templates with decision trees for what to do that are basically plans to follow or at least build a plan from to get sharpest RCA possible."*

Maintain a small library of **alert-shape → checklist** playbooks. Each playbook is a short structured checklist the LLM should walk before writing its RCA. The triage service picks the closest-matching playbook based on alert labels/name and injects it into the system prompt as *"Here is the RCA checklist for this class of alert; walk it before concluding."*

Concrete shapes to start with (expand iteratively):

1. **HTTP 5xx surge** → check Spring Boot deploy status → DB pool exhaustion? → upstream dependency health → recent deploys → regression window.
2. **HTTP 4xx surge** → client-side payload validation → recent client deploys → rate-limit / auth misconfig → noisy bot.
3. **Latency P95 spike** → DB query plans → GC pressure (JVM metrics) → downstream slow dep → noisy neighbor / CPU throttling.
4. **DB connection pool exhaustion** → leak (active > idle over time) → sudden traffic spike → RDS health → pool size misconfig.
5. **Trace drop / missing spans** → OTel collector health → agent version mismatch → propagator misconfig → batch processor queue size.

Each playbook = ~5–10 bullet SRE-style questions. Total ~50–100 lines of markdown.

Acceptance:

- [ ] New file `monitoring-triage-service/app/playbooks/` with one `.md` per alert shape and a `registry.py` mapping `alertname` regex → playbook path.
- [ ] `llm_client._build_prompt()` selects the best-matching playbook and injects it as a system-prompt section.
- [ ] If no playbook matches, fall back to a generic "check all three pillars" prompt (current behaviour).
- [ ] Log which playbook was selected per invocation (surface as `triage_playbook_selected_total{playbook=...}` counter).
- [ ] Test: at least 3 different alert shapes select 3 different playbooks; a garbage alertname selects the default.

### 2c — Actual LLM-driven MCP tool calling (bigger lift, needs model upgrade)

**Effort:** 3 pts + requires a cloud LLM path

Replace the single-shot prompt with a tool-calling loop. The LLM drives the investigation: it issues MCP queries ("find_traces service=spring-boot start=... end=..."), reads the results, issues follow-ups, then emits the final verdict. This is the "real MCP" shape.

**Blockers to address first:**

- `llama3.2:3b` tool-calling is unreliable — hallucinates tools, invents params, forgets to close loops. We need either (a) Anthropic's Claude via API, (b) a local model with solid tool support (`qwen3:7b-instruct` or similar), or (c) ollama's function-calling mode validated on a larger model.
- Each tool round-trip is one inference. On CPU that multiplies latency by (rounds+1). We need GPU (AWS quota) or a cloud API path for this to be responsive.
- MCP servers need a tools-manifest endpoint the LLM can see (standard MCP `/tools/list` / `/tools/call` shape).

Acceptance:

- [ ] Decide the model: either add `anthropic.api_key` support to `llm_client.py` or validate a larger local model end-to-end.
- [ ] Implement a tool-calling loop in `llm_client.py` (max 5 iterations, hard timeout per iteration).
- [ ] Expose a `/tools/list` endpoint on each MCP server describing its tools in the JSON-schema format the LLM expects.
- [ ] Add `triage_llm_tool_calls_total{tool=...}` + `triage_llm_tool_call_duration_seconds` metrics.
- [ ] Test: run the hourly synthetic alert through the new path, confirm the LLM calls at least 2 distinct MCP tools and the verdict references data obtained via those calls.

### Sequencing recommendation

Do 2a first (smallest, highest immediate value — makes current verdicts sharper). Then 2b (playbooks — pure system-prompt work, no model change). Save 2c for after the GPU quota lands or once we adopt a cloud LLM path.

### Related files

- `monitoring-triage-service/app/context.py` — add trace-linkage step (2a).
- `monitoring-triage-service/app/drain_analyzer.py` — add `extract_trace_ids` (2a).
- `monitoring-mcp-servers/jaeger_mcp/main.py` — add `/tools/get_trace` + `/tools/list` (2a, 2c).
- `monitoring-triage-service/app/llm_client.py` — playbook injection (2b), tool-calling loop (2c).
- `monitoring-triage-service/app/playbooks/` — new directory (2b).
- `monitoring-triage-service/app/config.py` — model selector (2c).

---

## 3. (placeholder — add next item as it's surfaced)

---

## How to add items to this backlog

When a Sprint 2 conversation surfaces a "let's do that in Sprint 3" follow-up, add a new numbered section here with:

- **Why it matters** — the argument for doing it at all.
- **What's already there** — so the next implementer doesn't redo work.
- **What's missing** — concrete gap list.
- **Acceptance criteria** — a checkbox list an implementer can work through.
- **Related files** — paths into the repos.

Commit and push. That way any future Claude Code session that clones the 6 repos will discover this file automatically.
