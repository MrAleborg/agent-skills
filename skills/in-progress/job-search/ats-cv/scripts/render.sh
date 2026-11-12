#!/usr/bin/env bash
# Usage: [NO_DOCX=1] render.sh <cv.html>
# Writes <cv>.pdf (headless Chromium print) and <cv>.docx (LibreOffice) next to the HTML.
set -euo pipefail

html="$(realpath "$1")"
dir="$(dirname "$html")"; base="$(basename "$html" .html)"

chrome="$(command -v chromium || command -v chromium-browser || command -v google-chrome || command -v google-chrome-stable || true)"
[ -n "$chrome" ] || { echo "No Chromium/Chrome found" >&2; exit 1; }

# Snap-confined Chromium can only see its own snap dir (not /tmp or hidden dirs).
case "$chrome" in
  /snap/*) root="$HOME/snap/chromium/common"; mkdir -p "$root"; stage="$(mktemp -d "$root/ats-cv.XXXXXX")" ;;
  *) stage="$(mktemp -d)" ;;
esac
trap 'rm -rf "$stage"' EXIT
cp "$html" "$stage/cv.html"

"$chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf-no-header \
  --print-to-pdf="$stage/cv.pdf" "file://$stage/cv.html" >/dev/null 2>&1
[ -s "$stage/cv.pdf" ] || { echo "Chromium produced no PDF" >&2; exit 1; }
cp "$stage/cv.pdf" "$dir/$base.pdf"
# NO_DOCX=1: PDF only (the cover-letter skill uses this).
if [ -n "${NO_DOCX:-}" ]; then ls "$dir/$base.pdf"; exit 0; fi

# LibreOffice turns the .emp separator border into a box around every paragraph: drop borders for the DOCX.
sed -E 's/border(-top|-bottom)?: *[^;]*;//g' "$stage/cv.html" > "$stage/cv.docx.html" && mv "$stage/cv.docx.html" "$stage/cv.html"
# Writer's HTML import gives a real Word document (not a Writer/Web one).
soffice --headless --infilter="HTML (StarWriter)" --convert-to 'docx:MS Word 2007 XML' \
  --outdir "$stage" "$stage/cv.html" >/dev/null 2>&1 || true
if [ -s "$stage/cv.docx" ]; then cp "$stage/cv.docx" "$dir/$base.docx"; else echo "WARN: DOCX conversion failed" >&2; fi

ls "$dir/$base".pdf "$dir/$base".docx 2>/dev/null
