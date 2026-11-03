#!/usr/bin/env bash
# Reference forensics: timecoded contact sheets, cut-detail sheets, title/end-card crops, spectrogram.
#   ref_sheets.sh ref.mp4 outdir [detail_start detail_dur ...]
# e.g. ref_sheets.sh work/ref/ref.mp4 work/ref 0 3 6 3 16.5 3
set -euo pipefail
REF=$1; OUT=$2; shift 2
mkdir -p "$OUT"
FONT=$(fc-match -f '%{file}' 'DejaVu Sans:bold' 2>/dev/null || true)
[ -f "$FONT" ] || FONT=$(dirname "$0")/../assets/fonts/Orbitron-700.ttf
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$REF")
echo "duration $DUR s"
# 2 fps overview, 20 tiles = 10 s per sheet
for s in $(seq 0 10 "${DUR%.*}"); do
  ffmpeg -v error -y -ss "$s" -t 10 -i "$REF" -vf "fps=2,scale=424:-1,drawtext=fontfile=$FONT:text='%{eif\:t+$s\:d}.%{eif\:mod((t+$s)*10\,10)\:d}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black,tile=4x5" -frames:v 1 "$OUT/sheet_$s.jpg"
done
# 10 fps detail sheets around cuts
while [ $# -ge 2 ]; do
  ffmpeg -v error -y -ss "$1" -t "$2" -i "$REF" -vf "fps=10,scale=340:-1,drawtext=fontfile=$FONT:text='%{eif\:t+$1\:d}.%{eif\:mod((t+$1)*10\,10)\:d}':x=4:y=4:fontsize=20:fontcolor=yellow:box=1:boxcolor=black,tile=5x6" -frames:v 1 "$OUT/detail_$1.jpg"
  shift 2
done
# spectrogram + loudness
ffmpeg -v error -y -i "$REF" -lavfi "showspectrumpic=s=1600x500:legend=1:scale=log" "$OUT/spectrum.png"
ffmpeg -hide_banner -i "$REF" -af ebur128 -f null - 2>&1 | grep -A3 "Integrated" | head -4
ls "$OUT"
echo "Next: crop title/end card at full res, e.g. ffmpeg -ss T -i REF -frames:v 1 -vf 'crop=W:H:X:Y,scale=iw*3:-1:flags=lanczos' title.png"
