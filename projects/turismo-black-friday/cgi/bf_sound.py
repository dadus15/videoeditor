"""Draft score for the Black Friday remake: synthesised, licence-free, on the reference's hit map.

Reference sound map (film time = recording time - 0.13 s):
- 0-2.90 quiet intro (pad, riser), glitch hit at 1.76-2.13 under the title glitch;
- 2.90 drop on the cut to the red-lit wheel; kicks on the reference's onsets, cut-synced;
- 14.90 hard stop with an impact on the cut to the final shot; room tone to the loop point (18.0).

    python3 cgi/bf_sound.py out/score.wav
"""
import subprocess
import sys

import numpy as np
from scipy import signal

SR = 48000
DUR = 18.0
OFF = 0.13
# kick onsets measured in the reference recording (s)
REC_ONSETS = [3.03, 3.21, 4.04, 4.26, 4.53, 4.71, 4.90, 5.46, 5.66, 6.05, 6.21, 6.44, 6.59, 7.14, 7.35, 7.53,
              7.71, 8.09, 8.28, 8.46, 8.65, 8.80, 9.00, 9.19, 9.63, 10.14, 10.35, 10.55, 10.71, 11.09, 11.28,
              11.46, 11.66, 12.05, 12.21, 12.59, 12.78, 13.05, 13.31, 13.53, 13.71, 14.09, 14.28, 14.46, 14.74]
KICKS = [t - OFF for t in REC_ONSETS]
DROP, STOP = 2.90, 14.90
TYPE_FRAMES = [378, 380, 382, 384, 386, 404, 407, 410, 413, 416, 419]

n = int(SR * DUR)
t = np.arange(n) / SR
mix = np.zeros((n, 2))
rng = np.random.default_rng(7)


def add(x, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= n:
        return
    x = x[: n - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i:i + len(x), 0] += x * gain * l * 1.414
    mix[i:i + len(x), 1] += x * gain * r * 1.414


def env(length, a=0.002, d=0.3):
    k = np.arange(int(length * SR)) / SR
    return np.minimum(k / a, 1) * np.exp(-k / d)


def kick(length=0.45, f0=150, f1=44, d=0.28):
    k = np.arange(int(length * SR)) / SR
    f = f1 + (f0 - f1) * np.exp(-k / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(length, 0.001, d)
    return np.tanh(x * 2.2) * 0.8


def bass808(freq, length=0.5):
    k = np.arange(int(length * SR)) / SR
    x = np.sin(2 * np.pi * freq * k + 0.4 * np.sin(2 * np.pi * freq * 2 * k)) * env(length, 0.004, 0.35)
    return np.tanh(x * 3) * 0.55


def noise(length, lo, hi, d):
    x = rng.normal(0, 1, int(length * SR))
    x = signal.sosfilt(signal.butter(4, [lo, hi], "band", fs=SR, output="sos"), x)
    return x * env(length, 0.001, d)


def clap():
    x = sum(np.pad(noise(0.25, 900, 6000, 0.06), (int(o * SR), 0))[: int(0.3 * SR)] for o in (0, 0.011, 0.022))
    return x * 0.35


def verb(x, length=1.6, d=0.5, wet=0.3):
    ir = rng.normal(0, 1, int(length * SR)) * np.exp(-np.arange(int(length * SR)) / SR / d)
    y = signal.fftconvolve(x, ir)[: len(x) + len(ir)]
    y = y / (np.abs(y).max() + 1e-9) * np.abs(x).max()
    return np.concatenate([x, np.zeros(len(y) - len(x))]) * (1 - wet) + y * wet


# intro pad (F minor) and riser
pad = np.zeros(n)
for f in (87.31, 103.83, 130.81, 174.61):
    for det in (-0.4, 0.4):
        pad += signal.sawtooth(2 * np.pi * (f + det) * t) * 0.05
pad = signal.sosfilt(signal.butter(2, 700, "low", fs=SR, output="sos"), pad)
pad *= np.clip(t / 0.4, 0, 1) * np.where(t < DROP, 1.0, np.where(t < STOP, 0.45, 0.0))
mix[:, 0] += pad
mix[:, 1] += pad
r_len = DROP - 1.0
riser = rng.normal(0, 1, int(r_len * SR))
sweep = signal.sosfilt(signal.butter(2, 2500, "high", fs=SR, output="sos"), riser)
riser = (riser * 0.15 + sweep * 0.6) * np.linspace(0, 1, len(riser)) ** 2.5 * 0.25
add(riser, 1.0, 1.0)
# title glitch (frames 56-64)
for k in range(9):
    add(noise(0.03, 2000, 9000, 0.02) * (0.5 if k % 2 else 0.25), 1.87 + k / 30, 0.8, pan=(-0.5 if k % 2 else 0.5))
add(kick(0.6, 110, 40, 0.4) * 0.7, 1.76, 0.7)                 # intro hit (reference onset 1.89)

# drop section
notes = [43.65, 43.65, 51.91, 38.89]                       # F1, F1, Ab1, Eb1
grp = 0
prev = None
for k_t in KICKS:
    add(kick(), k_t, 1.0)
    start = prev is None or k_t - prev > 0.3
    if start:
        grp += 1
        add(verb(clap(), 0.8, 0.25, 0.25), k_t, 0.8, pan=0.05)
    add(bass808(notes[grp % 4]), k_t, 0.8)
    prev = k_t
for k_t, nxt in zip(KICKS, KICKS[1:] + [STOP]):            # hats between hits
    m = k_t
    while m + 0.12 < nxt:
        m += 0.12
        add(noise(0.05, 7000, 14000, 0.015), m, 0.22, pan=0.3)
add(verb(noise(0.6, 3000, 12000, 0.4), 1.5, 0.6, 0.4) * 0.5, DROP - 0.02, 0.6)   # crash on the drop
# hard stop with an impact, then room tone
add(verb(kick(1.2, 90, 32, 0.6) + noise(0.4, 200, 5000, 0.1) * 0.4, 2.2, 0.7, 0.45), STOP, 1.0)
room = signal.sosfilt(signal.butter(2, [80, 900], "band", fs=SR, output="sos"), rng.normal(0, 1, n)) * 0.012
room *= np.clip((t - STOP) / 0.6, 0, 1)
mix[:, 0] += room
mix[:, 1] += room
for f in TYPE_FRAMES:                                       # quiet type-on ticks
    add(noise(0.02, 3000, 9000, 0.006), f / 30, 0.25, pan=0.1)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.9
out = sys.argv[1]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), out],
               input=mix.astype(np.float32).tobytes(), check=True)
print("wrote", out)
