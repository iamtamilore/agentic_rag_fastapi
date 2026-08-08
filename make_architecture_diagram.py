from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parent

SVC = "#cdd8e6"     # docker service
DATA = "#dce8d8"    # storage
SEC = "#f5c86a"     # security control
EXT = "#e6bfbf"     # user facing
INK = "#2f2f2f"


def box(ax, x, y, w, h, text, colour, fs=7.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.010,rounding_size=0.03",
                                facecolor=colour, edgecolor=INK, linewidth=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, linespacing=1.45, color=INK)


def arrow(ax, x1, y1, x2, y2, label=None):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=9, linewidth=0.95, color=INK))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, label, fontsize=6.6,
                ha="center", color=INK)


fig, ax = plt.subplots(figsize=(7.4, 5.4))
ax.set_xlim(0, 12); ax.set_ylim(0, 9.2); ax.axis("off")

ax.text(0.25, 8.75, "Smart Medical Records Engine", fontsize=11.5, weight="bold", color=INK)
ax.text(0.25, 8.35, "Self-hosted clinical RAG. Four Docker Compose services, one private network.",
        fontsize=8, color=INK)

# ---- boundary: everything inside stays on the hospital network -------------
ax.add_patch(FancyBboxPatch((0.25, 0.45), 11.5, 7.35,
                            boxstyle="round,pad=0.02,rounding_size=0.05",
                            facecolor="none", edgecolor="#8a8a8a",
                            linewidth=1.3, linestyle=(0, (6, 4))))
ax.text(0.45, 7.5, "hospital network boundary: no patient data leaves",
        fontsize=7.4, style="italic", color="#5a5a5a")

# ---- clinician ------------------------------------------------------------
box(ax, 0.6, 5.7, 1.9, 0.95, "clinician\nplain-English\nquestion", EXT)

# ---- web service ----------------------------------------------------------
box(ax, 3.1, 5.7, 2.3, 0.95, "web  (FastAPI)\nquery endpoint", SVC)
arrow(ax, 2.5, 6.17, 3.1, 6.17)

# ---- security gate --------------------------------------------------------
box(ax, 3.1, 4.05, 2.3, 1.25,
    "security layer\nJWT physician auth\nPII redaction\naudit log per access", SEC, 7.2)
arrow(ax, 4.25, 5.7, 4.25, 5.30)

# ---- retrieval ------------------------------------------------------------
box(ax, 6.1, 4.05, 2.5, 1.25,
    "retrieval\nscoped by patient_id\nso only this patient's\nnotes can surface", SEC, 7.2)
arrow(ax, 5.40, 4.67, 6.10, 4.67)

# ---- db -------------------------------------------------------------------
box(ax, 6.1, 2.15, 2.5, 1.15,
    "db\npgvector/pgvector:pg15\nvector(768) index", DATA, 7.4)
arrow(ax, 7.35, 4.05, 7.35, 3.30)
arrow(ax, 7.75, 3.30, 7.75, 4.05)

# ---- ollama ---------------------------------------------------------------
box(ax, 9.2, 4.05, 2.3, 1.25,
    "ollama\nnomic-embed-text\n(embeddings)\nllama3.1 (answers)", SVC, 7.2)
arrow(ax, 8.60, 4.67, 9.20, 4.67)

# ---- ingestion ------------------------------------------------------------
box(ax, 1.0, 2.15, 2.5, 1.15,
    "ingestion (one-shot)\nchunks records,\nembeds, loads", SVC, 7.4)
arrow(ax, 3.50, 2.72, 6.10, 2.72)
box(ax, 1.0, 0.75, 2.5, 0.85, "patient records\n(CSV / notes)", DATA, 7.4)
arrow(ax, 2.25, 1.60, 2.25, 2.15)

# ---- answer path back -----------------------------------------------------
ax.add_line(Line2D([10.35, 10.35], [5.30, 6.95], color=INK, lw=0.95))
ax.add_line(Line2D([1.55, 10.35], [6.95, 6.95], color=INK, lw=0.95))
arrow(ax, 1.55, 6.95, 1.55, 6.65)
ax.text(6.0, 7.08, "grounded answer, citing only this patient's own records",
        fontsize=6.9, ha="center", color=INK)

# ---- legend ---------------------------------------------------------------
legend = [(SVC, "Docker Compose service"),
          (SEC, "security / scoping control"),
          (DATA, "storage"),
          (EXT, "user")]
for i, (colour, label) in enumerate(legend):
    y = 1.75 - i * 0.36
    ax.add_patch(FancyBboxPatch((4.35, y), 0.26, 0.20,
                                boxstyle="round,pad=0.008",
                                facecolor=colour, edgecolor=INK, linewidth=0.8))
    ax.text(4.74, y + 0.10, label, fontsize=7.0, va="center", color=INK)

fig.tight_layout()
out = ROOT / "architecture.png"
fig.savefig(out, dpi=200, bbox_inches="tight")
print(f"[architecture] saved -> {out}")
