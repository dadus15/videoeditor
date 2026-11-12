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
