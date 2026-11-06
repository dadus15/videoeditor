#!/bin/bash
# Final reel v8, built in the Higgsfield sandbox at /home/user/final:
# - photoreal Seedance A and B (video_edit on previs v7.4) between the v6 opening and the v6 packshots;
# - the Montagem Samba cut as the score.
#   final_v8.sh A.mp4 B.mp4 music.wav out.mp4
set -e
cd /home/user/final
A=$1; B=$2; MUS=$3; OUT=$4
V6=/home/user/v6/Turismo_MSP02_GT3RS_Reel_9x16_v6.mp4
S="scale=1080:1920:flags=lanczos,setsar=1"
E="-c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -an"
# conform the 24 fps generations to 30 fps (motion-compensated) and to their exact frame count in the cut
ffmpeg -v error -y -i $A -vf "$S,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,tpad=stop_mode=clone:stop=6,trim=end_frame=232,setpts=N/30/TB" $E A30.mp4
ffmpeg -v error -y -i $B -vf "$S,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,tpad=stop_mode=clone:stop=6,trim=end_frame=141,setpts=N/30/TB" $E B30.mp4
ffmpeg -v error -y -i $V6 -t 1.04 -vf "$S,fps=30" -frames:v 31 $E s0.mp4
ffmpeg -v error -y -i A30.mp4 -frames:v 227 $E s1.mp4
# paint-on-paint swap: A 227-229 x B 0-2
ffmpeg -v error -y -i A30.mp4 -i B30.mp4 -filter_complex \
 "[0:v]trim=start_frame=227:end_frame=230,setpts=N/30/TB[a];[1:v]trim=end_frame=3,setpts=N/30/TB[b];[a][b]blend=all_expr='A*(1-(N+1)/4)+B*((N+1)/4)'" $E s2.mp4
ffmpeg -v error -y -i B30.mp4 -vf "trim=start_frame=3:end_frame=141,setpts=N/30/TB" $E s3.mp4
ffmpeg -v error -y -ss 13.30 -i $V6 -t 4.70 -vf "$S,fps=30" -frames:v 141 $E s4.mp4
printf "file s0.mp4\nfile s1.mp4\nfile s2.mp4\nfile s3.mp4\nfile s4.mp4\n" > cat.txt     # 31+227+3+138+141 = 540
ffmpeg -v error -y -f concat -i cat.txt -c copy video.mp4
ffmpeg -v error -y -i video.mp4 -i $MUS -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -t 18 $OUT
ffprobe -v error -show_entries format=duration:stream=width,height,nb_frames -of csv=p=0 $OUT
