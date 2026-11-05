# Seedance 2.5 `video_edit` prompts: v6 core (1.04–13.30 s)

The prompts were written with the cinema-worldbuilder skill. They use its Style & Mood / Dynamic Description /
Static Description grammar, give the runtime in the title and in the spec block, and use generic descriptors
instead of brand names.

The input video is the grey-box playblast from `cgi/guide.py`: the motion and framing are locked to it, and the
AI only repaints it photoreal. Image references are the client's photos and our keyframes, attached as
`image_references`.

| Segment | Guide | Runtime | Image references | Approx. cost at 720p |
|---|---|---|---|---|
| A, film 1.04–8.75 | `guide_A.mp4` (185 frames at 24 fps) | 7.7 s | `805977f1` (car front 3/4, studio) and `1544ce1b` (yellow-style stock car on the palm road) | about 59 credits |
| B, film 8.75–13.30 | `guide_B.mp4` (109 frames) | 4.6 s | `71613174` (side), `90bc2d6b` (rear 3/4), `8476b598` (MSP02 front), `1d27274d` (car in snow) | about 35 credits |

Settings: `model seedance_2_5`, `mode video_edit`, `resolution 720p`, `aspect_ratio 9:16`,
`generate_audio false`, `declined_preset_id 24bae836-2c4a-48e0-89b6-49fcc0b21612`.

## Seedance prompt, 7.7 s (segment A)

```
Style & Mood: premium high-end automotive CGI commercial in a clean photoreal render register, bright soft overcast daylight, calm luxury energy that turns into a mechanical metamorphosis, every motion and every framing of the input video kept exactly as it is. Dynamic Description: the camera starts rolled ninety degrees, skimming just above the front-left wheel and the glossy yellow front wing of the coupe as it drives along the seaside boulevard, then flies forward over the wheel arch, past the round headlight and the corner of the front bumper while steadily rolling back toward level, swinging out low in front of the car; the yellow stock front bonnet bursts open and is torn off, tumbling up and away out of frame and leaving the front luggage compartment open; a brand-new gloss-white front bonnet with two large black louvred vents drops in from above the frame, slows, and floats just above the car tilted toward the camera, swaying gently while it slowly descends as the car keeps driving toward the low camera; the bonnet lands and seats perfectly flush into the body; the camera arcs to the front-left three-quarter, pushes in low along the new white bonnet and dives into the vent until the frame is completely filled with smooth white paint. Static Description: a racing-yellow rear-engined two-door sports coupe of the 992 generation with round headlights, a black front splitter and black five-spoke stock wheels, the new bonnet gloss white with two large black vents and carbon detailing; a wide grey asphalt seaside boulevard with white lane markings, tall palm trees on both sides, a low grey rock revetment along the right edge and a pale calm sea beyond it, a bright white overcast sky with soft diffused light and gentle shadows under the car, no people, no text, no logos. Shot on a full-frame cinema camera with wide 18 to 24 millimetre primes on an FPV drone rig, motion exactly as in the input video, clean photoreal render with physically correct reflections on paint and glass, soft overcast key light, neutral grade with true whites and natural yellows, subtle motion blur on the road and wheels, 24fps base shutter 180 degrees, total runtime roughly seven point seven seconds. Audio: none.
```

## Seedance prompt, 4.6 s (segment B)

```
Style & Mood: premium high-end automotive CGI commercial in a clean photoreal render register, cold soft overcast alpine light, fast and confident, every motion and every framing of the input video kept exactly as it is. Dynamic Description: the shot opens on smooth white paint filling the frame at the side-window glass of the coupe, then pulls back and out along the left flank, revealing the black window seal, the dark tinted side window with sky reflections, the door mirror and the white door while the car drives fast along a wet mountain road, the camera rolling back toward level as it drops behind to the rear-left three-quarter; the tall swan-neck rear wing rises up into position as the car accelerates; the car pulls away down the wet road throwing a fine spray mist, the camera slowing so the car shrinks into the distance between snowy banks. Static Description: a gloss-white rear-engined two-door sports coupe in track specification with a large black swan-neck rear wing, black carbon side intakes and a black rear diffuser, on champagne-gold two-piece wheels with ten spokes that each fork into a Y, a raised gold bolt ring with twenty small silver rivets, a deep mirror-polished chrome stepped lip and a gold centre cap, red brake calipers; a wet dark asphalt alpine road with white lane markings and puddle reflections, snow banks on both sides, bare leafless trees, snow-covered mountains in the distance under a pale grey overcast sky, cold neutral palette, no people, no text, no logos. Shot on a full-frame cinema camera with 20 to 30 millimetre primes on an FPV drone rig, motion exactly as in the input video, clean photoreal render with physically correct reflections, wet-road spray and light mist, neutral cool grade with clean whites, subtle motion blur on road and wheels, 24fps base shutter 180 degrees, total runtime roughly four point six seconds. Audio: none.
```
