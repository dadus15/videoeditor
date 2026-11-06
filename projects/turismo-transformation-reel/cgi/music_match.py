"""Rank licensable tracks by similarity to the reference soundtrack (see MUSIC.md).

Input: tracks.json, {pathname: [genre, title, bpm, seconds, artists, preview_mp3_url]}. Build it from Epidemic
Sound genre pages: the track list is embedded in the page HTML.
Reference: the reference video's soundtrack, 1.2-17 s.
Score: timbre (mean mel spectrum) 35 %, chroma 25 %, tempo 25 %, cowbell peak around 1.46 kHz 15 %.
Each track is also tested slowed x0.92, x0.85 and x0.8, because the reference is a slowed edit.

    python3 music_match.py ref.mp4          # needs librosa
"""
import json
import os
import subprocess
import sys

import librosa
import numpy as np

tracks = json.load(open("tracks.json"))
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def feats(y, sr):
    oenv = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=oenv, sr=sr))[0])
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(1)
    key = max((np.corrcoef(np.roll(p, k), chroma)[0, 1], NOTES[k] + (" min" if p is MIN else " maj"))
              for p in (MAJ, MIN) for k in range(12))[1]
    mel = librosa.power_to_db(librosa.feature.melspectrogram(y=y, sr=sr, n_mels=64)).mean(1)
    S = np.abs(librosa.stft(y))
    fr = librosa.fft_frequencies(sr=sr)

    def band(a, b):
        return S[(fr >= a) & (fr < b)].mean()
    cow = band(1300, 1650) / (band(900, 1300) + band(1650, 2200) + 1e-9) * 2
    return dict(tempo=tempo, key=key, chroma=chroma / (np.linalg.norm(chroma) + 1e-9), mel=mel - mel.mean(), cow=cow)


subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", sys.argv[1], "-ss", "1.2", "-t", "15.8", "-ac", "1",
                "-ar", "22050", "ref.wav"], check=True)
y, sr = librosa.load("ref.wav", sr=22050)
R = feats(y, sr)
print("REF tempo %.1f key %s" % (R["tempo"], R["key"]))
res = []
for p, (g, t, b, d, a, u) in tracks.items():
    fn = "prev_" + p.strip("/").split("/")[-1] + ".mp3"
    if not os.path.exists(fn):
        subprocess.run(["curl", "-sf", "-o", fn, u])
    try:
        y, sr = librosa.load(fn, sr=22050, offset=30, duration=30)
    except Exception:
        continue
    best = None
    for rate in (1.0, 0.92, 0.85, 0.8):
        yy = librosa.resample(y, orig_sr=sr, target_sr=int(sr / rate)) if rate != 1.0 else y
        F = feats(yy, sr)
        tsim = max(1 - abs(F["tempo"] * k - R["tempo"]) / R["tempo"] for k in (0.5, 1, 2))
        csim = float(np.dot(F["chroma"], R["chroma"]))
        msim = float(np.corrcoef(F["mel"], R["mel"])[0, 1])
        score = 0.35 * msim + 0.25 * csim + 0.25 * max(tsim, 0) + 0.15 * min(F["cow"] / R["cow"], R["cow"] / F["cow"])
        if best is None or score > best[0]:
            best = (score, rate, F["tempo"], F["key"])
    res.append((best, t, a, p))
res.sort(key=lambda r: -r[0][0])
for (s, rate, tp, k), t, a, p in res[:12]:
    print(f"{s:.3f} {t[:34]:34s} {a[:22]:22s} x{rate}: {tp:5.1f} BPM {k:8s} https://www.epidemicsound.com{p}")
