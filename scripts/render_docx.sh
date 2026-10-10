#!/bin/zsh
# Approximate page images of a .docx on macOS without LibreOffice:
# Quick Look -> HTML -> headless Chrome PDF -> PNG pages. Equations (OMML) are not drawn and
# pagination is approximate; use it to check figures, captions, tables and fonts.
# usage: render_docx.sh file.docx outdir
set -e
DOCX="$1"; OUT="$2"; R=$(cd "$(dirname "$0")" && pwd)
rm -rf "$OUT"; mkdir -p "$OUT/pages"
cp "$DOCX" "$OUT/doc.docx"
qlmanage -p -o "$OUT" "$OUT/doc.docx" >/dev/null 2>&1
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CH" --headless=new --disable-gpu --hide-scrollbars --no-first-run --user-data-dir="$OUT/prof" \
  --print-to-pdf="$OUT/doc.pdf" --no-pdf-header-footer "file://$OUT/doc.docx.qlpreview/Preview.html" >/dev/null 2>&1 &
CPID=$!
for i in {1..90}; do   # Chrome often does not exit after printing: wait for a stable file, then kill it
  if [[ -s "$OUT/doc.pdf" ]]; then s1=$(stat -f %z "$OUT/doc.pdf"); sleep 2; s2=$(stat -f %z "$OUT/doc.pdf"); [[ "$s1" == "$s2" ]] && break; fi
  sleep 1
done
kill $CPID 2>/dev/null || true; pkill -f "$OUT/prof" 2>/dev/null || true
swift "$R/pdf2png.swift" "$OUT/doc.pdf" "$OUT/pages" 1.4
