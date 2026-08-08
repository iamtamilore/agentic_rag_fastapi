from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parent

HDR = "#2E2C6E"
BODY = "#eef0f6"
KEY = "#f5c86a"
AUD = "#dce8d8"
INK = "#2f2f2f"


def table(ax, x, y, w, name, rows, header=HDR):
    rh = 0.42
    h = rh * (len(rows) + 1)
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.01,rounding_size=0.04",
                                facecolor="white", edgecolor=INK, linewidth=1.1))
    ax.add_patch(FancyBboxPatch((x, y - rh), w, rh, boxstyle="square,pad=0",
                                facecolor=header, edgecolor="none"))
    ax.text(x + w / 2, y - rh / 2, name, ha="center", va="center",
            fontsize=8.6, weight="bold", color="white")
    for i, (col, kind) in enumerate(rows):
        yy = y - rh * (i + 1) - rh / 2
        if kind:
            ax.add_patch(FancyBboxPatch((x + 0.04, yy - rh / 2 + 0.05), w - 0.08, rh - 0.1,
                                        boxstyle="square,pad=0",
                                        facecolor=KEY if kind == "key" else AUD, edgecolor="none"))
        ax.text(x + 0.16, yy, col, ha="left", va="center", fontsize=7.4, color=INK)
    return h


fig, ax = plt.subplots(figsize=(8.4, 5.0))
ax.set_xlim(0, 14); ax.set_ylim(0, 9.4); ax.axis("off")

ax.text(0.3, 9.0, "Data model", fontsize=12.5, weight="bold", color=HDR)
ax.text(0.3, 8.6, "Per-patient scoping is enforced in the schema, not only in application code.",
        fontsize=8.2, color="#555555")

h1 = table(ax, 0.3, 7.9, 3.5, "patients", [
    ("id  PK", "key"), ("first_name, last_name", None), ("date_of_birth", None),
    ("gender, phone, address", None), ("emergency contact", None),
    ("medical_plan, plan_id", None),
    ("UNIQUE(name, dob)", "key")])

h2 = table(ax, 5.0, 7.9, 4.3, "medical_events", [
    ("id  PK", "key"),
    ("patient_id  FK -> patients", "key"),
    ("attending_physician", None),
    ("subjective   (SOAP)", None),
    ("objective    (SOAP)", None),
    ("assessment   (SOAP)", None),
    ("plan         (SOAP)", None),
    ("content", None),
    ("embedding  vector(768)", "key"),
    ("UNIQUE(patient_id, date, content)", "key")])

h3 = table(ax, 10.4, 7.9, 3.3, "doctors", [
    ("id  PK", "key"), ("username  UNIQUE", "key"),
    ("hashed_password", None), ("full_name", None)])

h4 = table(ax, 10.4, 4.9, 3.3, "audit_log", [
    ("id  PK", "key"), ("doctor_id  FK -> doctors", "key"),
    ("action", None), ("patient_id", None), ("timestamp", None)], header="#4a7a4a")

h5 = table(ax, 5.0, 2.8, 4.3, "query_logs", [
    ("id  PK", "key"), ("user_question", None), ("retrieved_context", None),
    ("llm_answer", None), ("timestamp", None)], header="#4a7a4a")

# relationships
ax.add_patch(FancyArrowPatch((3.8, 6.6), (5.0, 6.6), arrowstyle="-|>",
                             mutation_scale=10, lw=1.1, color=INK))
ax.text(4.4, 6.78, "1 : many", fontsize=7, ha="center", color=INK)

ax.add_patch(FancyArrowPatch((12.05, 6.1), (12.05, 4.9), arrowstyle="-|>",
                             mutation_scale=10, lw=1.1, color=INK))
ax.text(12.25, 5.5, "logs", fontsize=7, ha="left", color=INK)

# the point of the diagram
ax.add_patch(FancyBboxPatch((0.3, 2.0), 4.2, 2.4, boxstyle="round,pad=0.02,rounding_size=0.05",
                            facecolor="#fdf6e6", edgecolor="#d9a441", linewidth=1.1))
ax.text(0.55, 4.05, "Why this matters", fontsize=8.6, weight="bold", color="#8a6416")
ax.text(0.55, 3.62,
        "Every vector lives on a row that carries\n"
        "its own patient_id, so retrieval filters by\n"
        "patient before it ever ranks by similarity.\n\n"
        "Another patient's note cannot surface,\n"
        "even if it is the closer semantic match.",
        fontsize=7.6, va="top", color=INK, linespacing=1.5)

# legend
for i, (c, lab) in enumerate([(KEY, "key / constraint enforcing scoping"),
                              (AUD, "accountability field")]):
    y = 1.75 - i * 0.42
    ax.add_patch(FancyBboxPatch((10.4, y), 0.28, 0.22, boxstyle="round,pad=0.008",
                                facecolor=c, edgecolor=INK, linewidth=0.7))
    ax.text(10.82, y + 0.11, lab, fontsize=7.2, va="center", color=INK)

fig.tight_layout()
out = ROOT / "data_model.png"
fig.savefig(out, dpi=200, bbox_inches="tight")
print(f"saved -> {out}")
