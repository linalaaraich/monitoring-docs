---
render_with_liquid: false
---

# Work Report — What Was Done & What Needs Manual Action

> **Date:** 2026-04-13 (updated after audit pass)
> **Scope:** Sprint 2 Extension — Epics 3 (K8s Migration) & 4 (AI Hardening)
> **Audit status:** All code audited, issues found and fixed (see Post-Audit Fixes below)

---

## Summary

All code that can be written locally has been written. 4 repositories were modified across 6 parallel work streams. The K8s migration infrastructure is ready for deployment; the AI hardening code is implemented and tested. Documentation was updated with a comprehensive migration guide.

---

## 1. What Was Done (Code Changes)

### 1.1 Terraform Rescope (SCRUM-63 / E1-02) — `provisioning-monitoring-infra/`

**6 files modified, net -30 lines (simplification)**

| File | Changes |
|------|---------|
| `ec2.tf` | Replaced 4 EC2 instances (monitoring, backend, network, ai) with 3: monitoring (unchanged), k3s (new t3.xlarge), gpu (renamed from ai, g4dn.xlarge). Added AMI pinning support via `ubuntu_ami_id` variable. |
| `security-groups.tf` | Removed sg-backend and sg-network. Added sg-k3s with K8s ports (:6443 API, :10250 kubelet, :30000-32767 NodePort, :80/:443). Renamed sg-ai to sg-gpu. Updated RDS to allow MySQL from sg-k3s. Updated all locals maps. |
| `variables.tf` | Removed backend/network variables. Added `k3s_instance_type` (t3.xlarge), `k3s_volume_size` (50), `gpu_instance_type`, `gpu_volume_size`, `ubuntu_ami_id`. |
| `outputs.tf` | Replaced backend/network/ai outputs with `k3s_private_ip`, `k3s_public_ip`, `gpu_private_ip`, `gpu_public_ip`. |
| `providers.tf` | Pinned AWS provider to `~> 5.82`. |
| `generate-inventory.sh` | Updated to output k3s and gpu IPs instead of backend/network/ai. |

### 1.2 k3s Ansible Foundation (E3-01, E3-02) — `monitoring-project/`

**6 files modified + 4 new files**

| File | Status | Purpose |
|------|--------|---------|
| `requirements.yml` | Modified | Added `xanmanning.k3s` role v3.4.4 |
| `inventory/production.yml` | Modified | Added `k3s_cluster` and `gpu` host groups. Commented out legacy groups. |
| `inventory/group_vars/k3s_cluster.yml` | **New** | k3s config: release version, Traefik disabled, image tag, kubeconfig mode |
| `inventory/group_vars/all.yml` | Modified | Added `k3s_host_ip` and `gpu_host_ip` variables |
| `playbooks/k3s.yml` | **New** | Bootstraps k3s, fetches kubeconfig, rewrites server URL, includes image import role |
| `playbooks/site.yml` | Modified | Added k3s.yml import, commented out legacy application/network/ai playbooks |
| `roles/k3s_images/defaults/main.yml` | **New** | Image list and source repo paths for build+import |
| `roles/k3s_images/tasks/main.yml` | **New** | docker build → docker save → k3s ctr images import pipeline |

### 1.3 Helm Charts (E3-03, E3-04, E3-05) — `monitoring-project/charts/`

**24 new files across 3 charts**

#### `charts/spring-boot/` (8 files) — E3-03
- `Chart.yaml`, `values.yaml`
- `templates/`: deployment.yaml (with OTel Java Agent init container, probes, Prometheus annotations), service.yaml, configmap.yaml (Spring properties), secret.yaml (RDS credentials), serviceaccount.yaml, _helpers.tpl

#### `charts/kong/` (3 files) — E3-04
- `values-k3s.yaml` — Values for upstream kong/kong chart (DB-less, NodePort :30080)
- `kong-config.yaml` — ConfigMap with declarative kong.yml (routes to K8s service DNS)
- `README.md` — Install instructions

#### `charts/ai-stack/` (13 files) — E3-05
- `Chart.yaml`, `values.yaml`
- `templates/`: triage-deployment.yaml, triage-service.yaml, triage-pvc.yaml, triage-configmap.yaml (drain3.ini), mcp-deployments.yaml (loops over 5 servers), mcp-services.yaml, ollama-deployment.yaml (GPU resource request, model pull init), ollama-service.yaml, ollama-pvc.yaml (20Gi), secrets.yaml (SMTP), namespace.yaml, _helpers.tpl

### 1.4 K8s Observability (E3-06, E3-07, E3-08, E3-09) — `monitoring-project/manifests/` + role updates

**7 new manifest files + 2 role template updates**

| File | Story | Purpose |
|------|-------|---------|
| `manifests/nvidia-device-plugin/daemonset.yaml` | E3-06 | NVIDIA k8s device plugin DaemonSet (v0.15.0) |
| `manifests/nvidia-device-plugin/test-gpu-pod.yaml` | E3-06 | Test pod to verify GPU passthrough |
| `manifests/otel-collector/namespace.yaml` | E3-07 | Observability namespace |
| `manifests/otel-collector/rbac.yaml` | E3-07 | OTel Collector ServiceAccount + ClusterRole |
| `manifests/otel-collector/configmap.yaml` | E3-07 | OTel Collector config (filelog, k8sattributes, OTLP, Loki exporter) |
| `manifests/otel-collector/daemonset.yaml` | E3-07 | OTel Collector DaemonSet with host log mounts |
| `manifests/prometheus-rbac/rbac.yaml` | E3-08 | Prometheus scraper SA + ClusterRole + token Secret |
| `roles/prometheus/templates/prometheus.yml.j2` | E3-08 | Added `kubernetes_sd_configs` scrape jobs (guarded by `k3s_sd_enabled`) |
| `roles/grafana/templates/alertrules.yml.j2` | E3-09 | Alert rule selectors now use Jinja2 variables that switch between VM mode and K8s mode |
| `inventory/group_vars/monitoring.yml` | E3-09 | Added `k3s_sd_enabled` toggle variable |

### 1.5 K8s Validation Playbook (E3-10) — `monitoring-project/playbooks/`

**1 new file**

| File | Purpose |
|------|---------|
| `playbooks/integration-k8s.yml` | 10-step E2E validation: cluster health, pod status, monitoring health, K8s targets, load test, metrics, logs, traces, triage, Ollama |

### 1.6 AI Triage Hardening (AI-01, AI-02, AI-03) — `monitoring-triage-service/`

**8 files modified, +386 -103 lines, all 40 tests pass**

#### AI-01: Ollama Call Hardening
- `app/config.py`: Added `OLLAMA_REQUEST_TIMEOUT` (30s default)
- `app/llm_client.py`: Added `CircuitBreaker` class (CLOSED/OPEN/HALF_OPEN states, 5-failure threshold, 60s cooldown). Added retry with exponential backoff (2 retries, 1s/2s). Added `NEEDS_HUMAN_REVIEW` fallback.
- `app/metrics.py`: Added `ollama_request_duration_seconds`, `ollama_requests_total{status}`, `ollama_circuit_state` metrics.

#### AI-02: JSON Schema Enforcement
- `app/llm_client.py`: Added `"format": "json"` to Ollama API calls. Updated system prompt with JSON schema instructions.
- `app/models.py`: Updated `LLMDecision` with `INCONCLUSIVE` verdict option and `confidence` float field (0.0-1.0).
- `tests/test_llm_parsing.py`: Added tests for INCONCLUSIVE handling, confidence parsing, schema failure retry.
- `tests/test_models.py`: Added LLMDecision model validation tests.

#### AI-03: Triage Self-Observability
- `app/metrics.py`: Added `triage_queue_depth` gauge, `triage_mcp_requests_total{server,status}`, `triage_mcp_duration_seconds{server}`, `triage_fallback_total{reason}`.
- `app/context.py`: Instrumented MCP calls with duration and status metrics.
- `app/pipeline.py`: Added queue depth tracking (increment on receive, decrement on complete).

### 1.7 Documentation — `monitoring-docs/`

**2 files modified + 1 new file**

| File | Changes |
|------|---------|
| `k3s-migration-guide.html` | **New** — 10-tab comprehensive guide: Overview, Why k3s, Architecture, Terraform Changes, Ansible & k3s, Helm Charts, Observability, GPU & NVIDIA, Validation, Troubleshooting |
| `index.html` | Added navigation link and card for k3s migration guide. Updated status bar to reflect sprint extension to Apr 23. |

---

## 2. What Needs Manual Action (Cannot Be Done Locally)

### 2.1 Jira Housekeeping (requires Jira web UI access)

| Action | Ticket | Details |
|--------|--------|---------|
| **Rescope** | SCRUM-63 | Change summary to "Terraform — VPC, 1 k3s EC2, RDS, S3+CloudFront". Replace description per `SPRINT2-EXTENSION-README.md`. Set points to 5. |
| **Rescope** | SCRUM-64 | Change summary to "Ansible deploy — monitoring VM only". Set points to 3. |
| **Rescope** | SCRUM-65 | Change summary to "NVIDIA driver install on GPU host". Set points to 2. |
| **Close** | SCRUM-66 | Close as "Won't Do — Superseded" → link to SCRUM-128 (E3-10). |
| **Close** | SCRUM-82 | Close as "Won't Do — Superseded" → link to SCRUM-123 (E3-05). |
| **Update statuses** | SCRUM-67,72-80 | Many stories are code-complete but still show as "In Progress" or "To Do" in Jira. Update to match reality. |
| **Fix import** | SCRUM-117–131 | Verify Sprint, Story Points, and Due date fields on all 15 imported items. |

### 2.2 AWS Provisioning (requires AWS access)

1. **Run Terraform**: `cd provisioning-monitoring-infra && terraform plan && terraform apply`
2. **Update inventory**: Run `./generate-inventory.sh ../monitoring-project` to populate IPs
3. **Update group_vars**: Set `k3s_host_ip`, `gpu_host_ip`, `rds_endpoint`, `cloudfront_domain` in `all.yml`

### 2.3 Ansible Deployment (requires SSH access to EC2 instances)

1. **Install Ansible roles**: `ansible-galaxy install -r requirements.yml`
2. **Deploy monitoring VM**: `ansible-playbook playbooks/monitoring.yml`
3. **Bootstrap k3s**: `ansible-playbook playbooks/k3s.yml`
4. **Install Helm** on the control machine (if not already): `curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash`
5. **Deploy Helm charts**: Spring Boot → Kong → AI stack (see k3s-migration-guide.html for commands)
6. **Apply K8s manifests**: OTel Collector DaemonSet, Prometheus RBAC, NVIDIA device plugin
7. **Extract Prometheus SA token** and place on monitoring VM
8. **Set `k3s_sd_enabled: true`** and re-run monitoring playbook
9. **Run validation**: `ansible-playbook playbooks/integration-k8s.yml`

### 2.4 SMTP / Email Testing (requires Gmail App Password)

- Set `SMTP_USER`, `SMTP_PASSWORD` environment variables or Helm values for the triage service
- Trigger a test alert and verify escalation email is received

### 2.5 Ollama Model Pull (requires GPU EC2 running)

- After AI stack Helm chart is deployed, the init container will pull `llama3.1:8b`
- This downloads ~4.7GB — takes 5-10 minutes on first deploy
- Verify: `kubectl exec -n ai deploy/ollama -- ollama list`

### 2.6 Git Commits (requires your review)

All changes are staged but NOT committed. Review the changes in each repo and commit when satisfied:

```bash
# Terraform
cd /root/provisioning-monitoring-infra
git add -A && git commit -m "Rescope for k3s migration: 1 k3s EC2 + 1 GPU EC2"

# Ansible + Helm
cd /root/monitoring-project
git add -A && git commit -m "Add k3s bootstrap, Helm charts, K8s observability, validation playbook"

# Triage service
cd /root/monitoring-triage-service
git add -A && git commit -m "AI hardening: circuit breaker, JSON schema, self-observability"

# Documentation
cd /root/monitoring-docs
git add -A && git commit -m "Add k3s migration guide, update index for Sprint 2 extension"
```

---

## 3. Files Created/Modified — Complete Inventory

### New Files (62 total)

| Repo | Count | Files |
|------|-------|-------|
| monitoring-project | 34 | 24 Helm chart files + 7 K8s manifests + 2 k3s_images role + 1 k3s playbook + 1 k3s group_vars + 1 validation playbook |
| monitoring-docs | 1 | k3s-migration-guide.html |
| provisioning-monitoring-infra | 0 | (edits only) |
| monitoring-triage-service | 0 | (edits only) |

### Modified Files (22 total)

| Repo | Count | Files |
|------|-------|-------|
| provisioning-monitoring-infra | 6 | ec2.tf, security-groups.tf, variables.tf, outputs.tf, providers.tf, generate-inventory.sh |
| monitoring-project | 8 | requirements.yml, production.yml, all.yml, monitoring.yml, site.yml, prometheus.yml.j2, alertrules.yml.j2, architecture doc |
| monitoring-triage-service | 8 | config.py, context.py, llm_client.py, metrics.py, models.py, pipeline.py, test_llm_parsing.py, test_models.py |
| monitoring-docs | 1 | index.html |

---

## Post-Audit Fixes

After the initial implementation, 4 parallel audit agents scrutinized every file. Issues found and fixed:

| Issue | Severity | Fix |
|-------|----------|-----|
| Triage service: 4xx HTTP errors from Ollama were incorrectly counting toward circuit breaker threshold | Medium | Removed `record_failure()` call for non-retriable 4xx errors in `llm_client.py`. 4xx = client issue, not server unavailability. |
| k3s_images role: `synchronize` module requires `rsync` on remote host, but it wasn't in common packages | Medium | Added `rsync` to `common_packages` list in `group_vars/all.yml`. |
| k3s_images role: Dockerfile paths were absolute instead of relative to build context | Medium | Rewrote entire role to use `synchronize` to copy repos to remote, then `docker build` with correct relative paths. |
| Helm charts: Missing `nameOverride`/`fullnameOverride` in values.yaml | Low | Added to spring-boot and ai-stack values.yaml. |
| k3s playbook: Missing wait-for-ready loop after k3s bootstrap | Low | Added `until: "'Ready' in k3s_wait.stdout"` retry loop. |
| k3s playbook: Missing Helm installation step | Low | Added conditional Helm install on control machine. |
| site.yml: Missing k8s-manifests.yml playbook import | Medium | Added import for the manifest deployment playbook. |
| CLAUDE.md: Not updated with Sprint 2 Extension changes | Low | Updated with k3s commands, Helm install commands, new project status. |

### Second Audit Pass (Deep Scrutiny)

4 dedicated audit agents found additional critical issues:

| Issue | Severity | Fix |
|-------|----------|-----|
| OTel Collector ConfigMap missing `health_check` extension — pods would never become Ready | **Critical** | Added `extensions.health_check` and `service.extensions: [health_check]` to configmap.yaml |
| Alert rules `mon_node_selector` was a broken Jinja2 self-reference — Loki disk alert rules would have invalid PromQL | **Critical** | Fixed: `{% set mon_node_selector = 'job="mon-node-exporter"' %}` defined once, outside the if/else block |
| `integration-k8s.yml` had `gather_facts: false` but used `ansible_date_time` — Step 6 would fail | **Critical** | Changed to `gather_facts: true` |
| `requirements.yml` used `>=3.4.0` version range for community.docker collection — `ansible-galaxy` would fail | **Critical** | Changed to exact version `3.13.0` |
| AI stack Helm chart: RCA History MCP had no volume mount — SQLite data lost on pod restart | **High** | Added shared PVC mount (triage-data) as read-only to rca-history MCP deployment |
| GPU test pod missing toleration — wouldn't schedule on tainted GPU nodes | **Medium** | Added `nvidia.com/gpu` toleration |
| AI stack namespace hardcoded to "ai" instead of using Release.Namespace | **Medium** | Changed to `{{ .Release.Namespace }}` |
| Kong values.yaml had dead `plugins.configMaps` block (ignored by upstream chart) | **Medium** | Removed |
| OTel DaemonSet mounted `/var/lib/docker/containers` (unnecessary on k3s/containerd) | **Low** | Removed |

All 40 triage service tests pass after all fixes. Terraform passes `terraform fmt -check`. Both Helm charts render cleanly via `helm template`.

---

## 4. Architecture Decision Records

### ADR-1: Single-node k3s (not multi-node)
- **Decision:** Single-node for demo, HA deferred to Sprint 3
- **Rationale:** Simplicity, cost, sufficient for demo workload

### ADR-2: No container registry (k3s containerd import)
- **Decision:** Build images on host, import directly into containerd
- **Rationale:** Single-node + 1-2 contributors. ECR adds unnecessary complexity. Upgrade path documented.

### ADR-3: Monitoring stays on its own VM
- **Decision:** Don't migrate Prometheus/Grafana/Loki/Jaeger to K8s
- **Rationale:** Avoids circular dependency. Monitoring should survive cluster failures.

### ADR-4: Kong via NodePort (not LoadBalancer/Ingress)
- **Decision:** Expose Kong on NodePort :30080
- **Rationale:** Simplest for single-node. LoadBalancer requires cloud controller. Ingress is redundant when Kong IS the gateway.

### ADR-5: Alert rules use Jinja2 conditional selectors
- **Decision:** Single alertrules.yml.j2 template with `k3s_sd_enabled` toggle
- **Rationale:** Avoids maintaining two separate alert rule files. Clean switchover.

---

## 5. What's Left on the Critical Path

```
[DONE] Terraform rescope
[DONE] Ansible k3s bootstrap code
[DONE] Helm charts (Spring Boot, Kong, AI stack)
[DONE] K8s observability manifests
[DONE] Prometheus k8s_sd + alert migration
[DONE] Integration-k8s.yml playbook
[DONE] AI hardening code
[DONE] Documentation

[NEEDS YOU] Jira housekeeping (rescope/close tickets)
[NEEDS YOU] terraform apply (AWS access)
[NEEDS YOU] ansible-playbook runs (SSH access)
[NEEDS YOU] Helm installs (kubectl access)
[NEEDS YOU] NVIDIA device plugin deploy + GPU verification
[NEEDS YOU] Prometheus SA token extraction + placement
[NEEDS YOU] E2E validation run
[NEEDS YOU] Git commits + push
```

**Estimated remaining manual effort:** 2-3 days (mostly waiting for AWS provisioning and debugging GPU setup).
