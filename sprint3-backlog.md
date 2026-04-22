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

## 2. (placeholder — add next item as it's surfaced)

---

## How to add items to this backlog

When a Sprint 2 conversation surfaces a "let's do that in Sprint 3" follow-up, add a new numbered section here with:

- **Why it matters** — the argument for doing it at all.
- **What's already there** — so the next implementer doesn't redo work.
- **What's missing** — concrete gap list.
- **Acceptance criteria** — a checkbox list an implementer can work through.
- **Related files** — paths into the repos.

Commit and push. That way any future Claude Code session that clones the 6 repos will discover this file automatically.
