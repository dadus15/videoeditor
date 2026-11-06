# Status: v8 photoreal production DELIVERED (6 Nov 2026); only the licensed music WAV is pending

## Approved by the user
- **v7.2 = "idealnie"** (perfect): the camera through the metamorphosis.
  - Previs: media `79fadda9-a024-43ee-9013-68a649d06b81`.
  - Side by side: media `08b7a6c2-2c71-40b1-91ac-4b04bd82f734`.

## In progress: v7.3
The user asked for two things:
1. The summer-to-winter transition, done as in the reference.
2. Smoother, more realistic vehicle motion.

**Done in code** (`cgi/previs.py`, `cgi/previs_edit.sh`, branch `claude/zealous-fermi-ku8mii`):
- **Transition** (reference measured at 15 fps):
  - Segment A now runs to 8.75 s. The camera skims over the right vent, which slides out of the bottom of the
    frame, then glides and slows over the bonnet paint.
  - Segment B starts at 8.65 s, gliding on the new car's door paint and moving up. The window edge slides in from
    the top, then the camera pulls out.
  - The edit mixes A and B over 3 frames (8.65–8.75), where both frames are paint only (checked with
    `--probe`). There is no hold any more.
- **B camera:** arc-length timing from a smooth speed profile (`SPEED`). v7.2 stalled at 10.55 s and jumped at
  9.65 s. The maximum frame-to-frame speed change is now 0.5 m/s.
- **Car realism:** a sprung body (`CAR_RIG`: heave, pitch and roll), lane wander and yaw (`CAR_ALL`), and squat as
  the car pulls away. All of it runs on the scene clock, so it slows down with the slow motion.

**Render state:** Higgsfield sandbox, XL, at `/home/user/previs`.
- Frames needed: `A/0000-0231.png` (232) and `B/0000-0140.png` (141).
- At pause: A 31/232, B 36/141.
- Earlier versions are kept in `A_v70`, `A_v71`, `A_v72` and `B_v72`.

## Resume
1. In the sandbox:
   ```bash
   cd /home/user/previs
   ls A | wc -l
   ls B | wc -l
   ```
2. If frames are missing, run `/home/user/previs/wave73.sh` in the background on XL.
   - It runs 4 Blender processes, about 15 minutes a wave.
   - It resumes, skips existing frames and deletes broken PNGs.
   - About 2–3 waves are left.
3. If the sandbox lost its files:
   - Re-download `previs.py` and `previs_edit.sh` from GitHub raw on this branch (the repository is public).
   - Download the reference: media `3dc47f75-15bf-4ccf-8c72-1a1663b442bb`.
   - Get the v6 film from README v6 (needed for 0–1.04 s and the packshots).
   - Get `car.glb` from Hunyuan job `4cdddcc3`.
   - Build `score_v7.wav` with `reel_sound_v7.py`.
4. When all frames exist:
   - run `bash previs_edit.sh` (it writes `Turismo_Reel_previs_v7.mp4` and `..._vs_oryginal.mp4`);
   - upload with `media_upload`, then a PUT with `If-None-Match: *`, then `media_confirm`.
5. Check:
   - the transition at output frames 250–275;
   - B at frames 290–399, against the reference;
   - `camera_motion.py` on B.
