#!/usr/bin/env python3
"""Score for the Turismo transformation reel: 18.0 s, 120 BPM, hits on the reference's cut points.

Uses the voices of the project's cgi/sound.py (licence-free synthesis, no samples).

Sound map (from the VANTA reference):
- driving groove from 1.0 s;
- a riser into the wheels locking on (about 7.0 s);
- a breakdown under the dive and whip (7.7-9.0 s);
- a bigger groove with a bright layer from 9.0 s (the snow world);
- impacts on the hard cuts at 13.2, 15.2, 16.2 and 17.0 s;
- a shimmer as the logo resolves (17.3 s).

The loop restarts cleanly: the first hit at 0.0 s matches the last bar.

    python3 reel_sound.py out.wav
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cgi"))
import sound as S  # noqa: E402

LEN = 18.0
BEAT = 0.5
A1, C2, D2, E2, F1, G1 = 55.0, 65.41, 73.42, 82.41, 43.65, 49.0


def main(out):
    buf = np.zeros((S.n(LEN + 1.0), 2))
    add, db = S.add, S.db
    # 0-1 s: wheel on black: low pad + soft tick on each beat
    add(buf, 0.0, S.pad([A1 * 2, E2], 1.1, 380), db(-18))
    for t in (0.0, 0.5):
        add(buf, t, S.tick(), db(-22))
    # groove A (sunset world) 1.0-7.7
    prog = [A1, A1, F1 * 2, G1 * 2]
    t, k = 1.0, 0
    while t < 7.69:
        root = prog[(k // 4) % 4]
        add(buf, t, S.kick(), db(-7))
        add(buf, t + 0.25, S.hat(), db(-18), pan=0.3)
        if k % 2 == 1:
            add(buf, t, S.snare(), db(-15))
        add(buf, t, S.bass_note(root, 0.23, 300), db(-11))
        add(buf, t + 0.25, S.bass_note(root, 0.23, 260), db(-13))
        t += BEAT
        k += 1
    add(buf, 1.0, S.impact(), db(-8))
    add(buf, 1.0, S.pad([A1 * 4, C2 * 2, E2 * 2], 6.7, 700), db(-21))
    # wheels fly in and lock (3-7 s): whooshes, then a riser into the lock
    for t in (3.2, 4.4):
        add(buf, t, S.whoosh(0.7), db(-12))
    add(buf, 7.0 - 1.4, S.riser(1.4), db(-14))
    add(buf, 7.0, S.impact(0.8), db(-9))
    # breakdown: dive + whip (7.7-9.0)
    add(buf, 7.7, S.whoosh(0.9), db(-8))
    add(buf, 8.2, S.riser(0.8), db(-13))
    # groove B (snow world) 9.0-17.0, brighter
    add(buf, 9.0, S.impact(1.2), db(-5))
    t, k = 9.0, 0
    while t < 16.99:
        root = prog[(k // 4) % 4]
        add(buf, t, S.kick(), db(-7))
        add(buf, t + 0.25, S.hat(), db(-17), pan=-0.3)
        add(buf, t + 0.125, S.hat(), db(-24), pan=0.4)
        if k % 2 == 1:
            add(buf, t, S.snare(), db(-14))
        add(buf, t, S.bass_note(root, 0.23, 320), db(-11))
        add(buf, t + 0.25, S.bass_note(root, 0.23, 280), db(-13))
        t += BEAT
        k += 1
    add(buf, 9.0, S.pad([A1 * 8, C2 * 4, E2 * 4], 8.0, 2400), db(-23))
    for t in (13.2, 15.2, 16.2):
        add(buf, t, S.impact(0.8), db(-11))
        add(buf, t, S.tick(), db(-16))
    # end: wheel on black and logo
    add(buf, 17.0, S.impact(1.1), db(-7))
    add(buf, 17.3, S.shimmer(1.5), db(-15))
    add(buf, 17.0, S.pad([A1 * 2, E2], 1.0, 380), db(-17))

    buf = S.hp(buf, 26)[: S.n(LEN)]
    fade = S.n(0.08)
    buf[-fade:] *= np.linspace(1, 0, fade)[:, None]
    raw = Path(out).with_suffix(".raw.wav")
    S.write_wav(raw, buf)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                    "acompressor=threshold=-18dB:ratio=2:attack=10:release=180,"
                    "loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.78:level=false,"
                    f"apad,atrim=0:{LEN + 0.1:.2f}", "-ar", "48000", "-c:a", "pcm_s24le", str(out)], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    print(" ".join(r[r.rfind("Summary"):].split()))


if __name__ == "__main__":
    main(sys.argv[1])
