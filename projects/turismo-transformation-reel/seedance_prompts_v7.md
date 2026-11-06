# Production prompts: Seedance `video_edit` on previs v7.4 (approved by the user)

The input video is the approved Blender previs, which locks motion, timing and framing. Seedance only repaints it
photoreal. The previs is exported per segment, upscaled to 720×1280, at 24 fps. Image references are the client's
photos.

| Segment | Input (from previs v7.4) | Runtime | Image references |
|---|---|---|---|
| A, film 1.04–8.75 | `prod_A.mp4` (A frames 0000–0231) | 7.7 s | `805977f1` (car front 3/4, studio), `1544ce1b` (yellow stock car on the palm road) |
| B, film 8.65–13.32 | `prod_B.mp4` (B frames 0000–0140) | 4.7 s | `71613174` (side), `90bc2d6b` (rear 3/4), `8476b598` (MSP02 front), `1d27274d` (car in snow) |

**Edit:**
- Keep the 0–1.04 s opening and the 13.30–18 s packshots from v6, as in the previs.
- The worlds swap during the 3 paint-only frames at 8.65–8.75, as in the previs.
- Score: a licensed track (see `MUSIC.md`), cut to the sound map (drop at 1.04, break 7.6–8.3, stutter 8.4–9.3,
  drop at 9.4, hard stop at 17.0).

**Settings:**
- `model seedance_2_5`, `mode video_edit`, `generate_audio false`, `aspect_ratio 9:16`.
- Resolution 720p (about 7.6 credits a second of input, so about 95 credits for both segments) or 1080p if the
  plan allows.
- Check the exact price before submitting.

## Segment A, 7.7 s
```
Style & Mood: premium high-end automotive CGI commercial in a clean photoreal render register, bright soft overcast coastal daylight, calm luxury energy that turns into a slow-motion mechanical metamorphosis, every motion, every framing and every timing of the input video kept exactly as it is. Dynamic Description: the camera starts rolled ninety degrees, skimming just above the front-left wheel and the glossy racing-yellow front wing of the coupe as it drives along the seaside boulevard, flies forward over the wheel arch and the round headlight while rolling back toward level; the yellow stock front bonnet swings open on its hinge, showing its brown underside, then tears off and tumbles up and away; time slows down almost to a standstill; the camera arcs from the front-left to dead front, low; a brand-new gloss-white bonnet with two large black louvred vents drops in from far above standing upright like a shield, hovers just above the open front luggage compartment, slowly tips back from vertical to flat while swaying gently, and seats perfectly flush; the camera keeps drifting, arcs to the front-right three-quarter and pushes in low along the new white bonnet, skims over the right-hand vent so it slides out of the bottom of the frame, and glides on, slowing, over smooth white paint until the frame is only white paint. Static Description: a racing-yellow rear-engined two-door sports coupe of the 992 generation with round headlights, a black front splitter and black five-spoke stock wheels; the new bonnet gloss white with two large black louvred vents and carbon slats; a wide grey asphalt seaside boulevard with visible aggregate texture and white lane markings, tall palm trees on both sides, a low rock revetment and a pale calm sea, a bright white overcast sky with soft clouds, soft diffused light and gentle shadows under the car, no people, no text, no logos. Shot on a full-frame cinema camera with wide 14 to 22 millimetre primes on an FPV drone rig, motion exactly as in the input video, physically correct reflections on paint and glass, subtle suspension movement of the body, high-key neutral grade with true whites and natural yellows, motion blur on road and wheels, shallow depth of field in the close-ups, 24fps base shutter 270 degrees, total runtime roughly seven point seven seconds. Audio: none.
```

## Segment B, 4.7 s
```
Style & Mood: premium high-end automotive CGI commercial in a clean photoreal render register, cold soft overcast alpine light, fast and confident, every motion, every framing and every timing of the input video kept exactly as it is. Dynamic Description: the shot opens gliding over smooth gloss-white door paint of the coupe, moving up as the edge of the dark tinted side window with its black seal slides in from the top of the frame, the camera rolled about thirty-five degrees; it bursts back and out along the right flank, revealing the side window with sky reflections, the door mirror and the white door while the car drives along a wet mountain road, rolling back to level; it sweeps behind to the rear-right three-quarter as the tall swan-neck rear wing rises and locks into position; then it follows low and to the right as the car pulls slowly away down the wet road, its body moving softly on its suspension, throwing a fine spray mist. Static Description: a gloss-white rear-engined two-door sports coupe in track specification with a large black swan-neck rear wing, black carbon side intakes and a black rear diffuser, on champagne-gold two-piece wheels with ten spokes that each fork into a Y, a raised gold bolt ring with twenty small silver rivets, a deep mirror-polished chrome stepped lip and a gold centre cap, red brake calipers; a wet dark asphalt alpine road with white lane markings and puddle reflections, snow banks on both sides, bare leafless trees, jagged snow-covered mountains under a pale grey overcast sky with dramatic clouds, cold neutral palette, no people, no text, no logos. Shot on a full-frame cinema camera with 20 to 32 millimetre primes on an FPV drone rig, motion exactly as in the input video, physically correct reflections, wet-road spray and light mist, neutral cool grade with clean whites, motion blur on road and wheels, 24fps base shutter 270 degrees, total runtime roughly four point seven seconds. Audio: none.
```
