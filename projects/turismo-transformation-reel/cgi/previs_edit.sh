#!/bin/bash
# Assemble the 18 s previs and the side-by-side with the reference (Higgsfield sandbox).
#   A/0000-0231.png  film 1.04-8.74 s (Blender, previs.py --seg A): dive, over the vent, glide on the bonnet paint
#   B/0000-0140.png  film 8.65-13.32 s (previs.py --seg B): glide on the new car's door paint, out of the glass
#   The two worlds swap on the paint (as in the reference): a 3-frame mix where both frames are paint only.
#   0-1.04 and 13.30-18.0: the photoreal v6 opening and packshots (unchanged), score v7.
set -e
cd /home/user/previs
V6=/home/user/v6/Turismo_MSP02_GT3RS_Reel_9x16_v6.mp4
S="scale=540:960:flags=lanczos,setsar=1,fps=30,format=yuv420p"
E="-c:v libx264 -crf 16 -preset medium -an"
ffmpeg -v error -y -i $V6 -t 1.04 -vf "$S" $E s0.mp4
ffmpeg -v error -y -framerate 30 -i A/%04d.png -frames:v 227 -vf "$S" $E s1.mp4      # A 0-226: 1.04-8.59
mkdir -p xf
python3 - <<'PY'
from PIL import Image
for k, w in enumerate((0.25, 0.5, 0.75)):                     # A 227-229 x B 0-2, paint on paint
    a = Image.open(f"A/{227 + k:04d}.png").convert("RGB")
    b = Image.open(f"B/{k:04d}.png").convert("RGB").resize(a.size)
    Image.blend(a, b, w).save(f"xf/{k:04d}.png")
PY
ffmpeg -v error -y -framerate 30 -i xf/%04d.png -vf "$S" $E s2.mp4
ffmpeg -v error -y -framerate 30 -start_number 3 -i B/%04d.png -frames:v 138 -vf "$S" $E s3.mp4   # B 3-140
ffmpeg -v error -y -ss 13.30 -i $V6 -t 4.70 -vf "$S" $E s4.mp4
printf "file s0.mp4\nfile s1.mp4\nfile s2.mp4\nfile s3.mp4\nfile s4.mp4\n" > cat.txt
ffmpeg -v error -y -f concat -i cat.txt -c copy video.mp4              # 31+227+3+138+141 = 540 frames
ffmpeg -v error -y -i video.mp4 -i score_v7.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -t 18 \
  Turismo_Reel_previs_v7.mp4
# side by side: reference (left) and previs (right), same clock, labels on top
F=/usr/share/fonts/truetype/montserrat/Montserrat-SemiBold.ttf
[ -f $F ] || F=$(fc-list | grep -i montserrat | head -1 | cut -d: -f1)
# the reference is a variable-rate phone capture: make it 30 fps CFR first, then pair the two frame by frame
ffmpeg -v error -y -i ref.mp4 -vf "fps=30,scale=-2:960,setsar=1" -frames:v 540 -an -c:v libx264 -crf 14 ref30.mp4
ffmpeg -v error -y -i ref30.mp4 -i Turismo_Reel_previs_v7.mp4 -filter_complex \
  "[0:v]setpts=N/30/TB,drawtext=fontfile=$F:text='ORYGINAL':x=20:y=20:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=8[l];\
   [1:v]setsar=1,setpts=N/30/TB,drawtext=fontfile=$F:text='PREVIS v7 (Blender, 0 kredytow)':x=20:y=20:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=8,\
drawtext=fontfile=$F:text='%{pts\:hms}':x=w-tw-20:y=h-50:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=6[r];\
   [l][r]hstack=2,format=yuv420p[v]" -map "[v]" -map 1:a -c:v libx264 -crf 18 -c:a aac -b:a 192k -t 18 \
  Turismo_Reel_previs_v7_vs_oryginal.mp4
for f in Turismo_Reel_previs_v7.mp4 Turismo_Reel_previs_v7_vs_oryginal.mp4; do
  ffprobe -v error -show_entries format=duration:stream=width,height,nb_frames -of csv=p=0 $f
done
