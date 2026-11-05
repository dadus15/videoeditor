#!/usr/bin/env python3
"""Score v7 for the Turismo transformation reel, on the sound map measured in ANALIZA_ORYGINALU.md (section 9).

18.0 s, 120 BPM, beat grid on x.30 / x.80 so the packshot cuts (13.30, 15.30) land on the beat.
  0.0-0.2   silence
  0.2-1.04  intro without bass: pad and a high lead (about 1.46 kHz) in eighths
  1.04      bass drop on the match cut (impact + sub)
  1.3-7.6   groove: kick, snare on 2 and 4, hats, bass and lead in eighths; whooshes 1.6-2.1 and 2.7-3.0
  7.6-8.3   break: bass and lead cut to zero under the dive, only hats and a riser
  8.4-9.3   stutter: chopped lead in sixteenths, bass hits 8.4 and 8.8, whoosh 8.7-9.3
  9.4       full drop: the snow world comes in with the whole groove
  13.30 / 15.30 / 16.22  hits under the packshot cuts
  17.0      hard stop; only the reverb tail stays (loop to frame 0)

Licence-free synthesis with the voices of cgi/sound.py.

    python3 reel_sound_v7.py out.wav
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cgi"))
import sound as S  # noqa: E402

LEN = 18.0
BEAT = 0.5
GRID0 = 0.30
A1, C2, E2, F1, G1 = 55.0, 65.41, 82.41, 43.65, 49.0
LEAD = [1468.0, 1100.0, 1234.7, 1100.0, 1468.0, 1648.0, 1234.7, 1100.0]


def lead(f, dur=0.14):
    t = np.arange(S.n(dur)) / S.SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * S.saw(f, dur) * np.exp(-t / 0.03)
    return S.lp(x, 4200) * np.exp(-t / 0.06) * 0.5


def groove(buf, t0, t1, bright=False):
    prog = [A1, A1, F1 * 2, G1 * 2]
    t, k = t0, 0
    while t < t1 - 1e-6:
        root = prog[(k // 4) % 4]
        S.add(buf, t, S.kick(), S.db(-7))
        S.add(buf, t + 0.25, S.hat(), S.db(-17), pan=0.3)
        if bright:
            S.add(buf, t + 0.125, S.hat(), S.db(-24), pan=-0.4)
            S.add(buf, t + 0.375, S.hat(), S.db(-24), pan=0.4)
        if k % 2 == 1:
            S.add(buf, t, S.snare(), S.db(-14))
        S.add(buf, t, S.bass_note(root, 0.23, 320 if bright else 300), S.db(-11))
        S.add(buf, t + 0.25, S.bass_note(root, 0.23, 280 if bright else 260), S.db(-13))
        for j in range(2):
            S.add(buf, t + 0.25 * j, lead(LEAD[(2 * k + j) % 8]), S.db(-21 if bright else -23), pan=0.2 * (-1) ** j)
        t += BEAT
        k += 1


def main(out):
    buf = np.zeros((S.n(LEN + 3.0), 2))
    add, db = S.add, S.db
    # intro 0.2-1.04: pad + lead, no bass
    add(buf, 0.2, S.pad([A1 * 4, C2 * 2, E2 * 2], 0.95, 900), db(-20))
    for j, t in enumerate(np.arange(GRID0, 1.04, 0.25)):
        add(buf, t, lead(LEAD[j % 8]), db(-24))
    add(buf, GRID0, S.tick(), db(-24))
    add(buf, 0.80, S.tick(), db(-24))
    # 1.04 bass drop on the match cut
    add(buf, 1.04, S.impact(1.3), db(-5))
    add(buf, 1.04, S.bass_note(A1, 0.26, 340), db(-8))
    add(buf, 1.04, S.pad([A1 * 4, C2 * 2, E2 * 2], 6.5, 700), db(-22))
    groove(buf, GRID0 + 2 * BEAT, 7.6)
    add(buf, 1.6, S.whoosh(0.5), db(-11))
    add(buf, 2.7, S.whoosh(0.32), db(-12))
    add(buf, 3.05, S.whoosh(0.45, up=False), db(-16))          # the new bonnet drops in
    add(buf, 6.30, S.impact(0.6), db(-17))                     # it seats
    # 7.6-8.3 break: hats only + riser into the paint
    for t in np.arange(7.80, 8.3, 0.25):
        add(buf, t, S.hat(), db(-20))
    add(buf, 7.6, S.riser(0.8), db(-11))
    # 8.4-9.3 stutter
    for t in (8.4, 8.8):
        add(buf, t, S.kick(), db(-6))
        add(buf, t, S.bass_note(A1, 0.18, 340), db(-10))
    for j, t in enumerate(np.arange(8.4, 9.3, 0.0625)):
        if j % 2 == 0:
            add(buf, t, lead(LEAD[(j // 2) % 4], 0.05), db(-20), pan=0.3 * (-1) ** j)
    add(buf, 8.7, S.whoosh(0.6), db(-9))
    # 9.4 full drop: snow world
    add(buf, 9.4, S.impact(1.2), db(-5))
    groove(buf, 9.30, 17.0, bright=True)
    add(buf, 9.4, S.pad([A1 * 8, C2 * 4, E2 * 4], 7.6, 2400), db(-23))
    for t in (13.30, 15.30, 16.22):
        add(buf, t, S.impact(0.8), db(-11))
        add(buf, t, S.tick(), db(-16))
    # 17.0 hard stop, keep only a reverb tail of the last beat
    i = S.n(17.0)
    tail = S.reverb(buf[i - S.n(0.25):i].mean(1) * np.linspace(0.3, 1, S.n(0.25)), 2.4, 1.0)
    buf[i:] = 0
    add(buf, 17.0, tail, db(-8))
    add(buf, 17.3, S.shimmer(1.4), db(-22))

    buf = S.hp(buf, 26)[: S.n(LEN)]
    buf[:S.n(0.2)] = 0
    fade = S.n(0.05)
    buf[-fade:] *= np.linspace(1, 0, fade)[:, None]
    raw = Path(out).with_suffix(".raw.wav")
    S.write_wav(raw, buf)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                    "acompressor=threshold=-18dB:ratio=2:attack=10:release=180,"
                    "loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.78:level=false,"
                    f"apad,atrim=0:{LEN:.2f}", "-ar", "48000", "-c:a", "pcm_s24le", str(out)], check=True)
    raw.unlink()
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
