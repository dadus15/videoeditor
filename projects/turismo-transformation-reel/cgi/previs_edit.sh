#!/bin/bash
# Assemble the 18 s previs and the side-by-side with the reference (Higgsfield sandbox).
#   A/0000-0222.png  film 1.04-8.44 s (Blender, previs.py --seg A)
#   B/0000-0130.png  film 8.95-13.29 s (previs.py --seg B)
#   8.45-8.95 paint hold: the last dive frame, blurred to a soft paint gradient, with a slow creep
#   0-1.04 and 13.30-18.0: the photoreal v6 opening and packshots (unchanged), score v7.
set -e
cd /home/user/previs
V6=/home/user/v6/Turismo_MSP02_GT3RS_Reel_9x16_v6.mp4
S="scale=540:960:flags=lanczos,setsar=1,fps=30,format=yuv420p"
E="-c:v libx264 -crf 16 -preset medium -an"
ffmpeg -v error -y -i $V6 -t 1.04 -vf "$S" $E s0.mp4
ffmpeg -v error -y -framerate 30 -i A/%04d.png -frames:v 222 -vf "$S" $E s1.mp4      # 1.04-8.44 (222 frames)
last=$(ls A/*.png | tail -1)
ffmpeg -v error -y -loop 1 -i $last -t 0.5 -vf "gblur=sigma=45,scale=600:-2,zoompan=z='1+0.0015*on':d=1:s=540x960:fps=30,$S" $E s2.mp4
ffmpeg -v error -y -framerate 30 -i B/%04d.png -vf "$S" $E s3.mp4
ffmpeg -v error -y -ss 13.30 -i $V6 -t 4.70 -vf "$S" $E s4.mp4
printf "file s0.mp4\nfile s1.mp4\nfile s2.mp4\nfile s3.mp4\nfile s4.mp4\n" > cat.txt
ffmpeg -v error -y -f concat -i cat.txt -c copy video.mp4              # 31+222+15+131+141 = 540 frames
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
