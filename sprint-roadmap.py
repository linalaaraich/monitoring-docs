#!/usr/bin/env python3
"""
CIRES Observability Platform — Sprint roadmap (Sprints 1->6).

Renders a horizontal swim-lane / Gantt-style timeline with a "today" marker
and milestone diamonds above the bars. Output: sprint-roadmap.png at 300 DPI.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from datetime import datetime

# --- Palette (hybrid style) ---
BG = "#ffffff"
TEXT = "#0f1117"
MUTED = "#8890a0"
BLUE = "#4ea8de"     # past sprints (done)
GREEN = "#6bcf7f"    # current sprint
ORANGE = "#f0a050"   # planned next
PURPLE = "#b07ee8"   # research / forward-looking
CYAN = "#40d0d0"     # milestones
GRAY = "#c8ccd4"

plt.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]
plt.rcParams["axes.edgecolor"] = MUTED
plt.rcParams["axes.labelcolor"] = TEXT
plt.rcParams["xtick.color"] = TEXT
plt.rcParams["ytick.color"] = TEXT

# --- Sprint data ---
# (sprint_no, label, start, end, color, status)
SPRINTS = [
    (1, "Foundations — k3s + Prometheus + Loki + Grafana stack",
     "2026-03-12", "2026-03-26", BLUE, "done"),
    (2, "UEBA pillar + chaos test bed",
     "2026-03-26", "2026-04-09", BLUE, "done"),
    (3, "RAG + feedback US-5.3 + initial RCA pipeline",
     "2026-04-23", "2026-05-07", BLUE, "done"),
    (4, "Dedup hardening + dashboard v2 + email overhaul",
     "2026-05-20", "2026-06-03", GREEN, "current"),
    (5, "Microservice test bed + incident entity + operator config + 3-tier drain3",
     "2026-06-06", "2026-06-17", ORANGE, "planned"),
    (6, "RAG retrieval depth + agentic iterative gather + corpus reclass.",
     "2026-06-20", "2026-07-03", PURPLE, "research"),
]

MILESTONES = [
    # (date, label, color, vertical-guide?, label_y_offset, label_dx_days)
    # Labels are staggered both vertically (y_offset) and horizontally
    # (dx_days, applied to the label only; leader line connects marker→label).
    ("2026-05-23", "Supervisor v2 approval",    CYAN, False, 1.30, -8),
    ("2026-05-25", "DA-5/DA-4 shipped",         CYAN, False, 0.75,  0),
    ("2026-06-03", "Sprint 4 close",            CYAN, False, 1.30,  8),
    ("2026-06-26", "FYP defense window (est.)", CYAN, True,  0.75,  0),
]

TODAY = datetime.strptime("2026-05-25", "%Y-%m-%d")


def to_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def main() -> None:
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
    ax.set_facecolor(BG)

    # Layout constants
    bar_h = 0.55
    y_positions = list(range(len(SPRINTS), 0, -1))  # Sprint 1 at top

    # Plot sprint bars
    for (n, label, start, end, color, status), y in zip(SPRINTS, y_positions):
        s, e = to_date(start), to_date(end)
        width = (e - s).days
        # Soft fill via FancyBboxPatch for rounded corners
        bar = FancyBboxPatch(
            (mdates.date2num(s), y - bar_h / 2),
            width,
            bar_h,
            boxstyle="round,pad=0.02,rounding_size=1.5",
            linewidth=1.2,
            edgecolor=color,
            facecolor=color,
            alpha=0.85,
            zorder=2,
        )
        ax.add_patch(bar)

        # Sprint number (left, bold) + theme (right)
        mid = s + (e - s) / 2
        ax.text(
            mdates.date2num(s) + 0.5,
            y,
            f"S{n}",
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color="#ffffff",
            zorder=3,
        )
        # Theme label below the bar
        ax.text(
            mdates.date2num(mid),
            y - bar_h / 2 - 0.18,
            label,
            va="top",
            ha="center",
            fontsize=7.5,
            color=TEXT,
            zorder=3,
        )
        # Status pill on right end
        ax.text(
            mdates.date2num(e) + 1.5,
            y,
            status,
            va="center",
            ha="left",
            fontsize=7.5,
            color=MUTED,
            style="italic",
            zorder=3,
        )

    # Today line
    ax.axvline(
        TODAY,
        color="#606878",
        linestyle="--",
        linewidth=1.0,
        alpha=0.7,
        zorder=1,
    )

    # Milestone row above bars
    from datetime import timedelta
    milestone_y = len(SPRINTS) + 0.45
    for date_str, label, color, dashed, label_dy, label_dx_days in MILESTONES:
        d = to_date(date_str)
        ax.scatter(
            d,
            milestone_y,
            marker="D",
            s=55,
            color=color,
            edgecolors=TEXT,
            linewidths=0.6,
            zorder=4,
        )
        if dashed:
            ax.axvline(
                d, color=color, linestyle=":", linewidth=0.8, alpha=0.6, zorder=1
            )
        # Leader line from marker up & sideways to the staggered label
        label_y = milestone_y + label_dy
        label_x = d + timedelta(days=label_dx_days)
        ax.plot(
            [mdates.date2num(d), mdates.date2num(label_x)],
            [milestone_y + 0.10, label_y - 0.05],
            color=MUTED, linewidth=0.5, alpha=0.55, zorder=3,
        )
        ax.text(
            label_x,
            label_y,
            label,
            ha="center",
            va="bottom",
            fontsize=6.8,
            color=TEXT,
        )

    # "today" label positioned below the bars to avoid milestone collisions
    ax.text(
        TODAY,
        0.15,
        "today 2026-05-25",
        ha="center",
        va="bottom",
        fontsize=7,
        color=MUTED,
        style="italic",
    )

    # Axis configuration
    ax.set_ylim(-0.1, len(SPRINTS) + 2.4)
    ax.set_xlim(to_date("2026-03-05"), to_date("2026-07-10"))
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)

    # Month ticks
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator())
    ax.tick_params(axis="x", labelsize=8, colors=TEXT)

    # Title
    ax.set_title(
        "CIRES Observability Platform — Sprint roadmap",
        fontsize=13,
        color=TEXT,
        pad=18,
        loc="left",
        fontweight="bold",
    )

    # Legend (color key)
    legend_items = [
        (BLUE, "done"),
        (GREEN, "current"),
        (ORANGE, "planned"),
        (PURPLE, "research / forward-looking"),
        (CYAN, "milestone"),
    ]
    for i, (color, lbl) in enumerate(legend_items):
        x0 = 0.01 + i * 0.135
        fig.patches.append(
            plt.Rectangle(
                (x0, 0.01), 0.012, 0.018, transform=fig.transFigure,
                facecolor=color, edgecolor="none", zorder=10,
            )
        )
        fig.text(x0 + 0.016, 0.018, lbl, fontsize=7, color=MUTED, va="center")

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = "/root/monitoring-docs/sprint-roadmap.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=BG)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
