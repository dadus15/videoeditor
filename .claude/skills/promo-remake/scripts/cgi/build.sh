#!/usr/bin/env bash
# Build the Turismo Inventa promo end to end.
#   cgi/build.sh [res] [spp] [name]
#   res  CGI render height: 720 (default, upscaled to 1080p in post) or 1080 for a full-resolution master
#   spp  Cycles samples per pixel (default 16, denoised)
set -euo pipefail
cd "$(dirname "$0")/.."
RES=${1:-720}
SPP=${2:-16}
NAME=${3:-Turismo_Inventa_Promo_16x9}

python3 cgi/make_textures.py
python3 cgi/shots.py -- --res "$RES" --spp "$SPP" --skip-existing
python3 cgi/post.py --res "$RES" --out "work/film_${RES}.mp4"
python3 cgi/sound.py "work/film_${RES}.timeline.json" work/score.wav
mkdir -p renders
ffmpeg -v error -y -i "work/film_${RES}.mp4" -i work/score.wav -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart "renders/${NAME}.mp4"
# small review copy for chat
ffmpeg -v error -y -i "renders/${NAME}.mp4" -c:v libx264 -crf 23 -preset slow -c:a aac -b:a 160k \
  -movflags +faststart "renders/${NAME}_review.mp4"
ls -la renders/"${NAME}"*.mp4
