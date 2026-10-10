"""Demo with synthetic numbers: coefficient plot and China map.

    python examples/demo.py          # writes examples/output/{*.png, hires/, pdf/, svg/}
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import china_map as cm  # noqa: E402
import econ_style as st  # noqa: E402

st.setup(HERE / "output")


def coefficient_plot():
    rows = [dict(header="Panel A: Baseline"),
            dict(label="(1) Industry and year FE", b=-0.079, se=0.039, stars="**"),
            dict(label="(2) + Controls", b=-0.122, se=0.065, stars="*"),
            dict(label="(3) + Province FE", b=-0.127, se=0.068, stars="*"),
            dict(header="Panel B: Robustness"),
            dict(label="Alternative outcome", b=-0.153, se=0.072, stars="**"),
            dict(label="Excluding 2022", b=-0.123, se=0.063, stars="**"),
            dict(label="Two-way clustering", b=-0.133, se=0.070, stars="*")]
    fig = plt.figure(figsize=(st.TEXT_WIDTH, 2.9))
    ax = fig.add_axes([0.30, 0.22, 0.53, 0.72])
    st.coefplot(fig, ax, rows, xlim=(-0.35, 0.10), xticks=[-0.3, -0.2, -0.1, 0.0, 0.1],
                xlabel="Coefficient on the treatment variable", est_x=0.955,
                header_y=[(0.975, "Estimate")])
    st.ci_legend(fig, ax)
    st.save(fig, "demo_coefplot")


def china():
    prov, dash = cm.load()
    values = {code: (code // 10000) % 6 + 0.5 for code in cm.NAMES if code < 700000}
    fig = plt.figure(figsize=(st.TEXT_WIDTH / 2, 3.2))
    ax = fig.add_axes([0, 0.17, 1, 0.77])
    cm.choropleth(ax, prov, dash, values, edges=[0, 1, 2, 3, 5, 99],
                  labels=["< 1", "1 to 2", "2 to 3", "3 to 5", "≥ 5"], colors=cm.BLUES,
                  title="Synthetic index")
    st.save(fig, "demo_china_map")


if __name__ == "__main__":
    coefficient_plot()
    china()
