# econ-academic-figures

A [Claude Code](https://claude.com/claude-code) skill (also usable as a plain Python toolkit) for
**publication-quality figures in economics and management papers**: Times New Roman, no titles inside
images, grayscale-safe colours, and figures that go into the Word manuscript as crisp vector images.

一个 Claude Code 技能（也可以当普通 Python 工具包用），用来画**经济学 / 管理学论文的学术风图表**：
新罗马字体、图内不放标题、黑白打印可辨，并能把图以矢量形式插入 Word 稿件。

## What it covers / 功能

- **Style** (`scripts/econ_style.py`): rcParams, palette, typographic minus, panel letters; every figure saved as
  300 dpi PNG + 600 dpi PNG + PDF + SVG.
- **Coefficient plots**: 90 % (thick) and 95 % (thin) confidence intervals, stars copied from your tables,
  aligned estimate / Obs. columns, grouped panels — for baseline, robustness, heterogeneity and moderation results.
- **China province maps** (`scripts/china_map.py`): Albers projection, ten-dash line and South China Sea inset,
  classed legend below the map. Boundaries are downloaded from Alibaba DataV on first use (not redistributed here).
- **Word** (`scripts/docx_embed.py`): replace or insert figures in an existing `.docx` as SVG with a 600 dpi PNG
  fallback, sized to the text width, centred, old crops removed, image compression switched off.
- **Redrawing from an old image** (`references/digitize.md`): recover bar heights, points, fit lines and even
  missing standard errors from the original figure with two independent pixel methods.
- **Previewing a .docx on macOS** without LibreOffice (`scripts/render_docx.sh`).

## Install / 安装

As a Claude Code skill (personal):

```bash
git clone https://github.com/ZhuodLiu/econ-academic-figures ~/.claude/skills/econ-academic-figures
```

Then ask Claude Code e.g. "redraw the figures in my manuscript in academic style" / "把论文里的图重新画成学术风并放回 Word",
or type `/econ-academic-figures`.

As a Python toolkit:

```bash
pip install -r requirements.txt
python examples/demo.py      # writes examples/output/
```

```python
import sys; sys.path.insert(0, "econ-academic-figures/scripts")
import matplotlib.pyplot as plt
import econ_style as st

st.setup("output")
fig = plt.figure(figsize=(st.TEXT_WIDTH, 2.6))
ax = fig.add_axes([0.30, 0.22, 0.53, 0.72])
st.coefplot(fig, ax, [dict(label="(1) Baseline", b=-0.08, se=0.04, stars="**")],
            xlim=(-0.3, 0.1), xticks=[-0.3, -0.2, -0.1, 0, 0.1], xlabel="Coefficient", est_x=0.955)
st.ci_legend(fig, ax)
st.save(fig, "Fig4_baseline")
```

Put the figures into Word:

```bash
python scripts/docx_embed.py Manuscript.docx Manuscript_revised.docx --figs output \
    --replace Fig2_map Fig3_patterns Fig4_baseline \
    --insert-after <paraId> Fig1_new "Figure 1. Title" --a4
```

Requirements: Python ≥ 3.9 with matplotlib, numpy, pandas, statsmodels; maps also need geopandas, shapely, pyproj;
the Word step needs lxml. Times New Roman must be installed.

## Notes / 说明

- Numbers in figures should come from the paper's own tables; the skill's instructions tell Claude to separate
  formatting fixes from content issues and to leave the latter to the authors.
- Map data: Alibaba DataV.GeoAtlas. Maps of China published in China may need to follow the standard-map
  rules (审图号); check your journal's requirements. You are responsible for the boundaries you publish.

## License

MIT — see [LICENSE](LICENSE).
