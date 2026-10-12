"""Find which captured frames are new picture frames (the source is a ~40 fps screen capture of 25 fps film).
Writes work/unique.csv: capture_index, pts, diff_to_prev, is_new."""
import subprocess, numpy as np, sys
from pathlib import Path
src = sys.argv[1]
pts = np.array(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'frame=pts_time', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.split(), float)
Path('work').mkdir(exist_ok=True)
cmd = ["ffmpeg", "-v", "fatal", "-i", src, "-fps_mode", "passthrough", "-vf", "crop=448:268:0:50,scale=224:134,format=gray", "-f", "rawvideo", "-"]
raw = subprocess.run(cmd, capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 134, 224).astype(np.float32)
d = np.r_[99, np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))]
# a frame is "new" when it differs clearly more than encoder noise; noise floor ~0.3-0.6
new = d > np.maximum(0.9, 0.25 * np.convolve(d, np.ones(9) / 9, 'same'))
np.savetxt('work/unique.csv', np.c_[np.arange(len(d)), pts[:len(d)], d, new], delimiter=',', fmt=['%d', '%.4f', '%.3f', '%d'])
