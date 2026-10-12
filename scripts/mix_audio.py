#!/usr/bin/env python3
"""Mix music + SFX to the cue points of a rendered edit, then check loudness, peaks and phone playback.

Expects files in assets/audio/ (names are slots, see AUDIO_REQUEST.md):
  music.wav          Epidemic Sound track or track edit (required)
  sfx_impact.wav     short low impact on frame 1 (also reused, quieter, under the signature shot)
  sfx_riser.wav      short build that ENDS on the reveal cut
  sfx_subdrop.wav    deep sub accent on the reveal cut
  sfx_shimmer.wav    quiet metallic/glass texture under the TURISMO lettering (optional)

Usage:
  python3 scripts/mix_audio.py renders/X.timeline.json out.wav --music-drop 12.34 [--music-start 0]
    --music-drop  time (s) inside music.wav of the drop/bass entrance; it is placed on the reveal cut.
                  For an Epidemic track edit made with requiredRegionsAtOffsets at the reveal, pass the reveal time.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = Path(os.environ.get("AUDIO_DIR", ROOT / "assets/audio"))


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("out")
    ap.add_argument("--music-drop", type=float, required=True)
    ap.add_argument("--music-gain", type=float, default=0.0, help="dB")
    ap.add_argument("--target-lufs", type=float, default=-14.0)
    args = ap.parse_args()

    tl = json.loads(Path(args.timeline).read_text())
    T = tl["duration"]
    reveal = tl["cue_points"]["riser_end_reveal"]
    sig = tl["cue_points"]["signature"]
    shimmer_at = tl["shots"][1]["start"]
    mstart = args.music_drop - reveal
    if mstart < 0:
        sys.exit(f"music drop at {args.music_drop}s is earlier than the reveal ({reveal}s); pick a later drop or an edit")

    inputs, chains, labels = [], [], []

    def add(path, chain, label):
        inputs.extend(["-i", str(path)])
        chains.append(f"[{len(inputs) // 2 - 1}:a]{chain}[{label}]")
        labels.append(f"[{label}]")

    # Music: drop on the reveal, short fade-in to avoid a click, tail shaped so the loop
    # restarts into the opening impact instead of a hard stop.
    add(A / "music.wav",
        f"atrim=start={mstart:.4f}:duration={T:.4f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
        f"volume={args.music_gain}dB,afade=t=in:d=0.012,afade=t=out:st={T - 0.55:.3f}:d=0.55:curve=qsin", "mus")
    if (A / "sfx_impact.wav").exists():
        add(A / "sfx_impact.wav", "aformat=sample_rates=48000:channel_layouts=stereo,volume=-5dB,afade=t=in:d=0.004", "imp")
        add(A / "sfx_impact.wav", f"aformat=sample_rates=48000:channel_layouts=stereo,volume=-15dB,"
                                  f"adelay={int(sig * 1000)}|{int(sig * 1000)}", "imp2")
    if (A / "sfx_riser.wav").exists():
        rd = dur(A / "sfx_riser.wav")
        st = max(0.0, reveal - rd)
        add(A / "sfx_riser.wav", f"aformat=sample_rates=48000:channel_layouts=stereo,volume=-9dB,"
                                 f"atrim=start={max(0, rd - reveal):.3f},adelay={int(st * 1000)}|{int(st * 1000)}", "ris")
    if (A / "sfx_subdrop.wav").exists():
        add(A / "sfx_subdrop.wav", f"aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=28,volume=-8dB,"
                                   f"adelay={int(reveal * 1000)}|{int(reveal * 1000)}", "sub")
    if (A / "sfx_shimmer.wav").exists():
        add(A / "sfx_shimmer.wav", f"aformat=sample_rates=48000:channel_layouts=stereo,atrim=duration=2.2,volume=-22dB,"
                                   f"afade=t=in:d=0.25,afade=t=out:st=1.4:d=0.8,"
                                   f"adelay={int(shimmer_at * 1000)}|{int(shimmer_at * 1000)}", "shm")

    fc = ";".join(chains) + ";" + "".join(labels) + \
        f"amix=inputs={len(labels)}:normalize=0:duration=first,highpass=f=24," \
        f"acompressor=threshold=-14dB:ratio=2:attack=15:release=180:makeup=1," \
        f"loudnorm=I={args.target_lufs}:TP=-1.5:LRA=9,aresample=48000,alimiter=limit=0.80:attack=3:release=60:level=false,atrim=duration={T:.4f}[out]"
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-c:a", "pcm_s24le", args.out]
    subprocess.run(cmd, check=True)
    report(args.out)


def report(path):
    def ebu(extra=""):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"{extra}ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        tail = r[r.rfind("Summary"):]
        get = lambda k: tail.split(k)[1].split()[0]
        return float(get("I:")), float(get("Peak:"))
    i, tp = ebu()
    i_phone, _ = ebu("highpass=f=300,highpass=f=300,lowpass=f=9000,")  # crude phone-speaker band
    i_low, _ = ebu("lowpass=f=120,lowpass=f=120,")
    print(f"integrated {i:.1f} LUFS | true peak {tp:.1f} dBTP | phone-band {i_phone:.1f} LUFS "
          f"(drop {i - i_phone:.1f} dB) | <120 Hz {i_low:.1f} LUFS")
    if tp > -1.0:
        print("WARNING: true peak above -1 dBTP")
    if i - i_phone > 9:
        print("WARNING: mix relies on sub-bass; phone speakers will sound thin - reduce low end / sub drop")


if __name__ == "__main__":
    main()
