# Audi A8 W12 × Turismo Wheels: hook edit notes

Brief: combine two short projects (daylight at the house, golden hour in a field) into one cohesive hook, hide the licence plate, add an impressive wheel zoom and animation.

Concept: **one set of wheels, two kinds of light.** The film runs DAYLIGHT → GOLDEN HOUR, and the two shoots are joined by an iris through the wheel hub, so the light changes around the same wheel.

## Deliverables (`renders/`)

| File | Length | What it is |
|---|---|---|
| `Audi_A8_W12_Turismo_Hook_9x16_PICTURE-LOCK.mp4` | 16.8 s | **Main version.** Opens on the wheel at frame 1 (best for a YouTube hook) and ends on the Turismo end card. No audio. |
| `Audi_A8_W12_Turismo_BrandOpen_9x16_PICTURE-LOCK.mp4` | 18.7 s | Same film, opened by the Turismo logo card (UNLOCK YOUR STYLE), as on the Audi S8 piece. Loops white card → white card. No audio. |

Both are 1080×1920, 30 fps, H.264, BT.709. The source audio was dropped: it is a copyrighted song (Ice Cube, "Check Yo Self" remix on the daylight reel).

## Structure (120 BPM grid; shot lengths are in beats, so it re-times to the chosen track)

| Time | Shot | Treatment |
|---|---|---|
| 0.0–1.5 | Golden-hour wheel close-up, W12 badge | Hub-anchored push 100→116 %, light glint across the spokes, "One set of wheels." |
| 1.5–2.5 | Daylight: car under the carport | Slow push, **DAYLIGHT** label |
| 2.5–3.5 | Daylight: pan along the house | ← pairs with the previous pan |
| 3.5–4.5 | Daylight: front ¾ (plate removed) | **Crash zoom into the front wheel** (100→240 %, wheel pulled to centre, radial motion blur) |
| 4.5–5.5 | Daylight: wheel close-up | Lands from the zoom (170→100 %, blur decaying) |
| 5.5–6.5 | Daylight: low side, wheel | Push into the hub |
| **6.5–8.5** | **Golden hour: low side, wheel** | **Iris through the hub from the daylight wheel into the golden wheel; real 60 fps slow motion (0.5×); GOLDEN HOUR label. Music drop goes here.** |
| 8.5–9.75 | Golden hour: front ¾ (plate removed) | Slow creep on the wheel |
| 9.75–10.75 | Golden hour: head-on (plate removed) | Settle |
| 10.75–13.75 | Golden hour: hero profile | 0.5× slow motion, AUDI A8 W12 / TURISMO WHEELS in the sky, then a push into the front wheel |
| 13.3–16.8 | End card | Iris centred on the car's front wheel: the Turismo centre cap appears inside it, then the card zooms through the hub; light sweep and hold |

What makes the two shoots read as one piece: identical framing and window on every shot, one shared grade (contrast, light split-tone, tamed greens on the daylight shots), the same type and label system, a wheel in nearly every shot, and the hub-to-hub iris at the hand-over.

## Source forensics

- Both files are **phone screen-recordings of Instagram reels** (368×448, variable 60–120 Hz capture).
  - Reel picture: x 76–298, y 20–431 (223×412 px).
  - App overlays sit **on** the picture: avatar bubbles, username, music line and caption cover the bottom-left from y≈333 (golden) / 343 (daylight). Right of the avatars it stays clean down to y≈380. The usable area is L-shaped and every crop stays inside it.
  - The golden-hour reel has burned-in text "Peak Audi era" in the sky (x 150–213, y 136–144): removed by inpainting.
- Cuts: daylight 0.30 / 1.50 / 2.68 / 3.88 / 5.08 / 6.25 / 7.43 s; golden 1.56 / 3.04 / 4.65 / 6.15 / 7.59 s. Each reel loops inside its recording.
- Motion: golden-hour shots are locked off except the low side shot, which arcs around the wheel (the wheel stays put; the background pans) at a true ~60 fps. That is what allows real 0.5× slow motion with no interpolation.
- Unused: the daylight rear shot (2.68–3.88). Its "08 W12" plate fills a third of the frame; removing it cleanly isn't possible at this resolution, and the shot doesn't show the wheels.

## Licence plates

Removed (not blurred) in source pixels before scaling, so the fill moves with every zoom:
- daylight front ¾ `[102,316,128,325]`
- golden wide `[264,287,277,296]`
- golden front ¾ `[250,287,266,297]`
- golden head-on `[220,302,251,312]`

The fill is a feathered inpaint, slightly darkened, so the front reads as a clean, plate-free bumper. Checked at full resolution in every shot.

## Honest limits

- The reels are only 223 px wide inside the recordings, so every shot is upscaled about 4.9×. 1080×1920 is the delivery size, not recovered detail. For a sharper master, the original reel exports are needed (from the creator, @chronowsky / fishu_01 on the reels).
- The bottom of the frame is limited by the app overlays, so the wheels sit low in some shots.
- **The end card shows a different wheel design** (multi-spoke) from the mesh wheels on the car. A model-matched card would make the ending exact.
- **Rights:** the footage is a third-party creator's Instagram content. Make sure you have their permission to use it in a promo.
- **No audio yet** (see below).

## Audio (not yet in)

Epidemic Sound is configured but not authorised in this session, and the source music can't be reused. The cue points are in `renders/*.timeline.json`. For the main version:

| Cue | Time | Sound |
|---|---|---|
| Open | 0.00 | short low impact |
| Crash zoom | 4.0–4.5 | riser ending on the land at 4.5 (the zoom is fast, so keep it subtle) |
| **Drop** | **6.50** | music drop / bass entrance on the iris into golden hour, plus a sub accent |
| Signature | 10.75 | soft impact at −15 dB |
| End card | 13.30 | soft shimmer as the card opens |

The brand-open version has every cue 1.9 s later. Put `music.wav` and the SFX in `assets/audio/` (names in `AUDIO_REQUEST.md`), then:

```bash
.claude/skills/youtube-edit/scripts/finish.sh <drop_seconds_in_track> <bpm>
```

## Rebuild

```bash
python3 .claude/skills/youtube-edit/scripts/compose_multi.py edit/edl_a8w12_hook.json work/film_a8w12_hook.mp4 --crf 6
python3 .claude/skills/youtube-edit/scripts/bookends.py edit/edl_a8w12_hook.json work/film_a8w12_hook.mp4 renders/Audi_A8_W12_Turismo_Hook_9x16_PICTURE-LOCK.mp4
# brand-open: same film, then bookends with edit/edl_a8w12_brandopen.json
```

## QC done

- **Format:** 504 frames / 16.80 s (hook) and 561 frames / 18.70 s (brand-open); 1080×1920, 30 fps, BT.709.
- **Frames:** no black frames (`blackdetect`) and no single-frame flashes.
- **Cadence:** no repeated frames on any moving shot.
- **Cuts:** all fall on the beat grid (1.5 / 2.5 / 3.5 / 4.5 / 5.5 / 8.5 s, plus 4.37 at the peak of the crash-zoom blur).
- **Overlays:** no app UI, avatar or caption in any crop; "Peak Audi era" removed.
- **Plates:** removed in all four shots that show one.
- **Stills reviewed at full resolution:** hook glint, crash zoom, iris hand-over, the plates, titles and the end-card iris (the iris stays centred on the wheel).
