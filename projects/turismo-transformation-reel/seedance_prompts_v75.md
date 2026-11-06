# Production prompts v7.5: stiff suspension, photo-real summer world

**What changed from v7.4, after the user's feedback on v8:**
- **Suspension:** a GT3 RS has motorsport-stiff suspension, so the body must not visibly bounce, pitch or roll.
  - The previs rig is about 5× stiffer: heave ±1 mm, pitch ±0.05°, roll ±0.03°, squat 0.15°.
  - The prompts no longer ask for "suspension movement"; they ask for a planted, rigid body.
- **Summer scenery:** the guide for A is now rendered in Cycles with real materials (Poly Haven, CC0):
  - a photographed overcast HDRI sky;
  - photo-scanned asphalt;
  - granite rocks;
  - pinnate palms with real bark texture;
  - water.

  Seedance keeps the guide's textures, so the guide itself had to look real.
- **The end of A:** v8's A2 pass turned the final white-paint glide into clouds. The prompt now states that the
  last frames are gloss-white paint.

Settings and references are the same as v7.4, at 1080p:
- A: v6 coast stills `3dd8968f` and `04cca05e`, plus `1544ce1b`.
- B: `71613174`, `90bc2d6b`, `8476b598`, `1d27274d`.

## Segment A
```
The input video is a 3D layout of a real commercial shoot: keep every camera move, every framing, every timing and every object motion exactly as it is, and render it as real photographed live-action footage matching the photoreal look of the reference images, with real cloudy overcast sky, real Canary palm trees with detailed fronds, real weathered asphalt with cracks and grain, a real granite rock revetment and a real calm sea. Style & Mood: premium automotive commercial, bright soft overcast coastal daylight, calm luxury energy that turns into a slow-motion mechanical metamorphosis. Dynamic Description: the camera starts rolled ninety degrees, skimming just above the front-left wheel and the glossy racing-yellow front wing of the coupe as it drives along the seaside boulevard, flies forward over the wheel arch and the round headlight while rolling back toward level; the yellow front bonnet swings open on its hinge, then tears off and tumbles up and away; time slows almost to a standstill; the camera arcs to dead front, low; a brand-new gloss-white bonnet with two large black louvred vents drops in from far above standing upright like a shield, hovers above the open front luggage compartment, slowly tips back from vertical to flat and seats perfectly flush; the camera drifts, arcs to the front-right three-quarter, pushes in low along the new white bonnet, skims over the right-hand vent and glides on over the smooth gloss-white bonnet paint; the last frames are filled only with smooth gloss-white car paint, never sky. Static Description: a racing-yellow rear-engined 992-generation sports coupe with round headlights, a black front splitter and black five-spoke wheels, on stiff motorsport suspension: the body stays flat, planted and rigid, with no visible bounce, pitch or body roll; the new bonnet gloss white with two large black louvred vents and carbon slats; real seaside boulevard with palms on both sides, rock revetment and the sea, no people, no text, no logos. Shot on a full-frame cinema camera with wide primes on an FPV drone rig, physically correct reflections of the clouds and palms on paint and glass, high-key neutral grade with true whites and natural yellows, motion blur on road and wheels, shallow depth of field in the close-ups, 24fps 270 degree shutter. Audio: none.
```

## Segment B
```
Style & Mood: premium high-end automotive commercial, real photographed live-action look, cold soft overcast alpine light, fast and confident, every motion, every framing and every timing of the input video kept exactly as it is. Dynamic Description: the shot opens gliding over smooth gloss-white door paint of the coupe, moving up as the edge of the dark tinted side window with its black seal slides in from the top of the frame, the camera rolled about thirty-five degrees; it bursts back and out along the right flank, revealing the side window with sky reflections, the door mirror and the white door while the car drives along a wet mountain road, rolling back to level; it sweeps behind to the rear-right three-quarter as the tall swan-neck rear wing rises and locks into position; then it follows low and to the right as the car pulls away down the wet road, throwing a fine spray mist. The car sits on stiff motorsport suspension: the body stays flat, planted and rigid at all times, with no visible bounce, pitch, squat or body roll. Static Description: a gloss-white rear-engined two-door sports coupe in track specification with a large black swan-neck rear wing, black carbon side intakes and a black rear diffuser, on champagne-gold two-piece wheels with ten spokes that each fork into a Y, a raised gold bolt ring with twenty small silver rivets, a deep mirror-polished chrome stepped lip and a gold centre cap, red brake calipers; a wet dark asphalt alpine road with white lane markings and puddle reflections, snow banks on both sides, bare leafless trees, jagged snow-covered mountains under a pale grey overcast sky with dramatic clouds, cold neutral palette, no people, no text, no logos. Shot on a full-frame cinema camera with 20 to 32 millimetre primes on an FPV drone rig, physically correct reflections, wet-road spray and light mist, neutral cool grade with clean whites, motion blur on road and wheels, 24fps base shutter 270 degrees. Audio: none.
```
