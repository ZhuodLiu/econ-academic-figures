"""Academic (economics-journal) figure style for matplotlib.

Times New Roman throughout, no in-figure titles, grayscale-safe colours.
Every figure is saved as: 300 dpi PNG, 600 dpi PNG, vector PDF and SVG.

Usage:
    import sys; sys.path.insert(0, "<skill>/scripts")
    import econ_style as st
    st.setup(out_dir="output")          # call once
    fig = plt.figure(figsize=(st.TEXT_WIDTH, 2.8))
    ...
    st.save(fig, "Fig4_baseline")       # -> output/, output/hires/, output/pdf/, output/svg/
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory

# A4 with 1-inch margins (also fits Letter). Draw full-width figures at this width
# so that font sizes are true when the image is inserted at 100 %.
TEXT_WIDTH = 6.27

NAVY = "#1F3A5F"   # main series
RED = "#9E2A2B"    # contrast series (IV, moderator = 1, below median ...)
GREY = "#595959"
LIGHT = "#D9D9D9"  # CI bands
BAND = "#F2F2F2"   # alternating group shading
ZERO = "#7F7F7F"   # zero / reference lines

Z90, Z95 = 1.6449, 1.9600

OUT = Path("output")


def setup(out_dir="output"):
    global OUT
    OUT = Path(out_dir)
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman"],
        "mathtext.fontset": "custom",
        "mathtext.rm": "Times New Roman",
        "mathtext.it": "Times New Roman:italic",
        "mathtext.bf": "Times New Roman:bold",
        "font.size": 9,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "legend.frameon": False,
        "axes.linewidth": 0.6,
        "axes.edgecolor": "black",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "axes.unicode_minus": True,
        "lines.linewidth": 1.0,
        "hatch.linewidth": 0.5,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
        "pdf.fonttype": 42,   # embed TrueType: editable text in PDF
        "ps.fonttype": 42,
    })


def save(fig, name):
    """300 dpi PNG (deliverable), 600 dpi PNG (Word fallback), PDF and SVG (vector)."""
    dirs = {"png": OUT, "hires": OUT / "hires", "pdf": OUT / "pdf", "svg": OUT / "svg"}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    fig.savefig(dirs["png"] / f"{name}.png", dpi=300)
    fig.savefig(dirs["hires"] / f"{name}.png", dpi=600)
    fig.savefig(dirs["pdf"] / f"{name}.pdf")
    fig.savefig(dirs["svg"] / f"{name}.svg")
    plt.close(fig)
    print("saved", name)


def num(v, fmt="{:.4f}"):
    """Format a number with a typographic minus sign (U+2212)."""
    return fmt.format(v).replace("-", "−")


def panel_label(ax, letter, x=-0.02, y=1.02):
    """Panel letter only, e.g. '(a)'. Panel descriptions belong in the Word caption."""
    ax.text(x, y, f"({letter})", transform=ax.transAxes, ha="right", va="bottom", fontsize=10)


def coefplot(fig, ax, rows, xlim, xticks, xlabel, label_x=0.01, indent=0.018,
             est_x=None, extra_cols=None, header_y=None, bands=False, tickfmt="{:.1f}"):
    """Horizontal coefficient plot: 90 % CI thick, 95 % CI thin, point estimate.

    rows: list of dicts. {"header": "Panel A: ..."} is a bold group heading; other rows
    need label, b, se, stars (copied from the paper's tables) and may set color/marker.
    est_x: figure-x of an estimate column (number right-aligned, stars left-aligned,
    so decimals line up). extra_cols: [(fig_x, key, formatter)], e.g. observations.
    header_y: [(fig_x, "Estimate")] column headers above the plot.
    Leave ~0.3 of the figure width on the left for labels (fig.add_axes([0.30, ...])).
    """
    n = len(rows)
    ys = list(range(n, 0, -1))
    lab_tf = blended_transform_factory(fig.transFigure, ax.transData)
    has_headers = any("header" in r for r in rows)
    spans, cur = [], None
    for y, r in zip(ys, rows):
        if "header" in r:
            fig.text(label_x, y, r["header"], transform=lab_tf, ha="left", va="center",
                     fontsize=8.5, fontweight="bold")
            cur = [y, y]
            spans.append(cur)
            continue
        if cur is not None:
            cur[1] = y
        c = r.get("color", NAVY)
        b, se = r["b"], r["se"]
        ax.plot([b - Z95 * se, b + Z95 * se], [y, y], color=c, lw=0.9, solid_capstyle="butt", zorder=2)
        ax.plot([b - Z90 * se, b + Z90 * se], [y, y], color=c, lw=2.6, solid_capstyle="butt", zorder=3)
        ax.plot(b, y, marker=r.get("marker", "o"), ms=4.6, color=c, mec="white", mew=0.6, zorder=4)
        fig.text(label_x + (indent if has_headers else 0), y, r["label"], transform=lab_tf,
                 ha="left", va="center", fontsize=8.5)
        if est_x is not None:
            fig.text(est_x, y, num(b), transform=lab_tf, ha="right", va="center", fontsize=8.5)
            fig.text(est_x, y, r.get("stars", ""), transform=lab_tf, ha="left", va="center", fontsize=8.5)
        for cx, key, fmt in (extra_cols or []):
            fig.text(cx, y, fmt(r[key]), transform=lab_tf, ha="right", va="center", fontsize=8.5)
    if bands:
        for i, (top, bottom) in enumerate(spans):
            if i % 2 == 0:
                ax.axhspan(bottom - 0.5, top + 0.5, color=BAND, lw=0, zorder=0)
    ax.axvline(0, color=ZERO, lw=0.7, zorder=1)
    ax.set_xlim(*xlim)
    ax.set_xticks(xticks)
    ax.set_ylim(0.4, n + 0.6)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(xlabel)
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: num(v, tickfmt)))
    for cx, text in (header_y or []):
        fig.text(cx, n + 0.95, text, transform=lab_tf, ha="right", va="center",
                 fontsize=8.5, style="italic")
    return ys


def ci_legend(fig, ax, below_in=0.42, color=NAVY, ncol=3):
    """Legend (point / 90 % CI / 95 % CI) centred `below_in` inches under the axis."""
    ax_h = ax.get_position().height * fig.get_figheight()
    handles = [Line2D([], [], color=color, marker="o", ms=4.6, mec="white", mew=0.6, lw=0),
               Line2D([], [], color=color, lw=2.6, solid_capstyle="butt"),
               Line2D([], [], color=color, lw=0.9)]
    ax.legend(handles, ["Point estimate", "90% CI", "95% CI"], loc="upper center",
              bbox_to_anchor=(0.5, -below_in / ax_h), ncol=ncol, handlelength=1.8,
              columnspacing=1.6, borderaxespad=0)
