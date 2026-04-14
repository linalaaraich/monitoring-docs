# The Bigger Picture — Observability Platform Progress Tracker

> **Project:** AI-Powered Observability Platform with Root Cause Analysis
> **Organization:** CIRES Technologies, Tanger Med (Digital Factory Observability Service)
> **Author:** Lina Laaraich
> **Last Updated:** 2026-04-13
> **Sprint 2 Deadline:** ~~April 9, 2026~~ **Extended to April 23, 2026**
> **Jira Project:** SCRUM | **Jira Source:** `github.com/linalaaraich/jira`
> **Repositories:** 6 (monitoring-project, provisioning-monitoring-infra, monitoring-docs, monitoring-mcp-servers, monitoring-triage-service, jira)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Sprint 2 — Full Scope After Extension](#2-sprint-2--full-scope-after-extension)
3. [Epic 1 — AWS Infrastructure (Story-by-Story)](#3-epic-1--aws-infrastructure)
4. [Epic 2 — AI RCA System MVP (Story-by-Story)](#4-epic-2--ai-rca-system-mvp)
5. [Epic 3 — Kubernetes Migration (Story-by-Story)](#5-epic-3--kubernetes-migration-new)
6. [Epic 4 — AI Triage Hardening (Story-by-Story)](#6-epic-4--ai-triage-hardening-new)
7. [Ansible Congruence Audit](#7-ansible-congruence-audit)
8. [Overall Progress Dashboard](#8-overall-progress-dashboard)
9. [Rescoped & Superseded Tickets](#9-rescoped--superseded-tickets)
10. [Detailed Plans for Remaining Work](#10-detailed-plans-for-remaining-work)
11. [Critical Path & Sequencing](#11-critical-path--sequencing)
12. [Risk & Gap Analysis](#12-risk--gap-analysis)

---

## 1. Executive Summary

### Key Discovery: Sprint 2 Was Extended

The sprint2-backlog.html in monitoring-docs was the **initial** Sprint 2 plan (2 epics, 22 stories, 99 pts, due Apr 9). The actual Jira (exported CSV in `linalaaraich/jira` repo) shows Sprint 2 was **extended to April 23** with **2 new epics added** and **3 existing tickets rescoped + 2 superseded**.

### Progress at a Glance

| Metric | Value |
|--------|-------|
| **Total Epics** | 4 |
| **Total Stories** | ~40 (31 in CSV + ~9 Done not exported) |
| **Total Story Points** | ~141 (99 original + 42 new) |
| **Extended Deadline** | April 23, 2026 (10 days from now) |
| Done (Jira) | ~9 stories (not in CSV export) |
| In Review (Jira) | 5 stories (26 pts) |
| In Progress (Jira) | 6 stories (26 pts) |
| To Do (Jira) | 20 stories (69 pts) |
| **Code actually complete** | **~20 of original 22 stories** |
| **K8s migration (Epic 3)** | **0 of 10 stories started — all To Do** |
| **AI hardening (Epic 4)** | **0 of 3 stories started — all To Do** |
| **Jira manual steps pending** | Rescope 3 tickets + close 2 superseded |

### The Big Picture

**Epics 1 & 2 code is essentially done** — all Ansible roles, Terraform, MCP servers, triage service, and Drain3 integration are written. The Jira statuses lag behind the actual code (many stories marked "In Progress" or "To Do" are actually code-complete in the repos).

**Epic 3 (K8s Migration) is entirely new work** — 10 stories, 34 points, no code started. This migrates Spring Boot, Kong, and the AI stack from per-VM docker-compose to a single-node k3s cluster with Helm charts. The monitoring stack stays on its own VM.

**Epic 4 (AI Hardening) is entirely new work** — 3 stories, 8 points, no code started. Adds circuit breaker, JSON schema enforcement, and deeper self-observability to the triage service.

**The Jira itself needs housekeeping** — 3 tickets need rescoping (SCRUM-63, 64, 65), 2 need closing as superseded (SCRUM-66, 82), and 3 fields (Sprint, Story Points, Due date) may need manual fixing on imported items.

---

## 2. Sprint 2 — Full Scope After Extension

### Epics Overview

| Epic | Stories | Points | Status | Due |
|------|---------|--------|--------|-----|
| Epic 1 — AWS Infrastructure | 5 | 23 → ~15 (after rescope) | Mixed (In Progress / In Review / To Do) | Apr 23 |
| Epic 2 — AI RCA System MVP | 17 | 76 → ~71 (after supersession) | Mixed (Done / In Review / In Progress / To Do) | Apr 23 |
| **Epic 3 — K8s Migration** | **10** | **34** | **All To Do** | **Apr 23** |
| **Epic 4 — AI Triage Hardening** | **3** | **8** | **All To Do** | **Apr 23** |
| **Total** | **~35 active** | **~128** | | **Apr 23** |

### Status Breakdown (from Jira CSV export)

| Status | Stories | Points | Details |
|--------|---------|--------|---------|
| **Done** | ~9 | ~36 | Not in CSV (excluded from export). Likely includes MCP servers (E2-02, E2-03, E2-16, E2-17) and other completed work |
| **In Review** | 5 | 26 | E1-02, E1-03, E1-04, E2-04, E2-05 |
| **In Progress** | 6 | 26 | E1-01, E2-01, E2-06, E2-07, E2-08, E2-09 |
| **To Do** | 20 | 69 | E1-05, E2-10-15, E2-12-13, all E3-*, all AI-* |

---

## 3. Epic 1 — AWS Infrastructure

**Epic Key:** SCRUM-84 | **Status:** To Do (epic-level) | **Original: 23 pts, Rescoped: ~15 pts**

> **Important:** 3 of 5 stories in this epic are being rescoped due to the K8s migration. See [Section 9](#9-rescoped--superseded-tickets).

### E1-01 — AWS Account, IAM, Billing Alerts, SSH Keys
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-62 |
| **Status** | In Progress |
| **Points** | 2 |
| **Priority** | Must |

**Jira says:** In Progress
**Code evidence:** No code artifact (manual admin task). Terraform code assumes AWS access exists.
**Assessment:** Likely done or nearly done — prerequisite for all Terraform work which is already In Review.

---

### E1-02 — Terraform: VPC, EC2s, RDS, S3+CloudFront
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-63 |
| **Status** | In Review |
| **Points** | 8 → **5 (rescoped)** |
| **Priority** | Must |
| **RESCOPE PENDING** | Change from "3+1 EC2s" to "1 k3s EC2" |

**Jira says:** In Review
**Code evidence:** `/root/provisioning-monitoring-infra/` — 4 commits, VPC, 4 EC2s, RDS, S3+CloudFront, 5 SGs, 14 outputs. **Complete for original scope.**
**Rescope needed:** Per Jira instructions, reduce to 1 EC2 for k3s (or 1 k3s + 1 GPU if separate). Security groups need updating for k3s ports (6443, 10250). AMI ID must be pinned (not `most_recent`).
**Gap:** Current Terraform provisions 4 separate EC2s. K8s migration consolidates to 1-2 EC2s.
**Plan to close:**
1. Modify `ec2.tf`: Replace 3 separate EC2s (backend, network, ai) with 1 k3s EC2 (sized to run all workloads)
2. Keep monitoring EC2 as-is
3. Keep or add GPU EC2 (decision per E3-06)
4. Update `security-groups.tf`: Add k3s API (6443) and kubelet (10250) ingress from monitoring SG
5. Pin AMI ID in `variables.tf`
6. Commit `terraform.lock.hcl`
7. Update `outputs.tf`: Add `k3s_host_ip`

---

### E1-03 — Ansible Deploy to AWS
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-64 |
| **Status** | In Review |
| **Points** | 5 → **3 (rescoped)** |
| **Priority** | Must |
| **RESCOPE PENDING** | Narrow to monitoring VM only |

**Jira says:** In Review
**Code evidence:** Full Ansible project with 16 roles, 5 playbooks, 4 compose templates. **Complete for original scope.**
**Rescope needed:** Spring Boot, Kong, and AI stack deployment moves to Helm charts (Epic 3). This story narrows to deploying the monitoring VM only.
**What stays in scope:**
- `playbooks/monitoring.yml` deploys: Prometheus, Grafana, Loki, Jaeger, OTel Collector, node_exporter, cAdvisor
- Grafana provisioning (datasources, dashboards, alert rules)
- All existing monitoring roles unchanged
**What moves out:**
- `playbooks/application.yml`, `network.yml`, `ai.yml` — replaced by Helm charts in E3-03, E3-04, E3-05

---

### E1-04 — Ollama + NVIDIA Drivers on GPU Instance
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-65 |
| **Status** | In Review |
| **Points** | 5 → **2 (rescoped)** |
| **Priority** | Must |
| **RESCOPE PENDING** | Host driver only; container runtime moves to E3-06 |

**Jira says:** In Review
**Code evidence:** `roles/nvidia_docker/` and `roles/ollama/` exist with full tasks.
**Rescope needed:** Split into:
- **This story:** NVIDIA host driver install only (`nvidia-smi` works)
- **E3-06 (SCRUM-124):** K8s NVIDIA device plugin, containerd nvidia runtime, GPU scheduling

---

### E1-05 — End-to-End Cloud Validation
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-66 |
| **Status** | To Do |
| **Points** | 3 |
| **Priority** | Must |
| **SUPERSEDED** | Close in favor of E3-10 (SCRUM-128) |

**Jira says:** To Do
**Action needed:** Close as "Won't Do — Superseded" with comment linking to SCRUM-128 (E3-10). The K8s validation replaces the VM-target validation.

---

## 4. Epic 2 — AI RCA System MVP

**Epic Key:** SCRUM-85 | **Status:** To Do (epic-level) | **76 pts → ~71 pts after E2-11 superseded**

### Stories Confirmed Done (~9 stories not in CSV)

Based on the CSV gap (SCRUM-68 through SCRUM-71 missing = 4 stories) and the SPRINT2-EXTENSION-README stating "9 Done stories unchanged", these are likely Done:

| Story | Likely Key | Evidence |
|-------|-----------|---------|
| E2-02: Prometheus MCP (:8091) | SCRUM-68? | `monitoring-mcp-servers/prometheus_mcp/main.py` — fully implemented, 4 tools |
| E2-03: Loki MCP (:8092) | SCRUM-69? | `monitoring-mcp-servers/loki_mcp/main.py` — fully implemented, 4 tools |
| E2-16: Jaeger MCP (:8093) | SCRUM-70? | `monitoring-mcp-servers/jaeger_mcp/main.py` — fully implemented, 4 tools |
| E2-17: Cross-pillar correlation | SCRUM-71? | `triage-service/app/context.py` + `llm_client.py` — parallel queries + prompt |
| + 5 more stories | Various | Likely earlier Sprint 1 carryovers or sub-tasks |

### Stories In Review (code complete, awaiting sign-off)

#### E2-04 — FastAPI Scaffold: Webhook Receivers, Async Processing
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-75 |
| **Status** | In Review |
| **Points** | 3 |

**Code:** `monitoring-triage-service/app/main.py` (176 lines) — 7 endpoints, BackgroundTasks, Pydantic models, Dockerized.
**All 9 acceptance criteria met.** Ready to move to Done.

#### E2-05 — Alert Deduplication + 5-Min Grouping Window
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-76 |
| **Status** | In Review |
| **Points** | 5 |

**Code:** `monitoring-triage-service/app/dedup.py` (77 lines) — TTL dict, asyncio.Lock, re-fire handling. Tests in `test_dedup.py`.
**All 7 acceptance criteria met.** Ready to move to Done.

### Stories In Progress (code complete but Jira not updated)

#### E2-01 — Configure Grafana Alerting Webhook
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-67 |
| **Status** | In Progress |
| **Points** | 3 |

**Code:** Grafana role has webhook contact point to `:8090/webhook/grafana`, 17 alert rules migrated, Alertmanager removed.
**7 of 8 acceptance criteria met** (final needs live env). Should move to In Review or Done.

#### E2-06 — Parallel Context Fan-Out
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-77 |
| **Status** | In Progress |
| **Points** | 5 |

**Code:** `context.py` (121 lines) — asyncio.gather, 8s timeout, timing metrics.
**All 9 acceptance criteria met.** Should move to In Review.

#### E2-07 — LLM Prompt + ESCALATE/DISMISS Parser
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-78 |
| **Status** | In Progress |
| **Points** | 8 |

**Code:** `llm_client.py` (162 lines) — System prompt, JSON parser, retry + safe fallback, Pydantic LLMDecision. Tests in `test_llm_parsing.py`.
**All 9 acceptance criteria met.** Should move to In Review.

#### E2-08 — ESCALATE Email via SMTP
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-79 |
| **Status** | In Progress |
| **Points** | 5 |

**Code:** `notifier.py` (110 lines) — HTML email, aiosmtplib, graceful skip.
**7 of 8 criteria met** (needs live SMTP test). Should move to In Review.

#### E2-09 — 5-Minute Timeout Fallback (Safety Gate)
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-80 |
| **Status** | In Progress |
| **Points** | 3 |

**Code:** `pipeline.py` — timeout handling, raw alert email, stored as timeout_passthrough.
**5 of 6 criteria met.** Should move to In Review.

### Stories To Do (code exists but Jira says To Do)

#### E2-10 — Decision History + Dashboard + RCA History MCP
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-81 |
| **Status** | To Do |
| **Points** | 3 |

**Code actually complete:** `rca_store.py` (SQLite), `/decisions` endpoint, `/dashboard` HTML, RCA History MCP at :8095.
**All 8 acceptance criteria met in code.** Jira status significantly behind reality.

#### E2-11 — Docker-Compose for AI Stack
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-82 |
| **Status** | To Do |
| **Points** | 5 |
| **SUPERSEDED** | Close in favor of E3-05 (SCRUM-123) |

**Code exists:** `ai-compose.yml.j2` with 10+ services. But this story is **superseded** by the K8s migration — the AI stack will be a Helm chart instead.

#### E2-12 — End-to-End Integration Test
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-83 |
| **Status** | To Do |
| **Points** | 3 |

**Code:** Integration playbook and load tests exist. **Needs live environment.**
**Note:** This will effectively be replaced by E3-10 once K8s migration is done.

#### E2-13 — Drain3 Setup: Log Template Mining + Persistence
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-72 |
| **Status** | To Do |
| **Points** | 5 |

**Code actually complete:** `drain_analyzer.py` (251 lines) — Drain3 initialized, drain3.ini, file persistence, startup seeding, background ingestion, S3 snapshots.
**All 9 acceptance criteria met in code.** Jira far behind.

#### E2-14 — Drain3 + Loki Integration
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-73 |
| **Status** | To Do |
| **Points** | 5 |

**Code actually complete:** `drain_analyzer.py` has `annotate_logs()` with [ANOMALY]/[KNOWN] prefixes. Pipeline integrates it.
**5 of 6 criteria met.** Jira far behind.

#### E2-15 — Drain3 Observability + MCP
| Field | Value |
|-------|-------|
| **Jira Key** | SCRUM-74 |
| **Status** | To Do |
| **Points** | 3 |

**Code actually complete:** `/drain3/stats` endpoint, Prometheus metrics, Drain3 MCP at :8094 with 4 tools.
**7 of 8 criteria met** (Grafana drift detection alert rule may need adding).

---

## 5. Epic 3 — Kubernetes Migration (NEW)

**Epic Key:** SCRUM-117 | **Status:** To Do | **34 points | 10 stories | ~5-7 days**

> Migrate Spring Boot, Kong, and AI stack from per-VM docker-compose to a single-node k3s cluster. Monitoring stack stays on its own VM.

### ALL 10 STORIES ARE TO DO — NO CODE EXISTS YET

| ID | Jira Key | Story | Pts | Priority | Blocked By |
|----|----------|-------|-----|----------|------------|
| E3-01 | SCRUM-119 | Bootstrap k3s on EC2 via Ansible (xanmanning.k3s) | 3 | Highest | SCRUM-63 (Terraform) |
| E3-02 | SCRUM-120 | Image build + k3s containerd import (no registry) | 3 | Highest | E3-01 |
| E3-03 | SCRUM-121 | Helm chart — Spring Boot (Deployment+Service+ConfigMap+probes) | 3 | High | E3-01 |
| E3-04 | SCRUM-122 | Helm chart — Kong (upstream chart, DB-less, ConfigMap) | 3 | High | E3-01, E3-03 |
| E3-05 | SCRUM-123 | Helm chart — AI stack (triage+5 MCP+Ollama, GPU) | 5 | High | E3-01, E3-02, E3-06 |
| E3-06 | SCRUM-124 | NVIDIA device plugin DaemonSet + GPU verification (SPIKE) | 5 | Highest | E3-01 |
| E3-07 | SCRUM-125 | In-cluster OTel Collector DaemonSet (logs+traces) | 3 | High | E3-01, E3-03, E3-04, E3-05 |
| E3-08 | SCRUM-126 | Prometheus kubernetes_sd_configs scrape job + RBAC | 3 | High | E3-01, SCRUM-63 |
| E3-09 | SCRUM-127 | Migrate 17 Grafana alert rules to K8s label selectors | 3 | Highest | E3-03, E3-04, E3-05, E3-08 |
| E3-10 | SCRUM-128 | End-to-end K8s validation playbook | 3 | Highest | ALL above |

### Detailed Plans for Each E3 Story

#### E3-01: Bootstrap k3s on EC2 via Ansible
**What needs to be done:**
1. Add `xanmanning.k3s` role to `monitoring-project/requirements.yml`, pin v3.4.4
2. Create `monitoring-project/playbooks/k3s.yml` playbook
3. Add `k3s_cluster` group to `inventory/production.yml`
4. Add `inventory/group_vars/k3s_cluster.yml` with:
   - `k3s_release_version`: pin to specific `v1.30.x+k3s1`
   - `k3s_server.disable: [traefik]`
   - `write-kubeconfig-mode: '0644'`
5. Add post-task to fetch kubeconfig and rewrite server URL to EC2 IP
6. Wire into `playbooks/site.yml`
7. Verify: `kubectl get nodes` returns 1 Ready node

#### E3-02: Image Build + k3s Containerd Import
**What needs to be done:**
1. Ensure Dockerfiles exist in `monitoring-triage-service/` and `monitoring-mcp-servers/` (they do)
2. Create Ansible role/tasks in monitoring-project:
   - `docker build` each image on the k3s host
   - `docker save` to tarball
   - `k3s ctr images import` each tarball
3. Add `image_tag` variable to `group_vars/k3s_cluster.yml`
4. Ensure all Helm charts use `imagePullPolicy: IfNotPresent`
5. Verify: `k3s crictl images` shows all 6 `cires/*` images

#### E3-03: Helm Chart — Spring Boot
**What needs to be done:**
1. Create `monitoring-project/charts/spring-boot/` with Chart.yaml, values.yaml, templates/
2. Templates: Deployment, Service (ClusterIP 80→8080), ConfigMap, ServiceAccount
3. Add liveness/readiness probes (/actuator/health/liveness, /readiness)
4. Secret reference for RDS credentials
5. Resource requests + limits
6. OTel Java Agent injection (JAVA_TOOL_OPTIONS env var)
7. Image pinned by tag

#### E3-04: Helm Chart — Kong (Upstream)
**What needs to be done:**
1. Use upstream `kong/kong` Helm chart, pin version
2. DB-less mode, kong.yml as ConfigMap
3. Rewrite upstream URLs to K8s service DNS (`spring-boot.app.svc.cluster.local:80`)
4. OTel plugin → in-cluster OTel Collector
5. Prometheus plugin → annotation-based scraping
6. Expose externally via NodePort or LoadBalancer

#### E3-05: Helm Chart — AI Stack
**What needs to be done:**
1. Create `monitoring-project/charts/ai-stack/`
2. 7 Deployments: triage-service, 5 MCP servers, Ollama
3. Ollama: PVC (20Gi), GPU resource request (`nvidia.com/gpu: 1`), init job for model pull
4. Secret for SMTP credentials
5. All inter-service refs use K8s Service DNS
6. Health probes on all containers
7. **Replaces E2-11 (SCRUM-82) docker-compose approach**

#### E3-06: NVIDIA Device Plugin + GPU Verification (SPIKE)
**What needs to be done:**
1. Install NVIDIA Container Toolkit on k3s host (repurpose nvidia_docker role)
2. Configure containerd with nvidia runtime
3. Deploy NVIDIA device plugin DaemonSet (k8s-device-plugin v0.15.0)
4. Test pod with `nvidia.com/gpu: 1` request
5. Document GPU decision: same EC2 or separate g4dn.xlarge
6. If separate: node taint + Ollama toleration
7. Add troubleshooting guide to monitoring-docs
8. **SPIKE: budget 1-1.5 days for debugging**

#### E3-07: In-Cluster OTel Collector DaemonSet
**What needs to be done:**
1. Create manifests or chart in `observability` namespace
2. ServiceAccount + ClusterRole for pod/node/namespace access
3. DaemonSet with `otel/opentelemetry-collector-contrib` (version pinned)
4. ConfigMap: filelog receiver (/var/log/pods), k8sattributes processor, OTLP exporter to monitoring VM
5. Retire per-VM OTel Collector containers from compose templates

#### E3-08: Prometheus kubernetes_sd_configs + RBAC
**What needs to be done:**
1. Create ServiceAccount `prometheus-scraper` in `observability` namespace
2. ClusterRole + ClusterRoleBinding for metrics discovery
3. Extract SA token, store in Ansible Vault
4. Update `roles/prometheus/` with kubernetes_sd_configs scrape job
5. Relabel configs for annotation-based filtering
6. Update security groups: monitoring VM → k3s host on :6443 and :10250

#### E3-09: Migrate 17 Grafana Alert Rules
**What needs to be done:**
1. Audit all 17 Grafana alert rules
2. Rewrite label selectors from VM IPs to K8s pod/namespace labels
3. Update Grafana provisioning files
4. Test each rule fires correctly
5. **HIGH RISK: silent failure if any rule missed**

#### E3-10: End-to-End K8s Validation
**What needs to be done:**
1. Create `playbooks/integration-k8s.yml`
2. 10-step test sequence: load test → metrics → logs → traces → alert → webhook → triage → LLM → email
3. All checks scripted, exit 0 = pass
4. **Replaces E1-05 (SCRUM-66)**

---

## 6. Epic 4 — AI Triage Hardening (NEW)

**Epic Key:** SCRUM-118 | **Status:** To Do | **8 points | 3 stories**

> Independent of K8s migration — can run anytime in parallel.

### ALL 3 STORIES ARE TO DO — NO CODE EXISTS YET

| ID | Jira Key | Story | Pts | Priority | Blocked By |
|----|----------|-------|-----|----------|------------|
| AI-01 | SCRUM-129 | Ollama call hardening: timeout, retry, circuit breaker | 3 | Highest | None |
| AI-02 | SCRUM-130 | JSON schema enforcement (Ollama JSON mode + Pydantic) | 2 | Highest | AI-01 |
| AI-03 | SCRUM-131 | Triage self-observability: /metrics with full instrumentation | 3 | High | None |

### Detailed Plans for Each AI Story

#### AI-01: Ollama Call Hardening
**What needs to be done in `monitoring-triage-service/app/llm_client.py`:**
1. Add configurable per-request timeout (default 30s, env var override)
2. Implement retry with exponential backoff (max 2 retries)
3. Implement circuit breaker: 5 consecutive failures → 60s cooldown
4. Add `NEEDS_HUMAN_REVIEW` verdict as fallback (send via existing email path)
5. Add Prometheus metrics: `ollama_request_duration_seconds`, `ollama_request_total{status}`, `ollama_circuit_state`
6. Unit tests for timeout, retry, circuit breaker transitions
**Estimated current state:** `llm_client.py` has basic retry (1 retry on parse failure) and a pipeline-level timeout. Needs circuit breaker pattern and per-request timeout (distinct from pipeline timeout).

#### AI-02: JSON Schema Enforcement
**What needs to be done in `monitoring-triage-service/app/llm_client.py`:**
1. Add `format: json` to Ollama API call parameters
2. Update system prompt with documented JSON schema
3. Add `INCONCLUSIVE` as third verdict option
4. Add `confidence: 0-1` field to Pydantic model
5. On schema failure: retry with validation error appended
6. On second failure: use `NEEDS_HUMAN_REVIEW` from AI-01
7. Remove existing free-text ESCALATE/DISMISS parser
8. Document schema in monitoring-docs
**Estimated current state:** `llm_client.py` already has Pydantic validation and retry. Needs `format: json` mode, `INCONCLUSIVE` verdict, and `confidence` field.

#### AI-03: Triage Self-Observability
**What needs to be done in `monitoring-triage-service/app/metrics.py`:**
1. Add missing metrics: `triage_queue_depth`, `triage_mcp_request_total{server,status}`, `triage_mcp_duration_seconds{server}`, `triage_llm_token_count`, `triage_fallback_total{reason}`
2. Add Prometheus annotations to K8s Service manifest
3. Create "Triage Service Health" Grafana dashboard panel
4. Commit dashboard JSON to git
**Estimated current state:** `metrics.py` (68 lines) already has many metrics (webhooks_received, alerts_processed, pipeline_duration, etc.). Needs MCP-level metrics, queue depth gauge, token counting, and dedicated Grafana panel.

---

## 7. Ansible Congruence Audit

### Current State vs. Extended Sprint Scope

| What Exists in Ansible | Serves | Still Relevant After K8s? |
|------------------------|--------|---------------------------|
| 16 Ansible roles | Epics 1 & 2 | **Monitoring roles: YES.** App/network/AI roles: replaced by Helm charts |
| 4 docker-compose templates | Epics 1 & 2 | **monitoring-compose: YES.** Others: replaced by K8s manifests |
| 5 playbooks (site, monitoring, application, network, ai) | Epics 1 & 2 | **monitoring.yml: YES.** Others: replaced by k3s.yml + helm |
| integration.yml | E1-05 | **Replaced by integration-k8s.yml (E3-10)** |
| Terraform (provisioning repo) | Epic 1 | **Needs rescoping** (E1-02: fewer EC2s, new SG rules) |

### What Ansible NEEDS for Epic 3

| New Item Needed | Story | Status |
|----------------|-------|--------|
| `requirements.yml` update (xanmanning.k3s) | E3-01 | Not started |
| `playbooks/k3s.yml` | E3-01 | Not started |
| `inventory/group_vars/k3s_cluster.yml` | E3-01 | Not started |
| `k3s_cluster` group in production.yml | E3-01 | Not started |
| Image build + import role/tasks | E3-02 | Not started |
| `charts/spring-boot/` Helm chart | E3-03 | Not started |
| `charts/ai-stack/` Helm chart | E3-05 | Not started |
| OTel Collector DaemonSet manifests | E3-07 | Not started |
| Prometheus k8s_sd_configs in prometheus role | E3-08 | Not started |
| Updated Grafana alert rules | E3-09 | Not started |
| `playbooks/integration-k8s.yml` | E3-10 | Not started |
| Kong upstream Helm values | E3-04 | Not started |
| NVIDIA device plugin DaemonSet | E3-06 | Not started |

### Congruence Verdict

**Epics 1 & 2: 100% congruent** — all code exists, Jira statuses just need updating.

**Epics 3 & 4: 0% congruent** — no K8s code, no Helm charts, no k3s playbooks exist yet. This is the main gap.

---

## 8. Overall Progress Dashboard

### By Epic — Code Reality vs. Jira Status

| Epic | Jira Status | Code Reality | Gap |
|------|-------------|-------------|-----|
| Epic 1 (AWS) | 1 In Progress, 4 In Review/To Do | Code complete, needs rescoping | Jira behind code + needs rescope edits |
| Epic 2 (AI RCA) | ~9 Done, 2 In Review, 5 In Progress, 6 To Do | ~20 of 22 stories code-complete | Jira significantly behind code |
| Epic 3 (K8s) | All 10 To Do | No code exists | Jira accurate — work hasn't started |
| Epic 4 (AI Hardening) | All 3 To Do | No code exists | Jira accurate — work hasn't started |

### Time Budget (10 days remaining to Apr 23)

| Work | Estimated Effort | Priority |
|------|-----------------|----------|
| Jira housekeeping (rescope, close, update statuses) | 0.5 day | Immediate |
| E1-02 Terraform rescope | 1 day | High |
| E3-01 through E3-10 (K8s migration) | 5-7 days | Critical path |
| AI-01 through AI-03 (hardening) | 1.5 days | Can parallel with K8s |
| **Total estimated** | **~8-10 days** | **Tight but feasible** |

---

## 9. Rescoped & Superseded Tickets

Per `SPRINT2-EXTENSION-README.md`, these manual Jira changes are required:

### Tickets to Rescope (edit in Jira UI)

| Ticket | Current Summary | New Summary | Points Change |
|--------|----------------|-------------|---------------|
| SCRUM-63 | E1-02: Terraform — VPC, 3+1 EC2s, RDS, S3+CloudFront | E1-02: Terraform — VPC, 1 k3s EC2, RDS, S3+CloudFront | 8 → 5 |
| SCRUM-64 | E1-03: Ansible deploy to AWS — Spring Boot, React, Kong, observability | E1-03: Ansible deploy to AWS — monitoring VM only | 5 → 3 |
| SCRUM-65 | E1-04: Ollama + NVIDIA drivers on GPU instance | E1-04: NVIDIA driver install on GPU host (k3s runtime in E3-06) | 5 → 2 |

### Tickets to Close as Superseded

| Ticket | Summary | Superseded By | Action |
|--------|---------|---------------|--------|
| SCRUM-66 | E1-05: E2E cloud validation | E3-10 (SCRUM-128) | Close as "Won't Do — Superseded" |
| SCRUM-82 | E2-11: Docker-compose for AI stack | E3-05 (SCRUM-123) | Close as "Won't Do — Superseded" |

### Jira Import Fixes Needed

The CSV import of the 15 new items (Jira-additions.csv) may not have carried over 3 fields:
- **Sprint:** Should be "SCRUM Sprint 2" on all items
- **Story Points:** As specified in each story
- **Due date:** 23/Apr/26 on all items

Check each of SCRUM-117 through SCRUM-131 and fix these 3 fields manually if missing.

---

## 10. Detailed Plans for Remaining Work

### Phase 1: Jira Housekeeping + Terraform Rescope (Days 1-2)

**Day 1 (0.5 day):**
1. Update Jira statuses to match code reality:
   - Move SCRUM-67, 77, 78, 79, 80 from In Progress → In Review (code complete)
   - Move SCRUM-72, 73, 74, 81 from To Do → In Review (code complete)
   - Move SCRUM-75, 76 from In Review → Done
   - If MCP stories (SCRUM-68-71?) are already Done, verify
2. Rescope SCRUM-63, 64, 65 (copy descriptions from SPRINT2-EXTENSION-README)
3. Close SCRUM-66 and SCRUM-82 as superseded
4. Verify Sprint/Points/Due date on SCRUM-117 through SCRUM-131

**Days 1-2 (1 day):**
5. Rescope Terraform (SCRUM-63):
   - Modify ec2.tf: 1 k3s EC2 + 1 monitoring EC2 (+ optional GPU EC2)
   - Update security-groups.tf: k3s ports (6443, 10250)
   - Pin AMI ID
   - Commit terraform.lock.hcl
   - `terraform plan` to verify

### Phase 2: K8s Foundation (Days 2-4)

**Day 2 (E3-01):**
- Add xanmanning.k3s to requirements.yml
- Create k3s.yml playbook
- Test: `ansible-playbook playbooks/k3s.yml` → `kubectl get nodes` = 1 Ready

**Day 3 (E3-02 + E3-06 start):**
- Create image build + import Ansible tasks
- Start NVIDIA device plugin spike (may take 1-1.5 days)

**Day 4 (E3-06 finish + E3-03/04 start):**
- Finish GPU verification
- Start Helm charts for Spring Boot and Kong

### Phase 3: Helm Charts + Observability (Days 4-7)

**Days 4-5 (E3-03, E3-04, E3-05):**
- Spring Boot Helm chart
- Kong upstream Helm chart
- AI stack Helm chart

**Days 5-6 (E3-07, E3-08):**
- OTel Collector DaemonSet
- Prometheus kubernetes_sd_configs

**Day 6-7 (E3-09):**
- Migrate all 17 Grafana alert rules to K8s selectors
- Test each rule individually

### Phase 4: AI Hardening + E2E Validation (Days 7-10)

**Days 7-8 (AI-01, AI-02, AI-03) — can parallel with Phase 3:**
- Ollama circuit breaker + retry
- JSON schema enforcement
- Self-observability metrics + Grafana panel

**Day 9 (E3-10):**
- End-to-end K8s validation playbook
- Full pipeline test

**Day 10: Buffer**
- Prompt tuning, edge cases, documentation, demo prep

---

## 11. Critical Path & Sequencing

```
SCRUM-63 (Terraform rescope)
    │
    ▼
E3-01 (k3s bootstrap) ──┬──► E3-06 (NVIDIA spike, 1-1.5d)
                         │
                  E3-02 (images) ──┐
                         │         │
                         ▼         ▼
                  E3-03 (Spring) ──┐
                  E3-04 (Kong) ────┤
                  E3-05 (AI stack) ┤   (parallel)
                                   │
                                   ▼
                  E3-07 (OTel DS) ──┐
                  E3-08 (Prom SD) ──┤  (parallel)
                  E3-09 (alerts) ───┤
                                    │
                                    ▼
                                E3-10 (e2e validation)

AI-01, AI-02, AI-03 ──► independent, run anytime in parallel
                        (easier to test once E3-10 is green)
```

**Spine:** Terraform rescope → E3-01 → E3-02 → (E3-03/04/05 || E3-06) → (E3-07/08/09) → E3-10

**Parallel track:** AI-01 → AI-02 (sequential), AI-03 (independent)

---

## 12. Risk & Gap Analysis

### Risks for the April 23 Deadline

| Risk | Severity | Mitigation |
|------|----------|------------|
| **10 days for 13 new stories (42 pts) is tight** | High | AI-01/02/03 can parallel with K8s. Cut buffer days first. |
| **E3-06 (NVIDIA spike) is unbounded** | High | Budget 1-1.5 days. If GPU debugging runs long, fall back to Ollama CPU-only. |
| **K8s team onboarding required** | Medium | Team should work through Phases 1-4 of kubernetes-guide.html on k3d first. |
| **E3-09 (alert migration) is silent-failure risk** | High | Test each of 17 rules individually. No shortcuts. |
| **Jira statuses far behind code reality** | Medium | Fix immediately (Phase 1, Day 1). Blocks accurate sprint tracking. |
| **Terraform rescope could break things** | Medium | `terraform plan` before `apply`. May need new AMI for k3s. |
| **Network reachability: monitoring VM → k3s** | Medium | Confirm SG rules for :6443 and :10250 in SCRUM-63 rescope. |
| **E3-02 (image import) blocks E3-05** | High | Sequence carefully — without images, AI stack chart gets ImagePullBackOff. |

### What's Going Right

- **Epics 1 & 2 code is done** — no rework needed, just Jira cleanup
- **Monitoring stack is NOT migrating to K8s** — keeps scope manageable
- **k3s (not full K8s)** — simpler setup, single binary, fast bootstrap
- **No registry/CI needed** — containerd import sidesteps ECR/GitHub Actions complexity
- **AI hardening is independent** — can develop in parallel, not on critical path
- **Kubernetes guide already exists** — team onboarding material is ready
- **Existing Dockerfiles are ready** — triage service + 5 MCP servers have working Dockerfiles

---

## Appendix A: Full Jira Story Status Table

### From CSV Export (excludes ~9 Done stories)

| Jira Key | ID | Summary | Status | Points | Epic |
|----------|-----|---------|--------|--------|------|
| SCRUM-62 | E1-01 | AWS account, IAM, billing, SSH keys | In Progress | 2 | Epic 1 |
| SCRUM-63 | E1-02 | Terraform (RESCOPE PENDING) | In Review | 8→5 | Epic 1 |
| SCRUM-64 | E1-03 | Ansible deploy (RESCOPE PENDING) | In Review | 5→3 | Epic 1 |
| SCRUM-65 | E1-04 | Ollama+NVIDIA (RESCOPE PENDING) | In Review | 5→2 | Epic 1 |
| SCRUM-66 | E1-05 | E2E cloud validation (SUPERSEDED) | To Do | 3 | Epic 1 |
| SCRUM-67 | E2-01 | Grafana Alerting webhook | In Progress | 3 | Epic 2 |
| SCRUM-72 | E2-13 | Drain3 setup | To Do | 5 | Epic 2 |
| SCRUM-73 | E2-14 | Drain3 + Loki integration | To Do | 5 | Epic 2 |
| SCRUM-74 | E2-15 | Drain3 observability + MCP | To Do | 3 | Epic 2 |
| SCRUM-75 | E2-04 | FastAPI scaffold | In Review | 3 | Epic 2 |
| SCRUM-76 | E2-05 | Alert deduplication | In Review | 5 | Epic 2 |
| SCRUM-77 | E2-06 | Parallel context fan-out | In Progress | 5 | Epic 2 |
| SCRUM-78 | E2-07 | LLM prompt + parser | In Progress | 8 | Epic 2 |
| SCRUM-79 | E2-08 | ESCALATE email via SMTP | In Progress | 5 | Epic 2 |
| SCRUM-80 | E2-09 | 5-min timeout fallback | In Progress | 3 | Epic 2 |
| SCRUM-81 | E2-10 | Decision history + dashboard | To Do | 3 | Epic 2 |
| SCRUM-82 | E2-11 | Docker-compose AI stack (SUPERSEDED) | To Do | 5 | Epic 2 |
| SCRUM-83 | E2-12 | E2E integration test | To Do | 3 | Epic 2 |
| SCRUM-119 | E3-01 | Bootstrap k3s on EC2 | To Do | 3 | Epic 3 |
| SCRUM-120 | E3-02 | Image build + containerd import | To Do | 3 | Epic 3 |
| SCRUM-121 | E3-03 | Helm chart — Spring Boot | To Do | 3 | Epic 3 |
| SCRUM-122 | E3-04 | Helm chart — Kong | To Do | 3 | Epic 3 |
| SCRUM-123 | E3-05 | Helm chart — AI stack | To Do | 5 | Epic 3 |
| SCRUM-124 | E3-06 | NVIDIA device plugin (SPIKE) | To Do | 5 | Epic 3 |
| SCRUM-125 | E3-07 | OTel Collector DaemonSet | To Do | 3 | Epic 3 |
| SCRUM-126 | E3-08 | Prometheus k8s_sd_configs | To Do | 3 | Epic 3 |
| SCRUM-127 | E3-09 | Migrate 17 Grafana alert rules | To Do | 3 | Epic 3 |
| SCRUM-128 | E3-10 | E2E K8s validation | To Do | 3 | Epic 3 |
| SCRUM-129 | AI-01 | Ollama call hardening | To Do | 3 | Epic 4 |
| SCRUM-130 | AI-02 | JSON schema enforcement | To Do | 2 | Epic 4 |
| SCRUM-131 | AI-03 | Triage self-observability | To Do | 3 | Epic 4 |

### Done Stories (not in CSV, ~9 stories, ~36 pts)
Likely includes: E2-02 (Prometheus MCP), E2-03 (Loki MCP), E2-16 (Jaeger MCP), E2-17 (Cross-pillar correlation), and ~5 others completed earlier in the sprint.
