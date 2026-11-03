# Reverse engineering a reference promo

Goal: a shot map precise to about one frame (25 fps), plus the typography spec and the sound map, before any creative work.

## 1. Probe and clean up

```bash
ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames:format=duration -of default=nw=1 ref.mp4
```

- **Phone recordings of a laptop or TV** (the usual WhatsApp case):
  - The picture is a trapezoid inside the room, and the frame rate is variable (about 60 fps).
  - The player UI shows on top: play/pause icon, progress bar, red corner badge.
  - The audio is the laptop speakers through the phone mic, often around −37 LUFS.

  None of that belongs to the film. Note it so you don't copy it.
- **The source may start mid-animation.** Here the title was already half typed at 0.00 s. Rebuild the full
  animation, finishing at the same moment.

## 2. Contact sheets with timecodes

`scripts/ref_sheets.sh ref.mp4 outdir` writes:

- a 2 fps overview, one sheet per 10 s,
- 10 fps sheets you request around suspected cuts (`mk START DUR`),
- full-resolution crops of the title and end card.

Read every sheet. For each shot, write down:

- start and end time,
- framing (macro, 3/4, front, lying flat, line-up),
- camera move (push, truck, orbit, roll/whip, turntable),
- finish or colour,
- transition (hard cut, fade from or to white, whip with motion blur, dissolve, flash).

## 3. Brightness and motion trace

`python3 .claude/skills/youtube-edit/scripts/analyze_motion.py ref.mp4 motion.csv` (needs opencv) gives per-frame luma, diff and dx. Bucket it per 0.1 s:

- **Fades to and from white:** luma ramps over 0.3–1.6 s.
- **Hard cuts:** a single-frame diff spike of 20 or more.
- **Montage:** spikes every 0.1–0.5 s.
- **Whips:** a sustained high diff, and dx swings sign.

## 4. Typography

Crop the title and end card at full resolution, then upscale 3×. Typical premium-wheel layout (Vossen HF):

- **Label:** a small red box with letter-spaced white caps ("VOSSEN'S ALL-NEW", "AVAILABLE IN").
- **Bar:** a dark navy bar with three words, solid / outline / solid, in a wide heavy grotesk
  ("HYBRID FORGED SERIES", "6 EXCLUSIVE FINISHES").
- **Frame:** thin corner brackets at top-right and bottom-left, and a tiny brand mark under the bar's right end.
- **Animation:** the bar wipes open from the centre, the characters type on behind a block cursor, dark glitch
  blocks flicker, and the label box grows from the left.
- **End card:** a faint blue line drawing of the wheel behind it, top-cropped.

Map the layout onto the client's brand. For Turismo:

| Reference | Turismo |
|---|---|
| Red label | Red `#C7222A` |
| Dark bar | Navy `#0A1B2B` |
| Typeface | Orbitron, closest to the TURISMO wordmark |
| Small mark | GT logo artwork |

## 5. Sound map

`python3 scripts/audio_map.py ref.mp4` prints loudness, onsets, a BPM estimate and RMS per second.
`ffmpeg -i ref.mp4 -lavfi showspectrumpic=s=1600x500:legend=1:scale=log spec.png` shows the structure: tall
broadband columns are impacts, sweeps are whooshes and risers, and quiet bands are breakdowns under the white fades.
Write down:

- where impacts land (section cuts),
- the montage tick grid (0.25 s here, so 120 BPM eighths),
- the breakdowns.

Rebuild the score to the same map, licence-free, with `sound.py`. Never reuse the reference audio.

## 6. Shot map table (output of this phase)

| Time | Reference | Rebuild |
|---|---|---|
| 0.00–2.56 | Title card | Our title, same animation |
| 2.56–4.80 | Line-up of 6 finishes whips in, fades to white | ... |

Keep it in the project README. `post.py` `TIMELINE` and the Higgsfield segment plan are derived from it.
