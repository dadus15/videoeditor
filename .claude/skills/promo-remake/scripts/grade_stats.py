#!/usr/bin/env python3
"""Per-section grade fingerprint: luma p5/50/95, saturation, mean RGB, Laplacian sharpness.
Usage: python3 grade_stats.py video.mp4   (edit segs for your timeline). Compare reference vs ours."""
import subprocess, sys, numpy as np
f=sys.argv[1]
segs=[("world1",3.2,6.4),("transition",8.45,8.95),("world2",10.6,13.2),("parked",13.4,15.2),("wheel",15.4,16.1),("void",17.2,17.9)]
for name,a,b in segs:
    raw=subprocess.run(["ffmpeg","-v","error","-ss",str(a),"-t",str(b-a),"-i",f,"-vf","fps=4,scale=256:-2","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
    w=256; px=np.frombuffer(raw,np.uint8)
    h=len(px)//3//w
    img=px[:h*w*3].reshape(-1,w,3).astype(float)/255
    mx,mn=img.max(2),img.min(2); sat=(mx-mn)/(mx+1e-4); lum=img@[0.2126,0.7152,0.0722]
    lap=np.abs(lum[2:,1:-1]+lum[:-2,1:-1]+lum[1:-1,2:]+lum[1:-1,:-2]-4*lum[1:-1,1:-1])
    r,g,bb=[img[...,i].mean() for i in range(3)]
    print(f"{name:10s} luma p5/50/95 {np.percentile(lum,5):.2f}/{np.median(lum):.2f}/{np.percentile(lum,95):.2f}  sat {sat.mean():.2f}  RGB {r:.2f},{g:.2f},{bb:.2f}  sharp {lap.mean()*100:.2f}")
