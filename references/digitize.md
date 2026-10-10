# Redrawing a figure when only the old image exists

Use when the user says "just redraw it" and the numbers are not in any table or the data
do not reproduce the paper. Recover values from the original image, never invent them.

## 1. Get the original image
A `.docx` is a zip: `unzip -o paper.docx -d x/` → images are `x/word/media/imageN.png`.
Map image → caption by walking `word/document.xml` paragraphs: the drawing's `r:embed`
id → `word/_rels/document.xml.rels` target; the caption is the next paragraph.
Check `a:srcRect` on the old drawing: a crop hides part of the image (and will crop the
new image too if left in place).

## 2. Calibrate axes from tick marks (not from labels)
- Find the spine (longest dark run of pixels), then tick marks (short dark runs just
  outside the spine). Read the tick labels visually.
- Fit `value = a + b * pixel` on ≥ 3 ticks; report residuals (should be < 0.2 px).

## 3. Measure with two independent methods, then reconcile
- Bars: colour mask, bar bottom edge with sub-pixel interpolation of the colour transition;
  method B: column intensity profile through each bar centre.
- Points: colour mask + connected components; split overlapping blobs by
  area / single-marker area with `scipy.cluster.vq.kmeans2`; method B: template matching
  (`scipy.signal.fftconvolve` with a synthetic disc) + non-maximum suppression. Overlapping
  clusters: inspect upscaled crops (PIL `NEAREST` ×4) and use known counts (e.g. "20 bins").
- Lines: fit the line pixels by least squares over the full drawn span; report slope,
  intercept and drawn x-range.
- Box plots: box edges, whisker caps; a median line drawn in white on a box edge means
  median = that edge.
- Agreement target: ≤ 0.001 in data units. Where methods disagree, re-measure on crops.

## 4. Cross-check against the paper
- Values that also appear in tables must match them (e.g. scatter y = table means).
- Recompute fits from the recovered points and compare with the drawn line to identify the
  method (e.g. unweighted vs weighted OLS; t vs normal CI; marker area ∝ firms, not firm-years).
- Report anything that cannot be matched instead of smoothing it over.

## 5. Recovering a missing standard error from a drawn CI
If a table omits an SE but the old figure draws its CI: calibrate px → value using rows
whose CIs are known (`b ± 1.96·se`), measure the unknown row's cap positions,
`se = (hi − lo) / 3.92`, and check that the CI midpoint equals the reported estimate.
State in the script comments that the SE was recovered from the figure.

## Tools that work offline on macOS
numpy, scipy, PIL (no OpenCV needed). Keep scripts and downloaded data in separate folders.
