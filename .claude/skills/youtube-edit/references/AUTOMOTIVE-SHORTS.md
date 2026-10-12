---
name: youtube-edit-automotive-shorts
description: "Playbook for short vertical product and automotive films (Reels, TikTok, Shorts): source forensics, framing, transitions, brand bookends, audio, QC and gotchas. Learned on the Audi S8 D4 × Turismo Wheels Inventa project, approved by the client."
---

# Automotive and product shorts: playbook

Reference project: *Audi S8 D4 × Turismo Wheels Inventa* (October 2026). It was a 42.6 s, 448×368 WhatsApp copy of a screen-captured YouTube video, and became a 22.96 s, 1080×1920, 25 fps short with a brand intro and an end card. The client's verdict was "excellent". Everything below was used in that project and is reproducible from `templates/edl_automotive_example.json`.

## 1. Source forensics (before any creative decision)

| Check | How | What we found / why it matters |
|---|---|---|
| Letterbox per shot | `cropdetect` on each shot's time range. Over the whole file it reported "no bars" because the player UI at the end filled the frame | Picture 448×268 at rows 50–318; player-zoomed segments use rows 18–336 |
| Player overlays | Look at full-resolution frames and grids; check the black bars too | A message in the top bar (~9.6–11.2 s), faint "1.7x/1.8x" speed badges at the top centre of zoomed segments, and a "COMING SOON" end card with the full player UI |
| Baked cuts and fades | `scdet` + `blackdetect` + brightness trace (`analyze_motion.py`) | Every shot fades from or to black; only take the clean ranges |
| Baked music | `showspectrumpic` + `ebur128` | Continuous bass pulse and tonal lines with no ambience, so drop the source audio entirely and don't layer over it |
| True frame rate | `unique_frames.py`: count new frames per shot | A ~40 fps irregular capture of a 25 fps film, with zero dropped frames |
| Motion direction | `analyze_motion.py` (median optical-flow dx) | Pair shots by direction; the push-slide and the loop follow the opener's direction |
| Product positions | Grid-overlay stills, then confirm on a **rendered** frame | Hub positions estimated from source grids were off by about 20 px; always confirm on the output |

Make a shot map (source time, clean range, content, motion, overlays) before cutting.

## 2. Cadence: re-time film frames, don't resample time

The compositor picks "the k-th new film frame after `src_in`" for output frame k at the EDL fps (25). This removes capture jitter completely. Choosing frames by nearest timestamp at 30 fps repeated every 6th frame, which reads as judder on any camera move. Keep speed at 1.0; speed ramps on such sources judder, and frame interpolation warps spokes.

## 3. Framing system for low-resolution sources (9:16)

- **Square window** 1080×1080, centred at y=800, for detail shots (about 4× the source pixels). Used for the hook and build act.
- **Wide window** 1080×646 at the full source width (about 2.4×, the sharpest option). Used from the reveal on, so the whole car stays visible.
- **Background:** the current shot downscaled to 48 px, blurred, desaturated 45 % and scaled to about 17 % brightness, with a vertical falloff. It reads as atmosphere, not as a second picture.
- **Grade:** per-shot gamma and gain only (lift very dark shots to about 1.3 gamma). A soft shoulder above 86 % protects headlights and paint highlights. No added saturation, no noise reduction, an unsharp of 0.28 at most, and fine luma grain at 0.010 against banding.
- **Text:** DM Sans in one line below the window. Never over the product, never below y≈1450 or in the right-hand 120 px (Reels/TikTok UI).

## 4. Edit structure that worked (18 s film at 120 BPM, stored in beats)

| Beats | Role | Shot type |
|---|---|---|
| 2.5 | Hook: strongest clear wheel on frame 1, push 100→107.5 % on the moving hub, line 1 of the copy | square |
| 2 + 2.5 | Build: brand lettering, then headlight; line 2 of the copy | square |
| 3 | Tension: the car rolling into frame (real movement), riser | square |
| 4 | **Reveal on the drop:** side profile, aperture move square→wide anchored on the wheel, held about 2 s | square→wide |
| 2/1.5/1.5/1.5/**3**/1.5/3 | Rhythm: pairs matched by motion direction (→ → · ← ←), one relaxed 1.5 s shot | wide |
| 8 | Signature: hero wide, slow 100→107 % push on the front wheel, titles, then closes to a square on the wheel | wide→square |

Shot lengths in beats let `--bpm` re-time the whole cut to the chosen track (use BPM ≥ 120, since clean source ranges are short). Cut times are rounded to frames.

## 5. Treatments (three maximum)

1. **Product-anchored push.** Shrink the source crop around an anchor that tracks the hub, so the wheel holds its screen position while the camera moves. Use sub-pixel `warpAffine` with Lanczos; never integer crops (they jitter).
2. **Aperture reveal.** Interpolate the **window**, but derive the crop from it: crop height always equals the full picture height, and crop width = window width × picture height / window height. Interpolating the crop rect and the window rect independently changes the aspect ratio mid-move and **stretches the image**. Anchor the move on the wheel. Use an expo ease-out over 0.6 s for the reveal and a cubic ease-in over 0.62 s for the closing move.
3. **Masked title reveal.** The word rises out of a clip rect over 0.72 s with a cubic ease-out, after the prefix fades and rises (0.42 s in, 0.35 s out). A 72 px cyan hairline draws in under the title.

## 6. Brand bookends (`bookends.py`, EDL `bookends` block)

- **Intro (about 2.5 s):**
  - White card. The logo fades and settles from 94 % with a cubic ease-out, already partly visible on frame 1.
  - The tagline (e.g. `UNLOCK YOUR ` in the primary colour, `STYLE` in the accent) rises out of a mask, with each part about 0.27 s apart.
  - A 96 px accent rule draws in.
  - A 0.56 s in-out-cubic **push-slide** carries the film in from the side the opener moves toward.
- **Logo source:** use the largest clean copy available. Here the contact card's logo had about 2× the pixels of the logo file. Clean it by measuring distance from white against the nearest ink colour, then a smoothstep matte, so it re-inks exactly in the sampled brand colours with crisp edges.
- **Outro:**
  - An iris centred on the product's hub on the film's last frame, starting just outside the rim and growing geometrically to the frame diagonal over 0.8 s, with a 6 px soft edge.
  - Inside it, the end card zooms **through its own hub** from 2.2× to 1× with a cubic ease-out. The viewer first sees the card's branded centre cap sitting in the car's wheel.
  - ❌ Scaling the card *up from tiny* looked like a white cut-out pasted on the car; don't do that.
  - Then hold about 2.7 s with a 2.5 % push and a single light sweep (screen blend, so it only lifts dark spokes).
- **Loop:** a white end card back to the white logo card gives no brightness jump.
- **Geometry to measure per project:** the card wheel `[cx, cy, r]` (card px), the film hub `[x, y]` and rim radius (source px at the film's last frame). Verify by drawing the circle on a rendered frame.

## 7. Audio

- **Slots in `assets/audio/`:**
  - `music.wav`
  - `sfx_impact.wav`: frame 1, plus −15 dB under the signature shot
  - `sfx_riser.wav`: ends exactly on the reveal; about 1.6 s fits a 1.5 s build
  - `sfx_subdrop.wav`: on the reveal, high-passed at 28 Hz
  - `sfx_shimmer.wav`: optional; −22 dB under the detail texture and −24 dB as the end card opens
- **Mix bus:** high-pass 24 Hz → gentle 2:1 compression → `loudnorm` I=−14, TP=−1.5 → `alimiter` limit 0.80 with **`level=false`**. With `level` left on (the default), ffmpeg's limiter auto-levels the output back to 0 dBFS. Then `apad` and trim to the video length plus 0.12 s, so `-shortest` keeps every frame.
- **Loop:** the music tail is a 0.55 s quarter-sine fade, and the opening impact masks the restart.
- **Checks printed by `mix_audio.py`:** integrated LUFS, true peak, phone-band level (300 Hz–9 kHz) and level below 120 Hz. It warns if the mix relies on sub-bass.
- **Epidemic Sound:** search for "dark cinematic bass pulse automotive", "dark industrial electronic build drop" or "minimal dark electronic pulse", with `vocals:false`. Useful SFX searches: "deep sub boom impact cinematic", "short riser tension build cinematic" (filter < 4 s), "sub drop bass impact deep", "metallic shimmer texture subtle". Record every ID; never claim an un-auditioned track was chosen.

## 8. QC commands (run on every render)

```bash
ffprobe -v error -show_entries stream=width,height,r_frame_rate,nb_frames:format=duration -of csv=p=0 out.mp4
ffmpeg -hide_banner -i out.mp4 -vf blackdetect=d=0.04:pix_th=0.06 -f null - 2>&1 | grep -c black_start   # expect 0
```

Then, in Python (OpenCV, 135×240 greyscale):
- **Flash:** a frame differs by more than 8 from both neighbours while those neighbours match each other.
- **Cadence:** the per-frame differences on moving shots must not show a periodic low value (a repeated frame).
- **Loop:** compare the mean difference between the last and first frames.

Also review full-resolution stills of: frame 1, the reveal, the titles, the middle of each transition, and the last frame.

## 9. Gotchas

- `pgrep -f "<pattern>"` inside a wait loop matches its own shell command line and never exits. Wait on PIDs or on log files instead.
- Decoding a VFR capture with `-fps_mode passthrough` to rawvideo prints harmless "non monotonically increasing dts" errors. Verify the frame count matches `ffprobe` and silence them with `-v fatal`.
- Untagged versus tagged colour: decode with `scale=in_color_matrix=bt709:in_range=tv` and encode with `out_color_matrix=bt709` plus the matching tags.
- Chat file-send limit is about 30 MB. CRF 18 at 1080×1920, 25 fps, for 23 s is about 34 MB, so send a CRF 22 review copy (about 13 MB).
- Render a near-lossless film intermediate (`--crf 6`) before adding bookends, so the film isn't compressed twice at delivery quality.
