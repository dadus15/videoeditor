"""Per-frame brightness and global motion (median optical flow) of the source.
Usage: python3 scripts/analyze_motion.py <video> <out.csv>"""
import sys, cv2, numpy as np
cap = cv2.VideoCapture(sys.argv[1]); prev = None; rows = []
while True:
    ok, f = cap.read()
    if not ok: break
    t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
    g = cv2.cvtColor(f[50:318], cv2.COLOR_BGR2GRAY)  # active picture rows
    small = cv2.resize(g, (224, 134))
    dx = dy = 0.0
    if prev is not None:
        fl = cv2.calcOpticalFlowFarneback(prev, small, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        dx, dy = np.median(fl[..., 0]) * 2, np.median(fl[..., 1]) * 2
    rows.append((t, g.mean(), dx, dy, np.abs(small.astype(int) - (prev if prev is not None else small)).mean()))
    prev = small
np.savetxt(sys.argv[2], np.array(rows), delimiter=',', fmt='%.4f', header='t,luma,dx,dy,diff')
