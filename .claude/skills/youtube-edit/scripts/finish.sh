#!/usr/bin/env bash
# Final step once the music/SFX files are in assets/audio/ (see the project's AUDIO_REQUEST.md).
# Run from the PROJECT ROOT:
#   .claude/skills/youtube-edit/scripts/finish.sh <music_drop_seconds> [bpm] [name_prefix]
# music_drop_seconds: where the drop/bass entrance sits inside assets/audio/music.wav
# bpm: the track's tempo; re-times every cut to the beat grid (default: the EDL's bpm)
# Output name: the EDL's "output" field (else <prefix>_<variant>_9x16). Renders every edit/edl_*.json: film -> brand bookends (if the EDL has a "bookends" block) -> mix -> mux.
set -euo pipefail
S="$(cd "$(dirname "$0")" && pwd)"
DROP=${1:?music drop time in seconds}; BPM=${2:-}; PREFIX=${3:-Final}
mkdir -p work renders
for edl in edit/edl_*.json; do
  v=$(basename "$edl" .json); v=${v#edl_}
  bpm_arg=(); [ -n "$BPM" ] && bpm_arg=(--bpm "$BPM")
  python3 "$S/compose.py" "$edl" "work/film_$v.mp4" "${bpm_arg[@]}" --crf 6
  if grep -q '"bookends"' "$edl"; then
    python3 "$S/bookends.py" "$edl" "work/film_$v.mp4" "work/pic_$v.mp4" "${bpm_arg[@]}"
  else
    cp "work/film_$v.mp4" "work/pic_$v.mp4"; cp "work/film_$v.timeline.json" "work/pic_$v.timeline.json"
  fi
  python3 "$S/mix_audio.py" "work/pic_$v.timeline.json" "work/mix_$v.wav" --music-drop "$DROP"
  name=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("output", sys.argv[2]))' "$edl" "${PREFIX}_${v}_9x16")
  ffmpeg -v error -y -i "work/pic_$v.mp4" -i "work/mix_$v.wav" -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 256k -shortest -movflags +faststart "renders/$name.mp4"
done
ls -la renders/
