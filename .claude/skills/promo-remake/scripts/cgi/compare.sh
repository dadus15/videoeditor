#!/usr/bin/env bash
# side-by-side QC: reference (left) vs ours (right), 960x540 each, our audio
REF="$(dirname "$0")/../source/Vossen_HF_reference_phone-capture.mp4"
ffmpeg -v error -y -i "$REF" -i "$1" -filter_complex \
 "[0:v]fps=25,scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2,setsar=1,drawtext=fontfile=$(dirname "$0")/../.claude/skills/youtube-edit/assets/fonts/DMSans-700.ttf:text='VOSSEN (ref)  %{pts\:hms}':x=10:y=10:fontsize=20:fontcolor=yellow:box=1:boxcolor=black[a];\
  [1:v]scale=960:540,setsar=1,drawtext=fontfile=$(dirname "$0")/../.claude/skills/youtube-edit/assets/fonts/DMSans-700.ttf:text='TURISMO  %{pts\:hms}':x=10:y=10:fontsize=20:fontcolor=yellow:box=1:boxcolor=black[b];\
  [a][b]hstack=inputs=2[v]" -map "[v]" -map 1:a? -c:v libx264 -crf 24 -preset fast -c:a aac -b:a 128k -shortest "$2"
