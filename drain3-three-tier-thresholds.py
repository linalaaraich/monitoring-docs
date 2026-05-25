#!/usr/bin/env python3
"""
Hierarchical drain3 anomaly thresholds (Sprint 5 design).

Three-tier pyramid:
  - Tier 1: per (app, component) — many small boxes
  - Tier 2: per-app aggregate — 3 medium boxes
  - Tier 3: system-wide backstop — single box
Plus a struck-out "Intersection tier — REJECTED" annotation.

Output: drain3-three-tier-thresholds.png at 300 DPI.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

# --- Palette (hybrid style) ---
BG = "#ffffff"
TEXT = "#0f1117"
MUTED = "#8890a0"
GREEN = "#6bcf7f"
ORANGE = "#f0a050"
PURPLE = "#b07ee8"
RED = "#e06070"
ARROW_GRAY = "#a0a8b8"

plt.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]


def add_box(ax, x, y, w, h, label, color, fontsize=8, fontweight="normal",
            text_color="#0f1117", alpha=0.9):
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.0, edgecolor=color, facecolor=color, alpha=alpha,
        zorder=3,
    )
    ax.add_patch(box)
    ax.text(
        x, y, label,
        ha="center", va="center",
        fontsize=fontsize, fontweight=fontweight, color=text_color, zorder=4,
    )
    return box


def add_arrow(ax, x1, y1, x2, y2, color=ARROW_GRAY, lw=0.9, alpha=0.65):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=8,
        color=color, linewidth=lw, alpha=alpha, zorder=2,
    )
    ax.add_patch(arr)


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 6.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-1.2, 10.2)
    ax.set_ylim(-0.2, 10)
    ax.axis("off")

    # ----- Tier 3 (top, single box, purple) -----
    t3_y = 8.6
    # Content centerline (between the leftmost tier-1 box and the rejected box on
    # the right) — use this for all centered elements.
    CX = 4.7
    t3 = add_box(ax, CX, t3_y, 3.6, 0.8,
                 "System-wide threshold",
                 PURPLE, fontsize=10, fontweight="bold", text_color="#ffffff")
    ax.text(CX, t3_y - 0.6,
            "Tier 3 — system-wide backstop. Fires on 'everything's weird at\n"
            "once' outages no individual app would surface.",
            ha="center", va="top", fontsize=7.5, color=MUTED, style="italic")

    # ----- Tier 2 (middle, 3 boxes, green) -----
    t2_y = 6.0
    t2_xs = [CX - 2.4, CX, CX + 2.4]
    t2_labels = ["App A aggregate", "App B aggregate", "App C aggregate"]
    for x, lbl in zip(t2_xs, t2_labels):
        add_box(ax, x, t2_y, 2.0, 0.7, lbl, GREEN,
                fontsize=8.5, fontweight="bold", text_color="#0f1117")

    ax.text(CX, t2_y - 0.55,
            "Tier 2 — per-app aggregate. Fires when several Tier-1 components\n"
            "show subthreshold anomalies in concert.",
            ha="center", va="top", fontsize=7.5, color=MUTED, style="italic")

    # Arrows Tier-2 -> Tier-3
    for x in t2_xs:
        add_arrow(ax, x, t2_y + 0.35, CX, t3_y - 0.4)

    # ----- Tier 1 (bottom, 8 small boxes, orange) -----
    t1_y = 3.4
    t1_components = [
        ("app-a / backend", 0),
        ("app-a / frontend", 0),
        ("app-a / captor", 0),
        ("app-b / api", 1),
        ("app-b / db", 1),
        ("app-b / queue", 1),
        ("app-c / scraper", 2),
        ("app-c / parser", 2),
    ]
    # 8 boxes spread across the content area, leaving room for the side label
    # at the left and a small right margin.
    t1_x_start = 0.4
    t1_x_end = 9.0
    t1_x_step = (t1_x_end - t1_x_start) / 7
    t1_positions = []
    for i, (label, parent_idx) in enumerate(t1_components):
        x = t1_x_start + i * t1_x_step
        add_box(ax, x, t1_y, 1.05, 0.55, label, ORANGE,
                fontsize=6.8, fontweight="normal", text_color="#0f1117")
        t1_positions.append((x, parent_idx))

    ax.text(CX, t1_y - 0.55,
            "Tier 1 — narrowest scope: per (app, component). "
            "Threshold tuned per workload.",
            ha="center", va="top", fontsize=7.5, color=MUTED, style="italic")

    # Arrows Tier-1 -> Tier-2 (to respective parent)
    for x, parent_idx in t1_positions:
        target_x = t2_xs[parent_idx]
        add_arrow(ax, x, t1_y + 0.3, target_x, t2_y - 0.35)

    # ----- Rejected intersection tier (side annotation, lower-center) -----
    # Sits below the Tier-1 caption, centered. Dashed red border + light fill;
    # the label text gets a "strikethrough" effect via a thin line drawn
    # immediately above its baseline (so it crosses through letters cleanly).
    rej_w, rej_h = 3.0, 0.55
    rej_x, rej_y = CX, 1.6
    rej_box = FancyBboxPatch(
        (rej_x - rej_w / 2, rej_y - rej_h / 2), rej_w, rej_h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.2, edgecolor=RED, facecolor=RED, alpha=0.12,
        linestyle="--", zorder=3,
    )
    ax.add_patch(rej_box)
    ax.text(
        rej_x, rej_y,
        "Intersection tier — REJECTED",
        ha="center", va="center",
        fontsize=8.5, fontweight="bold", color=RED, zorder=5,
    )
    # Strikethrough across the label only (not the whole box)
    ax.plot(
        [rej_x - 1.1, rej_x + 1.1],
        [rej_y, rej_y],
        color=RED, linewidth=1.0, alpha=0.85, zorder=6,
    )
    ax.text(
        rej_x, rej_y - rej_h / 2 - 0.15,
        "Apps-sharing-infra grouping rejected: shared db / namespace /\n"
        "host overlap messily; operator config blows up.",
        ha="center", va="top", fontsize=6.8, color=MUTED, style="italic",
    )

    # ----- Title + subtitle -----
    fig.suptitle(
        "Hierarchical drain3 anomaly thresholds (Sprint 5 design)",
        fontsize=12.5, color=TEXT, fontweight="bold", y=0.97,
    )
    ax.text(
        CX, 9.7,
        "Three scopes; intersection tier rejected after design review 2026-05-25.",
        ha="center", va="top", fontsize=8.5, color=MUTED, style="italic",
    )

    # Tier-scope side labels (left margin, clear of the boxes)
    ax.text(-0.9, t3_y, "Tier 3",
            ha="left", va="center", fontsize=8.5, color=PURPLE, fontweight="bold")
    ax.text(-0.9, t2_y, "Tier 2",
            ha="left", va="center", fontsize=8.5, color=GREEN, fontweight="bold")
    ax.text(-0.9, t1_y, "Tier 1",
            ha="left", va="center", fontsize=8.5, color=ORANGE, fontweight="bold")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = "/root/monitoring-docs/drain3-three-tier-thresholds.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=BG)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
