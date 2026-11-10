# Audi A8 W12 × Turismo Wheels: hook edit notes

Brief: combine two short projects (daylight at the house, golden hour in a field) into one cohesive hook, hide the licence plate, show off the wheels.

Concept: **one set of wheels, two kinds of light.** The film runs DAYLIGHT → GOLDEN HOUR, joined by a straight match cut between the two low-side wheel shots (the wheel sits in the same place in both frames).

## Revision 4: cut to "Club Bizarre" (lene 3000)

- The client asked for the edit to follow "Club Bizarre" by lene 3000 (2025, 2:05) and gave a YouTube link.
  - YouTube is unreachable from the build environment, and ripping the audio isn't allowed (YouTube terms and the song's copyright), so **the track has not been heard or analysed**.
  - Plan for publishing: add the song in the YouTube Shorts sound picker at upload, so YouTube licenses it.
- **Tempo:** the published figure is 87.2 BPM (Spotify data). The cut sits on the 174.4 BPM grid (0.344 s), which fits both 87.2 and 174.4. All 9 cuts were verified on the exact grid frames.
- **Structure (grid beats at 174.4):**

  | Beats | Time | Shots |
  |---|---|---|
  | 0 | 0.00 s | hook |
  | 4–16 | 1.38–5.50 s | four daylight shots (1.03 / 0.69 / 0.69 / 0.69 s), then the low side (1.03 s) |
  | **16** | **5.505 s** | **match cut into golden hour, on a bar line: put the track's drop or strongest downbeat here** |
  | 20 / 24 / 28 | 6.88 / 8.26 / 9.63 s | golden front ¾ / head-on / hero |
  | 32 | 11.01 s | end of the film, dip into the end card |

- **Alignment in the Shorts editor:** start the song so its drop falls at 5.5 s (main version) / 7.4 s (brand-open). If the drop is on a beat, every other cut lands on the beat too.
- **To lock it exactly:** supply the audio file. Beat detection, any tempo correction and the drop placement are then a re-time via `finish.sh <drop_s> <bpm>`.
- **Lengths:** main version 14.1 s, brand-open 16.0 s.

## Revision 3 (client notes: "car motion at 12–14 s not natural", "super extra quality 1080p", "delete the text", "fit to Club Bizarre")

- **Unnatural motion, found and fixed.** The 3 s hero was built from the two captures of the looping reel. The car is slowly rolling and the camera follows it, and the second capture started 0.3 s *earlier* in the reel than where the first one ended. So the car jumped back and repeated its move. Frame matching shows the captures are offset by exactly 7.917 s (golden 0.00 s = 9.917 s in reel terms). The hero is now one continuous 1.5 s take, with cadence checked frame by frame (steady about −0.25 px/frame).
- **No freeze under the fade:** the dip to white now ends on the film's last frame.
- **Text removed** from the film: hook line, DAYLIGHT / GOLDEN HOUR and the titles. The brand cards (logo, tagline, contact details on the end card) are unchanged.
- **Quality:** the picture uses the full overlay-free height (1080×1500, centred), and the masters are encoded at CRF 12 (high bitrate). Multi-frame denoising was tested and rejected: the car rolls, so averaging smears the wheel spokes.
- **Music:** waiting for the track file. The cut is in beats (currently a 120 BPM placeholder); it will be re-timed to the track's real beats and drop once the audio is supplied.

## Revision 2 (client notes: "quality very poor", "rims look unnatural", "motion altered")

| Note | Cause in v1 | Fix in v2 |
|---|---|---|
| Quality very poor | ~4.9× Lanczos blow-up of a 223 px-wide reel, plus extra digital zooms (up to 2.4×), sharpening and grain | 4× AI super-resolution (Real-ESRGAN general-x4v3) on everything except the wheel masks; no extra zooms; no grain; bigger picture (1080×1400) |
| Rims look unnatural | Light glint over the spokes; wheel-inside-wheel iris; crash-zoom motion blur; the end card's cap composited into the car's wheel | All removed. In addition, small and mid-size wheels use a **faithful** upscale, because the AI scrambles the fine mesh into irregular spikes. Only the two big wheel close-ups use the AI, where it keeps the real spoke shapes. |
| Motion altered | Two shots at 0.5× slow motion; 30 fps output dropped half the reels' ~60 fps motion; digital pushes | Every shot plays at its **real speed at 60 fps** (the reels' native cadence); no pushes or zooms; straight cuts; dip through white into the end card |

## Deliverables (`renders/`)

| File | Length | What it is |
|---|---|---|
| `Audi_A8_W12_Turismo_Hook_9x16_PICTURE-LOCK.mp4` | 14.6 s | **Main version.** Opens on the wheel at frame 1, ends on the Turismo end card. No audio. |
| `Audi_A8_W12_Turismo_BrandOpen_9x16_PICTURE-LOCK.mp4` | 16.5 s | Same film, opened by the Turismo logo card (UNLOCK YOUR STYLE). No audio. |

Both are 1080×1920, 60 fps, H.264, BT.709. The source audio was dropped: it is a copyrighted song.

## Structure (120 BPM grid, shot lengths in beats; every shot at real speed)

| Time | Shot | Notes |
|---|---|---|
| 0.0–1.5 | Golden-hour wheel close-up, W12 badge | "One set of wheels." AI upscale on the wheel (large spokes) |
| 1.5–2.5 | Daylight: car drives in under the carport | **DAYLIGHT** |
| 2.5–3.5 | Daylight: car driving past the house | |
| 3.5–4.5 | Daylight: front ¾ | plate removed |
| 4.5–5.5 | Daylight: wheel close-up | AI upscale on the wheel |
| 5.5–6.5 | Daylight: low side, wheel | match cut ↓ |
| 6.5–7.75 | Golden hour: low side, wheel (camera arcs around it) | **GOLDEN HOUR**, music drop here |
| 7.75–9.0 | Golden hour: front ¾ | plate removed |
| 9.0–10.0 | Golden hour: head-on | plate removed |
| 10.0–13.0 | Golden hour: hero profile (two takes of the same locked-off shot) | AUDI A8 W12 / TURISMO WHEELS in the sky |
| 12.55–16.05 | End card | 0.8 s dip through white, then hold (titles clear by 12.45) |

## Picture pipeline

1. **Clean in source pixels:** inpaint the plates and the burned-in "Peak Audi era" sky text, feathered.
2. **Upscale ×4** the reel picture (x 76–299, y 20–432) with Real-ESRGAN general-x4v3, denoise 0.5.
   - `scripts/upscale.py`; weights in `work/models/`, not committed.
   - The weights are read without unpickling: an opcode-only parser, so a weight file can't run code.
3. **Wheel masks:** inside each wheel, a faithful Lanczos ×4 with a gentle unsharp. Wheels in moving shots are **tracked** frame by frame (template matching). Positions were checked on renders with `--show-masks`.
4. Crop the overlay-free area to a 1080×1400 window (×1.22 from the 4× image), on the dark blurred background. One shared light grade; the daylight shots get slightly warmer, with the greens tamed.
5. Upscaled frames are cached in `work/sr_cache/`, so re-renders take about a minute.

## Source forensics

- Both files are **phone screen-recordings of Instagram reels** (368×448, variable 60–120 Hz capture).
  - Reel picture: x 76–298, y 20–431.
  - App overlays sit **on** the picture: avatars and caption cover the bottom-left from y≈333 (golden) / 343 (daylight). Every crop stays clear of them.
- The reels carry ~60 fps motion; the output keeps it 1:1 in real time.
- **Plates removed** (not blurred): daylight front ¾ `[102,316,128,325]`, golden wide `[264,287,277,296]`, golden front ¾ `[250,287,266,297]`, golden head-on `[220,302,251,312]`.
- **Unused:** the daylight rear shot, where the "08 W12" plate fills a third of the frame.

## Honest limits

- The AI upscale makes the body, glass, lights and scenery much cleaner. It can't create real detail that the 223 px reels never had: the wheels in wide shots stay soft (by choice, so they look like the real wheels).
- The original reel files (from the creator, chronowsky / fishu_01) would still give a far better master.
- The end card shows a different wheel design (multi-spoke) from the mesh wheels on the car.
- The footage is a third-party creator's content, so permission is needed.
- **No audio yet:** Epidemic Sound isn't authorised in this session. Cues: impact at 0.0, music drop at **6.5 s** (main) / 8.4 s (brand-open), end card at 12.55 s. See `AUDIO_REQUEST.md`.

## Rebuild

```bash
# once: weights into work/models/ (see scripts/upscale.py header); pip install onnx onnxruntime
python3 .claude/skills/youtube-edit/scripts/compose_multi.py edit/edl_a8w12_hook.json work/film_a8w12_hook.mp4 --crf 8
python3 .claude/skills/youtube-edit/scripts/bookends.py edit/edl_a8w12_hook.json work/film_a8w12_hook.mp4 renders/Audi_A8_W12_Turismo_Hook_9x16_PICTURE-LOCK.mp4
# brand-open: same film, bookends with edit/edl_a8w12_brandopen.json
```
