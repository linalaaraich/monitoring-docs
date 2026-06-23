#!/usr/bin/env python3
"""Generator for the 100-test overarching validation batch card.

Authoring source of truth for `validation-batch-100-2026-06-22.html`.
Edit the TESTS data below and re-run:  python3 validation-batch-100-2026-06-22.py

Every test is a REAL induction (kill a pod, push a bad deploy, flood an API,
toggle a flagd flag, stress a node), per the platform invariant
`feedback_real_induction_tests_only` — NEVER a synthetic /webhook/grafana POST.
The "Result (live)" cell on each row is left blank to be filled on execution
day; the populated matrix is the artifact Lina shows at the soutenance.

Grounding (all code-verified 2026-06-22):
  - 24 Grafana alert rules / 4 groups (tracing 5, infrastructure 10,
    kubernetes 5, log 4), none paused.
  - Pipeline knobs: dedup 300s; pre-LLM suppression 600s (10min); cofire
    window 10min; recurrence_gate on MediumCpuUsage = pre_llm=4,llm_dismiss=10,
    window=2h; critical-flap = 3 dismiss / 360min / sample-every-4; circuit
    breaker 5 fails / 60s -> fail-open ESCALATE conf 0.0; pipeline_timeout 300s;
    exemplar_min_fit_score 0.25; Drain3 tiers component 0.25 / app 0.15 /
    system 0.10, noise floor 0.05, anomaly_threshold 5.
  - LLM qwen2.5:14b, temp 0, num_ctx 32768; median alert->emailed-RCA ~38s.
"""

import html

# ---------------------------------------------------------------------------
# Verdict / result legend used in the "Expected" column.
#   ESCALATE     -> real incident, email sent, named cause
#   DISMISS      -> transient/benign, correctly NOT paged (evidence-based)
#   INCONCLUSIVE -> honest uncertainty, no fabricated cause
#   CONSOLIDATED -> folded into a co-fire primary (one email for the family)
#   SUPPRESSED   -> recurrence/critical-flap/noise gate held it by design
#   RAW          -> circuit-breaker / timeout fail-open: raw alert still emailed
#   NO-FIRE      -> NEGATIVE test: platform correctly stays quiet
# ---------------------------------------------------------------------------

FAMILIES = [
    ("A", "Deployment &amp; configuration faults",
     "A developer pushes a bad change (wrong buildspec, bad env, bad image, "
     "bad probe, bad limits). The cause lives in the deploy, not the code "
     "logic. These exercise the kubernetes + log paths and the LLM&rsquo;s "
     "ability to tie a fresh failure to a configuration delta."),
    ("B", "Service availability (something is down)",
     "A pod, deployment, node, gateway, dependency or backend goes away. "
     "Exercises KubeWorkloadDown / ReplicasDeficit / TargetDown / "
     "OTelCollectorDown and the transient-vs-real distinction."),
    ("C", "Infrastructure faults",
     "Host-level CPU / memory / disk / IO / node pressure on the k3s and "
     "monitoring hosts. Exercises the 10-rule infrastructure group and the "
     "warning-noise controls."),
    ("D", "Client / traffic bottlenecks &amp; latency",
     "Real user-side pressure: traffic spikes, GC pauses, slow downstreams, "
     "pool/thread exhaustion. Exercises HighDemoFrontendP95Latency, the "
     "dormant Kong/Spring latency rules, and trace-decisive RCA."),
    ("E", "Data / database faults",
     "RDS MySQL app_db: failover blips, storage, deadlocks, slow queries, "
     "connection limits, schema drift. Exercises log-path detection and "
     "cause-naming on data-tier failures."),
    ("F", "Application-logic faults (flagd / Astronomy Shop)",
     "Behavioural faults injected via the OTel-Demo feature flags so the "
     "microservice bed misbehaves like a real app. Exercises Drain3 tiers, "
     "error spans, and per-service vs system-wide cause naming."),
    ("G", "Drain3 novel-log-pattern detection",
     "The novelty path (new template / frequency z-score / distribution "
     "shift), 3-tier (component 0.25 / app 0.15 / system 0.10). Includes the "
     "by-design NEGATIVE cases (silent on repeats, noise-floor absorb)."),
    ("H", "Pipeline noise-control &amp; resilience",
     "The five noise layers and the fail-safes: dedup, suppression, "
     "recurrence gate, co-fire consolidation, critical-flap, circuit breaker, "
     "pipeline timeout, bounded one-call agency, incident entity, severity floor."),
    ("I", "Multi-pillar correlation &amp; cascades",
     "Faults that surface across metrics + logs + traces at once. Exercises "
     "the correlation window + service label, and root-vs-symptom naming on "
     "cross-service cascades."),
    ("J", "Anti-hallucination firewall",
     "The two-layer firewall: MCP-only input + output validators. Thin "
     "evidence, dangerous actions, ungrounded deploy claims, wrong-archetype "
     "lures, PII, hedging. The mechanism Lina is proudest of."),
]

# Each test: (id, did, processed, expected)
TESTS = {
"A": [
 ("A1",
  "Roll the employees Helm release with the DB name typo&apos;d: <code>SPRING_DATASOURCE_URL=jdbc:mysql://&hellip;/app_d</code> (the <code>b</code> deleted from <code>app_db</code>). App boots, every query throws.",
  "Component-tier <b>Drain3</b> novelty on the new <code>Unknown database &apos;app_d&apos;</code> stack-trace template; if the app exits, <code>PodCrashLooping</code> / <code>KubeWorkloadReplicasDeficit</code>.",
  "<b>ESCALATE</b> &middot; names &ldquo;new deploy points at a non-existent schema <code>app_d</code> (typo of <code>app_db</code>)&rdquo;, ties it to the rollout window. quality=actionable."),
 ("A2",
  "Redeploy with a wrong <code>SPRING_DATASOURCE_PASSWORD</code> env value.",
  "Component-tier <b>Drain3</b> on <code>Access denied for user</code> auth errors; readiness fails &rarr; <code>KubeWorkloadReplicasDeficit</code>.",
  "<b>ESCALATE</b> &middot; cause = bad DB credential introduced by the deploy, auth rejected. quality=actionable."),
 ("A3",
  "Redeploy pointing <code>SPRING_DATASOURCE_URL</code> host at a typo&apos;d RDS endpoint.",
  "<code>Communications link failure</code> / connect-timeout templates &rarr; <b>Drain3</b> component tier; pod never Ready &rarr; <code>KubeWorkloadReplicasDeficit</code>.",
  "<b>ESCALATE</b> &middot; cause = unreachable DB host (endpoint/DNS typo in deploy). quality=actionable."),
 ("A4",
  "Set the image tag to a non-existent tag (<code>:v9.9.9-nope</code>) and apply.",
  "<code>ImagePullBackOff</code>; pod never Ready for 3m &rarr; <code>KubeWorkloadReplicasDeficit</code> + <code>KubeWorkloadDown</code> (critical).",
  "<b>ESCALATE</b> &middot; cause = image pull failure, bad/absent tag in the deploy. kube-state evidence (pod phase) cited. quality=actionable."),
 ("A5",
  "Remove a required env var/secret the app needs at boot (e.g. a mandatory profile/secret ref).",
  "Boot failure &rarr; <code>CrashLoopBackOff</code> &rarr; <code>PodCrashLooping</code> (restart-rate); Drain3 on the startup exception.",
  "<b>ESCALATE</b> &middot; cause = missing required configuration env var, app aborts on startup. quality=actionable."),
 ("A6",
  "<code>kubectl set resources&hellip; --limits=memory=64Mi</code> on employees &rarr; JVM can&apos;t start in the cgroup.",
  "<code>OOMKilled</code> (exit 137) restart loop &rarr; <code>PodCrashLooping</code>; <code>PodHighMemoryUsage</code> (&gt;85% cgroup).",
  "<b>ESCALATE</b> &middot; cause = memory limit set below the JVM footprint, OOMKilled. Runbook hint = raise the limit. quality=actionable."),
 ("A7",
  "<code>kubectl set resources&hellip; --limits=cpu=50m</code> on employees &rarr; heavy throttling.",
  "<code>PodHighCpuUsage</code> (&gt;80% of cgroup quota); under load <code>HighP95Latency</code>.",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; cause = CPU quota throttling introduced by the deploy. quality=actionable."),
 ("A8",
  "Patch the Service targetPort to a wrong port (8081 not 8080).",
  "Readiness probe fails, endpoints empty &rarr; <code>KubeWorkloadReplicasDeficit</code>; 502 at Kong.",
  "<b>ESCALATE</b> &middot; cause = service/container port mismatch after deploy; no healthy endpoints. quality=actionable."),
 ("A9",
  "Set a bad liveness probe path (<code>/healthz</code> instead of <code>/actuator/health</code>).",
  "Liveness fails &rarr; kubelet restarts the container in a loop &rarr; <code>PodCrashLooping</code>.",
  "<b>ESCALATE</b> &middot; cause = misconfigured liveness probe forcing restarts (app is otherwise healthy). quality=actionable."),
 ("A10",
  "Deploy a build that throws on startup (bad bean / NPE in config).",
  "<code>CrashLoopBackOff</code> &rarr; <code>PodCrashLooping</code>; Drain3 on the new exception template.",
  "<b>ESCALATE</b> &middot; cause = application crash on startup in the new build (names the exception). quality=actionable."),
 ("A11",
  "Patch the deployment with <code>nodeSelector: disktype=does-not-exist</code> &rarr; pod Pending, unschedulable. (the real method used in the co-fire test).",
  "Pod never schedules &rarr; <code>KubeWorkloadReplicasDeficit</code> + <code>KubeWorkloadDown</code> (both critical, co-fire family).",
  "<b>ESCALATE</b> (one CONSOLIDATED email) &middot; cause = unschedulable pod, nodeSelector matches no node. quality=actionable."),
 ("A12",
  "Bad rolling update: new ReplicaSet pods fail readiness, spec=3 available=1.",
  "<code>kube_deployment_spec_replicas - available &ge; 1</code> for 3m &rarr; <code>KubeWorkloadReplicasDeficit</code> (the gap KubeWorkloadDown misses).",
  "<b>ESCALATE</b> &middot; cause = failed rollout, new revision&apos;s pods never become Ready. quality=actionable."),
 ("A13",
  "Mount a non-existent ConfigMap in the deployment spec.",
  "Pod stuck <code>ContainerCreating</code> &rarr; <code>KubeWorkloadReplicasDeficit</code>.",
  "<b>ESCALATE</b> &middot; cause = deploy references a missing ConfigMap; container can&apos;t be created. quality=actionable."),
 ("A14",
  "Reference a renamed/missing Secret in <code>envFrom</code>.",
  "<code>CreateContainerConfigError</code> &rarr; <code>KubeWorkloadReplicasDeficit</code>.",
  "<b>ESCALATE</b> &middot; cause = missing/renamed Secret referenced by the deploy. quality=actionable."),
 ("A15",
  "Switch the deploy strategy to <code>Recreate</code> and roll &rarr; brief full-downtime window.",
  "Short <code>KubeWorkloadDown</code> / <code>TargetDown</code> blip that self-heals well under the gate.",
  "<b>DISMISS</b> (or critical-flap SUPPRESSED) &middot; transient rollout blip, recovered; correctly not paged. (NEGATIVE-ish: noise control.)"),
 ("A16",
  "Deploy with malformed JDBC URL params (good DB, bad option string).",
  "Connection-setup errors &rarr; <b>Drain3</b> component tier; intermittent latency.",
  "<b>ESCALATE</b> &middot; cause = malformed JDBC URL option in the deploy. quality=actionable."),
],
"B": [
 ("B1",
  "<code>kubectl delete pod</code> on the employees pod (ReplicaSet recreates in ~10s).",
  "Scrape gap &rarr; <code>TargetDown</code> for one or two intervals; pod returns Ready.",
  "<b>DISMISS</b> &middot; transient scrape gap, pod recreated by the controller; correctly no page."),
 ("B2",
  "<code>kubectl delete deployment ad</code> in otel-demo entirely.",
  "Unavailable series stops &rarr; <code>KubeWorkloadReplicasDeficit</code> fires (spec-vs-available + <code>noDataState: Alerting</code> watchdog).",
  "<b>ESCALATE</b> &middot; cause = deployment removed / 0 available, names <code>otel-demo/ad</code>. quality=actionable."),
 ("B3",
  "<code>kubectl scale ad --replicas=0</code> (deliberate scale-down, spec=0).",
  "spec=0, available=0 &rarr; deficit = 0 &rarr; <b>no rule fires</b> (intentional scale-to-0 caveat).",
  "<b>NO-FIRE</b> &middot; by design: desired=0 is intentional, not an outage. Documents the caveat for the jury."),
 ("B4",
  "<code>kubectl cordon</code> + <code>drain</code> the k3s node hosting demo workloads.",
  "Pods evicted/rescheduled &rarr; <code>KubeWorkloadDown</code> for the evicted set; possible node-exporter <code>TargetDown</code>.",
  "<b>ESCALATE</b> &middot; cause = node drained, workloads evicted; distinguishes maintenance from crash. quality=actionable."),
 ("B5",
  "Apply a NetworkPolicy blocking cart&rarr;checkout in otel-demo.",
  "checkout&rarr;cart gRPC fails &rarr; error spans + frontend errors &rarr; <code>HighDemoFrontendP95Latency</code> / Drain3.",
  "<b>ESCALATE</b> &middot; cause = network partition between checkout and cart (trace shows the broken edge). quality=actionable."),
 ("B6",
  "Stop the triage container so its own <code>:8090</code> scrape target drops, repeatedly across pushes.",
  "<code>TargetDown</code> on the triage target; repeated short blips.",
  "<b>SUPPRESSED</b> (critical-flap) after &ge;3 honest dismisses in 360m, still 1-in-4 sampled. Tests self-restart flap handling."),
 ("B7",
  "<code>systemctl stop</code> a Prometheus scrape target (node_exporter on k3s).",
  "<code>up == 0</code> for 2m &rarr; <code>TargetDown</code> (critical).",
  "<b>ESCALATE</b> &middot; cause = exporter/target unreachable on host X. quality=actionable (or DISMISS if it self-heals fast)."),
 ("B8",
  "<code>kubectl scale kong --replicas=0</code> (gateway down).",
  "Kong scrape target drops &rarr; <code>TargetDown</code>; <code>/api</code> route would 502.",
  "<b>ESCALATE</b> &middot; cause = API gateway down. quality=actionable."),
 ("B9",
  "<code>ssh GPU host; sudo systemctl stop ollama</code> for 60s while a real alert is mid-flight.",
  "LLM calls fail; 5 fails/60s opens the <b>circuit breaker</b>; pipeline_timeout backstops at 300s.",
  "<b>RAW</b> &middot; fail-open ESCALATE at confidence 0.0, raw alert still emailed (subject flags TIMEOUT). Never fail-silent."),
 ("B10",
  "Remove the app SG ingress to RDS (database unreachable).",
  "<code>Communications link failure</code> across all DB apps &rarr; <b>Drain3</b> app/system tier; <code>KubeWorkloadReplicasDeficit</code> if readiness fails.",
  "<b>ESCALATE</b> &middot; cause = database unreachable (network/SG), platform-wide. quality=actionable."),
 ("B11",
  "<code>systemctl stop loki</code> on the monitoring host.",
  "Ingestion stops &rarr; <code>LokiIngestionRateLow</code> (after 10m) and/or <code>TargetDown</code>.",
  "<b>ESCALATE</b> &middot; cause = Loki down, log ingestion stopped; also verifies triage degrades gracefully with no log evidence."),
 ("B12",
  "<code>systemctl stop jaeger</code> on the monitoring host, then induce a latency alert.",
  "No tracing alert directly; a latency investigation finds the Jaeger bridge empty.",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; investigation proceeds on metrics+logs, explicitly notes traces unavailable, <b>does not fabricate</b> a span. quality=needs_review."),
 ("B13",
  "Stop the in-cluster OTel Collector that the demo exports to.",
  "<code>up{otel} &lt; 1</code> for 1m &rarr; <code>OTelCollectorDown</code> (critical); all demo signals stop.",
  "<b>ESCALATE</b> &middot; cause = collector down, telemetry blackout (named as the observability gap, not a fake app fault). quality=actionable."),
 ("B14",
  "<code>kubectl scale currency --replicas=0</code> in otel-demo (downstream dependency).",
  "checkout/frontend currency calls fail &rarr; cascade errors &rarr; <code>HighDemoFrontendP95Latency</code> + Drain3.",
  "<b>ESCALATE</b> &middot; cause = currency service down is the downstream root, NOT the frontend symptom (trace-decisive). quality=actionable."),
],
"C": [
 ("C1",
  "<code>stress-ng --cpu 4 --timeout 360s</code> on the k3s node.",
  "<code>MediumCpuUsage</code> (80%/1m) then <code>HighCpuUsage</code> (85%/5m), <code>CriticalCpuUsage</code> if &gt;95%.",
  "<b>SUPPRESSED</b> &middot; MediumCpuUsage recurrence-gated (pre_llm=4, llm_dismiss=10/2h) + dedup-absorbed; criticals still escalate. Tests warning noise control."),
 ("C2",
  "<code>stress-ng --vm 2 --vm-bytes 90% --timeout 360s</code> on the k3s node.",
  "<code>HighMemoryUsage</code> (85%/5m), <code>CriticalMemoryUsage</code> (95%/2m).",
  "<b>ESCALATE</b> (critical) &middot; cause = node memory pressure / OOM risk on host X. quality=actionable."),
 ("C3",
  "<code>fallocate -l NNG /fill</code> on the k3s node root fs &gt;85%.",
  "<code>HighDiskUsage</code> (85%/5m); &gt;95% &rarr; <code>CriticalDiskUsage</code>.",
  "<b>ESCALATE</b> &middot; cause = root filesystem filling on the k3s node (names the path). quality=actionable."),
 ("C4",
  "Fill the monitoring host (Loki storage) root fs &gt;85%.",
  "<code>LokiHighDiskUsage</code> (85%/5m); &gt;95% &rarr; <code>LokiCriticalDiskUsage</code>.",
  "<b>ESCALATE</b> &middot; cause = monitoring-host / Loki storage disk pressure. quality=actionable."),
 ("C5",
  "Sustained write growth on the k3s node so the 6h trend projects exhaustion.",
  "<code>predict_linear &lt; 0</code> for 30m &rarr; <code>DiskFillingUp</code> (predictive warning). <i>Long-running, optional.</i>",
  "<b>ESCALATE</b> &middot; cause = disk projected to exhaust within 24h (proactive). quality=actionable."),
 ("C6",
  "<code>stress-ng --cpu</code> on the monitoring host (Prometheus/Grafana).",
  "<code>HighCpuUsage</code> / <code>CriticalCpuUsage</code> on the monitoring instance.",
  "<b>ESCALATE</b> &middot; cause = observability-host CPU saturation (self-monitoring). quality=actionable."),
 ("C7",
  "Drive employees JVM heap up (heap-pressure endpoint) toward the cgroup limit.",
  "<code>PodHighMemoryUsage</code> (&gt;85% of cgroup limit for 2m).",
  "<b>ESCALATE</b> &middot; cause = pod approaching OOM (heap growth); cites jvm_memory_used. quality=actionable."),
 ("C8",
  "Hammer a CPU-heavy endpoint on employees so its cgroup quota saturates.",
  "<code>PodHighCpuUsage</code> (&gt;80% of cgroup quota for 2m).",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; cause = pod CPU throttling under hot-endpoint load. quality=actionable."),
 ("C9",
  "<code>systemctl stop kubelet</code> on the k3s node briefly (node NotReady).",
  "Node NotReady &rarr; mass <code>KubeWorkloadDown</code> + node <code>TargetDown</code>. <i>Most disruptive, gate carefully.</i>",
  "<b>ESCALATE</b> &middot; cause = node down (kubelet), names the node + the impacted workload set (not N separate app faults). quality=actionable."),
 ("C10",
  "Stop only node_exporter on the k3s node.",
  "<code>up == 0</code> &rarr; <code>TargetDown</code> for that target; node infra metrics go stale.",
  "<b>ESCALATE/DISMISS</b> &middot; cause = exporter scrape target down (observability gap, not an app outage). quality=needs_review."),
 ("C11",
  "Stop cAdvisor so pod-level metrics disappear.",
  "<code>PodHigh*Usage</code> go NoData (noDataState: OK) &rarr; no false fire; KSM-derived rules still serve.",
  "<b>NO-FIRE</b> on the pod rules (correct), and any investigation notes the cAdvisor gap rather than inventing pod metrics."),
 ("C12",
  "<code>stress-ng --io 4</code> / <code>fio</code> on the k3s node (disk IO saturation).",
  "IO stall knock-on &rarr; <code>HighDemoFrontendP95Latency</code> and/or pod restarts.",
  "<b>ESCALATE</b> &middot; cause = host IO saturation as the latency root (vs app code). quality=actionable."),
 ("C13",
  "Skew the clock forward on a node (<code>date -s</code>) briefly.",
  "Cert/auth/scrape oddities &rarr; <code>TargetDown</code> and/or novel error logs &rarr; Drain3.",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; cause = time skew on host X. Edge case for honest uncertainty. quality=needs_review."),
 ("C14",
  "Exhaust file descriptors / inodes on the k3s node (mass small-file or socket churn).",
  "Service-level <code>Too many open files</code> errors &rarr; Drain3; possible <code>KubeWorkloadReplicasDeficit</code>.",
  "<b>ESCALATE</b> &middot; cause = fd/inode exhaustion on the host. quality=actionable."),
],
"D": [
 ("D1",
  "Run load-test <code>04-traffic-spike</code> against the demo frontend.",
  "Throughput surge; if p95 crosses 1000ms &rarr; <code>HighDemoFrontendP95Latency</code> (live rule, real loadgen traffic).",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; cause = traffic-driven latency, <b>no code fault</b> (distinguishes load from a bug). quality=needs_review."),
 ("D2",
  "flagd <code>adManualGc</code> (ad service forces a manual GC pause).",
  "ad p95 spikes &rarr; frontend ad calls slow &rarr; <code>HighDemoFrontendP95Latency</code>; trace shows the slow ad span.",
  "<b>ESCALATE</b> &middot; cause = ad-service GC pause (named from the trace waterfall), not the frontend. quality=actionable."),
 ("D3",
  "flagd <code>imageSlowLoad</code> (frontend images load slowly).",
  "Frontend HTTP latency climbs &rarr; <code>HighDemoFrontendP95Latency</code>.",
  "<b>ESCALATE</b> &middot; cause = slow image provider path in the frontend. quality=actionable."),
 ("D4",
  "flagd <code>adHighCpu</code> (ad service CPU burn).",
  "ad CPU &rarr; latency &rarr; <code>HighDemoFrontendP95Latency</code>.",
  "<b>ESCALATE</b> &middot; cause = ad-service CPU saturation as the latency root. quality=actionable."),
 ("D5",
  "Exhaust the employees HikariCP pool (many concurrent slow queries via SELECT SLEEP).",
  "Requests queue waiting for a connection &rarr; <code>HighP95Latency</code> (employees).",
  "<b>ESCALATE</b> &middot; cause = DB connection-pool exhaustion (HikariCP), not slow SQL per se. quality=actionable."),
 ("D6",
  "<code>LOCK TABLES employee WRITE</code> on app_db and hold it.",
  "Queries block &rarr; request latency &rarr; <code>HighP95Latency</code>.",
  "<b>ESCALATE</b> &middot; cause = DB lock contention / blocking transaction. quality=actionable."),
 ("D7",
  "Drive employees past its Tomcat max-threads under load.",
  "Requests rejected/queued &rarr; <code>HighP95Latency</code> + 503 logs &rarr; Drain3.",
  "<b>ESCALATE</b> &middot; cause = thread-pool saturation in the app server. quality=actionable."),
 ("D8",
  "Send real <code>/api</code> traffic through Kong AND induce upstream slowness.",
  "Kong p95 crosses 1000ms &rarr; <code>HighKongP95Latency</code> (dormant until real /api traffic exists).",
  "<b>ESCALATE</b> &middot; cause = gateway-layer latency; also proves the &ldquo;dormant, prod-relevant&rdquo; rule arms with traffic. quality=actionable."),
 ("D9",
  "flagd <code>loadgeneratorFloodHomepage</code> (loadgen floods the homepage).",
  "Traffic surge &rarr; <code>HighDemoFrontendP95Latency</code>.",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; cause = synthetic traffic flood from the load generator. quality=needs_review."),
 ("D10",
  "flagd <code>kafkaQueueProblems</code> (broker/consumer backlog).",
  "Consumer lag &rarr; checkout/accounting backlog &rarr; Drain3 + latency.",
  "<b>ESCALATE</b> &middot; cause = Kafka queue backlog / consumer lag. quality=actionable."),
 ("D11",
  "flagd <code>recommendationCacheFailure</code> (memory leak over time).",
  "Gradual <code>PodHighMemoryUsage</code> &rarr; eventual OOM &rarr; <code>PodCrashLooping</code>.",
  "<b>ESCALATE</b> &middot; cause = recommendation cache leak driving memory growth (slow-burn). quality=actionable."),
 ("D12",
  "Run <code>01-warmup</code> nominal load only (below thresholds).",
  "All latency rules stay under threshold (frontend p95 ~40ms).",
  "<b>NO-FIRE</b> &middot; correctly quiet under nominal traffic (false-positive guard)."),
],
"E": [
 ("E1",
  "Trigger an RDS reboot/failover (brief connection drop).",
  "Short burst of connection errors &rarr; Drain3 brief; latency blip; recovers.",
  "<b>DISMISS</b> &middot; transient DB failover, recovered within the window; evidence-based no-page. (Critical-ish DISMISS test.)"),
 ("E2",
  "Fill app_db to storage limit (writes start failing).",
  "<code>table is full</code> / write errors &rarr; Drain3 component tier.",
  "<b>ESCALATE</b> &middot; cause = database storage exhaustion. quality=actionable."),
 ("E3",
  "Induce a deadlock (two concurrent transactions, reversed lock order).",
  "<code>Deadlock found when trying to get lock</code> &rarr; novel Drain3 template.",
  "<b>ESCALATE</b> &middot; cause = DB deadlock between concurrent transactions. quality=actionable."),
 ("E4",
  "Drop a hot index, then drive the dependent query.",
  "Query latency climbs &rarr; <code>HighP95Latency</code>.",
  "<b>ESCALATE</b> &middot; cause = slow query from a missing index (regression). quality=actionable."),
 ("E5",
  "Open connections up to RDS <code>max_connections</code> and hold them.",
  "<code>Too many connections</code> &rarr; Drain3; app readiness/queries fail &rarr; deficit possible.",
  "<b>ESCALATE</b> &middot; cause = DB connection limit reached. quality=actionable."),
 ("E6",
  "Drop a column the app still selects (schema drift vs code).",
  "<code>Unknown column</code> SQL errors &rarr; component-tier Drain3.",
  "<b>ESCALATE</b> &middot; cause = schema/code mismatch (missing column) after a migration. quality=actionable."),
 ("E7",
  "Run a long table-locking migration during traffic.",
  "Blocked queries &rarr; <code>HighP95Latency</code>.",
  "<b>ESCALATE</b> &middot; cause = migration holding a table lock. quality=actionable."),
 ("E8",
  "Induce stale reads / replica lag (if a read path exists).",
  "Inconsistent reads / errors &rarr; Drain3. <i>Optional &mdash; single RDS instance may make this N/A.</i>",
  "<b>INCONCLUSIVE/ESCALATE</b> &middot; cause = replication/read lag; honest if evidence is thin. quality=needs_review."),
],
"F": [
 ("F1",
  "flagd <code>productCatalogFailure</code> (GetProduct errors).",
  "Product-catalog error spans + <code>Product Catalog Fail</code> logs &rarr; Drain3 component/system tier (error-rate may stay below the metric threshold).",
  "<b>ESCALATE</b> &middot; cause = product-catalog failure (named from the novel template), tied to a flag/regression. quality=actionable."),
 ("F2",
  "flagd <code>cartFailure</code> (EmptyCart fails).",
  "cart errors propagate to checkout &rarr; Drain3 component tier; error spans.",
  "<b>ESCALATE</b> &middot; cause = cart-service failure. quality=actionable."),
 ("F3",
  "flagd <code>paymentFailure</code> at 100% (charge fails).",
  "checkout&rarr;payment errors &rarr; Drain3 + error spans on the payment edge.",
  "<b>ESCALATE</b> &middot; cause = payment charge failures. quality=actionable."),
 ("F4",
  "flagd <code>paymentUnreachable</code> (payment endpoint unreachable).",
  "checkout&rarr;payment broken edge in traces &rarr; Drain3.",
  "<b>ESCALATE</b> &middot; cause = payment service unreachable (downstream), trace shows the cut edge. quality=actionable."),
 ("F5",
  "flagd <code>adFailure</code> (GetAds fails; site stays up).",
  "ad-slot errors; frontend degraded but serving.",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; cause = ad-service failure, partial degradation (not a full outage). quality=needs_review."),
 ("F6",
  "flagd <code>recommendationCacheFailure</code> (cache errors, not yet OOM).",
  "recommendation errors + slowness &rarr; Drain3 component tier.",
  "<b>ESCALATE</b> &middot; cause = recommendation cache failure. quality=actionable."),
 ("F7",
  "Enable 5+ flags at once (productCatalog + cart + ad + kafka + recommendation + payment).",
  "Many services erroring together &rarr; Drain3 escalates to <b>SYSTEM tier (0.10)</b>; co-fire family.",
  "<b>ESCALATE</b> (one consolidated email) &middot; cause = platform-wide novel-error surge (system-tier anomaly). quality=actionable. (The 2026-06-10 documented case.)"),
 ("F8",
  "Fail checkout only.",
  "checkout-scoped errors &rarr; Drain3 <b>component tier</b> on checkout (not system-wide).",
  "<b>ESCALATE</b> &middot; cause = checkout-service fault, scoped to one component (tier discrimination). quality=actionable."),
 ("F9",
  "Toggle a flag on then off within 5 minutes (single fault episode).",
  "Alert fires once; the repeat inside 300s is <b>dedup-absorbed</b>.",
  "<b>ESCALATE</b> once &middot; tests dedup: one investigation, not two. quality=actionable."),
 ("F10",
  "Re-enable a flag fault that was just DISMISSED, within 10 minutes.",
  "<b>Pre-LLM suppression</b> replays the recent DISMISS &mdash; no new LLM call.",
  "<b>SUPPRESSED</b> &middot; replays the prior DISMISS within 600s; saves a GPU investigation by design."),
],
"G": [
 ("G1",
  "Run <code>flood-anomalous-logs</code> (malformed JSON to <code>/api/employee</code>, 90s).",
  "Novel stack-trace templates never learned &rarr; <b>Drain3 component tier (0.25)</b>, anomaly rate climbs.",
  "<b>ESCALATE</b> &middot; cause = novel error template (quoted verbatim from the injected line), tied to malformed input/regression. quality=actionable."),
 ("G2",
  "Inject one brand-new unique exception template at low volume.",
  "New-template signal &rarr; component-tier fire even at low volume (novelty &gt; volume).",
  "<b>ESCALATE</b> &middot; cause names the new template; proves novelty-not-volume detection. quality=actionable."),
 ("G3",
  "Spread a new WARN pattern across several components of one app.",
  "Multiple components of one app elevated &rarr; <b>application tier (0.15)</b>.",
  "<b>ESCALATE</b> &middot; cause = app-wide novel warning pattern (tier = application). quality=actionable."),
 ("G4",
  "Spread a new pattern across many unrelated services.",
  "Broad scope &rarr; <b>system tier (0.10)</b> (lowest bar, widest blast).",
  "<b>ESCALATE</b> &middot; cause = platform-wide novel pattern (tier = system). quality=actionable."),
 ("G5",
  "Replay an ALREADY-LEARNED error template at high volume.",
  "Known template, no novelty &rarr; <b>Drain3 stays SILENT</b> (by design).",
  "<b>NO-FIRE</b> &middot; correct: repeated known failure is silent (novelty not volume). Key jury talking point."),
 ("G6",
  "Make a known template suddenly spike ~10&times; its baseline rate.",
  "Frequency z-score signal (via entity_baselines over Prometheus) &rarr; anomaly.",
  "<b>ESCALATE</b> &middot; cause = anomalous frequency spike of a known template. quality=actionable."),
 ("G7",
  "Sharply change the template mix (one pattern dominates).",
  "Distribution-shift signal &rarr; anomaly.",
  "<b>ESCALATE</b> &middot; cause = log distribution shift. quality=actionable."),
 ("G8",
  "Emit a trickle of anomalies below the 5% rate floor, no new templates.",
  "<code>drain3_noise_suppress</code> (&lt;5% AND no new templates) absorbs it.",
  "<b>NO-FIRE</b> &middot; noise floor holds; tests the suppress path."),
],
"H": [
 ("H1",
  "Induce ad unschedulable (A11) so Down + Deficit co-fire for the same service.",
  "<code>KubeWorkloadDown</code> + <code>KubeWorkloadReplicasDeficit</code>, same (family, service, 10m window).",
  "<b>CONSOLIDATED</b> &middot; primary emails naming the co-fire; sibling persists full RCA with <code>action_taken=consolidated</code>, NO second email."),
 ("H2",
  "Fire the same alert twice within 5 minutes.",
  "Second fire inside <code>dedup_window_seconds=300</code> &rarr; absorbed.",
  "<b>DISMISS/absorbed</b> &middot; one investigation, not two. Tests dedup."),
 ("H3",
  "Re-fire an alert that was just DISMISSED, within 10 minutes.",
  "<b>Pre-LLM suppression</b> (600s) replays the DISMISS &mdash; no LLM call.",
  "<b>SUPPRESSED</b> &middot; replays prior DISMISS; no GPU spend."),
 ("H4",
  "Flap MediumCpuUsage repeatedly (CPU bursts) for &gt;2h.",
  "<code>recurrence_gate=pre_llm=4,llm_dismiss=10,window=2h</code>: first 4 gated pre-LLM; 10 LLM-dismisses force one ESCALATE.",
  "<b>SUPPRESSED</b> then one <b>ESCALATE</b> backstop &middot; tests the human-catches-what-the-LLM-misses gate."),
 ("H5",
  "Repeatedly blip a critical (TargetDown via deploy restarts) over 36h-scale.",
  "Critical-flap: after &ge;3 honest dismisses in 360m AND latest verdict=dismiss, suppress; sample every 4th.",
  "<b>SUPPRESSED</b> with 1-in-4 sampling &middot; the documented 67&times;-in-36h flapper control; escalate breaks the streak instantly."),
 ("H6",
  "Stop Ollama (B9) so 5 LLM calls fail inside 60s.",
  "Circuit breaker opens (5/60s); subsequent alerts fail-open.",
  "<b>RAW</b> &middot; fail-open ESCALATE at confidence 0.0; raw alert emailed. Tests the breaker."),
 ("H7",
  "Force a very long investigation (huge context / stalled LLM).",
  "Whole pipeline in <code>asyncio.wait_for(timeout=300)</code> trips.",
  "<b>RAW</b> &middot; on timeout the raw alert is emailed (never silently lost). Tests pipeline_timeout."),
 ("H8",
  "Fire a thin-evidence alert (KubeWorkloadDown with sparse pre-fetched context).",
  "Bounded agency: the LLM requests <b>exactly ONE</b> extra MCP call (whitelisted, e.g. kube-state); triage composes+executes it.",
  "<b>ESCALATE</b> &middot; the one extra call yields the deciding evidence; the model never calls MCP itself. Tests bounded one-call agency."),
 ("H9",
  "Flap one alert ~40 times in a short window.",
  "Fires aggregate into ONE <code>incidents</code> row by fingerprint; <code>fire_count</code> grows.",
  "<b>1 incident</b>, not 40 emails &middot; tests the incident-entity rollup."),
 ("H10",
  "Send a critical that superficially looks like a flapper.",
  "Severity floor: criticals are exempt from every silent gate.",
  "<b>ESCALATE</b> (always investigated) &middot; &ldquo;toujours investigu&eacute;e, pas toujours remont&eacute;e&rdquo;; only warnings get suppressed."),
],
"I": [
 ("I1",
  "Hold a DB lock (D6) while frontend latency fires &mdash; the 9.6s cascade shape.",
  "<code>HighDemoFrontendP95Latency</code> (symptom) + slow downstream spans + DB-lock logs in the same window.",
  "<b>ESCALATE</b> &middot; RCA names the <b>DB lock as the root</b>, not the frontend (trace-decisive). The X7 standard. quality=actionable."),
 ("I2",
  "Two unrelated faults at once: ad down (otel-demo) + node CPU (k3s host).",
  "<code>KubeWorkloadDown</code> (ad) and <code>HighCpuUsage</code> (node) in the same window, different services.",
  "<b>2 separate ESCALATEs</b> &middot; correctly NOT grouped (different service/cause). Tests conservative grouping."),
 ("I3",
  "Fail one service so metric + log + trace all light up for it together.",
  "Same service, same window across three pillars &rarr; one correlated incident.",
  "<b>ESCALATE</b> &middot; one incident, evidence cites all three pillars; no triple-page. quality=actionable."),
 ("I4",
  "Node CPU pressure coincident with app latency on a pod on that node.",
  "<code>HighCpuUsage</code> (node) + <code>HighP95Latency</code> (app) correlated by host/window.",
  "<b>ESCALATE</b> &middot; RCA attributes latency to the infra cause, not the app code. quality=actionable."),
 ("I5",
  "flagd currency/payment cascade (downstream &rarr; checkout &rarr; frontend).",
  "Frontend latency/errors with the true fault several hops down the trace.",
  "<b>ESCALATE</b> &middot; RCA walks the trace to the downstream root (currency/payment), baseline-complete. quality=actionable."),
],
"J": [
 ("J1",
  "Fire KubeWorkloadDown with deliberately thin evidence (no logs/traces for it).",
  "MCP input layer serves only what exists; output validators scan for fabrication.",
  "<b>INCONCLUSIVE</b> (or evidence-bounded ESCALATE) &middot; <b>no invented service/cause</b>; names only what kube-state supports. quality=needs_review."),
 ("J2",
  "Drive a latency alert that tempts a templated <code>kubectl set resources</code> action (the 0b215ef3 class).",
  "Output validator <b>action-clamp</b>: actionable-but-unsupported &rarr; confidence clamped to 0.4, suggested action stripped, read-only diagnostics added.",
  "<b>ESCALATE</b> with NO dangerous action &middot; the cause-evidence-overlap + action-clamp catch it. The firewall&apos;s origin story."),
 ("J3",
  "Fire an alert with an empty deploy window and see if the model blames a deploy.",
  "Ungrounded-deploy guard: empty deploy evidence &rarr; a claimed deploy cause is rejected.",
  "<b>ESCALATE/INCONCLUSIVE</b> &middot; turns the ungrounded deploy claim into a supported negative (&ldquo;no deploy in window&rdquo;). quality=needs_review."),
 ("J4",
  "Fire an alert whose name pattern-matches an archetype but whose evidence differs.",
  "Exemplar score gate: regex match alone scores 0.10 &lt; <code>exemplar_min_fit_score=0.25</code> &rarr; neutral <code>generic-sre-shape</code>.",
  "<b>ESCALATE</b> &middot; cause derived from evidence, NOT dragged to the wrong archetype shape. Tests the score gate."),
 ("J5",
  "Induce a fault whose traces carry PII (<code>db.statement</code> literals, emails).",
  "Context sanitizer: literals &rarr; <code>?</code>, ids &rarr; <code>:id</code> BEFORE the LLM sees anything.",
  "<b>ESCALATE</b> with <b>no PII</b> in stored evidence &middot; verify the saved decision has only sanitized values. Tests the input firewall."),
 ("J6",
  "Provoke a hedge / banned-phrase first draft (data-starved alert).",
  "<code>response_validator</code> detects hedge/banned-phrase &rarr; bounded retry once.",
  "<b>INCONCLUSIVE</b> honest, OR a grounded second draft &middot; no &ldquo;investigation-only&rdquo; non-answer ships. Tests hedge detection + retry."),
],
}

# Order families per the FAMILIES list and number tests 1..N globally.
ORDERED = []
n = 0
for fid, fname, fdesc in FAMILIES:
    for (tid, did, processed, expected) in TESTS[fid]:
        n += 1
        ORDERED.append((n, fid, tid, did, processed, expected))
TOTAL = n

CSS = """
:root{--bg:#0f1117;--card:#1a1d27;--card2:#1e2130;--border:#2a2d3a;--text:#e0e0e0;
--muted:#8890a0;--accent-blue:#4ea8de;--accent-green:#6bcf7f;--accent-orange:#f0a050;
--accent-purple:#b07ee8;--accent-red:#e06070;--accent-cyan:#40d0d0;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter','Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);
min-height:100vh;line-height:1.7;}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:14px 32px;
background:#13151e;border-bottom:1px solid var(--border);}
.topbar-left{display:flex;align-items:center;gap:16px;}
.back-link{color:var(--muted);text-decoration:none;font-size:13px;}
.back-link:hover{color:var(--text);}
.topbar h1{font-size:16px;font-weight:700;}
.wrap{padding:32px;max-width:1320px;margin:0 auto;}
h2{font-size:22px;font-weight:800;margin:34px 0 14px;color:var(--accent-purple);letter-spacing:-.3px;}
h3{font-size:16px;font-weight:700;margin:22px 0 8px;color:var(--accent-green);}
p{margin:8px 0;font-size:14px;color:var(--muted);}
ul,ol{margin:8px 0 8px 22px;}
li{font-size:13.5px;color:var(--muted);margin:5px 0;line-height:1.6;}
li strong,li b{color:var(--text);}
a{color:var(--accent-blue);text-decoration:none;}a:hover{text-decoration:underline;}
code{font-family:'JetBrains Mono','Fira Code',monospace;font-size:11.5px;
background:rgba(78,168,222,.1);color:var(--accent-cyan);padding:1px 5px;border-radius:3px;}
.note{background:rgba(78,168,222,.06);border:1px solid rgba(78,168,222,.2);border-radius:8px;
padding:14px 18px;margin:16px 0;font-size:13.5px;color:var(--muted);}
.note strong{color:var(--accent-blue);}
.warn{background:rgba(224,96,112,.06);border:1px solid rgba(224,96,112,.25);border-radius:8px;
padding:14px 18px;margin:16px 0;font-size:13.5px;color:var(--muted);}
.warn strong{color:var(--accent-red);}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:12.5px;}
th{text-align:left;padding:9px 11px;background:var(--card2);color:var(--accent-purple);
font-weight:600;border:1px solid var(--border);vertical-align:bottom;}
td{padding:9px 11px;border:1px solid var(--border);color:var(--muted);vertical-align:top;}
td code{font-size:11px;}
td b{color:var(--text);}
.num{color:var(--accent-orange);font-weight:700;text-align:center;white-space:nowrap;}
.res{color:#5a6175;font-style:italic;font-size:11px;white-space:nowrap;}
.famhdr{background:rgba(176,126,232,.08);}
.famhdr td{color:var(--text);font-weight:700;font-size:13.5px;border-top:2px solid var(--accent-purple);}
.pill{display:inline-block;padding:2px 9px;border-radius:10px;font-size:11px;font-weight:600;}
.pill-green{background:rgba(107,207,127,.12);color:var(--accent-green);border:1px solid rgba(107,207,127,.3);}
.pill-orange{background:rgba(240,160,80,.12);color:var(--accent-orange);border:1px solid rgba(240,160,80,.3);}
.pill-red{background:rgba(224,96,112,.12);color:var(--accent-red);border:1px solid rgba(224,96,112,.3);}
.pill-blue{background:rgba(78,168,222,.12);color:var(--accent-blue);border:1px solid rgba(78,168,222,.3);}
.kpi{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0;}
.kpi-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 20px;min-width:150px;}
.kpi-box .v{font-size:24px;font-weight:800;color:var(--accent-cyan);}
.kpi-box .l{font-size:12px;color:var(--muted);margin-top:4px;}
"""

def esc(s):
    # Content already contains intentional HTML entities + tags (code/b/i),
    # so we DO NOT escape; the authoring strings are trusted.
    return s

rows_html = []
last_fam = None
for (num, fid, tid, did, processed, expected) in ORDERED:
    if fid != last_fam:
        fname = next(f[1] for f in FAMILIES if f[0] == fid)
        fdesc = next(f[2] for f in FAMILIES if f[0] == fid)
        count = len(TESTS[fid])
        rows_html.append(
            f'<tr class="famhdr"><td colspan="6">Family {fid} &mdash; {fname} '
            f'<span class="pill pill-blue">{count} tests</span><br>'
            f'<span style="font-weight:400;color:var(--muted);font-size:12.5px">{fdesc}</span></td></tr>'
        )
        last_fam = fid
    rows_html.append(
        "<tr>"
        f'<td class="num">{num}<br><span style="color:var(--muted);font-weight:400">{tid}</span></td>'
        f'<td>{did}</td>'
        f'<td>{processed}</td>'
        f'<td>{expected}</td>'
        f'<td class="res">verdict:&nbsp;___<br>cause&nbsp;&#10003;/&#10007;<br>~__s&nbsp;&middot;&nbsp;email&nbsp;Y/N</td>'
        f'<td class="res">&#9744; PASS<br>&#9744; MISS<br>&#9744; NUANCE</td>'
        "</tr>"
    )

TABLE = "\n".join(rows_html)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Overarching Validation Batch ({TOTAL} tests) &mdash; 2026-06-22 &mdash; CIRES Observability Platform</title>
<style>{CSS}</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-left">
    <a href="index.html" class="back-link">&larr; Back to Index</a>
    <span style="color:var(--border)">|</span>
    <h1>&#129514; Overarching Validation Batch &mdash; {TOTAL} real-induction tests</h1>
  </div>
  <span class="pill pill-orange">2026-06-22 &middot; PLAN (results filled on run)</span>
</div>

<div class="wrap">

<h2>What this is</h2>
<p>
  A single overarching validation campaign of <b>{TOTAL} real-induction tests</b> spanning every
  stage of the platform &mdash; from a developer pushing a bad buildspec, through a service going
  down, infrastructure faults, client bottlenecks, data-tier failures, and the noise-control /
  anti-hallucination machinery itself. It is built to be <b>executed live and then shown at the
  soutenance</b>: each row carries what I do (the injected ground truth), what the platform should
  process (which alert rule and/or Drain3 tier, which pipeline gate), and what the LLM should find
  (verdict + named root cause). The two right-hand columns are blank &mdash; they get filled in on
  the run, and the populated matrix is the artifact.
</p>
<div class="warn">
  <strong>Real induction only.</strong> Every test breaks something real &mdash; a pod, a deploy, a
  node, a flag, a query &mdash; so the MCP bridges serve real data to the model. There are
  <b>no synthetic <code>/webhook/grafana</code> POSTs</b> anywhere in this batch (platform invariant
  <code>feedback_real_induction_tests_only</code>: &ldquo;la cha&icirc;ne de preuves est le produit&rdquo;).
</div>
<div class="note">
  <strong>Environment.</strong> Triage + 6 MCP bridges + Ollama (<code>qwen2.5:14b</code>) on the
  us-west-2 GPU host; monitored systems = the k3s Astronomy-Shop bed (otel-demo, ~22 services,
  loadgen live) + the two Spring Boot apps (<code>app</code>/<code>rental</code>) + Kong + RDS MySQL
  <code>app_db</code> + the monitoring host. Faults land only on the <b>test-bed</b> (otel-demo,
  the app namespaces, the k3s node, RDS) &mdash; never the GPU crown jewel or the observability
  backends, except the deliberate, time-boxed Ollama-stop (B9/H6) and backend-down tests
  (B11/B12/B13) which are reverted immediately. Every scenario reverts; the bed is restored to
  <code>ad 1/1</code>, all flags off, no lingering stress at the end.
</div>

<h2>Why {TOTAL} tests across these stages</h2>
<p>The jury wants to see breadth and depth of validation, and that the platform was exercised the way
   a real incident arrives &mdash; at many layers, by many mechanisms. The batch is organised so each
   family targets a distinct stage of the system:</p>
<ul>
  <li><b>A. Deployment / config faults</b> ({len(TESTS['A'])}) &mdash; the &ldquo;dev pushed a bad change&rdquo; class (wrong DB name, bad image, bad probe, bad limits).</li>
  <li><b>B. Service availability</b> ({len(TESTS['B'])}) &mdash; pods, deployments, nodes, gateway, dependencies, backends going down.</li>
  <li><b>C. Infrastructure</b> ({len(TESTS['C'])}) &mdash; host CPU / memory / disk / IO / node pressure (the 10-rule infra group).</li>
  <li><b>D. Client / traffic bottlenecks</b> ({len(TESTS['D'])}) &mdash; traffic spikes, GC pauses, slow downstreams, pool/thread exhaustion.</li>
  <li><b>E. Data / database</b> ({len(TESTS['E'])}) &mdash; RDS failover, storage, deadlocks, slow queries, connection limits, schema drift.</li>
  <li><b>F. Application logic (flagd)</b> ({len(TESTS['F'])}) &mdash; behavioural microservice faults via the OTel-Demo feature flags.</li>
  <li><b>G. Drain3 novelty</b> ({len(TESTS['G'])}) &mdash; the novel-log path and its by-design negatives.</li>
  <li><b>H. Noise control &amp; resilience</b> ({len(TESTS['H'])}) &mdash; dedup, suppression, recurrence gate, co-fire, critical-flap, circuit breaker, timeout, bounded agency, incident entity, severity floor.</li>
  <li><b>I. Multi-pillar correlation</b> ({len(TESTS['I'])}) &mdash; metrics + logs + traces at once, root-vs-symptom on cascades.</li>
  <li><b>J. Anti-hallucination firewall</b> ({len(TESTS['J'])}) &mdash; thin evidence, dangerous actions, ungrounded claims, PII, hedging.</li>
</ul>

<h2>How to read each row</h2>
<p>Verdicts in the &ldquo;Expected&rdquo; column:
  <span class="pill pill-red">ESCALATE</span> real incident, email sent, named cause &middot;
  <span class="pill pill-green">DISMISS</span> transient/benign, correctly not paged &middot;
  <span class="pill pill-orange">INCONCLUSIVE</span> honest uncertainty, no fabricated cause &middot;
  <span class="pill pill-blue">CONSOLIDATED</span> folded into a co-fire primary &middot;
  <span class="pill pill-orange">SUPPRESSED</span> held by a noise gate by design &middot;
  <span class="pill pill-blue">RAW</span> circuit-breaker/timeout fail-open &middot;
  <span class="pill pill-green">NO-FIRE</span> negative test, correctly quiet.
  On the day, fill <b>Result (live)</b> with the actual verdict, whether the cause was named correctly,
  the alert&rarr;email latency, and tick PASS / MISS / NUANCE.</p>

<h2>The {TOTAL}-test catalog</h2>
<table>
  <tr>
    <th style="width:46px">#</th>
    <th style="width:24%">What I do (real induction = ground truth)</th>
    <th style="width:27%">What the platform processes (alert / Drain3 / gate)</th>
    <th style="width:27%">Expected LLM finding (verdict + named cause)</th>
    <th style="width:11%">Result (live)</th>
    <th style="width:8%">Pass?</th>
  </tr>
  {TABLE}
</table>

<h2>Scorecard to populate on the day</h2>
<p>Aggregate the run into the same KPI shape used in the prior prod-mimic reports, so the numbers are
   directly comparable to the 51/52-cause / 7/7-recall history.</p>
<div class="kpi">
  <div class="kpi-box"><div class="v">__/__</div><div class="l">Detection recall<br>(real faults that fired an alert path)</div></div>
  <div class="kpi-box"><div class="v">__/__</div><div class="l">Cause accuracy<br>(root cause named correctly)</div></div>
  <div class="kpi-box"><div class="v">__/__</div><div class="l">Paging precision<br>(real incidents that emailed)</div></div>
  <div class="kpi-box"><div class="v">__/__</div><div class="l">Negative tests<br>(correctly stayed quiet)</div></div>
  <div class="kpi-box"><div class="v">~__s</div><div class="l">Median alert&rarr;email<br>(target &lt; 60s; history ~38s)</div></div>
  <div class="kpi-box"><div class="v">__</div><div class="l">False pages<br>(emailed a non-incident)</div></div>
</div>

<h2>MCP data-plane check (run once at the start)</h2>
<p>Per the MCP-only invariant, confirm every bridge serves live data before the batch, then spot-check
   that an ESCALATE&apos;s stored <code>evidence</code> contains the real injected artifact (proves the
   chain bridge&rarr;context&rarr;LLM holds):</p>
<table>
  <tr><th>Plane</th><th>Bridge</th><th>Check</th><th>Result</th></tr>
  <tr><td>Metrics</td><td><code>prometheus-mcp:8091</code></td><td><code>up</code> matrix + k8s labels</td><td class="res">&#9744;</td></tr>
  <tr><td>Logs</td><td><code>loki-mcp:8092</code></td><td>200 + live log lines</td><td class="res">&#9744;</td></tr>
  <tr><td>Traces</td><td><code>jaeger-mcp:8093</code></td><td>real spans/durations</td><td class="res">&#9744;</td></tr>
  <tr><td>Templates</td><td><code>drain3-mcp:8094</code></td><td>healthy, stats reachable</td><td class="res">&#9744;</td></tr>
  <tr><td>History</td><td><code>rca-history-mcp:8095</code></td><td>healthy, DB reachable</td><td class="res">&#9744;</td></tr>
  <tr><td>Deploys</td><td><code>deploy-mcp:8096</code></td><td>rollout events from KSM (6th bridge; live only, kept out of the report)</td><td class="res">&#9744;</td></tr>
</table>

<h2>Execution runbook (so this can be driven live)</h2>
<p>All commands run from the controller against the live tailnet (MagicDNS, never raw IPs). Targets:
   <code>deploy@observability-rca-newacct-k3s</code> (k3s node),
   <code>ubuntu@observability-gpu-uswest2-newacct</code> (GPU host, passwordless sudo).</p>
<ul>
  <li><b>Deploy/config (A):</b> patch the live spec &mdash; <code>kubectl -n app set env / set resources / patch deploy</code>, or roll the Helm release with the bad value; revert by re-applying the known-good manifest.</li>
  <li><b>flagd (D,F):</b> toggle the OTel-Demo feature flags by editing the flagd config (<code>kubectl -n otel-demo edit configmap &lt;flagd-config&gt;</code> &rarr; set the failure variant) or via the demo&apos;s feature-flag UI; revert sets every flag back to <code>off</code>. <i>Confirm the exact flag keys against the live flagd config &mdash; names drift across demo versions.</i></li>
  <li><b>Availability (B):</b> <code>kubectl delete/scale/cordon/drain</code>; <code>systemctl stop</code> a target over SSH; SG edits via Terraform/console &mdash; each reverted immediately.</li>
  <li><b>Infra (C):</b> <code>stress-ng --cpu/--vm/--io</code>, <code>fallocate</code>/<code>dd</code> for disk, <code>tc qdisc add &hellip; netem</code> via <code>nsenter</code> into the pod netns; every one auto-removed on revert.</li>
  <li><b>Data (E):</b> <code>mysql</code> client to RDS &mdash; <code>SELECT SLEEP</code>, <code>LOCK TABLES</code>, connection floods, index drops on a throwaway copy; revert restores schema/locks.</li>
  <li><b>Drain3 (G):</b> the safe HTTP <code>flood-anomalous-logs</code> harness + targeted novel/known log injection.</li>
  <li><b>Resilience (H):</b> compose the above (e.g. Ollama-stop for the breaker, repeated blips for the flap gate); these are the only ones that touch the AI tier &mdash; time-box them.</li>
</ul>
<div class="warn">
  <strong>Pacing.</strong> Most rules have a <code>for:</code> of 2&ndash;5 min before they fire, and each
  investigation is ~38&ndash;180s, so {TOTAL} sequential inductions is a multi-hour campaign &mdash; run it
  in <b>batches by family</b> (the prior reports ran ~8 at a time), reverting between batches, and let the
  GPU idle-checker sleep the host between sittings. Negative tests (B3, C11, D12, G5, G8) and the
  resilience gates (H*) are the cheapest to demo live; the cascade (I) and firewall (J) families are the
  most jury-impressive.
</div>

<p style="margin-top:20px;">See also:
  <a href="stress-test-report-2026-06-10.html">2026-06-10 injected-vs-detected stress report</a>,
  <a href="prod-mimic-test-report-2026-06-11.html">2026-06-11 prod-mimic KPI report</a>,
  <a href="engineering-log.html">engineering log</a>, and the audit trail under
  <code>monitoring-audit-results/audits/</code>. Generator:
  <code>validation-batch-100-2026-06-22.py</code>.</p>

</div>
</body>
</html>
"""

if __name__ == "__main__":
    out = __file__.replace(".py", ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(HTML)
    print(f"wrote {out} with {TOTAL} tests across {len(FAMILIES)} families")
