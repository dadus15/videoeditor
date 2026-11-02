#!/usr/bin/env python3
"""Synthesised score and sound design for the Turismo Inventa promo, locked to the picture cut.

Everything is generated here from oscillators and noise (no samples, no licensed music), following the
reference's sound map: soft data blips while the title types on, a trailer impact on each section cut,
whooshes on the whips, a dark 120 BPM pulse under the detail act, a breakdown into the ghost hub, a
faster groove with a metallic tick on every montage cut, and a final hit with a shimmer on the end card.

    python3 cgi/sound.py work/film.timeline.json work/score.wav

Writes a 48 kHz stereo WAV normalised to -14 LUFS, true peak <= -1.5 dBTP (via ffmpeg loudnorm).
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(11)


def n(s):
    return int(round(s * SR))


def add(buf, t0, x, gain=1.0, pan=0.0):
    """Mix mono or stereo x into buf at time t0 (s) with gain (linear) and pan (-1..1)."""
    i = n(t0)
    if i >= buf.shape[0]:
        return
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x * l * 1.414, x * r * 1.414], 1)
    j = min(buf.shape[0], i + len(x))
    if i < 0:
        x = x[-i:]
        i = 0
    buf[i:j] += x[: j - i] * gain


def db(v):
    return 10 ** (v / 20)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def lp(x, f, order=2):
    sos = signal.butter(order, f, "lowpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def hp(x, f, order=2):
    sos = signal.butter(order, f, "highpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def env_exp(length, decay, attack=0.002):
    t = np.arange(n(length)) / SR
    e = np.exp(-t / decay)
    a = np.minimum(1, t / max(attack, 1e-4))
    return e * a


def reverb(x, size=1.8, mix=0.35, damp=5000):
    """Stereo convolution reverb from decaying, damped noise."""
    t = np.arange(n(size)) / SR
    ir = np.stack([rng.normal(0, 1, len(t)), rng.normal(0, 1, len(t))], 1) * np.exp(-t / (size / 6.5))[:, None]
    ir = lp(ir, damp)
    ir /= np.sqrt((ir ** 2).sum(0, keepdims=True))
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c]) for c in range(2)], 1)
    out = np.zeros_like(wet)
    out[: len(x)] += x * (1 - mix)
    out += wet * mix
    return out


# ------------------------------------------------------------------------------------------ voices

def impact(big=1.0):
    L = 2.6
    t = np.arange(n(L)) / SR
    f = 38 + 70 * np.exp(-t / 0.09)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    body = lp(rng.normal(0, 1, len(t)), 900) * np.exp(-t / 0.12) * 0.9
    crack = hp(rng.normal(0, 1, len(t)), 2500) * np.exp(-t / 0.018) * 0.6
    x = sub * 1.0 + body + crack
    x = np.tanh(x * 1.4 * big) / 1.1
    return reverb(x, 2.2, 0.30)


def whoosh(dur=0.55, up=True):
    t = np.arange(n(dur)) / SR
    x = rng.normal(0, 1, len(t))
    # sweeping band: filter in short blocks
    out = np.zeros_like(x)
    blk = 512
    zi = None
    for i in range(0, len(x), blk):
        u = i / len(x)
        fc = 250 * (14 ** (u if up else 1 - u)) if up else 3000 * (0.1 ** u)
        fc = float(np.clip(fc, 120, 9000))
        sos = signal.butter(2, [fc * 0.6, min(fc * 1.7, 20000)], "bandpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    pan = np.linspace(-0.7, 0.7, len(t))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    y = out * shape
    return reverb(np.stack([y * l, y * r], 1) * 1.4, 1.0, 0.25)


def riser(dur=1.4):
    t = np.arange(n(dur)) / SR
    u = t / dur
    noise = rng.normal(0, 1, len(t))
    x = np.zeros_like(noise)
    blk = 512
    zi = None
    for i in range(0, len(t), blk):
        fc = 400 + 7000 * (i / len(t)) ** 2
        sos = signal.butter(2, fc, "highpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        x[i:i + blk], zi = signal.sosfilt(sos, noise[i:i + blk], zi=zi)
    tone = np.sin(2 * np.pi * np.cumsum(180 + 620 * u ** 2) / SR) * 0.25
    y = (lp(x, 9000) * 0.35 + tone) * u ** 2.6
    y[-n(0.01):] *= np.linspace(1, 0, n(0.01))
    return reverb(y, 1.2, 0.3)


def kick(level=1.0):
    t = np.arange(n(0.35)) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    x += hp(rng.normal(0, 1, len(t)), 3000) * np.exp(-t / 0.004) * 0.25
    return np.tanh(x * 1.6) * level


def hat(open_=False):
    t = np.arange(n(0.18 if open_ else 0.05)) / SR
    x = hp(rng.normal(0, 1, len(t)), 7000) * np.exp(-t / (0.05 if open_ else 0.012))
    return x * 0.35


def snare():
    t = np.arange(n(0.4)) / SR
    x = bp(rng.normal(0, 1, len(t)), 900, 7000) * np.exp(-t / 0.07)
    x += np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.5
    return reverb(x * 0.7, 1.4, 0.35)


def tick():
    """Short metallic click on montage cuts (camera-shutter-like)."""
    t = np.arange(n(0.09)) / SR
    x = bp(rng.normal(0, 1, len(t)), 3500, 9000) * np.exp(-t / 0.008)
    x += np.sin(2 * np.pi * 2793 * t) * np.exp(-t / 0.02) * 0.25
    return reverb(x, 0.6, 0.25)


def blip(f=2400):
    t = np.arange(n(0.035)) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t / 0.008) * 0.6


def shimmer(dur=2.6):
    t = np.arange(n(dur)) / SR
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d) * a
            for f, d, a in [(1318.5, 1.4, 0.4), (1975.5, 1.0, 0.3), (2637, 0.8, 0.22), (3951, 0.5, 0.15), (2217.5, 1.2, 0.18)])
    return reverb(x * np.minimum(1, t / 0.01), 2.5, 0.45, 9000)


def saw(freq, length, detune=0.0):
    t = np.arange(n(length)) / SR
    ph = (freq * (1 + detune) * t) % 1.0
    return 2 * ph - 1


def bass_note(freq, length, cutoff=320):
    x = saw(freq, length) + saw(freq, length, 0.006) * 0.7 + np.sin(2 * np.pi * freq * np.arange(n(length)) / SR) * 0.8
    x = lp(x, cutoff, 2)
    e = env_exp(length, length * 0.55, 0.004)
    return np.tanh(x * e * 1.3) * 0.8


def pad(chord, length, cutoff=900):
    t = np.arange(n(length)) / SR
    x = np.zeros(len(t))
    for f in chord:
        for dt in (-0.004, 0.0, 0.005):
            x += saw(f, length, dt)
    x = lp(x / (3 * len(chord)), cutoff, 2)
    e = np.minimum(1, t / 1.2) * np.minimum(1, (length - t) / 1.0)
    return np.stack([x * e, np.roll(x, n(0.011)) * e], 1)


# -------------------------------------------------------------------------------------------- score

A1, C2, D2, E1, F1, G1 = 55.0, 65.41, 73.42, 41.2, 43.65, 49.0


def build(length, cues):
    buf = np.zeros((n(length + 0.5), 2))

    # title: a low swell, blips while characters type, glitch clicks
    add(buf, 0.0, pad([A1 * 2, A1 * 3], 2.7, 400), db(-20))
    for i, t in enumerate(np.arange(0.32, 1.16, 0.062)):
        add(buf, t, blip(2200 + 300 * (i % 3)), db(-27), pan=(i % 5 - 2) * 0.2)
    for t in (0.18, 0.47, 0.83):
        add(buf, t, hp(rng.normal(0, 1, n(0.03)), 2000) * np.exp(-np.arange(n(0.03)) / SR / 0.006), db(-26))

    # impacts, whooshes, risers
    for t in cues["impact"]:
        big = 1.25 if t in (2.56, 33.04) else 1.0
        add(buf, t, impact(big), db(-4 if big > 1 else -6))
    for t in cues["whoosh"]:
        add(buf, t - 0.30, whoosh(0.6), db(-8))
    for t in (10.56, 16.64, 24.60, 28.56):
        add(buf, t - 1.4, riser(1.4), db(-16))

    # section 1 groove: 120 BPM from 2.56 to 14.0, half-time kick, 8th-note bass pulse
    beat = 0.5
    prog = [A1, A1, F1 * 2, G1 * 2]           # one chord per bar (4 beats)
    t = 2.56
    k = 0
    while t < 13.95:
        bar = int(k // 4)
        root = prog[bar % 4]
        if k % 2 == 0:
            add(buf, t, kick(), db(-8))
        for e in (0, 0.25):
            if t + e < 13.95:
                add(buf, t + e, bass_note(root, 0.24, 260 + 120 * (k % 4 == 0)), db(-12))
        if k >= 8:
            add(buf, t + 0.25, hat(), db(-20), pan=0.3)
        t += beat
        k += 1
    add(buf, 2.56, pad([A1 * 4, C2 * 2, A1 * 6], 11.6, 700), db(-21))

    # breakdown into the ghost hub (14.0-16.64): pad only
    add(buf, 13.9, pad([F1 * 4, A1 * 4, C2 * 4], 2.9, 600), db(-19))

    # section 2: 120.8 BPM from 16.64 (cuts at 24.60, 28.56 and 33.04 land on beats)
    beat = 60 / 120.8
    t = 16.64
    k = 0
    while t < 32.70:
        bar = int(k // 4)
        root = prog[bar % 4]
        breakdown = 20.60 <= t < 24.55          # dark hero + fade: no drums, long bass notes
        if not breakdown:
            add(buf, t, kick(), db(-7))
            if k % 4 in (1, 3):
                add(buf, t, snare(), db(-15))
            add(buf, t + beat / 2, hat(), db(-19), pan=0.35)
            add(buf, t + beat / 2, bass_note(root, beat * 0.48), db(-12))
        if k % 2 == 0:
            add(buf, t, bass_note(root, beat * (1.9 if breakdown else 0.48), 220 if breakdown else 300),
                db(-12 if breakdown else -11))
        t += beat
        k += 1
    add(buf, 16.64, pad([A1 * 4, C2 * 2, E1 * 8], 4.2, 800), db(-21))
    add(buf, 20.60, pad([F1 * 4, A1 * 4, C2 * 4], 4.0, 520), db(-17))
    add(buf, 24.60, pad([A1 * 4, C2 * 2, E1 * 8], 8.3, 900), db(-20))

    # montage ticks
    for t in cues["tick"]:
        add(buf, t, tick(), db(-17), pan=float(rng.uniform(-0.4, 0.4)))

    # end card: shimmer and a soft low tail
    add(buf, 33.04, shimmer(), db(-14))
    add(buf, 33.04, pad([A1 * 2, A1 * 3], 1.9, 300), db(-18))

    buf = hp(buf, 26)
    end = n(length)
    fade = n(0.35)
    buf[end - fade:end] *= np.linspace(1, 0, fade)[:, None]
    return buf[:end]


def write_wav(path, x):
    x = np.clip(x / max(1e-6, np.abs(x).max()) * 0.7, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main():
    tl = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    length = tl["frames"] / tl["fps"]
    x = build(length, tl["sfx"])
    raw = out.with_suffix(".raw.wav")
    write_wav(raw, x)
    # loudness: -14 LUFS, true peak ceiling; limiter without auto-levelling
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                    "acompressor=threshold=-18dB:ratio=2:attack=10:release=180,"
                    "loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.78:level=false,"
                    f"apad,atrim=0:{length + 0.12:.3f}",
                    "-ar", str(SR), "-c:a", "pcm_s24le", str(out)], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    summ = r[r.rfind("Summary"):]
    print(" ".join(summ.split()))


if __name__ == "__main__":
    main()
