# Figma prompt — recreate the CIRES Observability architecture diagrams

Paste the prompt below into Figma Make (or Figma AI). It produces **two diagrams** that replace `AI RCA Architecture.png` and `AWS architecture.png`. Both diagrams target the **2026-04-28 architecture** — i.e. AI-on-laptop over Tailscale, 10-step pipeline, exemplar/validator/bounded-agency layers, k3s as the workload host.

---

## PROMPT — paste everything below

> Create two architecture diagrams for an AI-driven observability/RCA platform called **CIRES Observability**. Use a clean, modern, slightly playful style (rounded corners, soft shadows, pastel fills with stronger accent borders). All text in **Inter** for labels and **JetBrains Mono** for hostnames/ports/code. Colour palette:
>
> - **Sage / mint** `#a7d8b6` — observability data plane (Prometheus / Loki / Jaeger / OTel)
> - **Lavender** `#c9b8e3` — AI / triage / LLM components
> - **Peach** `#f5c6a0` — exporters and infra glue
> - **Pink** `#f4a6c0` — Grafana / alerting / dashboard surfaces
> - **Butter yellow** `#f3e08f` — Drain3 / pattern mining
> - **Teal** `#7fc8c8` — MCP bridge servers
> - **Blue-grey** `#b3c5d7` — workload (Spring Boot / Kong / MySQL)
> - **Slate background** `#1f2330` for envelopes; **off-white** `#fafafa` for component fills; borders 1.5 px in the saturated variant of each fill.
>
> Use **dotted lines** for control-plane / out-of-band traffic (Tailscale, SSH, ansible), **solid arrows** for runtime data flow, and **dashed arrows** for retry / feedback loops. Label every arrow with a one-line description (e.g. "webhook · POST /webhook/grafana") and where relevant a port or protocol. Title each diagram in 24 px bold; date-stamp it `2026-04-28` in the bottom-right corner of the canvas.
>
> ---
>
> ## DIAGRAM 1 — "AI RCA Pipeline (lifecycle view)"
>
> A vertical, top-to-bottom flow showing the **10-step triage pipeline** as it runs today. Render it as a single tall column of rounded cards, with side-rails on the left and right for the two parallel context-fan-out branches and the bounded-agency retry loop. Hostnames are **MagicDNS short names**, not IPs.
>
> **Top of canvas — alert origin (pink envelope titled "Detection · cloud"):**
> - **Grafana unified alerting** card — `observability-rca-monitoring` · `:3000` · "single contact point: triage-webhook (no Alertmanager)". Annotate: 18 alert rules, 3 of which are adaptive-threshold (`HighP95Latency`, `HighKongP95Latency`, `MediumCpuUsage`) — `noDataState=OK · execErrState=Error`.
> - **Drain3 self-fire** card (butter yellow) — note "background poll · 30 s · self-POSTs `/webhook/drain3` when novelty rate ≥ 10 % over 100 lines · 600 s cooldown".
>
> Both feed a single arrow labelled **"webhook · HTTPS over Tailscale · POST :8090/webhook/{grafana,drain3}"** into the next envelope.
>
> **Middle of canvas — triage pipeline (lavender envelope titled "Triage · `adolin-wsl` (laptop · WSL2 · Docker)"):**
>
> Render the 10 steps as stacked cards, numbered 1–10 in a left-side gutter. Each card is ~280 px wide and shows: step name (bold), one-line purpose (muted), and the module path in mono (e.g. `app/dedup.py`).
>
> 1. **Fingerprint dedup** — `app/dedup.py` — "10 min window · `(fingerprint, status)` key · returns `(is_dup, first_decision_id)`".
> 2. **Layer-2 suppression** — `app/pipeline.py` — "recurrence-gate (US-5.8 designed) · pre-LLM short-circuit for opted-in flappy alerts".
> 3. **Context fan-out** — `app/context_window.py` — render this card as a **horizontal split** with three teal sub-cards in parallel:
>    - `prometheus-mcp` `:8091`  · range query anchored on `alert.startsAt`
>    - `loki-mcp` `:8092`  · log slice ±5 min around fire
>    - `jaeger-mcp` `:8093`  · slowest spans for affected service
>    Annotate the join: "all three return ≤ 280 ms · joined into `GatheredContext`".
> 4. **Drain3 annotation** — `app/drain_analyzer.py` — "novel templates flagged · `match_count` joined to log slice".
> 5. **History lookup** — `rca-history-mcp` `:8095` — "similar prior RCAs · 7 d recurrence count for Drain3 templates".
> 6. **★ Exemplar injection** — `app/exemplars/` — **highlight this card** with a thicker border and a "NEW · D17" tag. Body: "11 archetypes scored on alertname × service × deployment_type × signal × severity · best match rendered as `## Reference exemplar` BEFORE evidence in the prompt". List the 11 archetype IDs in small caps in a sub-block: `oom-loop`, `upstream-latency-attribution`, `synthetic-blip-dismiss`, `cascade-incident`, `drain3-novelty-post-deploy`, `bounded-agency-retry`, `adaptive-threshold-no-op`, `closed-loop-feedback-override`, `crashloop-bad-config`, `network-firewall-attribution`, `tls-cert-expiry-pre-failure`.
> 7. **LLM call** — `Ollama :11434 · qwen2.5:7b-instruct · temp=0 · structured outputs · stable prefix prompt cache`. Annotate with the GPU runtime in a small footer: "**laptop GPU · NVIDIA GTX 1060 · 6 GB VRAM · ~25 s warm / 68 s cold**".
> 8. **Response validator** — `app/response_validator.py` — four scans, list them as bullet chips: `banned-phrases` · `vague-action` · `investigation-only` · `arch-mismatch`.
> 9. **Bounded-agency retry** (only if `data_starved`) — `app/bounded_agency.py` — render with a **dashed loop arrow** going back up to the MCP fan-out row. Body: "6-tool whitelist · `prometheus.range_query` · `loki.query` · `jaeger.search` · `rca_history.similar` · `rca_history.list_exemplars` · `rca_history.get_exemplar` · single retry budget".
> 10. **Action-template fallback** — `app/suggested_actions.yaml` — "remediation-only templates · never investigation-style · keyed by alertname + deployment_type".
>
> **Bottom of canvas — egress + persistence (sage envelope titled "Egress · persistence · UI"):**
> Three parallel cards under the pipeline:
> - **Email escalation** — SMTP · public — body: "rendered HTML email · only fires when verdict = ESCALATE · suppressed for DISMISS / data_starved".
> - **RCA history** — SQLite at `/var/lib/triage-service/rca_history.db` — body: "every decision persisted · drives Drain3 7d-recurrence (D8) · feeds closed-loop feedback (US-5.3 designed)".
> - **Operator dashboard** — `:8090/dashboard` (sage-themed) — "Figma-aligned dark-by-default · LeftNav with 6 disabled Epic-5 placeholders · `/dashboard/guide` operator manual".
>
> **Right-edge sidebar — three feedback dashed-arrows (top-to-bottom):**
> - From "Action-template fallback" back up to "LLM call" — labelled **"validator-triggered single retry"**.
> - From "RCA history" up to "History lookup (step 5)" — labelled **"prior verdicts + 7d-recurrence count fed into next prompt"**.
> - From "Operator dashboard" up to "Exemplar injection (step 6)" — labelled **"closed-loop feedback (US-5.3 designed) · `/feedback/override` + `/feedback/confirm` re-weight similar future alerts"**. Render this third one in a slightly faded style with a "PLANNED" pill so it's clear it's not live yet.
>
> **Footer (small caption row):** "Pipeline budget: end-to-end 2400 s · single-LLM-call 1800 s · typical 60–95 s · 89/89 tests green at 2026-04-28."
>
> ---
>
> ## DIAGRAM 2 — "Deployment topology (where things actually run)"
>
> A landscape-orientation diagram with **three environments** drawn as separate rounded-rectangle envelopes, connected by a **central horizontal Tailscale mesh bar** running across the canvas.
>
> The Tailscale bar is a thick lavender pill labelled **"Tailscale tailnet · WireGuard · MagicDNS · user `linalaaraich@`"** with four small node-pin glyphs hanging off it for the four tailnet members. Below the pill, render a small legend: "solid line = on tailnet · dotted line = public IP only · padlock glyph = SSH-key access".
>
> **Left envelope — "AWS us-east-1" (blue-grey background, AWS cloud glyph in corner):**
>
> Inside the envelope, two distinct EC2 boxes. **Do NOT draw a VPC peering link or any internal AWS networking** — the prior diagram's VPC envelope is wrong; the cross-environment link is purely Tailscale.
>
> 1. **`observability-rca-monitoring`** (EC2 t3.large · EIP `52.202.21.192` · public + tailnet `100.74.21.104`)
>    Inside this box, four sage cards in a 2×2 grid:
>    - **Prometheus** `:9090` · TSDB
>    - **Loki** `:3100` · log store + Badger
>    - **Jaeger** `16686 UI · 4318 OTLP-HTTP · 4317 gRPC`
>    - **Grafana** `:3000` (pink) — sub-label "unified alerting · single contact point `triage-webhook` · no Alertmanager · gmail-smtp removed 2026-04-24"
>    Plus a single **OTel Collector** card at the bottom (`4317 gRPC · 4318 HTTP`).
>    Side-rail: peach exporters card listing `node-exporter :9100` · `cAdvisor :8081`.
>
> 2. **`observability-rca-k3s`** (EC2 t3.large · EIP `52.5.239.234` · NOT on tailnet — public IP only · padlock glyph + caption "ansible-deploy via `~/.ssh/ansible_key` as `deploy@`")
>    Inside this box, three blue-grey workload cards:
>    - **Spring Boot API** (Deployment, replicas=3) · OpenTelemetry Java agent attached
>    - **MySQL** (StatefulSet) · application database
>    - **Kong API gateway** (DaemonSet · NodePort `:30080` public)
>    A small note in the corner: "Frontend · React · also lives in this cluster as a Service".
>    Side-rail: peach exporters card `node-exporter :9100` · `cAdvisor :8081` · `kube-state-metrics`.
>
> Connect the two AWS boxes with a **solid mint arrow** labelled "scrape · Prometheus pulls k3s exporters · `:9100`/`:8081`/`:30080`/spring-boot actuator `:8080/actuator/prometheus`".
>
> **Centre envelope — "Home · Lina's laptop" (warm slate background with a tiny house glyph):**
>
> 1. **`adolin`** (Windows host · tailnet `100.101.132.78`) — render small, just a Tailscale node and a Docker Desktop glyph; note "stays awake even when the lid is closed (verified during the 2026-04-23→24 incident)".
>
> 2. **`adolin-wsl`** (Ubuntu WSL2 inside `adolin` · tailnet `100.117.118.70`) — render this LARGE, as the visual focal point of the diagram. Inside it, group the components into four sub-clusters:
>    - **Triage service** (lavender) — FastAPI on `:8090` · `/webhook/grafana` · `/webhook/drain3` · `/dashboard` · `/decisions` · `/metrics` · `/health`
>    - **Ollama LLM host** (lavender, distinct card) — `:11434` · `qwen2.5:7b-instruct` · runtime: **NVIDIA GTX 1060 · 6 GB VRAM** (call this out in a yellow GPU pill in the corner)
>    - **MCP bridge servers** (teal cluster of 5 cards) — `prometheus-mcp :8091` · `loki-mcp :8092` · `jaeger-mcp :8093` · `drain3-mcp :8094` · `rca-history-mcp :8095`
>    - **Local infra** (peach) — `Watchtower` (pulls GHCR every 5 min for Continuous Delivery) · `node-exporter :9100` · `cAdvisor :8081`
>    Caption under the WSL2 box: "compose file at `~/cires-ai/docker-compose.yml` · `.env` ansible-managed by `roles/triage_laptop` (single-command CD from the controller)".
>
> **Right envelope — "Cloud shell · controller" (slate background):**
>
> 1. **`claude-controller`** (ephemeral EC2 · tailnet `100.86.159.84` · tailnet-only, no public IP) — small box with three glyphs: ansible control, GitHub Actions trigger, this Claude Code session. Caption: "the orchestration node · runs ansible playbooks against monitoring-vm + adolin-wsl + k3s · holds nothing stateful".
>
> **Cross-environment runtime arrows (label every one):**
> - Grafana → `adolin-wsl:8090/webhook/grafana` — solid lavender — "alert webhook · over Tailscale"
> - Triage MCPs → Prometheus / Loki / Jaeger on `observability-rca-monitoring` — solid mint, three parallel — "context fan-out queries · over Tailscale"
> - Triage → SMTP (Gmail public) — solid pink, exits the tailnet bar to the right edge — "escalation email · public internet"
> - Watchtower → GHCR (`ghcr.io/linalaaraich/...`) — dotted peach exiting upward — "image polling every 5 min · public internet · CD"
> - GitHub Actions → GHCR — dotted peach — "build + push on every commit"
> - Controller → all three environments — dotted lavender, three branches — "ansible · SSH"
>   - To `observability-rca-monitoring` — over Tailscale
>   - To `adolin-wsl` — over Tailscale
>   - To `observability-rca-k3s` — over PUBLIC SSH (padlock glyph) — sub-label "ansible_key · deploy@"
>
> **Bottom-right — "FUTURE" inset (faded, dashed border, ~25 % opacity):**
> A small ghosted EC2 box labelled **`g5.xlarge` · us-west-2 · A10G 24 GB VRAM** with a caption: "G+VT vCPU quota approved 2026-04-27 in us-west-2 only (limit 4 = exactly one g5.xlarge) · stand-up unblocked but DEFERRED · trigger to revisit: needing qwen2.5:14b / 32b-q4 or higher demo throughput · cross-region from us-east-1 monitoring → connectivity over Tailscale, not VPC peering". Dotted arrow from this future box back to the Tailscale mesh bar with the label "would join as a fifth tailnet node".
>
> **Top-right — title block:**
> Two-line title: "**CIRES Observability — deployment topology**" / sub-line "AI-on-laptop · cross-env Tailscale mesh · k3s workload · 2026-04-28". Below that, a 5-row legend (icon + label) for: tailnet pill · solid runtime arrow · dotted control-plane arrow · padlock = public SSH only · faded box = future / not deployed.
>
> ---
>
> ## CONSTRAINTS THAT APPLY TO BOTH DIAGRAMS
>
> 1. **Hostname accuracy is mandatory.** Use exactly: `claude-controller`, `adolin`, `adolin-wsl`, `observability-rca-monitoring`, `observability-rca-k3s`. Do NOT use the older aspirational names `cires-ai`, `lina-laptop`, `monitoring-vm` — those were never applied.
> 2. **No g4dn.xlarge anywhere.** The previous diagram showed AI on a g4dn.xlarge inside the VPC; that was never deployed. Today's GPU host is the **laptop GTX 1060**; the future GPU host is a **g5.xlarge in us-west-2** (rendered as ghosted "FUTURE").
> 3. **No VPC envelope around AWS resources.** Each EC2 is its own box; the only inter-environment link is Tailscale. Do not draw private IPs in the `192.168.x.x` range — those were from a deprecated VPC layout.
> 4. **Spring Boot, Kong, MySQL run on k3s, not on a "Network VM" or "App Backend VM".** Those VM titles from the prior diagram are stale.
> 5. **Drain3 is two things at once** — a *self-firing alert source* (its own webhook into the triage service) AND a *step inside the pipeline* (annotation at step 4). Diagram 1 must show both roles.
> 6. **The exemplar library is a first-class pipeline stage** (step 6 of 10). It is NOT a sidecar or an afterthought — it sits between history lookup and the LLM call.
> 7. **Tailscale, not VPC peering, is the cross-environment substrate.** Show MagicDNS short hostnames everywhere; show actual tailnet IPs only when a port is being called out (e.g. `100.117.118.70:8090`). Public EIPs only on `observability-rca-monitoring` (`52.202.21.192`) and `observability-rca-k3s` (`52.5.239.234`).
> 8. **Time-stamp every diagram `2026-04-28` in the bottom-right.** Future viewers should be able to tell at a glance how fresh the snapshot is.
> 9. **Use ports as labels, never as decoration.** If a port is on a card, it is the port the component actually listens on; don't invent ports for visual symmetry.
> 10. **Density target:** dense enough that an SRE could rebuild the system from the diagram, sparse enough to fit on one 16:10 slide each. Aim for ~60–80 visible labels per diagram, not 200.

---

## Verification checklist (before accepting Figma's output)

- [ ] No `g4dn.xlarge` and no `VPC` envelope on Diagram 2.
- [ ] Hostnames spelled exactly: `claude-controller`, `adolin`, `adolin-wsl`, `observability-rca-monitoring`, `observability-rca-k3s`.
- [ ] Exemplar injection card on Diagram 1 has the "NEW · D17" tag and lists 11 archetypes.
- [ ] Bounded-agency retry shown as a dashed loop, not a solid arrow.
- [ ] Tailscale bar runs across the centre of Diagram 2 with all 4 tailnet nodes hanging off it.
- [ ] k3s box has a padlock glyph (NOT on tailnet — public SSH only).
- [ ] `g5.xlarge us-west-2` ghosted FUTURE box is present and clearly faded.
- [ ] Both diagrams date-stamped `2026-04-28`.
- [ ] GTX 1060 / 6 GB VRAM called out as the current GPU runtime.
- [ ] qwen2.5:7b (not llama3:8b, not llama3.2:3b) is the named model.
