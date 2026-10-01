"""Figures for the manuscript. Numbers come from the built graph (see the article, Section 5)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

INK, MUTED, LINE, FILL, ACCENT = "#1f2a30", "#55646c", "#9aa7ae", "#eef2f4", "#2a6f7f"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.edgecolor": LINE})

# ---- Figure 2: coverage of relationship types (share of 20,545 manuscripts) ----
rows = [("Repository (HELD_AT)", 20423), ("Support material (MADE_OF)", 18598), ("Date (DATED_TO)", 12280),
        ("Contents (CONTAINS_TEXT)", 5996), ("Origin place (PRODUCED_AT)", 1246), ("Named scribe (COPIED_BY)", 784),
        ("Named patron (COMMISSIONED_BY)", 86)]
total = 20545
fig, ax = plt.subplots(figsize=(6.6, 3.1), dpi=300)
labels = [r[0] for r in rows][::-1]
share = [100 * r[1] / total for r in rows][::-1]
bars = ax.barh(labels, share, color=ACCENT, height=0.62)
for bar, (name, n) in zip(bars, rows[::-1]):
    pct = 100 * n / total
    ax.text(bar.get_width() + 1.2, bar.get_y() + bar.get_height() / 2, f"{pct:.1f}%  ({n:,})", va="center", fontsize=8.5, color=INK)
ax.set_xlim(0, 128)
ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0", "25", "50", "75", "100%"], color=MUTED)
ax.tick_params(axis="y", length=0, labelsize=8.5); ax.tick_params(axis="x", colors=MUTED, length=3)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.xaxis.grid(True, color="#dfe5e8", linewidth=0.6); ax.set_axisbelow(True)
ax.set_xlabel("Share of the 20,545 manuscripts that have at least one such relationship", color=MUTED, fontsize=8.5)
fig.tight_layout(); fig.savefig("figures/fig2_coverage.png"); plt.close(fig)

# ---- Figure 1: pipeline ----
fig, ax = plt.subplots(figsize=(6.6, 3.9), dpi=300)
ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")
def box(x, y, w, h, title, sub="", strong=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2", fc=("#dcebef" if strong else FILL), ec=(ACCENT if strong else LINE), lw=1.1))
    ax.text(x + w / 2, y + h - 1.8, title, ha="center", va="top", fontsize=8.3, fontweight="bold")
    if sub: ax.text(x + w / 2, y + h - 5.4, sub, ha="center", va="top", fontsize=7.1, color=MUTED, linespacing=1.25)
def arrow(a, b):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=9, lw=1.0, color=INK))
def line(xs, ys):
    ax.plot(xs, ys, color=INK, lw=1.0, solid_capstyle="butt")
ax.text(0.5, 59, "BUILD", fontsize=7.5, color=MUTED, fontweight="bold", va="top")
ax.text(0.5, 24.5, "QUERY", fontsize=7.5, color=MUTED, fontweight="bold", va="top")
box(1, 40, 21, 16, "TEI repositories", "Manuscripts (20,545)\nInstitutions, Persons,\nWorks (names)")
box(27, 40, 21, 16, "Adapters", "Explicit TEI mapping;\nunmapped items are\ncounted, not guessed")
box(53, 40, 21, 16, "Name loader", "Latin title = label;\nGeez and variants\n= aliases")
box(78, 40, 21, 16, "Property graph", "30,823 nodes\n84,800 relationships\nsource + access level", strong=True)
for x0, x1 in ((22.5, 26.5), (48.5, 52.5), (74.5, 77.5)): arrow((x0, 48), (x1, 48))
box(1, 4, 21, 16, "Plan", "Model proposes search\nterms and domains")
box(27, 4, 21, 16, "Retrieve", "Name / alias search, both\ndirections; cap of 25\nper match")
box(53, 4, 21, 16, "Coverage check", "Names the domains\nwith no evidence")
box(78, 4, 21, 16, "Answer", "From retrieved facts\nonly, each with its\nsource file")
for x0, x1 in ((22.5, 26.5), (48.5, 52.5), (74.5, 77.5)): arrow((x0, 12), (x1, 12))
# graph -> retrieve (elbow): the graph is read, with the caller's access level applied in the query
line([88.5, 88.5], [39.6, 30]); line([88.5, 37.5], [30, 30]); arrow((37.5, 30), (37.5, 20.6))
ax.text(63, 31.2, "read with the caller's access level, applied in the query", fontsize=7, color=MUTED, ha="center", va="bottom")
fig.tight_layout(); fig.savefig("figures/fig1_pipeline.png"); plt.close(fig)
print("ok")
