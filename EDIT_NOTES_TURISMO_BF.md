# Turismo BF: version 2 "Wheel Roulette" (creative, recommended)

13.52 s, 9:16, 1080×1920, 25 fps, 120 BPM, loops. EDL: `edit/spin_turismo_bf.json`. Renderer: `spin_roulette.py`.

| Time | What happens |
|---|---|
| 0.00 | Frame 1: brushed 6Y spinning at full speed (motion blur), red/blue light vortex, **KUTE** huge behind the wheel, "01 / 04" top-left, BLACK FRIDAY W TURISMO under the logo |
| 0.50 | Hard stop on the beat (whole turn, so the frame is the untouched still); the vortex swells |
| 2.0–2.5 | The word sinks behind the rim; the wheel spins up; the camera rushes in |
| 2.50 | Swap at peak blur to FORGED 10-spoke → stops at 3.0 → **FELGI** rises from behind the wheel |
| 5.0 / 7.5 | Split-Y → **W 48H**; matte 6Y → **OD RĘKI** |
| 10.0 | 2×2 grid of all four spins down and stops together at 10.5: numbers 1–4, **KTÓRĄ WYBIERASZ?**, "Wpisz numer w komentarzu" |
| 13.0–13.52 | The grid spins up → loops into frame 1 (also spinning) |

The end card was dropped in favour of the loop and the comment prompt. It can come back as a final hold if contact details on screen matter more than replays.

# Turismo Wheels: Black Friday "Kute felgi w 48h" hook short

14.56 s, 9:16, 1080×1920, 25 fps. EDL: `edit/stills_turismo_bf.json`. Renderer: `.claude/skills/youtube-edit/scripts/compose_stills.py`.

## Sources (`source/turismo_bf_stills/`)

| File | Content | Used |
|---|---|---|
| `01_promo_slide_kute_felgi_48h.jpg` | Carousel slide 1/9: copy over a blurred wheel, "SWIPE >>>" | **Copy only.** Its baked text and swipe prompt don't belong in a video |
| `02_wheel_10spoke_forged.jpg` | Thin double-spoke, matte black, "FORGED" on the lip | Detail + signature shot |
| `03_wheel_ysplit_multispoke.jpg` | Split-Y multi-spoke, matte black | Detail + rhythm |
| `04_wheel_6y_brushed.jpg` | 6 Y-spokes, brushed/gloss black | Hook + reveal |
| `05_wheel_6y_matte.jpg` | The same design as 04, matte black | Build (match cut into 04) + rhythm + top logo |

The stills are phone screenshots (about 1080–1130 px wide, JPEG). The baked Turismo logo, the "9/9" page counter (02) and the white screenshot edges (03, 04) are cropped off. One clean copy of the logo, taken from 05 and matted by brightness, sits at the top. 1080×1920 is the delivery size, not added detail; detail shots are 1.6–2.0× upscales.

## Cut (120 BPM)

| Time | Shot | Move | Copy |
|---|---|---|---|
| 0.00 | Brushed 6Y, spokes + hub | push 1.60→1.76× | **KUTE FELGI** / DOSTĘPNE W **48H** (masked) |
| 1.52 | FORGED lettering | drift → | |
| 2.52 | Split-Y spokes | drift → | |
| 3.52 | Matte 6Y hub | push-in, in-cubic (tension) | |
| **4.52** | **Brushed 6Y: match cut on the hub, pull-back to the full wheel (0.8 s, expo)** | drop | |
| 6.52 / 7.52 | Split-Y full / matte 6Y full | drift ← pair | "Prosto z polskiego magazynu." / "Bez czekania na produkcję." |
| 8.52 | FORGED full (signature) | slow push, then in-cubic dive into the centre cap | **BLACK FRIDAY**, cyan rule, TURISMO WHEELS · **48H** |
| 11.05 | Iris from the GT centre cap into the end card (card zooms through its hub 2.2×→1×) | | contact card |
| 11.85–14.56 | End card hold, 2.5 % push, one light sweep | | |

## Open points

- **Audio:** see `AUDIO_REQUEST_TURISMO_BF.md` (Epidemic Sound connector not authorized).
- **End card** (`assets/brand/turismo_end_card_gemini.jpg`) shows a different (multi-spoke, polished-lip) wheel than the ones in the film. A model-matched card would be better.
- **Loop:** the video ends on the white end card and restarts on a dark frame, so the loop isn't seamless. The fix would be a dark end card.
- Copy is the client's own Polish promo text (slide 1). No prices, sizes or model names were added.
