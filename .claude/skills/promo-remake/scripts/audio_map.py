#!/usr/bin/env python3
"""Sound map of a reference: onsets, tempo estimate, RMS per second.   python3 audio_map.py ref.mp4"""
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np


def main(path):
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "22050", str(wav)], check=True)
        w = wave.open(str(wav))
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    sr, hop, n = 22050, 256, 1024
    frames = np.array([x[i:i + n] * np.hanning(n) for i in range(0, len(x) - n, hop)])
    S = np.abs(np.fft.rfft(frames, axis=1))
    flux = np.maximum(0, np.diff(np.log1p(S), axis=0)).sum(1)
    t = np.arange(len(flux)) * hop / sr
    thr = np.convolve(flux, np.ones(40) / 40, "same") * 1.6
    on = [t[i] for i in range(1, len(flux) - 1) if flux[i] > thr[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
    dedup = []
    for v in on:
        if not dedup or v - dedup[-1] > 0.12:
            dedup.append(v)
    print(f"onsets ({len(dedup)}):", " ".join(f"{v:.2f}" for v in dedup))
    f = flux - flux.mean()
    ac = np.correlate(f, f, "full")[len(f) - 1:]
    fps = sr / hop
    lags = np.arange(int(fps * 60 / 180), int(fps * 60 / 70))
    print("tempo estimate (BPM):", round(60 * fps / lags[np.argmax(ac[lags])], 1))
    print("RMS dBFS per second:")
    for s in range(int(len(x) / sr)):
        seg = x[s * sr:(s + 1) * sr]
        print(f"  {s:3d}s {20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9):6.1f}")


if __name__ == "__main__":
    main(sys.argv[1])
