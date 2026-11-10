# Audi A8 W12 × Turismo Wheels: hook edit notes

Brief: combine two short projects (daylight at the house, golden hour in a field) into one cohesive hook, hide the licence plate, show off the wheels.

Concept: **one set of wheels, two kinds of light.** The film runs DAYLIGHT → GOLDEN HOUR, joined by a straight match cut between the two low-side wheel shots (the wheel sits in the same place in both frames).

## Revision 2 (client notes: "quality very poor", "rims look unnatural", "motion altered")

| Note | Cause in v1 | Fix in v2 |
|---|---|---|
| Quality very poor | ~4.9× Lanczos blow-up of a 223 px-wide reel, plus extra digital zooms (up to 2.4×), sharpening and grain | 4× AI super-resolution (Real-ESRGAN general-x4v3) on everything except the wheel masks; no extra zooms; no grain; bigger picture (1080×1400) |
| Rims look unnatural | Light glint over the spokes; wheel-inside-wheel iris; crash-zoom motion blur; the end card's cap composited into the car's wheel | All removed. In addition, small and mid-size wheels use a **faithful** upscale, because the AI scrambles the fine mesh into irregular spikes. Only the two big wheel close-ups use the AI, where it keeps the real spoke shapes. |
| Motion altered | Two shots at 0.5× slow motion; 30 fps output dropped half the reels' ~60 fps motion; digital pushes | Every shot plays at its **real speed at 60 fps** (the reels' native cadence); no pushes or zooms; straight cuts; dip through white into the end card |

## Deliverables (`renders/`)

| File | Length | What it is |
|---|---|---|
| `Audi_A8_W12_Turismo_Hook_9x16_PICTURE-LOCK.mp4` | 16.05 s | **Main version.** Opens on the wheel at frame 1, ends on the Turismo end card. No audio. |
| `Audi_A8_W12_Turismo_BrandOpen_9x16_PICTURE-LOCK.mp4` | 17.95 s | Same film, opened by the Turismo logo card (UNLOCK YOUR STYLE). No audio. |

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
