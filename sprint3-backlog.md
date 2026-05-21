# Sprint 3 Backlog

> **Project:** CIRES AI Observability Platform
> **Sprint 3 start:** TBD (after Sprint 2 closes 2026-04-23)
> **Status:** Living document — add items here as they're surfaced during Sprint 2 work.
>
> **Historical note (added 2026-05-21, audit I-3):** references to `llama3.2:3b` below are pre-Sprint-3 comparison baselines from the CPU-fallback feasibility analysis. The production model is `qwen2.5:7b-instruct` on Ollama; no CPU fallback is configured.
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

### 2c — Planner → Executor → Writer (bounded two-pass retrieval, Lina's 2026-04-22 idea)

**Effort:** 3 pts · **Status:** preferred design · **Replaces** the unbounded-agent-loop shape originally sketched here

> **Update 2026-04-23:** With the AI moved to a dedicated GPU box running `qwen2.5:14b-instruct` (see §4), the *unbounded* tool-calling shape also becomes viable — 14B-class models do tool calling reliably and GPU inference puts per-round latency at ~30s. Planner→Executor→Writer is still the **lower-risk default** (bounded latency, two inferences, works even if the model occasionally goes off-rails), but we can evaluate full tool-calling as a follow-on once §5 lands. The mechanics of that full-loop implementation are documented in §5.

Instead of a full ReAct loop (LLM → tool → LLM → tool → … → verdict), run a **two-inference** pipeline:

1. **Planner pass.** Same webhook, same MCP fan-out producing a *small* initial bundle. The LLM is prompted *not* to write a verdict, but to output a JSON plan: `{"reasoning","can_decide_now","requests":[...]}` where each request uses one of a fixed vocabulary of ~4 retrieval types (`traces_by_id`, `logs_by_pattern`, `metric_instant`, `operation_list`). Max 5 requests.
2. **Executor.** Pure code in the triage service: for each valid request, call the appropriate MCP tool. Unknown request types are ignored (not crashes). Merge the returned evidence with the initial bundle.
3. **Writer pass.** Same verdict schema we have today, now prompted with the *expanded* bundle. Writes the final RCA.

**Why this beats unbounded tool calling for our constraints:**

- **3B models can't reliably manage an agent loop**, but they CAN output a fixed-schema JSON list once. The planner phase asks for one well-defined thing, and our existing strict-JSON retry covers parse failures.
- **Exactly 2 inferences regardless of how much evidence is requested** — bounded latency. On CPU: 2 × ~10 min = ~20 min (within the 40-min pipeline budget). On GPU (Sprint 3 target): 2 × ~30s = ~1 min.
- **Same safety nets still apply** — circuit breaker, parse-retry, timeout passthrough, Layer 2 suppression all short-circuit before the planner phase when relevant.

**Short-circuits:**
- `can_decide_now=true` or `requests=[]` → skip executor, run writer on original bundle (same as today's one-shot).
- Planner-phase parse fail after retry → fall back to one-shot on original bundle.
- Writer-phase failure → existing NEEDS_HUMAN_REVIEW fallback path.

**Sandbox feasibility test (ran 2026-04-22 evening):** see `scripts/sandbox-planner-prompt.sh` and `/var/log/cires-sandbox-planner.log` on the k3s VM. Exercises the planner prompt against `llama3.2:3b` with a realistic connection-pool-exhaustion alert. If the output validates as `{reasoning, can_decide_now, requests:[typed]}` with no invented request types, the design is viable for the current model. If it hallucinates types or produces prose, we need either a larger model (see §3 below) or a stricter JSON-mode approach before implementation.

**Acceptance:**

- [ ] Planner system prompt in `llm_client.py` (separate constant from the current verdict prompt).
- [ ] `PlanRequest` Pydantic models for each of the four request types; `InvestigationPlan` envelope.
- [ ] `executor.py` (new) maps each request type to an MCP call and returns merged evidence.
- [ ] `pipeline.py` orchestrates planner → executor → writer with short-circuits.
- [ ] Writer prompt explicitly references "expanded evidence (targeted by planner)" so the model knows to ground its verdict in the specific requested data.
- [ ] New metrics: `triage_planner_requests_total{type=...}`, `triage_planner_parse_failures_total`, `triage_executor_duration_seconds`.
- [ ] Test end-to-end with an alert that clearly needs follow-up evidence (e.g. the `BackendHigh5xxRate` scenario with trace-linked log anomalies) — the resulting verdict's `evidence` field should cite data obtained via the executor, not the initial bundle.

### Sequencing recommendation

Do 2a first (smallest, highest immediate value — makes today's verdicts sharper without architectural change). Then 2b (playbooks — pure system-prompt work, no model change). Save 2c for after the GPU quota lands or once we adopt a new model per §3 below.

### Related files

- `monitoring-triage-service/app/context.py` — add trace-linkage step (2a).
- `monitoring-triage-service/app/drain_analyzer.py` — add `extract_trace_ids` (2a).
- `monitoring-mcp-servers/jaeger_mcp/main.py` — add `/tools/get_trace` + `/tools/list` (2a, 2c).
- `monitoring-triage-service/app/llm_client.py` — playbook injection (2b), planner prompt + two-pass orchestration (2c).
- `monitoring-triage-service/app/executor.py` — NEW, Planner request dispatcher (2c).
- `monitoring-triage-service/app/playbooks/` — new directory (2b).
- `monitoring-triage-service/app/config.py` — model selector (§3).

---

## 3. Model choice on private cloud + GPU — defer decision to post-demo <!-- SPRINT-3-MODEL-CHOICE -->

**Priority:** Decision · **Estimated effort:** 1 pt (evaluation) + implementation depends on choice · **Owner:** Lina (decision), engineer TBD (implementation)
**Surfaced on:** 2026-04-22 evening. Lina will have GPU instances in CIRES private cloud by Sprint 3. The question: once we have GPU *and* a no-external-API constraint (company security policy), which local model should we run, and does that unlock the Planner→Executor→Writer shape in §2c?

> **Update 2026-04-23:** Decision taken early. **`qwen2.5:14b-instruct` (Q4_K_M, ~9 GB VRAM) on a single A10G GPU (`g5.xlarge`, 24 GB)** is the first model+instance to ship. Rationale in §4. The benchmarks originally scheduled for Sprint 3 are being brought forward as part of the §4 migration — if qwen2.5:14b hits target numbers, it stays; if it doesn't, we'll iterate on `mistral-nemo:12b` or `qwen2.5-coder:14b` without re-provisioning (same VRAM envelope). The "deliberate non-decision" snapshot below is retained as a record of 2026-04-22 thinking.

### The constraint

**All inference must run inside the CIRES private cloud.** No OpenAI, no Anthropic API, no hosted anything. That's non-negotiable — it's why we picked Ollama + local models in the first place.

That rules out the "call Claude via Anthropic API" path. But it leaves a *larger* local-model space open once GPU is available.

### What GPU unlocks that CPU doesn't

- **Model size:** a 14B or 32B model fits in a single A10/A100/H100 GPU. On CPU, 3B is already the ceiling for sub-15-minute inference.
- **Tool-calling reliability:** the jump from 3B to 14B+ is where tool-calling / structured-output quality becomes production-grade. `qwen2.5:14b`, `deepseek-v3`, `llama3.1:70b`, and `mistral-nemo:12b` all do well on function-calling benchmarks; `llama3.2:3b` does not.
- **Latency:** GPU prefill eats ~5k tokens in a second. The 20–40-min single-shot we have now becomes ~30s.
- **Throughput:** Ollama/vLLM with continuous batching on GPU can process multiple alerts in parallel. No more 2-alert queue drama.

### Candidate local models (to evaluate in Sprint 3)

| Model | Size | Notes |
|-------|------|-------|
| `llama3.1:8b-instruct` | 8B | Decent structured output; middle-ground latency/quality. |
| `qwen2.5:14b-instruct` | 14B | Strong on JSON mode + tool calling; Apache 2.0; widely deployed in enterprise. |
| `qwen2.5-coder:14b` | 14B | Same family, stronger on structured/code outputs — good fit for our JSON schemas. |
| `mistral-nemo:12b-instruct` | 12B | Excellent instruction following; Apache 2.0. |
| `deepseek-r1:14b-distill` | 14B | Reasoning-tuned; may produce better RCA narratives. Check license. |
| `deepseek-v3` | bigger | Strong tool-calling reputation; bigger footprint. Reasonable on an A100. |

All of the above run under Ollama today. If we want higher throughput: vLLM or LMDeploy as the inference engine, same models. All stay inside the VPC.

### What this unlocks for 2c

With a 14B+ model that does reliable tool-calling:

- The **bounded Planner → Executor → Writer** shape from §2c is rock-solid. No prompt gymnastics needed.
- We *could* graduate to unbounded tool-calling (true ReAct) if we want — but honestly, Planner-Executor-Writer covers 90% of what unbounded calling buys us, with tighter latency guarantees. Still defensible to stay bounded.
- We can also keep `llama3.2:3b` as a fallback for when the GPU is saturated or cost-sensitive environments.

### What to evaluate before deciding

- [ ] Benchmark 3 candidate models on 10 representative CIRES alerts. Measure: verdict quality (manually scored), JSON-schema conformance rate, latency on target GPU, memory footprint.
- [ ] Confirm Ollama vs vLLM for serving. vLLM wins on throughput; Ollama wins on operational simplicity and first-party support for the quant variants we already use.
- [ ] Confirm the GPU instance type (A10/A100/H100 tier) and the provisioning cadence — if GPUs are scarce, a model that fits on a single A10 (like qwen2.5:14b Q4) may be the pragmatic choice.
- [ ] License audit for each candidate model (Apache 2.0, MIT, custom — some DeepSeek variants have use restrictions).
- [ ] Network policy: confirm the GPU instance can reach Prometheus/Loki/Jaeger MCPs without opening new SGs.

### Deliberate non-decision

**This section is a capture, not a plan.** The decision is to be made *after* the Sprint 2 presentation, with real data from the sandbox (§2c) and benchmarks (above). Don't commit to a model choice before presenting — keep the story "local, private-cloud, GPU-ready, model-TBD" for the demo, and pick the winner in Sprint 3 planning.

### Related files (for the eventual implementer)

- `monitoring-triage-service/app/config.py` — `ollama_model` is already a setting; expanding to `ollama_backend: str = "ollama"` (vs "vllm") is trivial.
- `monitoring-project/charts/ai-stack/values.yaml` — `ollama.model` and `ollama.gpu.enabled` toggles exist.
- `provisioning-monitoring-infra/ec2.tf` — `enable_gpu` var is already wired in; currently false.

---

## 4. AI Placement Migration — off k3s, onto a dedicated GPU instance <!-- SPRINT-3-AI-GPU-MIGRATION -->

**Priority:** In progress · **Estimated effort:** 1 day (infra + bring-up + benchmark) · **Owner:** Lina
**Surfaced on:** 2026-04-23. Sprint 2 demo was cancelled (supervisor unavailable), removing the "freeze the layout for the presentation" constraint. Lina declared the Sprint 2 end-state underwhelming (20–40 min per alert on CPU-bound `llama3.2:3b`) and pulled the GPU + bigger-model work forward so the architecture can actually be validated before investing in the tool-calling rewrite in §5.

### What's changing

The AI stack (Ollama + triage-service + 5 MCP servers) moves **out of the k3s cluster** onto a **dedicated GPU EC2 instance**. The k3s cluster keeps only the demo application workload (Spring Boot + Kong + React SPA) and its OTel collector agent, and gets downsized.

**Old topology (Sprint 2 end-state, 2026-04-22):**

| VM | Instance | Role |
|---|---|---|
| monitoring | `t3.large` (2 vCPU, 8 GB, CPU) | Prometheus / Grafana / Loki / Jaeger / OTel Collector |
| k3s | `t3.xlarge` (4 vCPU, 16 GB, CPU) | Demo app **+ ai-stack (Ollama `llama3.2:3b`, triage, 5 MCPs)** |
| — | — | Inference latency: **20–40 min per alert** |

**New topology (2026-04-23, in progress):**

| VM | Instance | Role |
|---|---|---|
| monitoring | `t3.large` (unchanged) | Prometheus / Grafana / Loki / Jaeger / OTel Collector |
| k3s | **`t3.large`** (downsized, in-place modify) | Demo app + OTel Collector only; ai-stack removed |
| **gpu (new)** | **`g5.xlarge` (4 vCPU, 16 GB, A10G 24 GB VRAM)** | Ollama `qwen2.5:14b-instruct-q4_K_M` + triage + 5 MCPs, under docker-compose |
| — | — | Expected inference latency: **~30–60s per alert** (to be confirmed by benchmark) |

The GPU box runs its services as a single docker-compose project — **no k3s, no Helm** — because for a single-node stack aimed at a one-day validation, compose is lower-ceremony and there's nothing a second cluster buys us.

### Why now (not Sprint 3 as originally planned)

Three compounding reasons:

1. **CPU inference caps the architecture.** Single-shot on `llama3.2:3b` already takes 20–40 min with the 5×-enriched bundle. Any of the Sprint 3 directions (Planner→Executor→Writer in §2c, LLM-driven tool calling in §5) requires ≥ 2 inferences per alert, ideally 3–5× for multi-round retrieval. On CPU that becomes 1–3 hours per alert — unusable regardless of how sharp the prompts get.
2. **Model-size ceiling matters for tool calling.** `llama3.2:3b` has weak tool-calling (30–40% accuracy ballpark on multi-tool-selection benchmarks). `qwen2.5:14b-instruct` is the smallest model with reliably strong tool-calling and fits in ~9 GB VRAM at Q4_K_M — exactly the envelope a single A10G offers with room for KV cache.
3. **The demo-freeze constraint is gone.** Supervisor won't see the 2026-04-23 demo, so we're free to cut the layout over now and spend the freed time actually validating the pipeline.

### Infra diff

- **Terraform** (`provisioning-monitoring-infra`):
  - `variables.tf`: add `gpu_ami_id` var (separately pinned, same no-drift philosophy as `ubuntu_ami_id` — we want a Deep Learning Base AMI so NVIDIA drivers + Docker + the NVIDIA container toolkit are already installed, saving bootstrap pain).
  - `ec2.tf`: `aws_instance.gpu` now uses `var.gpu_ami_id` instead of the shared Ubuntu AMI, with a dedicated user-data script (minimal — just create the `deploy` user; heavier lifting moves to Ansible).
  - `terraform.tfvars`: `enable_gpu = true`, `gpu_instance_type = "g5.xlarge"`, `gpu_volume_size = 100` (qwen2.5:14b Q4 is ~9 GB plus containers + logs), `k3s_instance_type = "t3.large"` (downsize), `gpu_ami_id = ami-...`.
  - `security-groups.tf`: add rule `gpu_triage_dashboard` for port 8090 from `allowed_ssh_cidrs` so the `/dashboard` decision inbox is reachable from the operator's browser. Ollama (11434) and the 5 MCP ports (8091–8095) stay inter-container on the compose network.
- **Ansible** (`monitoring-project`):
  - New `playbooks/gpu.yml` — rsync `monitoring-triage-service` + `monitoring-mcp-servers` sources to the box, `docker build` each image on the box, `ollama pull qwen2.5:14b-instruct-q4_K_M`, `docker compose up -d`.
  - `roles/grafana/templates/contactpoints.yml.j2`: webhook URL changes from `http://<k3s-ip>:30080/triage/webhook/grafana` to `http://<gpu-ip>:8090/triage/webhook/grafana`.
  - `playbooks/k3s.yml`: disable the `ai-stack` Helm release (`helm uninstall ai-stack -n ai`). Demo app + collector stay.
- **GPU-box runtime (docker-compose):** 7 services on one bridge network —

  ```
  ollama              (gpu-reserved; port 11434; model: qwen2.5:14b-instruct-q4_K_M)
  triage              (port 8090; decisions inbox at /dashboard)
  prometheus-mcp      (8091)
  loki-mcp            (8092)
  jaeger-mcp          (8093)
  drain3-mcp          (8094)
  rca-history-mcp     (8095)
  ```

  Shared named volume `triage-data` mounted at `/data` on `triage`, `rca-history-mcp` (SQLite DB), and `drain3-mcp` (Drain3 state). Triage reaches MCPs via docker-compose service DNS (`http://prometheus-mcp:8091` etc.) — same URL shape the existing k8s-service-DNS code already uses; only the hostnames change.

### AWS quota blocker

G-family on-demand vCPU quota in the CIRES account (`735115318342`) is 0 at start of 2026-04-23. A request for **8 vCPUs** (covers `g5.xlarge` today + headroom for `g5.2xlarge` later without a second request) was submitted 2026-04-23 morning: `RequestId 5eb7f81a4c3346d9bbba4e90cf41b72cOQHLSxux`. Expected auto-approval in 1–3 hours; manual-review cases can go to 1–2 business days. Everything downstream (`terraform apply`, compose bring-up, Grafana webhook repoint, benchmark) waits on `APPROVED`.

### Benchmark plan

Once the GPU box is live, fire the same synthetic alert payload that `scripts/hourly-demo-test.sh` already uses (so baseline-vs-new is apples-to-apples). Capture:

- **Time-to-verdict** — clock time between webhook POST and verdict committed to `/decisions`.
- **GPU utilization** — `nvidia-smi dmon -s u -c 60` during inference.
- **Tokens/sec** — from Ollama logs.
- **Verdict quality** — qualitative review: is the RCA specific to the alert, or generic "check all three pillars" text?

Target numbers (pass criteria):

- Verdict latency **p95 ≤ 60s** (vs. 20–40 min baseline). If we hit this, the tool-calling rewrite in §5 is tractable.
- GPU utilization during prefill **≥ 80%**. Lower implies a CPU-bound preprocessor bottleneck elsewhere in triage.
- Verdict quality visibly sharper than the CPU/3B baseline on at least 8 of 10 synthetic alerts.

Fail criteria (any one triggers a rollback or design rethink before investing further):

- Inference **> 3 min p95** on qwen2.5:14b Q4 — wrong quant level or prefill-bound on context; try lower quant or switch to `mistral-nemo:12b`.
- Tool-calling accuracy **< 80%** on a 10-alert smoke test — model not as strong as advertised for our prompt shape; fall back to Planner-Executor-Writer in §2c.
- GPU underutilized **(< 40%)** during inference — some container is serializing on CPU; diagnose triage-service I/O before the LLM call.

### Acceptance criteria

- [ ] Terraform applied cleanly: GPU instance running, EIP associated, k3s in-place modified to `t3.large`, EBS + EIP preserved.
- [ ] `sg-gpu` permits 11434 VPC-internal, 8090 from both `sg-monitoring` (webhook path) and `allowed_ssh_cidrs` (dashboard path).
- [ ] `playbooks/gpu.yml` converges to a running compose stack; `curl http://<gpu-ip>:8090/healthz` and `curl http://<gpu-ip>:11434/api/tags` return 200.
- [ ] `qwen2.5:14b-instruct-q4_K_M` loaded in Ollama; `nvidia-smi` shows VRAM allocated.
- [ ] `helm uninstall ai-stack -n ai` completed on the k3s cluster; no Ollama / triage / MCP pods left.
- [ ] Grafana contact point updated + `playbooks/monitoring.yml --tags grafana` re-run; alerts route to `http://<gpu-ip>:8090/triage/webhook/grafana`.
- [ ] Benchmark report committed under `monitoring-docs/` comparing CPU/3B baseline vs. GPU/14B on the same 10 synthetic alerts (raw numbers + three representative verdict diffs).

### Related files

- `provisioning-monitoring-infra/variables.tf`, `ec2.tf`, `security-groups.tf`, `terraform.tfvars`.
- `monitoring-project/playbooks/gpu.yml` (new), `roles/grafana/templates/contactpoints.yml.j2`, `playbooks/k3s.yml`.
- `monitoring-project/compose/ai-stack/docker-compose.yml` (new — authoritative runtime spec for the GPU box).
- `monitoring-triage-service/app/config.py` — `ollama_url` default changes from `http://ollama:11434` to the compose service name (still `http://ollama:11434` — no code change needed, just compose-network naming).

---

## 5. MCP Tool-Calling Architecture — native Ollama, not a proxy <!-- SPRINT-3-MCP-TOOLING -->

**Priority:** Architectural decision · **Estimated effort:** 5 pts (tool schemas + dispatcher + loop + tests) · **Owner:** Lina
**Surfaced on:** 2026-04-23, same session as §4. Once the LLM moves from "pre-gathered bundle in one chat-completion" to "driving tool calls itself," the shape of the harness between the LLM and the HTTP MCPs has to be decided.

### The question

When we enable LLM-driven MCP calls (either the bounded Planner→Executor→Writer of §2c or a full unbounded tool-calling loop on qwen2.5:14b from §4), **what sits between the LLM and the existing HTTP MCP services?**

Three candidates keep surfacing:

| Option | What it is | What it gives you | What it costs |
|---|---|---|---|
| **Native Ollama tool calling** | Call `/api/chat` with `tools=[{name, description, parameters}]`. Model returns `tool_calls` in the response; the orchestrator executes them against whatever backend and feeds results back as `role=tool` messages. Loop until no more tool calls. | **Zero new infra.** Works with the existing HTTP MCP services as-is. | The Ollama-specific tool-call format couples us to Ollama's API. Acceptable because we're staying on Ollama + private cloud per §3. |
| **`mcp-client-for-ollama`** ([jonigl/mcp-client-for-ollama](https://github.com/jonigl/mcp-client-for-ollama)) | Python CLI/library that connects to MCP-protocol servers and bridges their tools to Ollama's tool-call API. | Terminal chat with MCP-protocol tools in front of an Ollama model. | Shape mismatch — it's a chat client, not an embeddable orchestration library. Our triage service is a long-running service that writes structured verdicts, not an interactive chat. Also requires our "MCPs" to actually speak the MCP protocol, which they don't (see §4(c) of `prepare.html`). |
| **LiteLLM MCP proxy** | Unified gateway: register MCP servers once, LiteLLM exposes them as tools to any model (Ollama, OpenAI, Anthropic, vLLM…). Bundles rate limits, caching, observability, spend tracking, provider fallback. | Multi-model, multi-consumer, provider-neutral. | Overbuilt for today — one model, one consumer, one provider. Adds a layer with its own failure modes. Also still requires MCP-protocol servers upstream. |

### What we chose and why

**Native Ollama tool calling.** Four reasons:

1. **One LLM, one consumer.** The triage service is the only thing making LLM calls. There is no second agent, no second model, no provider fan-out. A proxy's primary value — unifying access across consumers and providers — does not apply.
2. **Our "MCPs" are HTTP microservices, not MCP-protocol servers.** Already documented in `prepare.html §4(c)`: the name reflects the *role* (security boundary + HTTP abstraction between the LLM harness and the observability plane), not the wire protocol. Both `mcp-client-for-ollama` and LiteLLM expect MCP-protocol servers upstream. Wrapping our HTTP services in the MCP protocol would be effort that gets us nothing a direct HTTP-dispatch loop doesn't already achieve.
3. **`mcp-client-for-ollama` is the wrong shape.** It's an interactive chat-terminal client. Embedding a chat client inside a programmatic orchestrator is architecturally awkward and adds no value over calling Ollama's `/api/chat` ourselves.
4. **LiteLLM is valuable later, not now.** Its strengths activate when you want provider-neutral code (swap to Claude tomorrow), multiple consumers sharing tools, or centralized spend/observability. None apply on a single GPU with one orchestrator. Revisit if any of those constraints change.

### What actually needs to change in the triage codebase

Small, localized rewrite. **No new services, no new containers.**

1. **Tool schema definitions.** For each operation the HTTP MCPs already expose, define a JSON-schema entry. Example sketch:

   ```python
   # monitoring-triage-service/app/tools.py (new)
   TOOLS = [
     {
       "type": "function",
       "function": {
         "name": "prometheus_query_range",
         "description": "Query Prometheus range data for a PromQL expression over a time window.",
         "parameters": {
           "type": "object",
           "properties": {
             "query": {"type": "string"},
             "start": {"type": "string", "description": "RFC3339"},
             "end":   {"type": "string", "description": "RFC3339"},
             "step":  {"type": "string", "description": "Prometheus step, e.g. '15s'"},
           },
           "required": ["query", "start", "end"],
         },
       },
     },
     # loki_query_range, loki_tail_around,
     # jaeger_get_trace, jaeger_search_by_tag,
     # drain3_mine_templates, drain3_annotate_lines,
     # rca_history_search,
     # ...
   ]
   ```

2. **Tool dispatcher.** A thin `execute_tool(name, args) -> dict` that maps `tool_call.function.name` to an HTTP POST against the right MCP on the compose network. Existing `context.py` already has most of these calls — refactor them into per-tool helpers.

3. **Tool-execution loop** — replaces the current single chat-completion in `llm_client.py`:

   ```python
   messages = [
     {"role": "system", "content": SYSTEM_PROMPT},
     {"role": "user",   "content": alert_summary_and_context},
   ]
   for iteration in range(MAX_ITERATIONS):
     resp = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
     msg  = resp["message"]
     messages.append(msg)
     tool_calls = msg.get("tool_calls") or []
     if not tool_calls:
       return parse_verdict(msg["content"])
     for tc in tool_calls:
       try:
         result = execute_tool(tc["function"]["name"], tc["function"]["arguments"])
       except ToolError as e:
         result = {"error": str(e), "tool": tc["function"]["name"]}
       messages.append({
         "role": "tool",
         "tool_call_id": tc["id"],
         "content": json.dumps(result),
       })
   # iteration budget exhausted → one forced verdict pass without tools
   return force_verdict(messages)
   ```

4. **Guardrails we already have** (keep them, they still apply):
   - Strict-JSON retry on the **final verdict** message (unchanged — the retry wraps only the last "write the verdict" pass).
   - Circuit breaker on Ollama error rate.
   - Per-alert pipeline timeout, now enforced **across all loop iterations** (not just one LLM call).
   - Layer 2 pre-LLM suppression — still short-circuits before any inference.

5. **New metrics** (add to the Grafana `triage-service-health` dashboard):
   - `triage_tool_calls_total{tool=...}` — how often each tool is invoked.
   - `triage_tool_errors_total{tool=..., kind=...}` — tool-side failures (HTTP 5xx, timeouts, unknown-tool-name).
   - `triage_loop_iterations` histogram — distribution of rounds per verdict.
   - `triage_loop_exhausted_total` — forced-verdict cases. Should stay near zero.

### Sequencing vs §2c

§2c (Planner → Executor → Writer) and this §5 (full tool-calling loop) are not mutually exclusive — they share the same tool-schema definitions, the same dispatcher, and the same set of MCP services. The actual shipping plan:

1. **§5 first, in the smallest form — Planner → Executor → Writer (§2c) implemented using the tool machinery from §5.** Planner is prompted with `tools=[…]` and instructed to emit *proposed* tool calls rather than execute them; executor runs them; writer does the final verdict pass with the expanded context. Two inferences, bounded latency, but built on the same primitives we'd need for the unbounded loop.
2. **Only if §2c benchmarks show headroom and the loop-exhaustion rate is low, graduate to the full unbounded loop** from the pseudocode above. This is an incremental unlock, not a separate rewrite.

### When to revisit the proxy options (future triggers)

- **A second LLM consumer appears** (a separate agent doing something else in the platform). LiteLLM then becomes genuinely useful as a shared gateway.
- **Provider fallback becomes a requirement** (local GPU saturated → spill to a sanctioned external provider, or Ollama → vLLM with the same model for higher throughput). LiteLLM is built for exactly this.
- **External MCP-ecosystem interop** — Claude Desktop, Cursor, Zed, or a future CIRES agent wants to use the same tools as the triage service. Then wrap each HTTP MCP in the `mcp` Python SDK (stdio or SSE transport) as an *additional* surface. The triage service can keep calling them directly over HTTP — the MCP protocol becomes a second entry point, not a replacement.

None of those are on the current roadmap. Native tool calling is the right call for the foreseeable horizon.

### Acceptance criteria

- [ ] `TOOLS` schema list covers every MCP operation currently invoked from `context.py`.
- [ ] `execute_tool` dispatcher routes by tool name; unknown tool names return a structured error (not an exception) so the loop can recover and the model can self-correct.
- [ ] Tool-execution loop in `llm_client.py` with `MAX_ITERATIONS=10` default and a hard per-alert wall-clock budget (reuses existing `pipeline_timeout`).
- [ ] Metrics (`triage_tool_calls_total`, `triage_tool_errors_total`, `triage_loop_iterations`, `triage_loop_exhausted_total`) surfaced on the Grafana `triage-service-health` dashboard.
- [ ] Smoke test: synthetic `BackendHigh5xxRate` alert produces a verdict whose `evidence` field cites data obtained via at least one tool call (not just the initial alert summary).
- [ ] Failure-mode test: force `ollama_request_timeout` expiry mid-loop — pipeline produces a `NEEDS_HUMAN_REVIEW` decision, not a crash.
- [ ] Ship as Planner → Executor → Writer (§2c) *first*, measuring loop-exhaustion rate; only graduate to the unbounded form if the exhaustion rate stays under 5% in a 50-alert window.

### Related files

- `monitoring-triage-service/app/llm_client.py` — tool-execution loop lives here (replaces the current single-shot chat completion).
- `monitoring-triage-service/app/tools.py` — NEW: tool schemas + `execute_tool` dispatcher.
- `monitoring-triage-service/app/context.py` — existing MCP HTTP calls refactor into per-tool helpers.
- `monitoring-triage-service/app/config.py` — add `max_tool_iterations: int = 10` and surface it via the chart values.
- `monitoring-mcp-servers/*/main.py` — no code changes required unless new operations are needed; the tool schemas describe the existing endpoints.

---

## 6. RCA prose quality — telemetry as the means, not the end <!-- SPRINT-3-RCA-PROSE -->

**Priority:** Done · **Effort:** ~½ day actual · **Owner:** Claude (operator-paired)
**Surfaced on:** 2026-04-28, during the post-exemplar-library audit. Operator review of live RCAs found the model leading every analysis with the PromQL expression and observed value, then concluding "this indicates that there are X experiencing Y" — restating the alert in different words instead of naming a cause.
**Status:** ✅ Shipped 2026-04-28 — see [decisions-log D19](decisions-log.html#d19). Listed here for backlog completeness so the cross-reference from sprint2-epic5-ueba isn't dead.

### Why this matters

The RCA is the operator's first read on what is broken. If it just paraphrases the alert, the operator opens a dashboard and starts from scratch — the analysis added no value. A real RCA names a specific failing component (saturated connection pool, tripped circuit-breaker, recent regression, severed network path) and uses telemetry as supporting evidence. Telemetry is the means; naming the cause is the end.

### What was already implemented (don't re-do)

- The exemplar library ([D17](decisions-log.html#d17)) gave the model a structural calibration target.
- The response validator ([D11](decisions-log.html#d11)) already enforced "no investigation in suggested_actions" and "deployment_type matches command family".
- The Sprint 2 dashboard rewrites surfaced the prose to the operator at all (without that, this regression would have been invisible).

### What was missing

- `SYSTEM_PROMPT` rule A in `app/llm_client.py` literally instructed the model to start every RCA with the PromQL expression and observed value. Three of the four surfaces shaping the prose (rule A, the closing imperative, the few-shot examples) were pulling toward symptom-first.
- The exemplar `rca` fields were good in spirit but several of them led with the metric value too — they didn't strongly counter rule A.
- The validator had no check for surface-only opening shapes — once the model produced "PromQL `<expr>` reported `<value>`...", nothing rejected it.

### What was shipped

- `SYSTEM_PROMPT` rule A rewritten to demand a cause-first lede; new rule J added for plain-language translation of raw PromQL; closing imperative rewritten.
- All three few-shot examples in `app/llm_client.py` rewritten to model cause-first prose.
- All 11 exemplar `rca` fields in `app/exemplars/library.yaml` rewritten — the structural calibration target now demonstrates the desired shape.
- `app/response_validator.py` gained a surface-only LEDE scan (regex on the first sentence) and a surface-only hedge scan (regex on the full prose). 6 new tests in `tests/test_response_validator_surface_only.py` lock in both checks plus a regression test proving cause-first prose with PromQL in evidence still passes.
- `docs/happy-path-scenarios.md` gained a "RCA prose quality" header section documenting the philosophy.

### Acceptance criteria (all met)

- [x] Test suite green: 95/95 (89 prior + 6 new).
- [x] Validator rejects "PromQL `<expr>` reported" lede, "The PromQL expression" lede, and "indicates that there are X experiencing Y" hedge.
- [x] Validator passes cause-first prose even when PromQL appears later in the same RCA.
- [x] Three reinforcing surfaces (system-prompt rules + exemplars + validator) all carry the same philosophy so future regressions are caught at multiple layers.

### Related files

- `monitoring-triage-service/app/llm_client.py` — SYSTEM_PROMPT + few-shot examples.
- `monitoring-triage-service/app/exemplars/library.yaml` — all 11 archetypes' `rca` fields.
- `monitoring-triage-service/app/response_validator.py` — surface-only LEDE + hedge regex sets.
- `monitoring-triage-service/tests/test_response_validator_surface_only.py` — 6 tests.
- `monitoring-triage-service/docs/happy-path-scenarios.md` — philosophy header.
- `monitoring-docs/decisions-log.html#d19` — full decision rationale.

---

## How to add items to this backlog

When a Sprint 2 conversation surfaces a "let's do that in Sprint 3" follow-up, add a new numbered section here with:

- **Why it matters** — the argument for doing it at all.
- **What's already there** — so the next implementer doesn't redo work.
- **What's missing** — concrete gap list.
- **Acceptance criteria** — a checkbox list an implementer can work through.
- **Related files** — paths into the repos.

Commit and push. That way any future Claude Code session that clones the 6 repos will discover this file automatically.
