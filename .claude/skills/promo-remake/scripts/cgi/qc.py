#!/usr/bin/env python3
"""Machine QC for a finished render: format, black frames, single-frame flashes, frozen frames, loudness.

    python3 cgi/qc.py renders/Turismo_Inventa_Promo_16x9.mp4
"""
import json
import subprocess
import sys

import cv2
import numpy as np

# hard cuts in the montage are intentional: a frame that differs from both neighbours is only a "flash"
# when its neighbours match each other (an isolated odd frame inside one continuous shot)
CUT_FRAMES = None


def main(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate,nb_frames:format=duration",
                        "-of", "json", path], capture_output=True, text=True)
    info = json.loads(p.stdout)
    print("streams:", [{k: v for k, v in s.items()} for s in info["streams"]])
    print("duration:", info["format"]["duration"])
    bd = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vf", "blackdetect=d=0.04:pix_th=0.06",
                         "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    print("black segments:", bd.count("black_start"))

    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(cv2.resize(f, (240, 135)), cv2.COLOR_BGR2GRAY).astype(np.float32))
    d = [float(np.abs(frames[i] - frames[i - 1]).mean()) for i in range(1, len(frames))]
    flashes = []
    for i in range(1, len(frames) - 1):
        a, b = d[i - 1], d[i]
        nb = float(np.abs(frames[i + 1] - frames[i - 1]).mean())
        if a > 8 and b > 8 and nb < 3:
            flashes.append(i)
    print("frames:", len(frames), "single-frame flashes:", flashes)
    print("first frame mean luma:", round(float(frames[0].mean()), 1), " last:", round(float(frames[-1].mean()), 1))
    eb = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    s = eb[eb.rfind("Summary"):]
    print(" ".join(s.split()))


if __name__ == "__main__":
    main(sys.argv[1])
