"""Cut a track to the reel's sound map (ANALIZA_ORYGINALU.md, section 9).

- The track's strongest drop lands on 9.4 s.
- Intro: low-passed, without bass, until the 1.04 cut.
- Break 7.6-8.3: bass and lead out.
- Stutter 8.4-9.3.
- Full track from 9.4.
- Hard stop at 17.0 with a reverb tail.

    python3 cutmusic.py in.mp3 out.wav rate        # rate < 1 = "slowed" (tempo and pitch drop, like the reference)
"""
import subprocess
import sys

import numpy as np
from scipy import signal

src, out, rate = sys.argv[1], sys.argv[2], float(sys.argv[3])
SR = 44100
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-af", f"asetrate={int(SR * rate)},aresample={SR}",
                      "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
lo = signal.sosfilt(signal.butter(4, 150, "low", fs=SR, output="sos"), x.mean(1))
hop = int(0.05 * SR)
e = np.sqrt(np.add.reduceat(lo ** 2, np.arange(0, len(lo), hop)) / hop)
t = np.arange(len(e)) * 0.05
best, bt = -1, None
for i in range(len(e)):                       # strongest rise of sub-bass energy (the drop)
    if t[i] < 14 or t[i] > t[-1] - 12:
        continue
    rise = e[i:i + 20].mean() - e[max(0, i - 20):i].mean()
    if rise > best:
        best, bt = rise, t[i]
off = bt - 9.4
print("drop at %.2f s in the track, offset %.2f" % (bt, off))
seg = x[int(off * SR):int((off + 18.0) * SR)].copy()


def n(s):
    return int(s * SR)


def filt(a, kind, f):
    return signal.sosfiltfilt(signal.butter(4, f, kind, fs=SR, output="sos"), a, axis=0)


y = seg.copy()
y[:n(0.2)] = 0
y[n(0.2):n(1.04)] = filt(seg, "low", 900)[n(0.2):n(1.04)] * 0.6          # intro without bass and punch
y[n(7.6):n(8.3)] = filt(seg, "high", 2500)[n(7.6):n(8.3)] * 0.7          # break: bass and lead out
st = seg[n(8.4):n(9.3)].copy()                                            # stutter: 1/16 gates
g = (np.floor((np.arange(len(st)) / SR) / 0.0625) % 2 == 0).astype(np.float32)
g = signal.lfilter([0.02], [1, -0.98], g)
y[n(8.4):n(9.3)] = st * g[:, None]
y[n(8.3):n(8.4)] *= 0.5
tail = y[n(16.75):n(17.0)].copy()
y[n(17.0):] = 0
ir = np.random.default_rng(1).normal(0, 1, (n(2.0), 2)) * np.exp(-np.arange(n(2.0)) / n(0.45))[:, None]
rv = np.stack([signal.fftconvolve(tail[:, c], ir[:, c]) for c in range(2)], 1)
rv = rv / (np.abs(rv).max() + 1e-9) * np.abs(tail).max() * 0.5
k = min(len(rv), len(y) - n(17.0))
y[n(17.0):n(17.0) + k] += rv[:k]
f = n(0.015)
for a in (1.04, 7.6, 8.3, 9.4, 17.0):                                     # click-free joins
    i = n(a)
    y[i - f:i + f] *= np.concatenate([np.linspace(1, 0.3, f), np.linspace(0.3, 1, f)])[:, None]
y = y / (np.abs(y).max() + 1e-9) * 0.89
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", out],
               input=y.astype(np.float32).tobytes(), check=True)
print("wrote", out)
