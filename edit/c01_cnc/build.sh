#!/bin/bash
# Build the Turismo Forged C01 film: cut -> brand intro (youtube-edit skill, bookends.py) -> mix -> delivery encode.
# Run from the project root:  bash edit/c01_cnc/build.sh
set -euo pipefail
SKILL=.claude/skills/youtube-edit/scripts
OUT=renders/Turismo_Forged_C01_CNC_9x16.mp4
INTRO=1.90          # bookends.py INTRO_HOLD: the film enters with the slide at this time
SFX_ONSET=1.090     # impact onset inside sfx_logo_impact.mp3
SFX_AT=0.12         # where the impact lands in the intro (as the logo appears)
mkdir -p work

# 1) the cut (no titles), with its own sound
python3 edit/c01_cnc/assemble.py source/c01_cnc work/c01_film.mov

# 2) intro audio: one forged-steel impact under the logo, then the film's sound from the slide on
DELAY_MS=$(python3 -c "print(int(round(($INTRO)*1000)))")
python3 - <<EOF
import subprocess
onset, at = $SFX_ONSET, $SFX_AT
subprocess.run(["ffmpeg","-y","-v","error",
  "-ss", f"{onset-at:.3f}", "-i", "source/c01_cnc/sfx_logo_impact.mp3",
  "-i", "work/c01_film.mov",
  "-filter_complex",
  "[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=0dB,afade=t=out:st=2.6:d=0.8[s];"
  "[1:a]adelay=${DELAY_MS}|${DELAY_MS}[f];"
  "[s][f]amix=inputs=2:normalize=0:duration=longest[m]",
  "-map","[m]","-c:a","pcm_s16le","work/c01_intro_mix.wav"], check=True)
EOF

# 3) brand intro from the skill: dark card, steel logo with one light sweep, push-slide down into the billet drop
python3 $SKILL/bookends.py edit/c01_cnc/bookends.json work/c01_film.mov work/c01_with_intro.mp4 --audio work/c01_intro_mix.wav

# 4) delivery: static gain to -14 LUFS, true-peak-safe limiter, grain-friendly H.264 under ~30 MB
I=$(ffmpeg -hide_banner -i work/c01_with_intro.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
GAIN=$(python3 -c "print(round(-14.0 - ($I), 2))")
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 work/c01_with_intro.mp4)
ffmpeg -y -v error -i work/c01_with_intro.mp4 \
  -af "volume=${GAIN}dB,alimiter=limit=0.74:level=false,apad,atrim=0:${DUR}" \
  -c:v libx264 -preset slow -crf 21 -tune grain -profile:v high -maxrate 9M -bufsize 18M \
  -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k -t "$DUR" "$OUT"
cp work/c01_with_intro.timeline.json "${OUT%.mp4}.timeline.json"
echo "wrote $OUT ($DUR s, gain ${GAIN} dB)"
