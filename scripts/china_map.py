"""Province-level choropleth of China in the standard published form.

- Boundaries: Alibaba DataV GeoJSON, downloaded on first use to ../data/ (not shipped), which contains the
  ten-dash line (feature adcode '100000_JD'); refresh from
  https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json if needed.
- Albers equal-area conic projection; South China Sea islands in a lower-right inset placed in
  open sea east of Taiwan; Taiwan / Hong Kong / Macao drawn (grey "No data" if not in sample).
- Classed colours (5 classes) with a legend below the map, never on top of the land.

Usage:
    import econ_style as st, china_map as cm
    st.setup("output")
    prov, dash = cm.load()
    fig = plt.figure(figsize=(st.TEXT_WIDTH, 3.25))
    ax = fig.add_axes([0, 0.17, 0.495, 0.77])
    cm.choropleth(ax, prov, dash, values={110000: 7.2, ...},  # adcode -> value
                  edges=[0, 1.5, 2.5, 3.5, 5, 99], labels=[...], colors=cm.GREENS,
                  title="Patents per firm-year")
    ax.text(0, 1.02, "(a)", transform=ax.transAxes, fontsize=10)
    st.save(fig, "Fig2_map")
"""
import json
from pathlib import Path

import geopandas as gpd
from matplotlib.patches import Patch
from shapely.geometry import shape
from shapely.ops import unary_union

DATA = Path(__file__).resolve().parent.parent / "data" / "china_provinces_datav.json"
ALBERS = "+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +x_0=0 +y_0=0 +ellps=krass +units=m +no_defs"
NODATA = "#E3E3E3"
BLUES = ["#EFF3FF", "#BDD7E7", "#6BAED6", "#3182BD", "#08519C"]
GREENS = ["#EDF8E9", "#BAE4B3", "#74C476", "#31A354", "#006D2C"]
INSET_W, INSET_H = 0.19, 0.31

# adcode -> English name (31 mainland provinces + TW/HK/MO)
NAMES = {110000: "Beijing", 120000: "Tianjin", 130000: "Hebei", 140000: "Shanxi",
         150000: "Inner Mongolia", 210000: "Liaoning", 220000: "Jilin", 230000: "Heilongjiang",
         310000: "Shanghai", 320000: "Jiangsu", 330000: "Zhejiang", 340000: "Anhui",
         350000: "Fujian", 360000: "Jiangxi", 370000: "Shandong", 410000: "Henan",
         420000: "Hubei", 430000: "Hunan", 440000: "Guangdong", 450000: "Guangxi",
         460000: "Hainan", 500000: "Chongqing", 510000: "Sichuan", 520000: "Guizhou",
         530000: "Yunnan", 540000: "Tibet", 610000: "Shaanxi", 620000: "Gansu",
         630000: "Qinghai", 640000: "Ningxia", 650000: "Xinjiang", 710000: "Taiwan",
         810000: "Hong Kong", 820000: "Macao"}


DATAV_URL = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"


def fetch(path=DATA, url=DATAV_URL):
    """Download the province boundaries (Alibaba DataV.GeoAtlas) once; not redistributed here."""
    import urllib.request
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as r:
        path.write_bytes(r.read())
    print("downloaded", path)
    return path


def load(path=DATA):
    if not Path(path).exists():
        fetch(path)
    raw = json.loads(Path(path).read_text(encoding="utf8"))
    recs, dash = [], None
    for f in raw["features"]:
        code = str(f["properties"]["adcode"])
        geom = shape(f["geometry"])
        if code.endswith("_JD"):
            dash = geom
            continue
        recs.append(dict(adcode=int(code), geometry=geom))
    prov = gpd.GeoDataFrame(recs, crs="EPSG:4326")
    prov["geometry"] = prov.geometry.make_valid()  # some DataV rings self-intersect
    return prov.to_crs(ALBERS), gpd.GeoSeries([dash], crs="EPSG:4326").to_crs(ALBERS)


def extents(prov):
    """Main-map extent (mainland + Hainan, widened east so the inset clears Taiwan) and inset extent."""
    ll = prov.to_crs("EPSG:4326").explode(index_parts=False)
    keep = ll[ll.geometry.representative_point().y > 17.5].to_crs(ALBERS)
    x0, y0, x1, y1 = keep.total_bounds
    pad = 0.02 * (x1 - x0)
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    tw_x = prov.loc[prov["adcode"] == 710000].total_bounds[2]
    x1 = max(x1, (tw_x + 0.03 * (x1 - x0) - INSET_W * x0) / (1 - INSET_W))
    scs = gpd.GeoSeries.from_xy([105.5, 124.5], [2.5, 24.5], crs="EPSG:4326").to_crs(ALBERS)
    return (x0, y0, x1, y1), (scs.x.min(), scs.y.min(), scs.x.max(), scs.y.max())


def _draw(ax, prov, dash, colors, ext, lw=0.3, outline=None):
    prov.plot(ax=ax, color=colors, edgecolor="white", linewidth=lw, zorder=1)
    if outline is not None:
        gpd.GeoSeries([outline], crs=ALBERS).boundary.plot(ax=ax, color="#4D4D4D", linewidth=0.45, zorder=2)
    dash.plot(ax=ax, color="#4D4D4D", edgecolor="#4D4D4D", linewidth=0.5, zorder=3)
    ax.set_xlim(ext[0], ext[2])
    ax.set_ylim(ext[1], ext[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")  # geopandas adds 'Easting/Northing [metre]' labels otherwise
    ax.set_ylabel("")
    for s in ax.spines.values():
        s.set_visible(False)


def classify(v, edges):
    for k in range(len(edges) - 1):
        if edges[k] <= v < edges[k + 1]:
            return k
    raise ValueError(v)


def choropleth(ax, prov, dash, values, edges, labels, colors, title):
    """values: {adcode: value}. edges: len(colors)+1 class bounds; labels low -> high."""
    main_ext, scs_ext = extents(prov)
    fill = [colors[classify(values[c], edges)] if c in values else NODATA for c in prov["adcode"]]
    _draw(ax, prov, dash, fill, main_ext, outline=unary_union(prov.geometry.values))
    ins = ax.inset_axes([1 - INSET_W, 0.0, INSET_W, INSET_H])
    _draw(ins, prov, dash, fill, scs_ext, lw=0.2)
    for s in ins.spines.values():
        s.set_visible(True)
        s.set_linewidth(0.5)
    ins.text(0.5, 0.03, "South China Sea", transform=ins.transAxes, ha="center", va="bottom", fontsize=5.5)
    handles = [Patch(fc=c, ec="#7F7F7F", lw=0.3) for c in reversed(colors)] + [Patch(fc=NODATA, ec="#7F7F7F", lw=0.3)]
    ax.legend(handles, list(reversed(labels)) + ["No data"], title=title, loc="upper center",
              bbox_to_anchor=(0.5, -0.01), ncol=3, fontsize=7, title_fontsize=7.5, handlelength=1.3,
              handleheight=0.9, labelspacing=0.3, columnspacing=1.2, borderaxespad=0.0)
