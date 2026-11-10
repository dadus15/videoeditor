# Audi A8 W12 × Turismo Wheels: hook edit notes

Brief: combine two short projects (daylight at the house, golden hour in a field) into one cohesive hook, hide the licence plate, show off the wheels.

Concept: **one set of wheels, two kinds of light.** The film runs DAYLIGHT → GOLDEN HOUR, joined by a straight match cut between the two low-side wheel shots (the wheel sits in the same place in both frames).

## TikTok versions (9:16, framed for TikTok's interface)

| File | Length |
|---|---|
| `renders/Audi_A8_W12_Turismo_Hook_TikTok_9x16_PICTURE-LOCK.mp4` | 13.4 s |
| `renders/Audi_A8_W12_Turismo_BrandOpen_TikTok_9x16_PICTURE-LOCK.mp4` | 15.3 s |

Both are 1080×1920, 60 fps, ~19–22 Mbps. EDLs: `edit/edl_a8w12_*_tiktok.json`. The cut is the same as v6.

- **Problem found:** in v6 9:16 every wheel sat at y≈1400–1710, under TikTok's caption and music block.
- **Fix:**
  - The picture is 960×1333 at (60, 100). Every wheel and the car now sit in the UI-free area x 60–960, y 160–1480. The top tabs, the right button column and the bottom caption block lie over the blurred background (cover, 28 %).
  - The end card is fitted inside [100, 110, 980, 1470] on white, so the phone number and e-mail stay above the caption.
  - Full-width shots come out ~1:1 from the 4× AI upscale.
- **QC:**
  - No black frames or flashes; cuts on the grid.
  - TikTok UI simulated over key frames (`work/tiktok_overlay.jpg`).
  - Pixel QA against v6 9:16: sharpness +40–50 %, fine detail +30–40 %, blockiness ~1.0.
- **Sound:** add "Club Bizarre" (lene 3000) in TikTok's sound picker, with the drop at 4.8 s (main) / 6.7 s (brand-open).

## 16:9 1920×1080 version of the v6 brand-open film

`renders/Audi_A8_W12_Turismo_BrandOpen_16x9_PICTURE-LOCK.mp4`: 1920×1080, 60 fps, 15.3 s, ~31 Mbps. EDL: `edit/edl_a8w12_brandopen_16x9.json`.

The cut, speeds, slow motion and masks are identical to v6.
- **Picture:** the portrait reel fills the full height (777×1080 panel). Full-width shots are therefore **downscaled 0.88×** from the 4× AI upscale with an area filter, instead of enlarged 1.22× as in 9:16.
- **Sides:** a blurred cover of the same frame at 28 % brightness.
- **Brand cards:** the logo card is laid out for 16:9; the end card fits the full height on white, with its sides feathered into the white.
- **Dither and encode:** TPDF dither before 8-bit; x264 `slower`, `tune film`, aq-mode 3, CRF 10 (film intermediate CRF 4).

Pixel analysis inside the picture (v6 9:16 → 16:9):

| Shot | Sharpness (Laplacian var.) | Fine detail (energy above ¼ Nyquist) | Blockiness (8-px edge ratio) |
|---|---|---|---|
| golden front ¾ | 136 → 192 | 0.74 → 1.37 % | 1.38 → 0.98 |
| carport drive-in | 174 → 287 | 2.13 → 3.98 % | 1.07 → 0.98 |
| daylight front ¾ | 222 → 342 | 1.75 → 3.00 % | 1.05 → 1.00 |
| daylight low side | 29 → 75 | 0.42 → 0.86 % | 1.13 → 0.97 |
| drop, golden low side | 37 → 95 | 0.75 → 1.51 % | 1.14 → 1.02 |
| hero | 109 → 179 | 0.66 → 1.21 % | 1.12 → 1.01 |

- Sky banding, measured as staircase steps in a 40-column averaged profile, is below visibility in both versions (~0.35 code-value RMS). It comes mostly from faint source compression structure. The dither protects against new terraces when YouTube re-encodes the upload.
- A first banding metric (local 1–2 level terraces) was misleading: dither raises it by design.
- **QC:** 919 frames, 15.32 s; no black frames or flashes; cuts on the grid (+1.9 s intro).

## Revision 6 (client notes: "the shot at 2 s is badly framed, you only see part of the rim"; "add a slow-motion effect that fits the track")

- **Whole rim in every shot:**
  - The house drive-by, where the wheels were cut by the bottom edge and the front wheel left frame, is replaced by the carport drive-in.
  - The arc-only wheel close-up is replaced by the front ¾.
  - The daylight low side is reframed into the clean area right of the avatars (x ≥ 144, y ≤ 380).
  - The drop shot is reframed into a measured clean rect (x ≥ 137, y ≤ 344; the rim ends at y≈339).
  - The opening is now the golden front ¾ (whole glowing rim) instead of the arc-only close-up.
- **Slow motion fitted to the track (real frames only, no interpolation):**

  | Shot | Speed | Length |
  |---|---|---|
  | Carport drive-in | 0.5× | |
  | Drop shot (beat 14 = 4.82 s) | enters at 1.0× and eases to 0.45× in 0.35 s | one bar |
  | Hero | 0.5× | one bar |

  The two golden shots step evenly through the real 60 fps frames (`retime: index`); the longest hold is 2–4 frames.
- **Structure:** 6 shots.

  | Beat | Time | Shot |
  |---|---|---|
  | 0 | 0.00 s | golden front ¾ |
  | 4 | 1.38 s | daylight carport drive-in (0.5×) |
  | 8 | 2.75 s | daylight front ¾ |
  | 11 | 3.78 s | daylight low side |
  | **14** | **4.82 s** | **drop: golden low side, speed ramp** |
  | 22 | 7.57 s | hero, 0.5× |
  | 30 | 10.32 s | end card |

- **Lengths:** main version 13.4 s, brand-open 15.3 s.
- **Drop position in the Shorts editor:** 4.8 s (main) / 6.7 s (brand-open).

## Revision 5: fewer cuts (client: "too many cut scenes", in both halves)

- **7 shots instead of 10**, each close to its full clean length, still at real speed and on the 174.4 grid:

  | Beat | Time | Shot | Length |
  |---|---|---|---|
  | 0 | 0.00 s | golden wheel close-up | 1.38 s |
  | 4 | 1.38 s | daylight: car driving past the house | 1.03 s |
  | 7 | 2.41 s | daylight: wheel close-up | 1.03 s |
  | 10 | 3.44 s | daylight: low side | 1.03 s |
  | **13** | **4.47 s** | **golden low side: match cut, the drop goes here** | 1.38 s |
  | 17 | 5.85 s | golden front ¾ | 1.38 s |
  | 21 | 7.23 s | hero profile | 1.38 s |
  | 25 | 8.60 s | dip into the end card | |

- **Dropped:** the carport drive-in, the daylight front ¾ and the golden head-on shots.
- **Lengths:** main version 11.7 s, brand-open 13.6 s.
- **Drop position in the Shorts editor:** 4.5 s (main) / 6.4 s (brand-open).
- **QC:** all 6 cuts verified on the grid frames; no backward motion, flashes or black frames.

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
