#!/usr/bin/env bash
# Final step once the Epidemic Sound files are in assets/audio/ (see AUDIO_REQUEST.md).
#   scripts/finish.sh <music_drop_seconds> [bpm]
# music_drop_seconds: where the drop/bass entrance sits inside assets/audio/music.wav
# bpm: the track's tempo; re-times every cut to the beat grid (default 120, use >=120)
set -euo pipefail
cd "$(dirname "$0")/.."
DROP=${1:?music drop time in seconds}; BPM=${2:-120}
for v in hero:Hero alt:AltOpen; do
  edl=${v%%:*}; name=${v##*:}
  python3 scripts/compose.py edit/edl_${edl}.json work/film_${edl}_bpm${BPM}.mp4 --bpm "$BPM" --crf 6  # film
  python3 scripts/bookends.py edit/edl_${edl}.json work/film_${edl}_bpm${BPM}.mp4 work/${edl}_bpm${BPM}.mp4 --bpm "$BPM"  # logo intro + end card
  python3 scripts/mix_audio.py work/${edl}_bpm${BPM}.timeline.json work/${edl}_mix.wav --music-drop "$DROP"
  ffmpeg -v error -y -i work/${edl}_bpm${BPM}.mp4 -i work/${edl}_mix.wav -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 256k -shortest -movflags +faststart renders/Audi_S8_D4_Inventa_${name}_9x16.mp4
done
ls -la renders/
