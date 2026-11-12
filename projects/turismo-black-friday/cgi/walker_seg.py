"""Person matte for the final walker shot (the Higgsfield sandbox; run with a venv that has rembg[cpu]).

    PYTHONPATH= /home/user/venv/bin/python cgi/walker_seg.py

The temporal-median plate difference missed the black T-shirt over the dark car and steps, so the date card
showed through the body. rembg u2net_human_seg segments only people (not the car) at about 0.15 s a frame.
Writes gen/final_audi_walker_alpha.npy: uint8 alpha for rows WALK_BAND (200-1720) of each 1080x1920 frame,
from t=0.55 s of final_audi_1080.mp4 (93 frames), which bf_draft.py loads when it builds the walker matte.
Install: python3 -m venv /home/user/venv && PYTHONPATH=/pkg/ /home/user/venv/bin/pip install "rembg[cpu]"
(the sandbox's PYTHONPATH includes the unreadable /root, which breaks pip).
"""
import subprocess
import time

import numpy as np
from rembg import new_session, remove

W, H, Y0, Y1 = 1080, 1920, 200, 1720
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.55", "-i", "/home/user/bf/gen/final_audi_1080.mp4", "-vf",
                      f"fps=30,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-frames:v", "93",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
v = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
s = new_session("u2net_human_seg")
out = np.zeros((len(v), Y1 - Y0, W), np.uint8)
t0 = time.time()
for k, fr in enumerate(v):
    out[k] = np.asarray(remove(fr[Y0:Y1], session=s, only_mask=True, post_process_mask=False))
    print(k, round(time.time() - t0, 1), flush=True)
np.save("/home/user/bf/gen/final_audi_walker_alpha.npy", out)
print("saved", out.shape)
