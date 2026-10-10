"""Put redrawn figures into an existing Word manuscript (crisp, vector-first).

For every replaced picture:
  * the PNG fallback is the 600 dpi file (<figs>/hires/<stem>.png) and a vector SVG
    (<figs>/svg/<stem>.svg) is attached through the Office 2016+ asvg:svgBlip extension,
    so Word shows the vector and older Word / WPS show the high-res PNG;
  * size = text width (A4, 1-inch margins) with the image's own aspect ratio;
  * old crops (a:srcRect) and effect extents are removed - a stale crop silently cuts the
    top/bottom off the new image;
  * paragraph centred + keepNext (picture stays with the caption below it);
  * alt text = the caption text of the next paragraph.
Package level: svg content type, <w:doNotAutoCompressPictures/> (no downsampling on save),
optional A4 page size.

Usage:
  python docx_embed.py IN.docx OUT.docx --figs output \
      --replace Fig2_map Fig3_patterns ... \          # stems, in document order of existing pictures
      [--insert-after 50B72810 Fig1_framework "Figure 1. Theoretical framework"] [--a4]
  Use '-' in --replace to keep a picture unchanged. Validate afterwards (docx skill validate.py).
"""
import argparse
import copy
import random
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
ASVG = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
SVG_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
IMG_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
NS = {"w": W, "wp": WP, "a": A, "pic": PIC, "r": R}
TEXT_WIDTH_EMU = (11906 - 2 * 1440) * 635  # 6.27 in
# CT_Settings children that must FOLLOW doNotAutoCompressPictures (schema order)
SETTINGS_AFTER = {"forceUpgrade", "captions", "readModeInkLockDown", "smartTagType", "schemaLibrary",
                  "shapeDefaults", "doNotEmbedSmartTags", "decimalSymbol", "listSeparator"}


def q(t):
    p, l = t.split(":")
    return f"{{{NS[p]}}}{l}"


def load(p):
    return etree.parse(str(p), etree.XMLParser(remove_blank_text=False, huge_tree=True))


def save(tree, p):
    tree.write(str(p), xml_declaration=True, encoding="UTF-8", standalone=True)


def png_size(p):
    with open(p, "rb") as f:
        return struct.unpack(">II", f.read(24)[16:24])


def text_of(p):
    return "".join(t.text or "" for t in p.iter(q("w:t")))


class Package:
    def __init__(self, root):
        self.root = Path(root)
        self.rels_path = self.root / "word/_rels/document.xml.rels"
        self.rels = load(self.rels_path)

    def target(self, rid):
        return next(r.get("Target") for r in self.rels.getroot() if r.get("Id") == rid)

    def add_rel(self, target):
        for r in self.rels.getroot():
            if r.get("Target") == target:
                return r.get("Id")
        rid = "rId" + str(max(int(r.get("Id")[3:]) for r in self.rels.getroot()) + 1)
        etree.SubElement(self.rels.getroot(), f"{{{PR}}}Relationship", Id=rid, Type=IMG_REL, Target=target)
        return rid

    def finish(self):
        save(self.rels, self.rels_path)


def set_picture(pkg, drawing, png, svg, alt, width=TEXT_WIDTH_EMU):
    inline = drawing.find(".//wp:inline", NS)
    blip = drawing.find(".//a:blip", NS)
    media = pkg.target(blip.get(q("r:embed")))
    shutil.copyfile(png, pkg.root / "word" / media)
    w_px, h_px = png_size(png)
    cx, cy = str(width), str(round(width * h_px / w_px))
    inline.find("wp:extent", NS).attrib.update({"cx": cx, "cy": cy})
    inline.find(".//a:xfrm/a:ext", NS).attrib.update({"cx": cx, "cy": cy})
    eff = inline.find("wp:effectExtent", NS)
    if eff is not None:
        eff.attrib.update({"l": "0", "t": "0", "r": "0", "b": "0"})
    for crop in inline.findall(".//pic:blipFill/a:srcRect", NS):
        crop.getparent().remove(crop)
    inline.attrib.update({"distL": "0", "distR": "0"})
    for el in (inline.find("wp:docPr", NS), inline.find(".//pic:cNvPr", NS)):
        el.set("descr", alt)
    if svg is not None and Path(svg).exists():
        svg_target = str(Path(media).with_suffix(".svg"))
        shutil.copyfile(svg, pkg.root / "word" / svg_target)
        rid = pkg.add_rel(svg_target)
        for old in blip.findall("a:extLst", NS):
            blip.remove(old)
        ext = etree.SubElement(etree.SubElement(blip, q("a:extLst")), q("a:ext"), uri=SVG_URI)
        etree.SubElement(ext, f"{{{ASVG}}}svgBlip", nsmap={"asvg": ASVG}).set(q("r:embed"), rid)


def centre_and_keep(p):
    ppr = p.find("w:pPr", NS)
    if ppr is None:
        ppr = etree.Element(q("w:pPr"))
        p.insert(0, ppr)
    jc = ppr.find("w:jc", NS)
    if jc is None:
        jc = etree.SubElement(ppr, q("w:jc"))
    jc.set(q("w:val"), "center")
    if ppr.find("w:keepNext", NS) is None:
        ps = ppr.find("w:pStyle", NS)
        ppr.insert(1 if ps is not None else 0, etree.Element(q("w:keepNext")))


def para_of(el):
    while el.tag != q("w:p"):
        el = el.getparent()
    return el


def caption_after(p):
    nxt = p.getnext()
    return text_of(nxt).strip() if nxt is not None and text_of(nxt).strip().startswith(("Figure", "Fig.")) else ""


def package_settings(root, a4):
    ct_path = root / "[Content_Types].xml"
    ct = load(ct_path)
    if not any(d.get("Extension") == "svg" for d in ct.getroot()):
        ct.getroot().insert(0, etree.Element(f"{{{CT}}}Default", Extension="svg", ContentType="image/svg+xml"))
        save(ct, ct_path)
    st_path = root / "word/settings.xml"
    st = load(st_path)
    s = st.getroot()
    if s.find("w:doNotAutoCompressPictures", NS) is None:
        el = etree.Element(q("w:doNotAutoCompressPictures"))
        for child in s:
            qn = etree.QName(child)
            if qn.localname in SETTINGS_AFTER or qn.namespace not in (W, M):
                child.addprevious(el)
                break
        else:
            s.append(el)
        save(st, st_path)
    if a4:
        doc_path = root / "word/document.xml"
        doc = load(doc_path)
        for sp in doc.getroot().iter(q("w:sectPr")):
            pg = sp.find("w:pgSz", NS)
            if pg is None:
                pg = etree.Element(q("w:pgSz"))
                mar = sp.find("w:pgMar", NS)
                mar.addprevious(pg) if mar is not None else sp.insert(0, pg)
            pg.set(q("w:w"), "11906")
            pg.set(q("w:h"), "16838")
        save(doc, doc_path)


def insert_figure(pkg, body_root, after_para_id, png, svg, caption):
    """Clone the first picture paragraph and its caption; place them after a paragraph."""
    paras = list(body_root.iter(q("w:p")))
    anchor = next(p for p in paras if p.get(f"{{{W14}}}paraId") == after_para_id)
    first_img = next(p for p in paras if p.find(".//w:drawing", NS) is not None)
    img_p, cap_p = copy.deepcopy(first_img), copy.deepcopy(first_img.getnext())
    used = {p.get(f"{{{W14}}}paraId") for p in paras}
    for p in (img_p, cap_p):
        pid = f"{random.randint(0x10000000, 0x7FFFFFFF):08X}"
        while pid in used:
            pid = f"{random.randint(0x10000000, 0x7FFFFFFF):08X}"
        used.add(pid)
        p.set(f"{{{W14}}}paraId", pid)
    media = f"media/image_new_{Path(png).stem}.png"
    shutil.copyfile(png, pkg.root / "word" / media)
    drawing = img_p.find(".//w:drawing", NS)
    drawing.find(".//a:blip", NS).set(q("r:embed"), pkg.add_rel(media))
    max_id = max(int(d.get("id")) for d in body_root.iter(q("wp:docPr")))
    drawing.find(".//wp:docPr", NS).set("id", str(max_id + 1))
    set_picture(pkg, drawing, png, svg, caption)
    # caption: bold label run + regular title run, formats taken from the cloned caption
    runs = [r for r in cap_p.findall("w:r", NS) if r.find("w:t", NS) is not None]
    label_r, title_r = copy.deepcopy(runs[0]), copy.deepcopy(runs[-1])
    for r in cap_p.findall("w:r", NS):
        cap_p.remove(r)
    label, _, title = caption.partition(". ")
    label_r.find("w:t", NS).text = label + ". "
    label_r.find("w:t", NS).set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    title_r.find("w:t", NS).text = title
    cap_p.append(label_r)
    cap_p.append(title_r)
    anchor.addnext(img_p)
    img_p.addnext(cap_p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--figs", required=True, help="folder with hires/<stem>.png and svg/<stem>.svg")
    ap.add_argument("--replace", nargs="*", default=[], help="stems in document order of existing pictures; '-' = keep")
    ap.add_argument("--insert-after", nargs=3, action="append", default=[],
                    metavar=("PARAID", "STEM", "CAPTION"))
    ap.add_argument("--a4", action="store_true")
    a = ap.parse_args()
    figs = Path(a.figs)
    random.seed(20261009)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(a.src) as z:
            z.extractall(root)
        pkg = Package(root)
        doc_path = root / "word/document.xml"
        doc = load(doc_path)
        drawings = doc.getroot().findall(".//w:drawing", NS)
        assert len(a.replace) <= len(drawings), f"{len(drawings)} pictures in document"
        for drawing, stem in zip(drawings, a.replace):
            if stem == "-":
                continue
            p = para_of(drawing)
            set_picture(pkg, drawing, figs / "hires" / f"{stem}.png", figs / "svg" / f"{stem}.svg",
                        caption_after(p) or stem)
            centre_and_keep(p)
            print(f"replaced -> {stem}")
        for pid, stem, cap in a.insert_after:
            insert_figure(pkg, doc.getroot(), pid, figs / "hires" / f"{stem}.png", figs / "svg" / f"{stem}.svg", cap)
            print(f"inserted {stem} after {pid}")
        save(doc, doc_path)
        pkg.finish()
        package_settings(root, a.a4)
        with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(root.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(root).as_posix())
    print("written", a.dst)


if __name__ == "__main__":
    main()
