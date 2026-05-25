#!/usr/bin/env python3
"""
Operator decision matrix — what reaches the operator's inbox.

Two visual zones (stacked vertically):
  Zone 1 (top third)    — Pre-LLM lane: 4 paths that bypass the LLM entirely.
  Zone 2 (bottom 2/3rds) — 3x3 matrix of (LLM verdict) x (RCA quality)
                           mapped to final action_taken, plus annotation panel
                           explaining the "shelved-in-disguise" downgrade gate.

Output: operator-decision-matrix.png at 300 DPI (11in x 8.5in landscape).
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

# --- Palette (hybrid style — matches Lina's existing FYP diagrams) ---
BG = "#ffffff"
TEXT = "#0f1117"
MUTED = "#8890a0"
RED = "#e06070"      # escalation (operator paged)
ORANGE = "#f0a050"   # shelved (LLM said escalate but signals said no)
CYAN = "#40d0d0"     # suppressed (no operator-visible email)
BLUE = "#4ea8de"     # suppressed_duplicate (linked to prior RCA)
PURPLE = "#b07ee8"   # emailed_raw (timeout fallback)
GREEN = "#6bcf7f"    # note/legend accents
GRID_GRAY = "#d8dce4"

plt.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def add_filled_box(
    ax, x, y, w, h, *, face_color, edge_color=None, alpha=0.15,
    linewidth=1.4, zorder=2, rounding=0.04,
):
    """Rounded rectangle with low-alpha fill + crisp border."""
    if edge_color is None:
        edge_color = face_color
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.0,rounding_size={rounding}",
        linewidth=linewidth, edgecolor=edge_color,
        facecolor=face_color, alpha=alpha, zorder=zorder,
    )
    ax.add_patch(box)
    # Re-draw the border crisp (the alpha bleed dulls it)
    border = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.0,rounding_size={rounding}",
        linewidth=linewidth, edgecolor=edge_color,
        facecolor="none", alpha=1.0, zorder=zorder + 1,
    )
    ax.add_patch(border)
    return box


# -----------------------------------------------------------------------------
# Zone 1 — pre-LLM lane (top strip)
# -----------------------------------------------------------------------------
PRELLM_BOXES = [
    {
        "title": "Suppressed duplicate",
        "action": "see_previous_rca:<id>",
        "caption": (
            "DA-5 family / DA-4 content-hash\n"
            "dedup matched. Links prior RCA."
        ),
        "color": BLUE,
    },
    {
        "title": "Triage suppressed",
        "action": "suppressed",
        "caption": (
            "Layer 2 pre-LLM suppression:\n"
            "recent dismissed history matches."
        ),
        "color": CYAN,
    },
    {
        "title": "Recurrence gated",
        "action": "suppressed",
        "caption": (
            "US-5.8 recurrence gate:\n"
            "N fires within window."
        ),
        "color": CYAN,
    },
    {
        "title": "Timeout passthrough",
        "action": "emailed_raw",
        "caption": (
            "Pipeline exceeded 180s budget.\n"
            "Raw alert forwarded unchanged."
        ),
        "color": PURPLE,
    },
]


def draw_prellm_lane(ax, x0, y0, width, height):
    """Draw the 4 pre-LLM boxes side-by-side within (x0, y0, width, height)."""
    # Header
    header_h = 0.30
    ax.text(
        x0 + width / 2, y0 + height - 0.02,
        "Pre-LLM lane — these never reach the LLM (no LLM cost incurred)",
        ha="center", va="top",
        fontsize=11, fontweight="bold", color=TEXT,
    )

    # Boxes
    n = len(PRELLM_BOXES)
    gap = 0.20
    box_w = (width - (n - 1) * gap) / n
    box_h = height - header_h
    box_y = y0

    for i, spec in enumerate(PRELLM_BOXES):
        bx = x0 + i * (box_w + gap)
        add_filled_box(
            ax, bx, box_y, box_w, box_h,
            face_color=spec["color"], alpha=0.20,
            linewidth=1.6, rounding=0.06,
        )
        cx_box = bx + box_w / 2
        # Title (bold)
        ax.text(
            cx_box, box_y + box_h - 0.13,
            spec["title"],
            ha="center", va="top",
            fontsize=10, fontweight="bold", color=TEXT,
        )
        # Action label (muted) on its own line, then the value on a 2nd line —
        # keeps each line short enough to fit narrow boxes.
        ax.text(
            cx_box, box_y + box_h - 0.40,
            "action_taken:",
            ha="center", va="top",
            fontsize=7.3, color=MUTED,
        )
        ax.text(
            cx_box, box_y + box_h - 0.57,
            spec["action"],
            ha="center", va="top",
            fontsize=8.5, color=spec["color"], fontweight="bold",
            family=["DejaVu Sans Mono", "monospace"],
        )
        # Caption
        ax.text(
            cx_box, box_y + 0.10,
            spec["caption"],
            ha="center", va="bottom",
            fontsize=7.4, color=MUTED, style="italic",
        )


# -----------------------------------------------------------------------------
# Zone 2 — the 3x3 matrix
# -----------------------------------------------------------------------------
VERDICTS = ["ESCALATE", "DISMISS", "INCONCLUSIVE"]
QUALITIES = [
    # (canonical_name, short_label, brief_gloss_for_column_header)
    ("actionable",   "fits",   "RCA + suggested_action"),
    ("data_starved", "thin",   "RCA hedged / no evidence"),
    ("needs_review", "review", "conf < 0.30 or flagged"),
]

# Per-cell action mapping (mirrors pipeline._is_shelved_in_disguise +
# _investigate_and_act, verified from the prompt's ground truth).
CELLS = {
    # row -> col -> (action, color, caption)
    "ESCALATE": {
        "actionable":   ("emailed",   RED,    "operator paged"),
        "data_starved": ("shelved",   ORANGE, "shelved-in-disguise gate"),
        "needs_review": ("shelved",   ORANGE, "shelved-in-disguise gate"),
    },
    "DISMISS": {
        "actionable":   ("suppressed", CYAN, "no email"),
        "data_starved": ("suppressed", CYAN, "no email"),
        "needs_review": ("suppressed", CYAN, "no email"),
    },
    "INCONCLUSIVE": {
        "actionable":   ("suppressed", CYAN, "no email"),
        "data_starved": ("suppressed", CYAN, "no email"),
        "needs_review": ("suppressed", CYAN, "no email"),
    },
}


def draw_matrix(ax, x0, y0, width, height):
    """Draw the 3x3 verdict x quality matrix within (x0, y0, width, height)."""
    # Reserve space for row/col labels.
    # Top band: axis title + q_name (bold) + ("short") + gloss = 4 lines.
    # Left band: needs to fit "INCONCLUSIVE" + "(PENDING on UI)" below.
    label_left_w = 1.50
    label_top_h = 1.10
    grid_x = x0 + label_left_w
    grid_y = y0
    grid_w = width - label_left_w
    grid_h = height - label_top_h

    n_rows = len(VERDICTS)
    n_cols = len(QUALITIES)
    cell_gap = 0.12

    cell_w = (grid_w - (n_cols - 1) * cell_gap) / n_cols
    cell_h = (grid_h - (n_rows - 1) * cell_gap) / n_rows

    # ----- Axis label "RCA quality" (top of column-label band) -----
    ax.text(
        grid_x + grid_w / 2, grid_y + grid_h + label_top_h - 0.06,
        "RCA quality  (app/rca_store.py:_classify_rca_quality)",
        ha="center", va="top",
        fontsize=9, color=TEXT, fontweight="bold",
    )

    # ----- Column headers (RCA quality) -----
    # Stacked: q_name (bold mono) on its own line, "short" + gloss on the next.
    for j, (q_name, q_short, q_desc) in enumerate(QUALITIES):
        cx = grid_x + j * (cell_w + cell_gap) + cell_w / 2
        # q_name (bold mono)
        ax.text(
            cx, grid_y + grid_h + 0.46,
            q_name,
            ha="center", va="bottom",
            fontsize=10.5, fontweight="bold", color=TEXT,
            family=["DejaVu Sans Mono", "monospace"],
        )
        # short label
        ax.text(
            cx, grid_y + grid_h + 0.26,
            f'("{q_short}")',
            ha="center", va="bottom",
            fontsize=8.5, color=MUTED, fontweight="bold",
        )
        # gloss line below
        ax.text(
            cx, grid_y + grid_h + 0.08,
            q_desc,
            ha="center", va="bottom",
            fontsize=7.3, color=MUTED, style="italic",
        )

    # ----- Axis label "LLM verdict" rotated left of row labels -----
    ax.text(
        x0 + 0.10, grid_y + grid_h / 2,
        "LLM verdict  (app/models.py Decision)",
        ha="center", va="center", rotation=90,
        fontsize=9, color=TEXT, fontweight="bold",
    )

    # ----- Row labels (LLM verdict) -----
    for i, v in enumerate(VERDICTS):
        rx = x0 + label_left_w - 0.10  # right-aligned, just left of the cell
        ry = grid_y + (n_rows - 1 - i) * (cell_h + cell_gap) + cell_h / 2
        # Verdict name centered on the row
        ax.text(
            rx, ry + (0.10 if v == "INCONCLUSIVE" else 0.0),
            v,
            ha="right", va="center",
            fontsize=10.5, fontweight="bold", color=TEXT,
            family=["DejaVu Sans Mono", "monospace"],
        )
        # PENDING note for INCONCLUSIVE — just below the verdict text,
        # still within the row-label gutter (above the bottom of the cell).
        if v == "INCONCLUSIVE":
            ax.text(
                rx, ry - 0.14,
                "(PENDING on UI)",
                ha="right", va="center",
                fontsize=6.8, color=MUTED, style="italic",
            )

    # ----- Cells -----
    for i, v in enumerate(VERDICTS):
        for j, (q_name, _q_short, _q_desc) in enumerate(QUALITIES):
            cx = grid_x + j * (cell_w + cell_gap)
            cy = grid_y + (n_rows - 1 - i) * (cell_h + cell_gap)
            action, color, caption = CELLS[v][q_name]
            add_filled_box(
                ax, cx, cy, cell_w, cell_h,
                face_color=color, alpha=0.20,
                linewidth=1.5, rounding=0.05,
            )
            # Action label (bold, centered, slightly above cell midline)
            ax.text(
                cx + cell_w / 2, cy + cell_h / 2 + 0.18,
                action,
                ha="center", va="center",
                fontsize=15, fontweight="bold", color=TEXT,
                family=["DejaVu Sans Mono", "monospace"],
            )
            # Caption underneath
            ax.text(
                cx + cell_w / 2, cy + cell_h / 2 - 0.22,
                caption,
                ha="center", va="center",
                fontsize=8, color=MUTED, style="italic",
            )


# -----------------------------------------------------------------------------
# Annotation panel — shelved-in-disguise gate explanation
# -----------------------------------------------------------------------------
def draw_annotation_panel(ax, x0, y0, width, height):
    """Boxed text describing the shelved-in-disguise downgrade gate."""
    add_filled_box(
        ax, x0, y0, width, height,
        face_color=ORANGE, alpha=0.10,
        edge_color=ORANGE, linewidth=1.4, rounding=0.04,
    )
    # Header
    ax.text(
        x0 + 0.15, y0 + height - 0.15,
        "Shelved-in-disguise gate",
        ha="left", va="top",
        fontsize=10.5, fontweight="bold", color=ORANGE,
    )
    ax.text(
        x0 + 0.15, y0 + height - 0.40,
        "pipeline._is_shelved_in_disguise",
        ha="left", va="top",
        fontsize=7.8, color=MUTED, style="italic",
        family=["DejaVu Sans Mono", "monospace"],
    )
    # Body intro (wrapped on 2 lines so it fits the panel width)
    body_y = y0 + height - 0.70
    ax.text(
        x0 + 0.15, body_y,
        "An ESCALATE verdict downgrades to\nshelved if any of:",
        ha="left", va="top",
        fontsize=8.5, color=TEXT,
    )
    bullets = [
        "confidence < 0.40",
        "quality in {needs_review, data_starved}",
        "all suggested_actions = \"shelved\"",
    ]
    for k, b in enumerate(bullets):
        ax.text(
            x0 + 0.30, body_y - 0.46 - k * 0.22,
            "• " + b,
            ha="left", va="top",
            fontsize=7.8, color=TEXT,
            family=["DejaVu Sans Mono", "monospace"],
        )

    # Footer note
    ax.text(
        x0 + 0.15, y0 + 0.12,
        "Outcome: operator paged only when LLM is\n"
        "confident AND the RCA is grounded.",
        ha="left", va="bottom",
        fontsize=7.8, color=MUTED, style="italic",
    )


# -----------------------------------------------------------------------------
# Legend
# -----------------------------------------------------------------------------
def draw_legend(ax, x0, y0, width, height):
    """Inline color legend for the matrix outcomes."""
    add_filled_box(
        ax, x0, y0, width, height,
        face_color=GREEN, alpha=0.06,
        edge_color=GREEN, linewidth=1.2, rounding=0.04,
    )
    ax.text(
        x0 + 0.15, y0 + height - 0.12,
        "Color legend",
        ha="left", va="top",
        fontsize=10.5, fontweight="bold", color=GREEN,
    )
    items = [
        (RED,    "emailed",              "operator paged"),
        (ORANGE, "shelved",              "escalated but downgraded"),
        (CYAN,   "suppressed",           "no operator email"),
        (BLUE,   "suppressed_duplicate", "linked to prior RCA"),
        (PURPLE, "emailed_raw",          "timeout fallback"),
    ]
    # Single-line entry per item: [swatch] name — desc
    # Layout (in inches inside a ~3.40in-wide panel):
    #   swatch:  x0+0.20 .. x0+0.38  (0.18in)
    #   name  :  x0+0.50 .. x0+1.55  (mono, ~1.05in -> "suppressed_duplicate")
    #   gloss :  x0+1.60 .. x0+3.30  (italic, ~1.70in)
    sw_w, sw_h = 0.18, 0.18
    sw_x = x0 + 0.20
    name_x = sw_x + sw_w + 0.14
    gloss_x = x0 + 1.65
    row_y = y0 + height - 0.55
    for color, name, desc in items:
        # swatch
        ax.add_patch(Rectangle(
            (sw_x, row_y - sw_h / 2), sw_w, sw_h,
            facecolor=color, edgecolor=color, alpha=0.65, linewidth=1.0,
        ))
        # name (mono, bold)
        ax.text(
            name_x, row_y + 0.02,
            name,
            ha="left", va="center",
            fontsize=8.3, fontweight="bold", color=TEXT,
            family=["DejaVu Sans Mono", "monospace"],
        )
        # gloss column
        ax.text(
            gloss_x, row_y + 0.02,
            "— " + desc,
            ha="left", va="center",
            fontsize=7.6, color=MUTED, style="italic",
        )
        row_y -= 0.38


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    # Letter landscape — 11in x 8.5in
    fig, ax = plt.subplots(figsize=(11, 8.5), facecolor=BG)
    ax.set_facecolor(BG)

    # Use a 0..11 x 0..8.5 coordinate system that maps 1:1 to inches; makes
    # layout math trivially predictable.
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    # --- Title + subtitle (top) ---
    fig.text(
        0.5, 0.965,
        "Operator decision matrix — what reaches the operator's inbox",
        ha="center", va="top",
        fontsize=15, fontweight="bold", color=TEXT,
    )
    fig.text(
        0.5, 0.935,
        "LLM verdict  ×  RCA quality  →  final action_taken. "
        "Pre-LLM lane (top) intercepts before any LLM cost.",
        ha="center", va="top",
        fontsize=10, color=MUTED, style="italic",
    )

    # --- Zone 1: pre-LLM lane (top strip) ---
    # Occupy x: 0.3 .. 10.7 ; y: 6.40 .. 7.85
    draw_prellm_lane(ax, x0=0.30, y0=6.40, width=10.40, height=1.45)

    # Divider line between zones
    ax.plot(
        [0.5, 10.5], [6.20, 6.20],
        color=GRID_GRAY, linewidth=1.0, linestyle=":", zorder=1,
    )
    ax.text(
        5.5, 6.17,
        "↓  remainder enters the LLM pipeline  ↓",
        ha="center", va="top",
        fontsize=8.5, color=MUTED, style="italic",
    )

    # --- Zone 2: matrix (left, ~7in wide) + annotation/legend (right ~3.3in) ---
    # Matrix area: x 0.35 .. 7.05 (w=6.70), y 0.45 .. 5.65 (h=5.20)
    draw_matrix(ax, x0=0.35, y0=0.45, width=6.70, height=5.20)

    # Annotation panel: x 7.25 .. 10.65 (w=3.40), y 3.20 .. 5.55 (h=2.35)
    # Top edge is below the matrix's column-header band (which ends ~5.65)
    draw_annotation_panel(
        ax, x0=7.25, y0=3.20, width=3.40, height=2.35,
    )

    # Legend: x 7.25 .. 10.65 (w=3.40), y 0.45 .. 3.00 (h=2.55)
    draw_legend(
        ax, x0=7.25, y0=0.45, width=3.40, height=2.55,
    )

    # Tight layout via figure-level adjustment (we managed coords manually)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)

    out = "/root/monitoring-docs/operator-decision-matrix.png"
    fig.savefig(out, dpi=300, facecolor=BG)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
