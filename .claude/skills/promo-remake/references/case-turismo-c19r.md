# Case: Vossen Hybrid Forged Series → Turismo Forged C19R (Nov 2026)

The client's feedback ran in this order:

1. Reverse engineering "perfekcyjny".
2. On the CGI version: "sceneria, animacje i dźwięk obłędnie dobre, ale całość nie jest znakomita".
3. They asked for the real product (C19R), AI video instead of 3D, the font from the Turismo logo, and no 3–4 h
   renders.
4. The AI version: "jestem w szoku. Genialny efekt końcowy."

## Inputs

| Input | Detail |
|---|---|
| Reference | 34.68 s WhatsApp phone capture of a laptop playing the Vossen HF promo (848×478, VFR 60). Now in `source/Vossen_HF_reference_phone-capture.mp4`. |
| Product | Two client renders on white: C19R in Neodyme bronze and G-SR silver, 2000×2000 (`assets/product/`) |
| Brand | Turismo logo from the end card; navy `#0A1B2B`, red `#C7222A`; font **Orbitron**; tagline UNLOCK YOUR STYLE |
| C19R design | Five Y-split spokes with webbed branches, deep concave face, a **windowed outer lip** with about 24 rounded rectangular pockets, a smooth silver cap engraved with a dark GT logo, five open lug holes and no visible nuts |

## Shot map / film timeline (25 fps, 868 frames = 34.72 s)

| Time (s) | Content | Source in final |
|---|---|---|
| 0.00–2.56 | Title: label "TURISMO WHEELS · C19R", bar UNLOCK [YOUR outline] STYLE, brackets, GT mark | 2D bookends |
| 2.56–4.80 | Line-up of 6 finishes whips in from the right, drifts, fades to white at 4.0–4.6 | patch p1 (perspective row) |
| 4.80–6.16 | Low macro on the lower lip, fades in from white | seg1 |
| 6.16–6.76 | Whip spin into the hub | seg1 |
| 6.76–7.56 | Silver 3/4 face push | seg1 |
| 7.56–8.52 | Gloss flash, then wheel lying flat with whip | patch p3 |
| 8.52–10.40 | Turntable wheel turns to front, fades to white | seg1 |
| 10.40–10.56 | White bridge | 2D |
| 10.56–14.30 | Macro along the windowed lip, tilt onto the edge, blur and fade | seg2 (perfect: the C19R really has pockets) |
| 14.80–16.64 | Ghost hub fades in, trucking left | patch p2 + ghost treatment |
| 16.64–20.60 | Montage A, 16 cuts of 0.08–0.72 s in all finishes | seg3; cap close-up 19.08–19.32 and hub flash 20.2–20.6 from p2 |
| 20.60–24.40 | Dark hero close-up with light sweep, slow fade | seg3 from film 21.25 s, stretched (`span`) |
| 24.40–24.60 | White bridge | 2D |
| 24.60–28.56 | Montage B, the same micro-shots re-cut, plus standing wheels | seg4 |
| 28.56–32.40 | Bronze hero 3/4 turning to front with push | seg4 |
| 32.40–33.04 | Whip zoom into the cap | patch p4 at 2× speed |
| 33.04–34.72 | End card: AVAILABLE IN / 6 EXCLUSIVE FINISHES over a blue line drawing of the C19R | 2D bookends |

**Sound** (`sound.py`):
- Impacts at 2.56, 10.56, 16.64, 24.60, 28.56 and 33.04 s.
- Whooshes before 2.56, 6.16, 8.32, 13.70 and 32.72 s.
- Risers into 10.56, 16.64, 24.60 and 28.56 s.
- 120 BPM from 2.56 s, then 120.8 BPM from 16.64 s, so 24.60, 28.56 and 33.04 land on the beat.
- Ticks on every montage cut.
- Shimmer on the end card.
- Result: −14.3 LUFS, −1.7 dBTP.

## Spend and time

**Credits** (balance 842.5 → 431.5, 411 spent):

| Item | Credits |
|---|---|
| Test (seg4) | 64 |
| Four segments | about 228 |
| Four patches | 119 |

**Wall clock for the AI version**, once inputs were uploaded: about 75 min. Most of it was waiting for Seedance:
the batch took about 8 min, one patch took 20 min. Assembly took 75 s.

**The CGI version, for comparison:**
- previz at 216p, 4 spp: 18 min;
- final at 720p, 16 spp: about 3 h 40 min;
- composite: 2 min.

## IDs (for re-use within 24 h; media stay in the user's Higgsfield library)

See `cgi/higgsfield_media.json` in the project. The final master was media `f226a2a0-4b97-4123-8728-c01e53802d48`,
uploaded as `Turismo_C19R_Promo_16x9.mp4`.

## What the client flagged and how it was fixed

| Feedback | Fix |
|---|---|
| "Brakuje prologu", "za krótkie", "brak muzyki" | They had judged the 8 s test segment as the whole film. The final film has the full length, the prologue and the score. **Lesson:** when showing a test, say clearly that it is one segment without bookends or music. |
| "Są chwile kiedy widać design z animacji 3D" | Leak QC plus four patches; see `higgsfield-pipeline.md` |
| Font "przypomina Vossen" | Orbitron, the closest open match to the TURISMO wordmark (wide, rounded-rectangle letters) |
| Wheel model | The Inventa (the CGI stand-in, modelled from the client's Audi film) became the real C19R, from the photos |

## Open items left with the client

- **Claim to confirm:** "6 EXCLUSIVE FINISHES".
- **1080p:** a 1080p AI pass would cost about 520 credits.
- **Line-up:** it is in perspective rather than a flat row; a 35-credit re-roll is possible.
- **Repository copy:** the final file is not in the git repo, because the network blocks the CDN.
