# VANTA reference: technical ("back-end") breakdown, and our spec to match it

Measured on `source/ref_vanta_clean_512x850.mp4` (5 Nov 2026) with ffprobe, mpdecimate, optical flow
(`camera_motion.py`, 0.2 s windows), spectral flux and RMS of the audio, and per-section luma, saturation, RGB and
Laplacian-sharpness stats. Comparison values are from our v5.

## 1. Delivery format

| | Reference | Our v5 | Target for the final |
|---|---|---|---|
| Container | H.264 High, yuv420p, BT.709, AAC 48 kHz stereo | same | same |
| Frame rate | **30 fps content** (a 60–66 fps VFR phone capture; frame diffs change on every 2nd frame) | 30 fps | **30 fps**, from 24 fps Seedance via optical-flow interpolation to 96 fps |
| Shutter / motion blur | **Strong directional and rotational motion blur**, about 180–270° shutter: background streaks, rolled frames smear | Crisp AI frames, little blur | **Temporal supersampling**: average 96 fps sub-frames to a **270° shutter** |
| Depth of field | Shallow on close-ups (bonnet, glass); background soft | Deep, everything sharp | Seedance prompt plus a light defocus on backgrounds in close-ups |
| Lens | Wide FPV (about 14–20 mm full-frame), slight barrel distortion | Normal | Wide in the guide (14–20 mm) |

## 2. Fluidity: camera speed profile ("motion curves")

Optical-flow energy per 0.2 s (reference):

```
1.0  1.2  1.8  2.2  2.6  2.8  3.0 | 3.0–6.6     | 6.8  7.2  7.8  8.2 | 8.4–8.9  | 9.2  9.6  10.0 10.4 | 10.6–13.2
1.2  1.8  5.6  4.5  3.0  1.1  0.3 | 0.1–0.4     | 0.7  1.1  2.7  6.1 | 0.0      | 0.7  7.5  4.4  1.1  | ~0.05
FPV: ease-in-out, peak 1.8 s      | hero hold   | exponential ramp-in| hold     | ramp-out, peak 9.6  | locked follow
```

What carries the "płynność" (fluidity):
- **No linear moves anywhere.** Every move eases in and out.
- **Speed ramps around the transition.** An exponential **ramp-in** (6.8–8.2 s, zoom up to +4.6 %/frame) runs into
  a **0.5 s hold on flat paint** (8.45–8.95). Then a mirrored **ramp-out** bursts out (peak 9.6 s, −4.3 %/frame) and
  settles into a locked follow.
- **Contrast of pace.** Fast FPV, then a calm hero hold (3.0–6.6), then fast again. The calm part gives the
  metamorphosis room to breathe.
- **Hard cuts only at rest.** Every cut lands on a static or near-static frame (13.3, 15.3, 16.2, 17.07),
  never mid-move.

The v6 guide carries the same curves in `cgi/guide.py` `WARP`: beta-shaped speed profiles with peaks at about 1.9
and 9.6 s, an exponential ramp-in, and the hold.

## 3. Transitions (names and frames)

| Time (s) | Type | Detail |
|---|---|---|
| 1.04 | **Hard cut + graphic match cut** | Black-void wheel → rolled FPV over the car's wheel, same position and size |
| 1.04–3.0 | **Continuous FPV fly-through with barrel-roll correction** (90° → 45° → 0°) | Motion blur carries the roll |
| 2.25–2.6 | **In-camera action beat** (part removal) | No cut |
| 3.0–6.6 | **Hero hold / slow creep-in** | Near-locked camera; the object animates |
| 6.8–8.45 | **Speed-ramped push-in** (ease-in, slight roll) | Accelerates into the vent |
| 8.45–8.95 | **Push-through / object-wipe transition with a colour hold** (an "invisible cut" through the surface) | The frame becomes flat paint in the *new* colour; the world changes behind it |
| 8.95–10.4 | **Reverse whip / pull-back reveal** out of the side glass | Heavy motion blur, roll 30° → 0° |
| 10.4–13.3 | **Follow (chase) shot, decelerating** | |
| 13.30 / 15.30 / 16.22 | **Hard cuts on the beat** to static beauty shots (packshots) with a micro creep | About 0.07 %/frame |
| 17.07 | **Hard cut to the loop frame** (black void) | The last frame flows into frame 1: a **seamless loop** |

No dissolves, no flash frames, no whip-pan effects added in the edit. Every transition happens in camera.

## 4. Sound design and sync

- **Music:** 120 BPM; beats at x.36 and x.86 s. The hard cuts at 13.3, 15.3 and 16.2 sit on beats (±60 ms,
  which is about the capture's A/V offset).
- **Drop sync:**
  - the music **dips to −24 dB at 7.5–8.4** during the ramp-in;
  - the spectral centroid rises to 3.4 kHz at 8.25, a **riser/whoosh into the dive**;
  - the **bass drop** comes at about 9.0–9.5 (−14 dB, centroid 1.3 kHz) as the snow world bursts out.
- **Ends:** silence at 0–0.5 s; a −21 dB tail on the black-void loop.

Our score (`reel_sound.py`) already has a breakdown at 7.7–9.0 with a riser into an impact at 9.0. For the final,
move the breakdown to 7.5 and put the impact on the burst at 8.95.

## 5. Image: grade and texture

| Section | Reference luma p5/50/95, sat, RGB, sharpness | v5 |
|---|---|---|
| World 1 (3.2–6.4) | 0.13/**0.74**/0.98, sat **0.13**, RGB .68/.67/.63, sharp 3.5 | 0.06/**0.38**/0.82, sat **0.46**, RGB .53/.42/.27 (orange), 4.2 |
| Transition (8.45–8.95) | flat light-blue paint, luma 0.74, sharp 0.6 | — |
| World 2 (10.6–13.2) | 0.18/**0.84**/0.98, sat 0.16, RGB .68/.75/.77 (cool), sharp **2.5** | 0.21/0.48/0.82, sat 0.13, sharp **6.9** |
| Parked (13.4–15.2) | 0.20/0.69/0.90, sat 0.20, sharp 7.2 | 0.12/0.44/0.79, sat 0.13, 6.0 |
| Wheel close-up | 0.04/0.64/0.88, sat 0.26, sharp 3.9 | 0.02/0.37/0.86, sat 0.17, **8.4** |

What this means:
- The reference is **high-key**: median luma about 0.7–0.85, highlights near 1.0, lifted shadows.
- It is **pastel and desaturated** in world 1 (sat 0.13), **cool** in world 2, and neutral overall.
- It is **soft**: motion blur and diffusion, with no sharpening.

Ours is about 1 stop darker, 3.5× more saturated in world 1, orange, and 2–3× too sharp in motion. That
over-sharpness is a large part of the "AI look".

**Finishing spec for the final (`reel_finish.py` grade):**
- Exposure +0.8 to +1.0 stop, with a soft highlight roll-off to 0.98 and shadows lifted to about 0.13.
- Saturation 0.45–0.5 in world 1 (Seedance output on overcast prompts), with a neutral-to-cool white balance in
  world 2.
- Diffusion (Pro-Mist-style bloom) at about 0.15, plus a 0.6 px soften instead of sharpening.
- Grain 0.005; no chromatic aberration.
- Motion blur from 96 fps sub-frames at a 270° shutter.
