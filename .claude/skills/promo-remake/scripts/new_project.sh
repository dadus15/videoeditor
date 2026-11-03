#!/usr/bin/env bash
# Copy the promo-remake toolkit into a project:  new_project.sh /path/to/project
# -> <project>/cgi/*.py|sh, <project>/assets/fonts/*, plus work/ and renders/ folders.
set -euo pipefail
P=${1:?project dir}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$P/cgi" "$P/assets/fonts" "$P/assets/brand" "$P/assets/product" "$P/work" "$P/renders" "$P/source"
for f in "$HERE"/cgi/*; do
  [ -f "$f" ] || continue
  dst="$P/cgi/$(basename "$f")"
  if [ -e "$dst" ]; then echo "keep existing $dst"; else cp "$f" "$dst"; fi
done
[ -e "$P/cgi/hf_assemble.py" ] || cp "$HERE/hf_assemble.py" "$P/cgi/"
for f in "$HERE"/../assets/fonts/*; do [ -e "$P/assets/fonts/$(basename "$f")" ] || cp "$f" "$P/assets/fonts/"; done
grep -qxF "work/" "$P/.gitignore" 2>/dev/null || echo "work/" >> "$P/.gitignore"
echo "Toolkit copied. Next: put the reference in source/, logo/end card in assets/brand/, product renders in assets/product/."
echo "Then: pip install bpy numpy opencv-python-headless pillow scipy && python3 cgi/make_textures.py"
