"""Pixel-level quality analysis of a render: per shot, inside the picture window.
sharpness  : variance of the Laplacian (higher = more fine detail)
detail_hf  : share of spectral energy above 1/4 Nyquist (how much real fine detail the pixels carry)
noise      : median absolute deviation of the high-pass in flat areas (grain/compression noise)
block      : 8x8 blockiness ratio (luma steps on 8-px boundaries vs elsewhere; 1.0 = none)
banding    : in smooth gradients (sky), share of pixels whose 3x3 neighbourhood has exactly 1-2 distinct
             levels with a step of >=1 code value (flat terraces) - higher = more visible banding
"""
import subprocess, sys, json, numpy as np, cv2
f, tl, box = sys.argv[1], json.load(open(sys.argv[2])), [int(v) for v in sys.argv[3].split(',')]
x0, y0, x1, y1 = box
info = subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height','-of','csv=p=0',f],capture_output=True,text=True).stdout.strip().split(',')
W, H = int(info[0]), int(info[1])
def frame_at(t):
    raw = subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',f,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(H,W,3)
rows=[]
for s in tl['shots']:
    if s.get('src_in') is None: continue
    vals=[]
    for u in (0.3, 0.6):
        im = frame_at(s['start'] + u*(s['end']-s['start']))[y0:y1, x0:x1]
        g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY).astype(np.float32)
        lap = cv2.Laplacian(g, cv2.CV_32F).var()
        F = np.abs(np.fft.fftshift(np.fft.fft2(g - g.mean())))**2
        h, w = g.shape; yy, xx = np.mgrid[0:h, 0:w]; yy = yy - h // 2; xx = xx - w // 2
        r = np.hypot(yy/(h/2), xx/(w/2)); hf = F[(r > 0.25) & (r <= 1)].sum() / F[r <= 1].sum()
        hp = g - cv2.GaussianBlur(g, (0,0), 1.5)
        flat = cv2.GaussianBlur(np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0)) + np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1)), (0,0), 3) < 6
        noise = np.median(np.abs(hp[flat])) * 1.4826 if flat.any() else 0
        dx = np.abs(np.diff(g, axis=1)); col = np.arange(dx.shape[1])
        block = dx[:, (col % 8) == 7].mean() / (dx[:, (col % 8) != 7].mean() + 1e-6)
        smooth = cv2.GaussianBlur(np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1)), (0,0), 4) < 2.5
        mn = cv2.erode(g, np.ones((5,5))); mx = cv2.dilate(g, np.ones((5,5)))
        terr = smooth & ((mx - mn) >= 1) & ((mx - mn) <= 2)
        band = terr.sum() / max(smooth.sum(), 1)
        vals.append((lap, hf, noise, block, band))
    v = np.mean(vals, axis=0); rows.append((s['name'], *v))
print(f"{'shot':24s} {'sharp':>7s} {'detailHF':>8s} {'noise':>6s} {'block':>6s} {'banding':>7s}")
for r in rows: print(f"{r[0]:24s} {r[1]:7.1f} {r[2]*100:7.2f}% {r[3]:6.2f} {r[4]:6.3f} {r[5]*100:6.1f}%")
