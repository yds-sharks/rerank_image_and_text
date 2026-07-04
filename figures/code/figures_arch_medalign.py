#!/usr/bin/env python3
"""MedAlign-RAG system architecture (AAAI Figure 2, cross-column figure*).

Agentic closed-loop data flow (left->right, with a return loop):
  Query -> Dual-Path Retrieval -> pool C -> Qwen Reranker
        -> Cross-Modal Evidence Agent  --accept-->  VLM Generation -> Answer
                                       --rewrite-->  (loop back to Retrieval)
Density-Aware Modality Routing is a control module on top of retrieval: reads
the query, emits budget (N_t/N_i) and fusion weight (w); re-run every round.
Training only: an answer-utility reward (lift in P(correct answer)) flows back
from Answer to the Agent (dashed).

Robustness: every title/label goes through fit_text(), which measures the
rendered text width and shrinks the font until it fits inside its box -- this
eliminates the text-overflow problem. Badges sit inside the top-left corner as
left-aligned section headers rather than straddling borders.
"""
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Polygon
from matplotlib.lines import Line2D

t0 = time.time()

C = {
    "query_f": "#DCE9F5", "query_e": "#2C5F8A",
    "retr_f":  "#D6E6F6", "retr_e":  "#2C5F8A",
    "route_f": "#FBE8C8", "route_e": "#B5771F",
    "rer_f":   "#EAE3F2", "rer_e":   "#6B4E9B",
    "ag_f":    "#E4F2E7", "ag_e":    "#3D7A4A", "ag_hd": "#D2E9D8",
    "gen_f":   "#F6DECB", "gen_e":   "#C4703A",
    "ans_f":   "#EDEDED", "ans_e":   "#555555",
    "chip_f":  "#FFFFFF", "grp_e":   "#9AA0A6",
    "txt":     "#1A1A1A", "arrow":   "#3A3A3A",
    "sha":     "#CBCFD4",
    "img_f":   "#DCEBE6", "img_e":   "#4E8C7C",
    "line":    "#8A94A0",
    "rew":     "#B5771F", "loop":    "#3D7A4A",
    "keep":    "#2E7D32", "drop":    "#B0453A",
}

fig_w, fig_h = 7.16, 3.75
fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.set_xlim(0, 100)
ax.set_ylim(0, 66)
ax.axis("off")

UX, UY = fig_w / 100.0, fig_h / 66.0
ASP = UY / UX
_renderer = None


def _rend():
    global _renderer
    if _renderer is None:
        fig.canvas.draw()
        _renderer = fig.canvas.get_renderer()
    return _renderer


def shadow(x, y, w, h, r, off=0.55):
    ax.add_patch(FancyBboxPatch((x + off, y - off), w, h,
                 boxstyle=f"round,pad=0,rounding_size={r*min(w,h)}",
                 linewidth=0, facecolor=C["sha"], zorder=1.4, alpha=0.85))


def box(x, y, w, h, fc, ec, r=0.06, lw=1.2, ls="-", z=2, sh=False):
    if sh:
        shadow(x, y, w, h, r)
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle=f"round,pad=0,rounding_size={r*min(w,h)}",
                 linewidth=lw, edgecolor=ec, facecolor=fc, linestyle=ls, zorder=z))


def _tw(t):
    bb = t.get_window_extent(renderer=_rend())
    inv = ax.transData.inverted()
    (x0, _), (x1, _) = inv.transform([[bb.x0, 0], [bb.x1, 0]])
    return abs(x1 - x0)


def fit_text(cx, cy, s, maxw, size=8, weight="normal", color=C["txt"],
             style="normal", ha="center", z=6, minsize=3.6):
    """Place text and shrink font until it fits within maxw (data units)."""
    t = ax.text(cx, cy, s, fontsize=size, fontweight=weight, color=color,
                style=style, ha=ha, va="center", zorder=z)
    for _ in range(14):
        if _tw(t) <= maxw or size <= minsize:
            break
        size *= 0.93
        t.set_fontsize(size)
    return t


def text(x, y, s, size=8, weight="normal", color=C["txt"], style="normal",
         ha="center", va="center", z=6):
    ax.text(x, y, s, fontsize=size, fontweight=weight, color=color,
            style=style, ha=ha, va=va, zorder=z)


def arrow(x1, y1, x2, y2, color=C["arrow"], lw=1.7, ls="-", z=4, mut=12,
          rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=mut, linewidth=lw, color=color, linestyle=ls,
                 connectionstyle=f"arc3,rad={rad}", zorder=z))


def badge(cx, cy, n, color, ry=1.55):
    ax.add_patch(Ellipse((cx, cy), 2 * ASP * ry, 2 * ry, facecolor=color,
                 edgecolor="white", linewidth=1.1, zorder=8))
    text(cx, cy - 0.12, str(n), size=6.8, weight="bold", color="white", z=9)


def section_header(gx, gy_top, gw, n, title, color, size=7.4):
    """Numbered badge in top-left corner + left-aligned title beside it."""
    by = gy_top - 2.4
    bx = gx + 2.2
    badge(bx, by, n, color)
    tx = bx + 1.9 * ASP + 0.6
    fit_text(tx, by, title, gx + gw - tx - 1.2, size=size, weight="bold",
             color=color, ha="left")


def text_tile(cx, cy, w=2.6, h=3.0, ec=C["retr_e"], z=5, alpha=1.0):
    box(cx - w / 2, cy - h / 2, w, h, "#FFFFFF", ec, r=0.14, lw=0.9, z=z)
    for fy in (0.66, 0.5, 0.34):
        yy = cy - h / 2 + h * fy
        ax.add_line(Line2D([cx - w * 0.28, cx + w * 0.28], [yy, yy],
                    color=C["line"], linewidth=0.7, zorder=z + 1, alpha=alpha))


def img_tile(cx, cy, w=2.6, h=3.0, ec=C["img_e"], z=5):
    box(cx - w / 2, cy - h / 2, w, h, C["img_f"], ec, r=0.14, lw=0.9, z=z)
    ax.add_patch(Polygon([[cx - w * 0.30, cy - h * 0.26],
                          [cx - w * 0.02, cy + h * 0.14],
                          [cx + w * 0.30, cy - h * 0.26]],
                 closed=True, facecolor=C["img_e"], edgecolor="none",
                 zorder=z + 1))


def mark_keep(cx, cy, s=1.0):
    xs = [cx - 0.7 * s * ASP, cx - 0.15 * s * ASP, cx + 0.85 * s * ASP]
    ys = [cy - 0.05 * s, cy - 0.6 * s, cy + 0.7 * s]
    ax.add_line(Line2D(xs, ys, color=C["keep"], linewidth=1.7, zorder=9,
                solid_capstyle="round", solid_joinstyle="round"))


def mark_drop(cx, cy, s=0.85):
    for dx in (1, -1):
        ax.add_line(Line2D([cx - 0.7 * s * ASP * dx, cx + 0.7 * s * ASP * dx],
                    [cy - 0.7 * s, cy + 0.7 * s], color=C["drop"],
                    linewidth=1.7, zorder=9, solid_capstyle="round"))


MID = 30  # main-row centerline

# ---------------------------------------------------------- 0. Query
qx, qw, qh = 1.5, 10, 15
box(qx, MID - qh / 2, qw, qh, C["query_f"], C["query_e"], lw=1.4, sh=True)
fit_text(qx + qw / 2, MID + 4.2, "Query", qw - 1.5, size=9, weight="bold")
fit_text(qx + qw / 2, MID + 0.6, r"$q$: text + options", qw - 1.2, size=6.4)
fit_text(qx + qw / 2, MID - 2.6, r"image $I_q$", qw - 1.2, size=6.4)

# ---------------------------------------------------------- 1. Retrieval
rgx, rgw = 14, 18
rg_y, rg_h = MID - 17, 34
box(rgx, rg_y, rgw, rg_h, "none", C["grp_e"], r=0.03, lw=1.1,
    ls=(0, (4, 3)), z=1)
section_header(rgx, rg_y + rg_h, rgw, 1, "Dual-Path Retrieval", C["retr_e"])
box(rgx + 1.8, MID + 3.0, rgw - 3.6, 8.5, C["retr_f"], C["retr_e"], sh=True)
fit_text(rgx + rgw / 2, MID + 8.2, "Text Path", rgw - 5, size=7.2,
         weight="bold")
fit_text(rgx + rgw / 2, MID + 5.0, "BGE-M3  ·  top-20", rgw - 5, size=6.0,
         style="italic")
box(rgx + 1.8, MID - 12.5, rgw - 3.6, 8.5, C["retr_f"], C["retr_e"], sh=True)
fit_text(rgx + rgw / 2, MID - 7.3, "Image Path", rgw - 5, size=7.2,
         weight="bold")
fit_text(rgx + rgw / 2, MID - 10.5, "Qwen3-VL  ·  top-20", rgw - 5,
         size=6.0, style="italic")

# ---------------------------------------------------------- 2. Reranker
rer_x, rer_w = 34.5, 11
rer_y, rer_h = MID - 10, 20
box(rer_x, rer_y, rer_w, rer_h, C["rer_f"], C["rer_e"], lw=1.3, sh=True)
fit_text(rer_x + rer_w / 2, MID + 6.8, "Qwen Reranker", rer_w - 1.5, size=7.4,
         weight="bold", color=C["rer_e"])
text_tile(rer_x + rer_w / 2 - 2.2, MID - 0.3, w=2.5, h=2.9)
img_tile(rer_x + rer_w / 2 + 2.2, MID - 0.3, w=2.5, h=2.9)
fit_text(rer_x + rer_w / 2, MID - 4.6, r"pool $\mathcal{C}$: $N_t{+}N_i$ cand.",
         rer_w - 1.2, size=5.6, style="italic")
fit_text(rer_x + rer_w / 2, MID - 7.3, "(prior order)", rer_w - 1.2, size=5.2,
         style="italic", color=C["line"])

# ---------------------------------------------------------- 3. Agent (star)
agx, agw = 48, 23
ag_y, ag_h = MID - 14, 28
box(agx, ag_y, agw, ag_h, C["ag_f"], C["ag_e"], lw=1.7, sh=True)
# tinted header band
box(agx + 0.0, ag_y + ag_h - 5.0, agw, 5.0, C["ag_hd"], C["ag_e"], r=0.06,
    lw=0, z=2.2)
section_header(agx, ag_y + ag_h, agw, 2, "Cross-Modal Evidence Agent",
               C["ag_e"], size=7.2)
fit_text(agx + agw / 2, ag_y + ag_h - 6.8,
         r"vision-language policy $\pi_\theta$  ·  RL-trained",
         agw - 2.5, size=6.0, style="italic", color=C["txt"])
# candidate-judging strip: keep some, drop some (cross-modal)
fit_text(agx + agw / 2, MID + 2.0, "judge each candidate (image + text):",
         agw - 2.5, size=5.7, color=C["txt"])
strip_y = MID - 2.6
cs = [("t", True), ("i", True), ("t", False), ("i", True)]
n = len(cs)
gap = 5.0
x0 = agx + agw / 2 - (n - 1) * gap / 2
for k, (kind, keep) in enumerate(cs):
    cx = x0 + k * gap
    if kind == "t":
        text_tile(cx, strip_y, w=2.3, h=2.7,
                  ec=C["retr_e"] if keep else C["grp_e"])
    else:
        img_tile(cx, strip_y, w=2.3, h=2.7,
                 ec=C["img_e"] if keep else C["grp_e"])
    (mark_keep if keep else mark_drop)(cx, strip_y - 3.2)
fit_text(agx + agw / 2, MID - 8.0,
         r"keep $\rightarrow$ accept $E$   ·   none useful $\rightarrow$ rewrite $q'$",
         agw - 2.5, size=5.6, color=C["ag_e"])
fit_text(agx + agw / 2, MID - 10.8,
         r"reward $=P_G(a^\star|E)-P_G(a^\star|\varnothing)$", agw - 2.5,
         size=5.8, color=C["rew"])

# ---------------------------------------------------------- 4. Generation
ggx, ggw = 73.5, 12
gg_y, gg_h = MID - 9, 18
box(ggx, gg_y, ggw, gg_h, C["gen_f"], C["gen_e"], lw=1.4, sh=True)
section_header(ggx, gg_y + gg_h, ggw, 3, "VLM Generation", C["gen_e"],
               size=7.2)
img_tile(ggx + ggw / 2 - 2.1, MID - 0.5, w=2.4, h=2.8, ec=C["gen_e"])
text_tile(ggx + ggw / 2 + 2.1, MID - 0.5, w=2.4, h=2.8, ec=C["gen_e"])
fit_text(ggx + ggw / 2, MID - 4.8, "image + text fed unaltered", ggw - 1.5,
         size=5.6, style="italic")

# ---------------------------------------------------------- 5. Answer
anx, anw = 88, 10
an_y, an_h = MID - 7.5, 15
box(anx, an_y, anw, an_h, C["ans_f"], C["ans_e"], lw=1.3, sh=True)
fit_text(anx + anw / 2, MID + 4.4, "Answer", anw - 1.5, size=7.6, weight="bold")
opts = ["A", "B", "C", "D"]
correct = 1
ow, og = 1.75, 0.35
row_w = 4 * ow + 3 * og
sx = anx + anw / 2 - row_w / 2
for k, o in enumerate(opts):
    ox = sx + k * (ow + og)
    hit = (k == correct)
    box(ox, MID - 1.5, ow, 2.7, "#CDEBD6" if hit else "#FFFFFF",
        C["ag_e"] if hit else C["grp_e"], r=0.18,
        lw=1.4 if hit else 0.8, z=5)
    text(ox + ow / 2, MID - 0.15, o, size=5.6,
         weight="bold" if hit else "normal",
         color=C["ag_e"] if hit else C["txt"], z=6)
fit_text(anx + anw / 2, MID - 4.8, r"predicted $\hat{a}$", anw - 1.5, size=6.0,
         style="italic")

# ---------------------------------------------------------- Routing (top-left)
rx, ry, rw, rh = 14, 51, 31, 10
box(rx, ry, rw, rh, C["route_f"], C["route_e"], lw=1.4, sh=True)
fit_text(rx + rw / 2, ry + rh - 2.7, "Density-Aware Modality Routing", rw - 2.5,
         size=7.2, weight="bold", color=C["route_e"])
fit_text(rx + rw / 2, ry + 3.6,
         r"Mengzi-BERT: density $L_0{-}L_4$, image-dep. $R_1{-}R_3$", rw - 2.5,
         size=5.8)
fit_text(rx + rw / 2, ry + 1.1,
         r"$\rightarrow$ budget $N_t/N_i$, fusion $w$   (re-run each round)",
         rw - 2.5, size=5.8, color=C["route_e"])

# ---------------------------------------------------------- main-flow arrows
arrow(qx + qw, MID + 2.5, rgx + 1.6, MID + 6.5)   # query -> text path
arrow(qx + qw, MID - 2.5, rgx + 1.6, MID - 8.5)   # query -> image path
arrow(rgx + rgw, MID, rer_x - 0.2, MID)           # retrieval -> rerank
arrow(rer_x + rer_w, MID, agx - 0.2, MID)         # rerank -> agent
arrow(agx + agw, MID, ggx - 0.2, MID)             # agent -> generation
arrow(ggx + ggw, MID, anx - 0.2, MID)             # generation -> answer

# ---------------------------------------------------------- rewrite loop (bottom)
lc = C["loop"]
loop_y = rg_y - 5.5
lx_out = agx + agw / 2 - 4
lx_in = rgx + rgw / 2
arrow(lx_out, ag_y, lx_out, loop_y + 0.2, color=lc, lw=1.5)
ax.add_line(Line2D([lx_out, lx_in], [loop_y, loop_y], color=lc, linewidth=1.5,
            zorder=4))
arrow(lx_in, loop_y, lx_in, rg_y - 0.3, color=lc, lw=1.5)
fit_text((lx_out + lx_in) / 2, loop_y - 1.9,
         r"rewrite query $q'$  ·  re-retrieve", abs(lx_out - lx_in) + 6,
         size=5.9, style="italic", color=lc)

# ---------------------------------------------------------- reward loop (top)
rwc = C["rew"]
rew_y = ag_y + ag_h + 7
rx_out = anx + anw / 2
rx_in = agx + agw / 2 + 4
arrow(rx_out, an_y + an_h, rx_out, rew_y - 0.2, color=rwc, ls=(0, (3, 2)),
      lw=1.3)
ax.add_line(Line2D([rx_out, rx_in], [rew_y, rew_y], color=rwc, linewidth=1.3,
            linestyle=(0, (3, 2)), zorder=4))
arrow(rx_in, rew_y, rx_in, ag_y + ag_h + 0.3, color=rwc, ls=(0, (3, 2)),
      lw=1.3)
fit_text((rx_out + rx_in) / 2, rew_y + 1.8,
         "answer-utility reward  (training only)", abs(rx_out - rx_in) + 4,
         size=5.9, style="italic", color=rwc)

# ---------------------------------------------------------- routing control arrow
arrow(rx + 9, ry, rgx + rgw / 2, rg_y + rg_h + 0.3, color=C["route_e"],
      ls=(0, (3, 2)), lw=1.3)

out_pdf = "figures/data/tmp/figures_arch_medalign.pdf"
out_png = "figures/data/tmp/figures_arch_medalign.png"
fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.03)
fig.savefig(out_png, dpi=220, bbox_inches="tight", pad_inches=0.03)
print(f"saved: {out_pdf}\nsaved: {out_png}\nelapsed {time.time()-t0:.2f}s")
