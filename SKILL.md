---
name: econ-academic-figures
description: Draw or redraw publication-quality economics/management paper figures in academic style (Times New Roman, no in-figure titles, grayscale-safe), and put them into the Word manuscript as crisp vector images. Use for coefficient/event-study plots, moderation figures, China province maps (with South China Sea inset), binned scatters, bar/box plots, and for redrawing figures from an old manuscript image. Triggers - 论文图表, 学术风, 新罗马字体, 重绘/重新绘制图片, 经济学绘图, 系数图, 中国地图, 把图放进Word, journal figure, AER/QJE style.
---

# Academic figures for economics papers

Scripts (import with `sys.path.insert(0, "<this skill>/scripts")`):
- `econ_style.py` – rcParams, palette, `save()` (300/600 dpi PNG + PDF + SVG), `coefplot()`, `ci_legend()`, `num()` (typographic minus), `panel_label()`.
- `china_map.py` – province choropleth: DataV GeoJSON with ten-dash line (downloaded to `data/` on first use), Albers, South China Sea inset, classed legend.
- `docx_embed.py` – replace/insert figures in an existing .docx (SVG + 600 dpi PNG fallback, text-width sizing, crop removal, no-compression setting, A4).
- `render_docx.sh` + `pdf2png.swift` – page images of a .docx on macOS without LibreOffice.
- `references/digitize.md` – recovering values from an old figure image.

Needs Python with matplotlib, numpy, pandas, statsmodels; maps also geopandas, shapely, pyproj; Word step lxml.
Find an existing env before installing (`find ~ -path "*site-packages/geopandas" -maxdepth 6`); in mainland China
PyPI can be very slow – use `uv pip install --index-url https://mirrors.aliyun.com/pypi/simple/` in a throwaway venv.

## Workflow
1. **Inventory.** List every figure: caption, where its numbers come from (paper table, data file, or only the
   old image). Read the paper's tables and the hypotheses before drawing anything.
2. **Numbers come from the paper.** Copy coefficients, SEs, stars and Ns from the tables (cite table/column in a
   comment). If a figure needs data the folder does not reproduce, or exists only as an image, digitise the old
   image (`references/digitize.md`) – never recompute from a different sample without telling the user.
3. **Draw** with `econ_style` at `TEXT_WIDTH` (6.27 in), one script per figure group, data in `data/*.json`.
4. **Look at every PNG** (Read tool) for overlaps, clipping, legend collisions, missing glyphs; fix and re-render.
5. **Word**: `docx_embed.py` into a NEW file (`*_revised.docx`), validate with the docx skill's `validate.py`,
   render with `render_docx.sh` and look at the pages. Never overwrite the user's original.

## Style rules (what users of this skill asked for)
- Times New Roman everywhere (text, ticks, legends, mathtext). Body 8.5–9.5 pt at final size.
- **No figure titles inside images.** Multi-panel figures get only "(a)", "(b)"; descriptions go in the Word
  caption. Explanatory notes ("dashed line: median", "grey band: 95% CI") become legend entries or caption notes.
- Palette: navy `#1F3A5F` main, dark red `#9E2A2B` contrast, greys; hatching for a second bar series so it
  survives grayscale. **Circles only** for point estimates (users found mixed squares odd); distinguish groups by colour.
- Spines: left/bottom only; zero line thin grey; no gridlines.
- Typographic minus (`num()`), en dash in ranges (5–95) and two-name eponyms (Kleibergen–Paap).
- Unicode glyphs missing from Times New Roman (e.g. ∝, ↓) render as boxes – write words instead.
- Outputs: 300 dpi PNG for the user's folder (they asked for 300 DPI), plus `hires/` 600 dpi PNG, `pdf/` and
  `svg/` for Word and journal upload.

## Figure recipes
**Coefficient plots** (baseline specs, robustness, heterogeneity, moderation margins, all-coefficient summary):
`st.coefplot(fig, ax, rows, ...)` with 90 % (thick) + 95 % (thin) CIs; stars exactly as in the tables (the
90 % bar explains why a `*` estimate's 95 % CI crosses zero); estimate column right-aligned with stars left-aligned;
optional Obs. column; group headers ("Panel A: …") bold; alternating `BAND` shading for many groups.
If the text says "95 per cent confidence interval", update it to mention both intervals.

**Moderation**: marginal effect at moderator = 0 / 1; put the interaction coefficient in the group header
(e.g. "Moderator Z (X × Z = 0.170***)"). Missing SE at moderator = 1 → lincom output, or
recover from the old figure's CI (digitize.md §5).

**China map**: `china_map.choropleth()`; 5 classes with interpretable breaks; darker = stronger; legend below
the map; inset in open sea east of Taiwan; geopandas axis labels removed; `make_valid()` before `unary_union`.

**Bar + scatter + box (cross-sectional patterns)**: bars sorted, median line in legend; scatter with OLS line and
95 % band over the data range only, bubble area stated in the legend ("marker size: number of firms" – check which variable the original used), labels at
fixed hand-placed positions with thin grey leader lines in dense clusters (greedy auto-placement fails there);
box plot with explicit `bxp` stats when only summary numbers are known.

**Binned scatter (first stage)**: bin means as navy circles, red fit line through the origin for residualised
variables, annotation text kept verbatim from the paper.

## Putting figures into Word (`docx_embed.py`)
```
python docx_embed.py Manuscript.docx Manuscript_revised.docx --figs output \
  --replace Fig2_map Fig3_patterns Fig4_baseline ... \
  --insert-after <paraId of the sentence citing the new figure> Fig1_new "Figure 1. Title" --a4
```
Why each step matters (all were real bugs): plain 300 dpi PNG looked blurry in Word → SVG + 600 dpi fallback and
`doNotAutoCompressPictures`; an old `a:srcRect` crop cut 10 % off a new figure; old extents were wider than A4 text
width; image paragraphs were justified, not centred; alt text carried old figure numbers;
`doNotAutoCompressPictures` must follow `m:mathPr` in settings.xml (schema order) or validation fails.
Then renumber captions and in-text "Figure N" references (duplicates are common after insertion), cite every
figure in the text before it appears, and make figure-text descriptions match the redrawn content.

## Checking the manuscript after insertion (only fix what the user approves)
Common problems found in pandoc/WPS-produced manuscripts: font family "Times New Roman Regular/Bold" (not a real
family on Windows) → "Times New Roman"; no `w:pgSz` (A4/Letter undefined); headings typed as body text; yellow
highlights left over; inline equations whose eqArr ends in "#(n)" print "#(1)" literally (make them display
equations or use tab-based numbering); significance-star legends eaten by Markdown ("`, and denote`"); duplicate
table rows; inconsistent caption punctuation; undefined abbreviations (FE, IV, CI, SD, CEO, ESG, ST) and duplicate
definitions. Separate **mechanical** fixes from **content** issues (wrong numbers, mislabeled columns, sample
inconsistencies) and list content issues for the authors instead of changing them.
