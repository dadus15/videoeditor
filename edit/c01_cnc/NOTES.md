# Turismo Forged C01: CNC → craftsman → car (9:16, 51.7 s, no music, no on-screen text)

Render: `renders/Turismo_Forged_C01_CNC_9x16.mp4` (1080×1920, 24 fps, H.264 + AAC, −14.4 LUFS, true peak −1.9 dBTP).
Rebuild everything: `bash edit/c01_cnc/build.sh` (cut → intro → mix → delivery encode, about 7 minutes).

All footage is AI-generated (Higgsfield). Keyframes: GPT Image 2.6 / Nano Banana with the client's C01 photo
(`source/c01_cnc/keyframes/C01_reference_brushed-grey.png`) as the design reference. Motion and sound: Kling 3.0 Pro,
image-to-video, native 24 fps. Logo impact SFX: Mirelo.

## Revision 2 (client notes)
- The Mercedes did not wear the C01 and the wheel design drifted → new car keyframes made with the C01 photo plus the
  finished-wheel frame as references; the car is now a C218 CLS 63 S facelift widebody.
- New craftsman scene after machining: lifts the wheel out of the CNC, carries it to his bench, brushes the aluminium,
  paints it deep black in the booth.
- Car section is now five moves around the car and the wheels, joined by 0.25 s dissolves, over the V8 idle from
  revision 1 (looped from its steady part, 2.2–4.9 s of `s6.mp4`).
- All titles removed.
- Brand intro added with the skill's `bookends.py` (new dark theme): steel-grey Turismo logo on black, one light sweep,
  a forged-steel impact, then a push-slide down into the falling billet.

## Revision 3 (client notes)
- The finished-wheel orbit (it showed the back of the wheel and read as a spinning wheel) is removed.
- Brushing is now ~10 s in three shots: macro of the grain forming behind the pad, the wheel on the lathe with
  a dust plume in the light, compressed-air blow-off with a light sweep over the satin grain.
- Centre caps made consistent: in-process shots (machining, lift, carry, brushing, paint) show the open centre
  bore with no cap, as on a real raw wheel; on the car the generated caps are covered by one rendered Turismo cap
  (logo cut from the brand file, silver mark with the red square) tracked to the hub by `cap_overlay.py`
  (`*_cap.mp4`). The two wide car shots keep the generated caps: there the cap is a few pixels and the logo is
  not readable.

## Timeline
| Time | Shot | Sound |
|---|---|---|
| 0.0–2.46 | Intro: logo, light sweep, push-slide down | steel impact |
| 1.9–6.4 | Billet drops into the chuck | impact, ring, hum |
| 6.4–12.9 | Milling along the spokes | spindle, cutting |
| 12.9–16.4 | Pull-back, machine reveal | machine |
| 16.4–18.2 | Craftsman lifts the raw wheel out | drips, scrape |
| 18.2–22.2 | Carries it to his bench | footsteps, clunk |
| 22.2–25.7 | Brushing, macro | abrasive strokes |
| 25.7–28.2 | Brushing on the lathe, dust plume | lathe, brush hiss |
| 28.2–32.2 | Air blow-off, light sweep over the grain | air bursts |
| 32.2–36.7 | Paint booth, deep black | spray gun, booth fan |
| 36.7–37.2 | Hard cut to black | silence |
| 37.2–51.7 | CLS 63: arc, wheel slide, side track, wheel push-in, final pull-back | V8 idle |

Cap overlay (rebuild a clip): `python3 edit/c01_cnc/cap_overlay.py source/c01_cnc/car_wheelpush.mp4
source/c01_cnc/car_wheelpush_cap.mp4 --start 1.2 --cx 585 --cy 957 --r 48`
(car_wheelslide: `--start 0.6 --cx 577 --cy 939 --r 40`; car_side: `--start 0.8 --cx 522 --cy 1012 --r 23 --gain 0.9`).

## Caveats
- The car and the CNC process are AI-rendered, not a record of a real customer car or of Turismo's machines.
- The craftsman is an AI-generated person.
- The wheel follows the C01 photo closely but is still a generated image; check it against the real part before paid use.

## QC (final render)
1240 frames; cuts on the planned frames; black only at 36.7–37.2 (intended); no single-frame flashes; no frozen frames;
no music in any clip; V8 bed even (natural idle pulse, no loop seams).
