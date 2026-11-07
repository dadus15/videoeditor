# Turismo Forged C01: CNC → craftsman → car (9:16, 50.4 s, no music, no on-screen text)

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

## Revision 3 (client notes)
- The finished-wheel orbit (it showed the back of the wheel and read as a spinning wheel) is removed.
- Brushing is now ~10 s in three shots: macro of the grain forming behind the pad, the wheel on the lathe with
  a dust plume in the light, compressed-air blow-off with a light sweep over the satin grain.
- Centre caps made consistent: in-process shots (machining, lift, carry, brushing, paint) show the open centre
  bore with no cap, as on a real raw wheel; on the car the generated caps are covered by one rendered Turismo cap
  (logo cut from the brand file, silver mark with the red square) tracked to the hub by `cap_overlay.py`
  (`*_cap.mp4`). The two wide car shots keep the generated caps: there the cap is a few pixels and the logo is
  not readable.

## Revision 4 (client notes)
- The car shot where the parked car's rear wheel turned (0:42–0:45 in rev 3) is removed. (In rev 2 the note
  about it was misread and the finished-wheel orbit was cut instead.)
- Brushing re-done as it is really done: the wheel lies flat on a padded turntable at a finishing bench, the lip
  masked with tape; the craftsman runs a pneumatic inline sander with a Scotch-Brite pad along each spoke, then
  wipes the dust and checks the grain under ordinary shop light. No dust plumes or staged light beams.
- The carry shot with the unnatural walk is replaced by a static shot: he lays the wheel on the turntable.
- Centre caps on the car no longer composited onto finished video (it read as a floating cap). The exact
  Turismo emblem is put into the still start frame with `cap_still.py` (old emblem removed, cap face rebuilt,
  emblem drawn as a raised silver badge), then Kling animates the frame, so the emblem is part of the cap.
  Checked across both car close-ups: it stays upright and intact.

## Timeline
| Time | Shot | Sound |
|---|---|---|
| 0.0–2.46 | Intro: logo, light sweep, push-slide down | steel impact |
| 1.9–6.4 | Billet drops into the chuck | impact, ring, hum |
| 6.4–12.9 | Milling along the spokes | spindle, cutting |
| 12.9–16.4 | Pull-back, machine reveal | machine |
| 16.4–18.2 | Craftsman lifts the raw wheel out | drips, scrape |
| 18.2–21.7 | Lays it flat on the turntable | thud on the pad |
| 21.7–25.7 | Air sander + Scotch-Brite along a spoke | sander, air hiss |
| 25.7–29.7 | Close-up: the satin grain forms | sander strokes |
| 29.7–32.7 | Wipes and checks the grain | cloth on metal |
| 32.7–37.2 | Paint booth, deep black | spray gun, booth fan |
| 37.2–37.7 | Hard cut to black | silence |
| 37.7–50.4 | CLS 63: arc, front-wheel slide, push-in to the cap, final pull-back | V8 idle |

Emblem on a car keyframe (before animating it):
`PYTHONPATH=edit/c01_cnc python3 edit/c01_cnc/cap_still.py in.png out.png --cx X --cy Y --r R`
(`cap_overlay.py` tracks a cap onto finished video; kept as a tool, but not used in this cut.)

## Caveats
- The car and the CNC process are AI-rendered, not a record of a real customer car or of Turismo's machines.
- The craftsman is an AI-generated person.
- The wheel follows the C01 photo closely but is still a generated image; check it against the real part before paid use.

## QC (final render)
1210 frames; cuts on the planned frames; black only at 37.2–37.7 (intended); no single-frame flashes; no frozen frames;
no music in any clip; V8 bed even (natural idle pulse, no loop seams).
