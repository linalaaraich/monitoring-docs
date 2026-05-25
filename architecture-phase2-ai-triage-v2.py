#!/usr/bin/env python3
"""
CIRES Observability Platform — Phase 2 AI triage (designer-style v2).

Matplotlib-rendered, A4-portrait infographic showing the AI triage layer:
webhook -> MCP context -> LLM verdict -> operator brief. Renders horizontal
swim-lane bands with rounded cards, drop shadows, and the MCP
"hallucination firewall" boxed in red.

Output: architecture-phase2-ai-triage-v2.png at 300 DPI.
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
SHADOW = "#000000"

BLUE = "#4ea8de"     # triggers / outputs
GREEN = "#6bcf7f"    # not used heavily
CYAN = "#40d0d0"     # outputs
ORANGE = "#f0a050"   # triage pipeline
PURPLE = "#b07ee8"   # LLM
RED = "#e06070"      # MCP firewall / safety

plt.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]


def add_card(ax, cx, cy, w, h, title, subtitle=None, accent=BLUE,
             title_fs=9.5, sub_fs=7.2, title_weight="bold",
             dashed=False, alpha=1.0, fill_color=None):
    """Rounded card with drop shadow, accent border, white fill."""
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

    fc = fill_color if fill_color is not None else CARD_BG
    card = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=style,
        facecolor=fc, alpha=alpha, zorder=3, **edge_kw,
    )
    ax.add_patch(card)

    if subtitle:
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
              style="-|>", mut=16, connectionstyle=None, linestyle="-"):
    kw = dict(
        arrowstyle=style, mutation_scale=mut,
        color=color, linewidth=lw, alpha=alpha, zorder=5, linestyle=linestyle,
    )
    if connectionstyle is not None:
        kw["connectionstyle"] = connectionstyle
    arr = FancyArrowPatch((x1, y1), (x2, y2), **kw)
    ax.add_patch(arr)


def add_layer_band(ax, y0, y1, color, label, x_left=2.5, x_right=98):
    ax.axhspan(y0, y1, xmin=x_left / 100, xmax=x_right / 100,
               color=color, alpha=0.06, zorder=0)
    mid_y = (y0 + y1) / 2
    spaced = " ".join(label)
    ax.text(1.4, mid_y, spaced, ha="center", va="center",
            fontsize=8.0, fontweight="bold", color=color,
            rotation=90, zorder=1, alpha=0.95)


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.27, 11.69), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 140)
    ax.set_axis_off()

    # ---------- Title block ----------
    ax.text(50, 134.5, "CIRES Observability Platform",
            ha="center", va="center", fontsize=22, fontweight="bold",
            color=TEXT, zorder=10)
    ax.text(50, 130.0, "P H A S E   2     ·     A I   T R I A G E   L A Y E R",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color=PURPLE, zorder=10)
    ax.text(50, 126.5,
            "webhook  ->  MCP context  ->  LLM verdict  ->  operator brief",
            ha="center", va="center", fontsize=10.5, color=MUTED,
            style="italic", zorder=10)

    ax.plot([18, 82], [123.5, 123.5], color=MUTED, linewidth=0.6, alpha=0.5,
            zorder=1)

    # ---------- Layer bands (top -> bottom) ----------
    # Total content area: ~5 -> 122
    L1_TOP, L1_BOT = 122, 113    # TRIGGERS (blue)
    L2_TOP, L2_BOT = 111, 72     # TRIAGE PIPELINE (orange)
    L3_TOP, L3_BOT = 70, 41      # MCP LAYER (red firewall)
    L4_TOP, L4_BOT = 39, 27      # LLM (purple)
    LS_TOP, LS_BOT = 25, 20      # SAFETY OVERLAY (red, thin band)
    L5_TOP, L5_BOT = 18, 5       # OUTPUTS (cyan)

    add_layer_band(ax, L1_BOT, L1_TOP, BLUE, "TRIGGERS")
    add_layer_band(ax, L2_BOT, L2_TOP, ORANGE, "TRIAGE PIPELINE")
    add_layer_band(ax, L3_BOT, L3_TOP, RED, "MCP LAYER")
    add_layer_band(ax, L4_BOT, L4_TOP, PURPLE, "LLM")
    # Safety overlay is a thin red band with stronger tint
    ax.axhspan(LS_BOT, LS_TOP, xmin=0.025, xmax=0.98,
               color=RED, alpha=0.09, zorder=0)
    add_layer_band(ax, L5_BOT, L5_TOP, CYAN, "OUTPUTS")

    # ============================================================
    # LAYER 1 — TRIGGERS
    # ============================================================
    layer1_cy = (L1_TOP + L1_BOT) / 2

    trig_w, trig_h = 22, 6.5
    trig_xs = [18, 50, 82]
    trig_titles = [
        "Grafana alert webhook",
        "Drain3 anomaly producer",
        "Manual webhook (curl)",
    ]
    for x, t in zip(trig_xs, trig_titles):
        add_card(ax, x, layer1_cy - 0.5, trig_w, trig_h, t, accent=BLUE,
                 title_fs=8.5)

    # ============================================================
    # LAYER 2 — TRIAGE PIPELINE (vertical chain of 5 cards)
    # ============================================================
    # Section header offset to right so trigger->pipeline arrows can pass
    # cleanly down the centerline.
    ax.text(85, L2_TOP - 2.2, "Triage pipeline",
            ha="right", va="center", fontsize=11.5, fontweight="bold",
            color=TEXT, zorder=4)

    pipe_w, pipe_h = 56, 5.6
    # Available band y-range for stages: leave room for header at top
    pipe_top = L2_TOP - 6.5
    pipe_bot = L2_BOT + 1.5
    pipe_step = (pipe_top - pipe_bot) / 4
    pipe_ys = [pipe_top - i * pipe_step for i in range(5)]
    stages = [
        ("Dedup",
         "DA-5 family + DA-4 content-hash  ·  shipped 2026-05-25 b8fa2c8"),
        ("Pre-LLM suppression",
         "Layer 2 — silently drop noisy / repeating alerts"),
        ("Recurrence gate",
         "US-5.8 — guard against same incident re-triggering LLM"),
        ("Context gather",
         "MCP fan-out — pull metrics, logs, traces for incident window"),
        ("Drain3 annotate logs",
         "tag with template ID + cluster freq before passing to LLM"),
    ]
    for y, (title, sub) in zip(pipe_ys, stages):
        add_card(ax, 50, y, pipe_w, pipe_h, title, subtitle=sub,
                 accent=ORANGE, title_fs=10, sub_fs=7.0)

    # Arrows from TRIGGERS down into first pipeline stage
    trig_bottom_y = layer1_cy - 0.5 - trig_h / 2
    first_pipe_top_y = pipe_ys[0] + pipe_h / 2
    for x in trig_xs:
        add_arrow(ax, x, trig_bottom_y, 50, first_pipe_top_y,
                  color=BLUE, lw=1.5,
                  connectionstyle=("arc3,rad=0.0" if x == 50
                                   else f"arc3,rad={'-' if x < 50 else ''}0.05"))

    # Arrows between adjacent pipeline stages (downward)
    for i in range(len(pipe_ys) - 1):
        y_top = pipe_ys[i] - pipe_h / 2
        y_bot = pipe_ys[i + 1] + pipe_h / 2
        add_arrow(ax, 50, y_top, 50, y_bot, color=ORANGE, lw=2.0, mut=18)

    # ============================================================
    # LAYER 3 — MCP LAYER (Hallucination Firewall)
    # ============================================================
    # Big red dashed rectangle around the MCP cluster
    mcp_band_y_mid = (L3_TOP + L3_BOT) / 2
    firewall_top = L3_TOP - 1.5
    firewall_bot = L3_BOT + 0.5
    firewall_left = 5
    firewall_right = 95
    fw_rect = Rectangle(
        (firewall_left, firewall_bot),
        firewall_right - firewall_left,
        firewall_top - firewall_bot,
        linewidth=2.0, edgecolor=RED, facecolor=RED, alpha=0.04,
        linestyle=(0, (6, 3)), zorder=1,
    )
    ax.add_patch(fw_rect)

    # Bold red label inside firewall, near the top
    ax.text(50, firewall_top - 2.5,
            "MCP LAYER  ·  HALLUCINATION FIREWALL",
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            color=RED, zorder=4)
    ax.text(50, firewall_top - 5.3,
            "every byte the LLM sees passed through here",
            ha="center", va="center", fontsize=8.5, color=RED, style="italic",
            zorder=4)

    # 6 MCP cards in a row inside the firewall. Use 2-line labels stacked.
    # Reduce width and increase center spacing to leave gap between cards.
    mcp_w, mcp_h = 12, 9
    mcp_xs = [11, 26, 41, 56, 71, 86]
    mcp_data = [
        ("Prometheus", "MCP", False),
        ("Loki", "MCP", False),
        ("Jaeger", "MCP", False),
        ("Drain3", "MCP", False),
        ("RCA-history", "MCP", False),
        ("k8s / Rancher", "Sprint 5", True),
    ]
    mcp_cy = firewall_bot + 6.5   # vertical center of MCP card row
    for x, (line1, line2, dashed) in zip(mcp_xs, mcp_data):
        # Manual placement so two lines stack nicely inside a narrow card
        shadow = FancyBboxPatch(
            (x - mcp_w / 2 + 0.4, mcp_cy - mcp_h / 2 - 0.4), mcp_w, mcp_h,
            boxstyle="round,pad=0.02,rounding_size=0.35",
            linewidth=0, facecolor=SHADOW, alpha=0.12, zorder=2,
        )
        ax.add_patch(shadow)
        ls = (0, (4, 2)) if dashed else "-"
        card = FancyBboxPatch(
            (x - mcp_w / 2, mcp_cy - mcp_h / 2), mcp_w, mcp_h,
            boxstyle="round,pad=0.02,rounding_size=0.35",
            facecolor=CARD_BG, edgecolor=RED, linewidth=1.6,
            linestyle=ls, zorder=3,
        )
        ax.add_patch(card)
        ax.text(x, mcp_cy + 1.4, line1, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=TEXT, zorder=4)
        if dashed:
            ax.text(x, mcp_cy - 1.4, line2, ha="center", va="center",
                    fontsize=6.8, color=MUTED, style="italic", zorder=4)
        else:
            ax.text(x, mcp_cy - 1.4, line2, ha="center", va="center",
                    fontsize=8.0, fontweight="bold", color=TEXT, zorder=4)

    # Arrows from final pipeline stage down into MCP layer (one per MCP)
    pipe_last_bot_y = pipe_ys[-1] - pipe_h / 2
    for x in mcp_xs:
        add_arrow(ax, 50, pipe_last_bot_y, x, mcp_cy + mcp_h / 2,
                  color=ORANGE, lw=1.2, alpha=0.65,
                  connectionstyle=f"arc3,rad={(x - 50) * 0.004}")

    # "Reads back from Phase 1" callout — appended to the firewall subtitle
    # as a third line, in the same red, italic style. Keeps the visual story
    # tight without needing a separate chip that conflicts with arrows.
    ax.text(50, firewall_top - 7.5,
            "these MCPs read back from Phase 1 storage   "
            "Prometheus / Loki / Jaeger / Drain3",
            ha="center", va="center", fontsize=7.8, color=RED,
            style="italic", fontweight="bold", zorder=4)

    # ============================================================
    # LAYER 4 — LLM
    # ============================================================
    layer4_cy = (L4_TOP + L4_BOT) / 2

    llm_w, llm_h = 76, 11
    add_card(ax, 50, layer4_cy, llm_w, llm_h,
             "Ollama  ·  qwen2.5:14b (primary) + 7b (fallback)",
             subtitle="g5.xlarge  ·  A10G  ·  us-west-2     median 38 s end-to-end",
             accent=PURPLE, title_fs=11, sub_fs=8.5)

    # Arrows from each MCP down into the LLM
    mcp_bottom_y = mcp_cy - mcp_h / 2
    llm_top_y = layer4_cy + llm_h / 2
    for x in mcp_xs:
        add_arrow(ax, x, mcp_bottom_y, 50, llm_top_y,
                  color=RED, lw=1.3, alpha=0.7,
                  connectionstyle=f"arc3,rad={(50 - x) * 0.004}")

    # ============================================================
    # LAYER 5 — OUTPUTS
    # ============================================================
    layer5_cy = (L5_TOP + L5_BOT) / 2

    out_w, out_h = 19, 8
    out_xs = [13, 36, 60, 84]
    out_data = [
        ("Email notifier", "SMTP"),
        ("/dashboard/v2", "FastAPI"),
        ("RCA SQLite store", "history table"),
        ("Operator feedback", "/feedback/rate"),
    ]
    for x, (t, sub) in zip(out_xs, out_data):
        add_card(ax, x, layer5_cy, out_w, out_h, t, subtitle=sub,
                 accent=CYAN, title_fs=9, sub_fs=7.5)

    # ============================================================
    # SAFETY OVERLAY band — LLM output passes THROUGH clamp_actions
    # before reaching the OUTPUTS row. (Semantically correct: bounded agency
    # filter intercepts unsafe LLM-suggested actions.)
    # ============================================================
    safety_cy = (LS_TOP + LS_BOT) / 2
    sbox_w, sbox_h = 88, 4.0
    sshadow = FancyBboxPatch(
        (50 - sbox_w / 2 + 0.3, safety_cy - sbox_h / 2 - 0.3),
        sbox_w, sbox_h,
        boxstyle="round,pad=0.02,rounding_size=0.3",
        linewidth=0, facecolor=SHADOW, alpha=0.10, zorder=2,
    )
    ax.add_patch(sshadow)
    sbox = FancyBboxPatch(
        (50 - sbox_w / 2, safety_cy - sbox_h / 2),
        sbox_w, sbox_h,
        boxstyle="round,pad=0.02,rounding_size=0.3",
        facecolor=CARD_BG, edgecolor=RED, linewidth=1.5,
        linestyle=(0, (4, 2)), zorder=3,
    )
    ax.add_patch(sbox)
    ax.text(50, safety_cy + 0.6, "SAFETY OVERLAY  ·  bounded agency",
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            color=RED, zorder=4)
    ax.text(50, safety_cy - 0.9,
            "clamp_actions strips unsafe systemctl / kubectl / ssh actions "
            "when actionable AND no named cause",
            ha="center", va="center", fontsize=6.6, color=TEXT, zorder=4)

    # LS layer side label (red, on left margin like other layer labels)
    spaced = " ".join("SAFETY")
    ax.text(1.4, safety_cy, spaced, ha="center", va="center",
            fontsize=8.0, fontweight="bold", color=RED,
            rotation=90, zorder=1, alpha=0.95)

    # Arrows: LLM → safety band → outputs (two short hops keeps flow visible)
    llm_bottom_y = layer4_cy - llm_h / 2
    out_top_y = layer5_cy + out_h / 2
    # Single arrow from LLM down to safety
    add_arrow(ax, 50, llm_bottom_y, 50, safety_cy + sbox_h / 2,
              color=PURPLE, lw=2.0, mut=18)
    # Branching arrows from safety down to each output
    for x in out_xs:
        add_arrow(ax, 50, safety_cy - sbox_h / 2, x, out_top_y,
                  color=RED, lw=1.3, alpha=0.7)

    # (Safety overlay rendered separately — see bottom of main())

    # ---------- Footer (small legend) ----------
    legend_y = 2.0
    chips = [
        (BLUE, "triggers"),
        (ORANGE, "pipeline"),
        (RED, "mcp / firewall"),
        (PURPLE, "llm"),
        (CYAN, "outputs"),
    ]
    chip_x = 6
    for color, lbl in chips:
        ax.add_patch(Rectangle((chip_x, legend_y - 0.4), 1.6, 0.9,
                               facecolor=color, edgecolor="none", zorder=4))
        ax.text(chip_x + 2.2, legend_y, lbl, fontsize=7,
                color=MUTED, va="center", ha="left", zorder=4)
        chip_x += 14

    fig.savefig(
        "/root/monitoring-docs/architecture-phase2-ai-triage-v2.png",
        dpi=300, bbox_inches="tight", pad_inches=0.3, facecolor=BG,
    )
    print("wrote /root/monitoring-docs/architecture-phase2-ai-triage-v2.png")


if __name__ == "__main__":
    main()
