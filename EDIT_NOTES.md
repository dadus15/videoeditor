# Audi S8 D4 × Turismo Wheels Inventa: edit notes

Concept: *the detail that transforms the entire silhouette.* 22.96 s, 9:16, 1080×1920, 25 fps.

**Structure (revision 2, from client notes):**

| Time | Section |
|---|---|
| 0–1.9 s | Turismo brand card on white: logo eases in, then **UNLOCK YOUR STYLE** (navy `#0A1B2B`, STYLE in red `#C7222A`) rises out of a mask, and a red rule draws in |
| 1.9–2.46 s | Push-slide left into the film, matching the opener's leftward camera move |
| 1.9–19.9 s | The 18 s film below, unchanged |
| 19.45–20.25 s | Ending: an iris centred on the Audi's front wheel reveals the Turismo centre cap first, then zooms through the hub into the end card (2.2× → 1×) |
| 20.25–22.96 s | End card hold with a slow 2.5 % push and one light sweep across the wheel |

The loop runs from the white end card back to the white logo card.

- **Logo:** taken from the end card's own logo, the same artwork at about 2× the pixels of the 280 px logo file. It's cleaned onto white and re-inked in the two sampled brand colours.
- **Assets:** `assets/brand/`.
- **End card (`turismo_end_card_gemini.jpg`, 768×1376):** scaled 1.41× to fill the frame. It shows a different, multi-spoke wheel design, not the Inventa.

The film times below are relative to the film; add 1.9 s for the final video.

## Deliverables (`renders/`)

| File | State |
|---|---|
| `Audi_S8_D4_Inventa_Hero_9x16_PICTURE-LOCK.mp4` | Final picture, **no audio** (Epidemic access blocked, see `AUDIO_REQUEST.md`) |
| `Audi_S8_D4_Inventa_AltOpen_9x16_PICTURE-LOCK.mp4` | Alternative opening, **no audio** |
| `Audi_S8_D4_Inventa_Hero_9x16.mp4` / `..._AltOpen_9x16.mp4` | Made by `scripts/finish.sh` once the audio files exist |

Both versions now share the logo intro. The alternative differs from the film's first shot onward (2 s in).
| `*.timeline.json` | Cut list and audio cue points for each render |

## Source analysis

- The file is a **phone screen-capture of a YouTube player**, not the original film:
  - Picture area is 448×268 inside a 448×368 frame (letterbox bars at top and bottom).
  - Capture runs at about 40 fps with uneven timing. The film underneath is 25 fps, and every moving shot has exactly 25 new frames per second with no dropped frames.
- **Player overlays:**
  - At 9.6–11.2 s the message "Powiększono, wypełniając ekran" sits in the top black bar, outside the picture.
  - At 5.1–6.2 s and 7.4–9.4 s the player is zoomed in and a faint "1.7x/1.8x" badge appears at the top centre.
  - At 41–42.6 s a "COMING SOON" card plays with the full player UI.
  - Every crop in the edit stays clear of these areas, so no message or badge is visible.
- **Baked-in edit:**
  - Every shot fades from or to black; these fades are excluded.
  - There are no speed ramps or transitions beyond those fades.
  - The audio is **wall-to-wall music** (continuous bass pulse and tonal lines, no usable ambience). It is dropped entirely and nothing is layered over it.
- No higher-quality original exists in the project.

| Source | Shot | Clean range | Motion |
|---|---|---|---|
| 1.6–3.0 | Empty warehouse, crane | | static |
| 3.0–4.95 | Rear wheel, car rolls into frame | 3.0–4.95 | car moves in |
| 5.1–6.2 | Rear wheel (player-zoomed, badge) | 5.15–6.0 | |
| 7.4–9.4 | TURISMO lettering (player-zoomed, badge) | 7.6–9.3 | slight drift |
| 10.4–12.0 | Headlight (message in top bar) | 10.39–11.9 | static |
| 12.6–14.5 | Rear wheel, bright warehouse | 12.7–14.45 | camera → right |
| 16.2–18.3 | Audi rings (very dark) | 16.6–18.2 | static |
| 19.2–20.4 | Taillight + paint reflection | 19.19–20.35 | ← left |
| 21.3–22.6 | **Front wheel, chrome on black** | 21.30–22.55 | ← left |
| 23.5–27.2 | Taillight, rear corner | | slight ← |
| 27.9–29.5 | Front ¾ low, wheel enters | 27.9–29.5 | ← left |
| 30.0–32.1 | **Low side profile** | 30.06–32.10 | ← left |
| 32.3–34.4 | Dolly toward the car | 32.9–34.45 | → right |
| 34.5–35.8 | Rear ¾ | 34.5–35.82 | → right |
| 36.6–40.9 | **Hero wide, orange crane** | 36.58–40.90 | near static |

## Cut (at 120 BPM; re-timeable)

| Edit | Shot | Frame | Purpose |
|---|---|---|---|
| 0.00 | Front wheel (21.31) | square | hook: wheel on frame 1, push 100→107.5 % on the hub, "One detail." |
| 1.25 | TURISMO lettering (7.62) | square | "A whole new character." |
| 2.25 | Headlight (10.45) | square | |
| 3.50 | Rear wheel rolls in (3.45) | square | build, riser |
| **5.00** | **Side profile (30.08)** | square → wide | **reveal on the drop: wheel-anchored aperture pull-back, held 2 s** |
| 7.00 | Rear wheel, bright (12.74) | wide | rhythm: → pair |
| 8.00 | Rear ¾ (34.55) | wide | → |
| 8.75 | Audi rings (16.85) | wide | |
| 9.50 | Taillight (19.22) | wide | ← pair |
| 10.25 | Front ¾ (27.95) | wide | the one relaxed 1.5 s shot, ← |
| 11.75 | Taillight, rear corner (25.0) | wide | |
| 12.50 | Approach (32.92) | wide | |
| 14.00 | Hero wide (36.6) | wide → square | "AUDI S8 D4" / "TURISMO WHEELS · INVENTA", slow push on the front wheel, closes to a square on that wheel and loops into frame 1 |

**Alt version** (`edit/edl_alt.json`): opens on the bright rear wheel against the warm warehouse, with a hub-anchored push. The chrome front wheel moves to the 7.0 s rhythm slot. Everything else is identical.

## The three treatments

The skill's scripts, animation library and HyperFrames aren't installed here. The README describes them, but they're absent from this environment. So I built the three treatments as equivalents in `scripts/compose.py` (Python, OpenCV and FFmpeg):

1. **Wheel-anchored push.** A sub-pixel push of 100→107.5 % around the moving hub on the opening accent, plus a slow push of 100→107 % on the front wheel in the hero shot. Geometry is untouched (uniform scale only).
2. **Aperture match reveal.** On the drop, the side profile starts framed as a square on its front wheel, in the same position as the preceding wheel close-up. The window then opens to the full silhouette over 0.6 s (expo ease-out). It always shows the full picture height at one uniform scale, so nothing stretches. The ending runs the move in reverse (wide → square on the wheel) so the loop closes.
3. **Masked INVENTA reveal.** The word rises out of a clip mask over 0.72 s (cubic ease-out) after "TURISMO WHEELS ·" fades in, with a 72 px cyan (#0AF0F0) hairline drawn under the title.

Not used, by choice:
- **Speed ramps:** the source jitter makes them judder.
- **Frame interpolation:** it risks warping the spokes.
- Any generated wheel detail, rotation, smoke or engine sound.

Text is DM Sans 500/700 (converted from the OFL @fontsource package), white, in a single line below the picture. It never covers the wheels and keeps clear of the Reels/TikTok bottom UI.

## Picture treatment and quality limits

- **Framing:**
  - Detail act: 1080×1080 square windows (4.0× the source pixels).
  - From the reveal on: the **full source width** at 1080×646 (2.4×), so the whole car stays visible.
  - Background: a dark, desaturated blurred duplicate at about 17 % brightness.
  - Nothing is stretched, and no shot is blown up to fill the full 9:16 frame.
- **Grade:** per-shot gamma/gain only, with lifts on the dark rings and lettering shots. A soft shoulder above 86 % protects headlights and paint highlights. No added saturation and no noise reduction.
- **Detail:** Lanczos resampling with a light 0.28 unsharp, plus fine luma grain against banding in the dark gradients.
- **Motion:** each film frame is mapped to exactly one output frame at 25 fps, which removes the capture stutter. A 30 fps render showed a repeat every 6th frame.
- **Honest limits:**
  - 1080×1920 is a delivery container, not recovered detail. The image is soft, about 2.4× upscaled for the wide shots and 4× for the square details.
  - YouTube/WhatsApp compression blocking shows in flat dark areas.
  - The rings and lettering shots are inherently dim.
  - For a sharper master, the original export of the film is needed.

## QC done on the picture locks

- **Format:** 450 frames, 18.000 s, 1080×1920, 25 fps, BT.709 tagged.
- **Frames:** no black frames (`blackdetect`), and no single-frame flashes (a frame that differs from both neighbours).
- **Overlays:** no player message, badge or UI visible (crops verified against the overlay rows).
- **Frame 1:** shows the wheel (no black open), with text in from 0.12 s.
- **Cadence:** frame-difference analysis confirms even motion with no repeated frames.
- **Cuts:** all fall on the planned frames.
- **Loop:** the last frame is a square close-up of the front wheel, cutting to the opening wheel.

**Still to do once audio exists:**
- Music sync and loop audio continuity.
- Headphone and phone-band check; `mix_audio.py` reports these.

## Rebuild

```bash
python3 scripts/compose.py edit/edl_hero.json work/film_hero.mp4 --crf 6         # the 18 s film
python3 scripts/bookends.py edit/edl_hero.json work/film_hero.mp4 renders/<name>.mp4  # logo intro + end card
python3 scripts/analyze_motion.py "<source>" work/motion.csv   # per-frame motion/brightness used for the shot map
python3 scripts/unique_frames.py "<source>"                    # 25 fps film-frame detection report
scripts/finish.sh <drop_s> <bpm>                               # after AUDIO_REQUEST.md files are in place
```

Requires `ffmpeg` and Python with `numpy`, `opencv-python-headless` and `pillow`.
