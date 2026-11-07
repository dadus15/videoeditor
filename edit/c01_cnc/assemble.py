#!/usr/bin/env python3
"""Assemble the Turismo Forged C01 film (9:16, 24 fps, no music, no on-screen text).

Usage (from the project root):
    python3 edit/c01_cnc/assemble.py <clips_dir> <out.mov>

Writes a high-quality intermediate with audio; edit/c01_cnc/build.sh then adds the brand intro
(bookends.py from the youtube-edit skill) and makes the delivery encode.
Cut list and audio levels live in CUTS / BED below.
"""
import json
import subprocess
import sys
from pathlib import Path

W, H, FPS = 1080, 1920, 24

# (clip, source in, source out, audio LUFS / None = silence / "bed" = V8 bed, dissolve into this cut in s)
CUTS = [
    ("s1.mp4", 0.0, 4.5, -13.0, 0),           # billet drops into the chuck (impact 1.64 s)
    ("s2.mp4", 0.0, 6.5, -13.0, 0),           # milling along the spokes
    ("s3.mp4", 0.5, 4.0, -14.0, 0),           # pull-back, machine reveal
    ("m_lift2.mp4", 0.1, 1.9, -16.0, 0),      # craftsman lifts the raw wheel out (no cap yet)
    ("m_carry2.mp4", 0.4, 4.4, -16.0, 0),     # carries it to his bench, sets it on the stand
    ("b_macro.mp4", 0.3, 3.8, -15.0, 0),      # brushing, macro: the grain appears behind the pad
    ("b_lathe.mp4", 1.0, 3.5, -15.0, 0),      # brushing on the lathe, dust plume in the light
    ("b_air.mp4", 0.5, 4.5, -16.0, 0),        # dust blown off, light sweep shows the satin grain
    ("m_paint2.mp4", 0.3, 4.8, -15.0, 0),     # paint booth, deep black
    (None, 0.0, 0.5, None, 0),                # hard cut: black + silence
    ("car_arc.mp4", 0.3, 3.8, "bed", 0),      # CLS 63: arc around the front
    ("car_wheelslide_cap.mp4", 0.6, 3.1, "bed", 0.25),   # *_cap: Turismo cap composited (cap_overlay.py)
    ("car_side_cap.mp4", 0.8, 3.8, "bed", 0.25),
    ("car_wheelpush_cap.mp4", 1.2, 3.7, "bed", 0.25),
    ("car_hero.mp4", 0.8, 4.8, "bed", 0.25),  # final pull-back
]

# V8 idle under the whole car section: the approved idle from the first cut, looped seamlessly.
BED = {"clip": "s6.mp4", "in": 2.2, "out": 4.9, "lufs": -20.0, "xfade": 0.7, "fade_out": 0.8}


def run(cmd):
    print(" ".join(str(c) for c in cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def measure_lufs(src, start, dur):
    """Integrated loudness (LUFS) of a clip section."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{start}", "-t", f"{dur}", "-i", str(src),
                          "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    lines = [l for l in res.stderr.splitlines() if l.strip().startswith("I:")]
    return float(lines[-1].split()[1])


def main(clips, out):
    clips, out = Path(clips), Path(out)
    work = Path("work") / out.stem
    work.mkdir(parents=True, exist_ok=True)
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
          f"fps={FPS},setsar=1,format=yuv420p")
    enc = ["-c:v", "libx264", "-crf", "10", "-preset", "fast", "-pix_fmt", "yuv420p"]

    # 1) Video segments and the timeline (a dissolve overlaps the previous cut).
    vids, timeline, t = [], [], 0.0
    for i, (clip, a, b, _, xf) in enumerate(CUTS):
        nfr = round((b - a) * FPS)            # whole frames, so the cut points stay exact
        dur = nfr / FPS
        seg = work / f"v{i:02d}.mp4"
        if clip is None:
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={dur + 1}",
                 "-frames:v", str(nfr), *enc, str(seg)])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a}", "-i", str(clips / clip),
                 "-an", "-vf", vf, "-frames:v", str(nfr), *enc, str(seg)])
        start = t - xf
        timeline.append({"cut": i, "clip": clip, "in": a, "out": round(a + dur, 4), "start": round(start, 4),
                         "end": round(start + dur, 4), "dissolve": xf})
        vids.append(seg)
        t = start + dur
    total = t

    # 2) Join: hard cuts with concat, dissolves with xfade (chained in order).
    inputs, fc, last, acc = [], [], None, 0.0
    for i, seg in enumerate(vids):
        inputs += ["-i", str(seg)]
        fc.append(f"[{i}:v]settb=1/{FPS},setpts=N,format=yuv420p[s{i}]")
    for i, seg in enumerate(vids):
        dur, xf = timeline[i]["end"] - timeline[i]["start"], CUTS[i][4]
        if last is None:
            last, acc = f"s{i}", dur
            continue
        lbl = f"j{i}"
        if xf > 0:
            fc.append(f"[{last}][s{i}]xfade=transition=fade:duration={xf}:offset={acc - xf:.4f}[{lbl}]")
            acc += dur - xf
        else:
            fc.append(f"[{last}][s{i}]concat=n=2:v=1:a=0,settb=1/{FPS},setpts=N[{lbl}]")
            acc += dur
        last = lbl
    grade = ("colorbalance=rs=-0.03:bs=0.04:rm=-0.02:bm=0.03:rh=-0.01:bh=0.02,"
             "eq=saturation=0.82:contrast=1.04,noise=alls=3:allf=t,format=yuv420p")
    fc.append(f"[{last}]{grade}[v]")
    video = work / "video.mp4"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]",
         "-r", str(FPS), *enc, str(video)])

    # 3) Audio: each cut's own sound at a fixed loudness, silence where the brief wants it,
    #    and the looped V8 bed under the car section.
    pieces = []
    for i, (clip, a, b, lufs, _) in enumerate(CUTS):
        if lufs == "bed":
            continue
        dur = timeline[i]["end"] - timeline[i]["start"]
        wav = work / f"a{i:02d}.wav"
        if lufs is None:
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                 "-t", f"{dur}", str(wav)])
        else:
            src = clips / clip
            gain = lufs - measure_lufs(src, a, dur)
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a}", "-t", f"{dur}", "-i", str(src), "-vn",
                 "-af", f"aresample=48000,aformat=channel_layouts=stereo,volume={gain:.2f}dB,"
                        f"apad,atrim=0:{dur},afade=t=in:d=0.01,afade=t=out:st={dur - 0.02}:d=0.02",
                 str(wav)])
        pieces.append(wav)
    bed_start = next(c["start"] for c in timeline if CUTS[c["cut"]][3] == "bed")
    bed_len = total - bed_start
    seg_len = BED["out"] - BED["in"]
    reps = 1
    while reps * seg_len - (reps - 1) * BED["xfade"] < bed_len + 0.2:
        reps += 1
    src = clips / BED["clip"]
    gain = BED["lufs"] - measure_lufs(src, BED["in"], seg_len)
    one = work / "bed_one.wav"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{BED['in']}", "-t", f"{seg_len}", "-i", str(src), "-vn",
         "-af", f"aresample=48000,aformat=channel_layouts=stereo,volume={gain:.2f}dB", str(one)])
    bin_ = sum((["-i", str(one)] for _ in range(reps)), [])
    chain, lastb = [], "0:a"
    for r in range(1, reps):
        chain.append(f"[{lastb}][{r}:a]acrossfade=d={BED['xfade']}:c1=qsin:c2=qsin[b{r}]")
        lastb = f"b{r}"
    chain.append(f"[{lastb}]atrim=0:{bed_len},afade=t=in:d=0.01,"
                 f"afade=t=out:st={bed_len - BED['fade_out']}:d={BED['fade_out']}[bed]")
    bed = work / "bed.wav"
    run(["ffmpeg", "-y", "-v", "error", *bin_, "-filter_complex", ";".join(chain), "-map", "[bed]", str(bed)])
    pieces.append(bed)
    lst = work / "audio.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in pieces))
    audio = work / "audio.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-af", f"highpass=f=24,apad,atrim=0:{total}", str(audio)])

    # 4) Mux the intermediate (audio is limited in the final step, after the intro is added).
    run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "pcm_s16le", "-t", f"{total}", str(out)])
    meta = {"duration": round(total, 3), "fps": FPS, "size": [W, H], "cuts": timeline,
            "car_bed": {"start": round(bed_start, 3), **BED}}
    out.with_suffix(".timeline.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"wrote {out} ({total:.2f} s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
