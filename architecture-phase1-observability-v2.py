#!/usr/bin/env python3
"""
CIRES Observability Platform — Phase 1 architecture (designer-style v2).

Matplotlib-rendered, A4-portrait infographic showing the observability
foundation: instrument -> store -> visualise -> alert. Renders horizontal
swim-lane bands with rounded cards, drop shadows, and color-coded arrows.

Output: architecture-phase1-observability-v2.png at 300 DPI.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

# --- Palette (hybrid light bg + dashboard accents) ---
BG = "#fafafa"
TEXT = "#0f1117"
MUTED = "#8890a0"
CARD_BG = "#ffffff"
SHADOW = "#000000"  # used at low alpha

BLUE = "#4ea8de"     # application
GREEN = "#6bcf7f"    # collectors
CYAN = "#40d0d0"     # storage
ORANGE = "#f0a050"   # surfacing / processing
PURPLE = "#b07ee8"   # AI / output bridge
RED = "#e06070"      # safety / alert

plt.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]


def add_card(ax, cx, cy, w, h, title, subtitle=None, accent=BLUE,
             title_fs=9.5, sub_fs=7.2, title_weight="bold",
             dashed=False, alpha=1.0):
    """Rounded card with drop shadow, accent border, white fill.

    cx, cy are the center. Title/subtitle are vertically stacked within.
    Offsets are computed from h so cards of any height look right.
    """
    # Drop shadow (offset down-right, light gray)
    shadow = FancyBboxPatch(
        (cx - w / 2 + 0.4, cy - h / 2 - 0.4), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.35",
        linewidth=0, facecolor=SHADOW, alpha=0.12, zorder=2,
    )
    ax.add_patch(shadow)

    style = "round,pad=0.02,rounding_size=0.35"
    edge_kw = dict(linewidth=1.6, edgecolor=accent)
    if dashed:
        edge_kw["linestyle"] = (0, (4, 2))

    card = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=style,
        facecolor=CARD_BG, alpha=alpha, zorder=3, **edge_kw,
    )
    ax.add_patch(card)

    if subtitle:
        # Place title slightly above center, subtitle below — both well inside.
        title_y = cy + h * 0.14
        sub_y = cy - h * 0.20
        ax.text(cx, title_y, title, ha="center", va="center",
                fontsize=title_fs, fontweight=title_weight, color=TEXT, zorder=4)
        ax.text(cx, sub_y, subtitle, ha="center", va="center",
                fontsize=sub_fs, color=MUTED, style="italic", zorder=4)
    else:
        ax.text(cx, cy, title, ha="center", va="center",
                fontsize=title_fs, fontweight=title_weight, color=TEXT, zorder=4)


def add_arrow(ax, x1, y1, x2, y2, color=MUTED, lw=1.6, alpha=0.85,
              style="-|>", mut=16, connectionstyle=None):
    kw = dict(
        arrowstyle=style, mutation_scale=mut,
        color=color, linewidth=lw, alpha=alpha, zorder=5,
    )
    if connectionstyle is not None:
        kw["connectionstyle"] = connectionstyle
    arr = FancyArrowPatch((x1, y1), (x2, y2), **kw)
    ax.add_patch(arr)


def add_layer_band(ax, y0, y1, color, label, x_left=2.5, x_right=98):
    """Tinted horizontal band with a small all-caps left-margin label."""
    ax.axhspan(y0, y1, xmin=x_left / 100, xmax=x_right / 100,
               color=color, alpha=0.06, zorder=0)
    # Left margin label (rotated 90 deg, magazine layout style)
    mid_y = (y0 + y1) / 2
    # Use spaces between letters to fake letter-spacing
    spaced = " ".join(label)
    ax.text(1.4, mid_y, spaced, ha="center", va="center",
            fontsize=8.0, fontweight="bold", color=color,
            rotation=90, zorder=1, alpha=0.95)


def main() -> None:
    # A4 portrait: 8.27 x 11.69 inches
    fig, ax = plt.subplots(figsize=(8.27, 11.69), facecolor=BG)
    ax.set_facecolor(BG)
    # Coordinate system: 0-100 x, 0-140 y (taller than wide for portrait)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 140)
    ax.set_axis_off()

    # ---------- Title block ----------
    ax.text(50, 134.5, "CIRES Observability Platform",
            ha="center", va="center", fontsize=22, fontweight="bold",
            color=TEXT, zorder=10)
    ax.text(50, 130.0, "P H A S E   1     ·     O B S E R V A B I L I T Y   F O U N D A T I O N",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color=BLUE, zorder=10)
    ax.text(50, 126.5,
            "instrument  ->  store  ->  visualise  ->  alert",
            ha="center", va="center", fontsize=10.5, color=MUTED,
            style="italic", zorder=10)

    # A thin horizontal accent rule under the title
    ax.plot([18, 82], [123.5, 123.5], color=MUTED, linewidth=0.6, alpha=0.5,
            zorder=1)

    # ---------- Layer bands (top -> bottom) ----------
    # Layer y-ranges (top to bottom). Total content area: 18 -> 120
    L1_TOP, L1_BOT = 120, 100   # APPLICATION (blue)
    L2_TOP, L2_BOT = 98,  80    # COLLECTORS (green)
    L3_TOP, L3_BOT = 78,  56    # STORAGE (cyan)
    L4_TOP, L4_BOT = 54,  32    # SURFACING (orange)
    L5_TOP, L5_BOT = 30,  12    # OUTPUT EDGE (purple)

    add_layer_band(ax, L1_BOT, L1_TOP, BLUE, "APPLICATION")
    add_layer_band(ax, L2_BOT, L2_TOP, GREEN, "COLLECTORS")
    add_layer_band(ax, L3_BOT, L3_TOP, CYAN, "STORAGE")
    add_layer_band(ax, L4_BOT, L4_TOP, ORANGE, "SURFACING")
    add_layer_band(ax, L5_BOT, L5_TOP, PURPLE, "OUTPUT EDGE")

    # ============================================================
    # LAYER 1 — APPLICATION
    # ============================================================
    layer1_cy = (L1_TOP + L1_BOT) / 2 + 1   # nudge up a touch for header room

    # Section header inside the band
    ax.text(50, L1_TOP - 3.0, "Application stack   ·   react-springboot-mysql on k3s",
            ha="center", va="center", fontsize=11.0, fontweight="bold",
            color=TEXT, zorder=4)

    # Three side-by-side app cards. Use 2-line labels stacked inside each card
    # so the title text fits comfortably within the card width.
    app_w, app_h = 18, 8.5
    app_xs = [11, 32, 53]
    app_data = [
        ("react", "frontend"),
        ("spring-boot", "backend"),
        ("mysql", "database"),
    ]
    for x, (line1, line2) in zip(app_xs, app_data):
        cx, cy = x, layer1_cy - 1.5
        shadow = FancyBboxPatch(
            (cx - app_w / 2 + 0.4, cy - app_h / 2 - 0.4), app_w, app_h,
            boxstyle="round,pad=0.02,rounding_size=0.35",
            linewidth=0, facecolor=SHADOW, alpha=0.12, zorder=2,
        )
        ax.add_patch(shadow)
        card = FancyBboxPatch(
            (cx - app_w / 2, cy - app_h / 2), app_w, app_h,
            boxstyle="round,pad=0.02,rounding_size=0.35",
            facecolor=CARD_BG, edgecolor=BLUE, linewidth=1.6, zorder=3,
        )
        ax.add_patch(card)
        ax.text(cx, cy + 1.2, line1, ha="center", va="center",
                fontsize=10, fontweight="bold", color=TEXT, zorder=4)
        ax.text(cx, cy - 1.4, line2, ha="center", va="center",
                fontsize=10, fontweight="bold", color=TEXT, zorder=4)

    # Kong gateway card (separated to the right with visible gap)
    kong_x, kong_y = 81, layer1_cy - 1.5
    add_card(ax, kong_x, kong_y, 20, 8.5, "kong api gateway",
             subtitle="network layer", accent=BLUE, title_fs=9.5)

    # ============================================================
    # LAYER 2 — TELEMETRY COLLECTORS
    # ============================================================
    layer2_cy = (L2_TOP + L2_BOT) / 2

    ax.text(50, L2_TOP - 2.8, "Telemetry collectors",
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            color=TEXT, zorder=4)

    coll_w, coll_h = 22, 8.5
    coll_xs = [22, 50, 78]
    coll_data = [
        ("node-exporter", "host metrics"),
        ("OTel collector", "spans + JVM"),
        ("promtail / loki agent", "logs"),
    ]
    for x, (t, sub) in zip(coll_xs, coll_data):
        add_card(ax, x, layer2_cy - 1.5, coll_w, coll_h, t, subtitle=sub,
                 accent=GREEN, title_fs=10)

    # Arrows: APPLICATION -> COLLECTORS
    # App row card centers: 11, 32, 53 (apps) + 81 (kong), card height 8.5
    # Collector row card centers: 22, 50, 78, card height 8.5
    arrow_color_app = BLUE
    app_bottom_y = layer1_cy - 1.5 - 8.5 / 2   # bottom edge of app cards
    coll_top_y = layer2_cy - 1.5 + 8.5 / 2     # top edge of collector cards
    # frontend -> node-exporter
    add_arrow(ax, 11, app_bottom_y, 22, coll_top_y,
              color=arrow_color_app)
    # backend -> OTel
    add_arrow(ax, 32, app_bottom_y, 50, coll_top_y,
              color=arrow_color_app)
    # mysql -> promtail (logs)
    add_arrow(ax, 53, app_bottom_y, 78, coll_top_y,
              color=arrow_color_app)
    # kong -> OTel (gateway emits its own telemetry)
    add_arrow(ax, 81, app_bottom_y, 56, coll_top_y,
              color=arrow_color_app, alpha=0.55,
              connectionstyle="arc3,rad=-0.18")

    # ============================================================
    # LAYER 3 — STORAGE
    # ============================================================
    layer3_cy = (L3_TOP + L3_BOT) / 2

    ax.text(50, L3_TOP - 2.8, "Storage — time-series + object",
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            color=TEXT, zorder=4)

    # 4 storage cards, well-separated
    store_w, store_h = 19, 11
    store_xs = [14, 38, 62, 86]
    store_data = [
        ("Prometheus", "metrics  ·  15d"),
        ("Loki", "logs  ·  7d"),
        ("Jaeger", "traces  ·  ~24h"),
        ("Drain3 store", "log-template clusters"),
    ]
    for x, (t, sub) in zip(store_xs, store_data):
        add_card(ax, x, layer3_cy - 1.0, store_w, store_h, t, subtitle=sub,
                 accent=CYAN, title_fs=10)

    # Arrows: COLLECTORS -> STORAGE
    # Collector card centers: 22, 50, 78. Storage centers: 14, 38, 62, 86
    arrow_color_coll = GREEN
    coll_bottom_y = layer2_cy - 1.5 - 8.5 / 2
    store_top_y = layer3_cy - 1.0 + 11 / 2
    # node-exporter -> Prometheus
    add_arrow(ax, 22, coll_bottom_y, 14, store_top_y,
              color=arrow_color_coll)
    # OTel -> Prometheus (metrics, slight curve to avoid overlap)
    add_arrow(ax, 50, coll_bottom_y, 18, store_top_y,
              color=arrow_color_coll, alpha=0.6,
              connectionstyle="arc3,rad=-0.18")
    # OTel -> Jaeger (traces)
    add_arrow(ax, 50, coll_bottom_y, 62, store_top_y,
              color=arrow_color_coll)
    # promtail -> Loki
    add_arrow(ax, 78, coll_bottom_y, 38, store_top_y,
              color=arrow_color_coll,
              connectionstyle="arc3,rad=0.18")
    # promtail -> Drain3 (logs feed template extraction)
    add_arrow(ax, 78, coll_bottom_y, 86, store_top_y,
              color=arrow_color_coll)

    # ============================================================
    # LAYER 4 — SURFACING
    # ============================================================
    layer4_cy = (L4_TOP + L4_BOT) / 2

    ax.text(50, L4_TOP - 2.8, "Surfacing — operator UX",
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            color=TEXT, zorder=4)

    # Two big cards
    # Grafana dashboards (left)
    add_card(ax, 27, layer4_cy - 0.5, 32, 11,
             "Grafana dashboards",
             subtitle="host  ·  app  ·  latency overviews",
             accent=ORANGE, title_fs=11)
    # Grafana alerting (right) — needs more text below
    alert_x, alert_y, alert_w, alert_h = 72, layer4_cy + 1.5, 32, 8
    add_card(ax, alert_x, alert_y, alert_w, alert_h,
             "Grafana alerting rules", accent=ORANGE, title_fs=11)
    ax.text(alert_x, alert_y - 6.5,
            "HighCpuUsage  ·  HighMemoryUsage\n"
            "HighP95Latency  ·  Drain3AnomalyDetected  ·  ...",
            ha="center", va="center", fontsize=7.6, color=MUTED,
            style="italic", zorder=4)

    # Arrows: STORAGE -> SURFACING
    # Storage centers: 14, 38, 62, 86. Dashboards center: 27, Alerts center: 72
    arrow_color_store = CYAN
    store_bottom_y = layer3_cy - 1.0 - 11 / 2
    dash_top_y = layer4_cy - 0.5 + 11 / 2
    alert_top_y = alert_y + alert_h / 2
    # Prometheus -> dashboards
    add_arrow(ax, 14, store_bottom_y, 22, dash_top_y,
              color=arrow_color_store)
    # Prometheus -> alerts
    add_arrow(ax, 14, store_bottom_y, 62, alert_top_y,
              color=arrow_color_store, alpha=0.5,
              connectionstyle="arc3,rad=-0.18")
    # Loki -> dashboards
    add_arrow(ax, 38, store_bottom_y, 30, dash_top_y,
              color=arrow_color_store)
    # Jaeger -> dashboards
    add_arrow(ax, 62, store_bottom_y, 38, dash_top_y,
              color=arrow_color_store,
              connectionstyle="arc3,rad=0.18")
    # Drain3 -> alerts (the Drain3AnomalyDetected rule)
    add_arrow(ax, 86, store_bottom_y, 80, alert_top_y,
              color=arrow_color_store)

    # ============================================================
    # LAYER 5 — OUTPUT EDGE (bridge to Phase 2)
    # ============================================================
    layer5_cy = (L5_TOP + L5_BOT) / 2

    # The big bridge card
    bridge_w, bridge_h = 64, 12
    bridge_cx, bridge_cy = 50, layer5_cy + 1
    # Shadow + colored card (use purple for bridge to Phase 2)
    add_card(ax, bridge_cx, bridge_cy, bridge_w, bridge_h,
             "Webhook  ->  /webhook/grafana  ->  Phase 2 AI Triage",
             subtitle="bridge to AI layer",
             accent=PURPLE, title_fs=12.5)

    # Arrow from alerts down into the bridge
    add_arrow(ax, alert_x, alert_y - alert_h / 2,
              bridge_cx + 12, bridge_cy + bridge_h / 2,
              color=ORANGE, lw=2.2, mut=20,
              connectionstyle="arc3,rad=0.15")

    # Phase 2 cue arrow exiting the bottom of the bridge
    add_arrow(ax, bridge_cx, bridge_cy - bridge_h / 2,
              bridge_cx, 4.0,
              color=PURPLE, lw=2.4, mut=22)

    ax.text(bridge_cx, 2.2,
            "continues in Phase 2 diagram",
            ha="center", va="center", fontsize=8.5, color=PURPLE,
            fontweight="bold", style="italic", zorder=4)

    # ---------- Footer (small legend) ----------
    legend_y = 7.5
    chips = [
        (BLUE, "application"),
        (GREEN, "collectors"),
        (CYAN, "storage"),
        (ORANGE, "surfacing"),
        (PURPLE, "bridge"),
    ]
    chip_x = 6
    for color, lbl in chips:
        ax.add_patch(Rectangle((chip_x, legend_y - 0.4), 1.6, 0.9,
                               facecolor=color, edgecolor="none", zorder=4))
        ax.text(chip_x + 2.2, legend_y, lbl, fontsize=7,
                color=MUTED, va="center", ha="left", zorder=4)
        chip_x += 14

    fig.savefig(
        "/root/monitoring-docs/architecture-phase1-observability-v2.png",
        dpi=300, bbox_inches="tight", pad_inches=0.3, facecolor=BG,
    )
    print("wrote /root/monitoring-docs/architecture-phase1-observability-v2.png")


if __name__ == "__main__":
    main()
