# Turismo Forged C01: CNC → craftsman → car (9:16, 52 s, no music, no on-screen text)

Render: `renders/Turismo_Forged_C01_CNC_9x16.mp4` (1080×1920, 24 fps, H.264 + AAC, −14.5 LUFS, true peak −2.0 dBTP).
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

## Timeline
| Time | Shot | Sound |
|---|---|---|
| 0.0–2.46 | Intro: logo, light sweep, push-slide down | steel impact |
| 1.9–6.4 | Billet drops into the chuck | impact, ring, hum |
| 6.4–12.9 | Milling along the spokes | spindle, cutting |
| 12.9–16.4 | Pull-back, machine reveal | machine |
| 16.4–19.6 | Craftsman lifts the wheel out | drips, scrape |
| 19.6–23.6 | Carries it to his bench | footsteps, clunk |
| 23.6–26.6 | Brushing | abrasive strokes |
| 26.6–31.1 | Paint booth, deep black | spray gun, booth fan |
| 31.1–31.6 | Hard cut to black | silence |
| 31.6–37.6 | Finished wheel in darkness, orbit | silence |
| 37.6–52.1 | CLS 63: arc, wheel slide, side track, wheel push-in, final pull-back | V8 idle |

## Caveats
- The car and the CNC process are AI-rendered, not a record of a real customer car or of Turismo's machines.
- The craftsman is an AI-generated person.
- The wheel follows the C01 photo closely but is still a generated image; check it against the real part before paid use.

## QC (final render)
1250 frames; cuts on the planned frames; black only at 31.1–31.6 (intended); no single-frame flashes; no frozen frames;
no music in any clip; V8 bed even (natural idle pulse, no loop seams).
