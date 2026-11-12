---
name: promo-remake
description: "Reverse-engineer a reference product commercial (a competitor's wheel, car-part or product promo, often a phone recording of a screen) and rebuild it 1:1 for our own brand and product. Same cut, timing, camera moves, transitions, typography layout and sound map, with our product, logo, font, copy and music. The product footage is AI video (Higgsfield Seedance) driven by a CGI motion guide made in Blender. Use this skill whenever the user sends a promo, ad, teaser or product video and asks to recreate, remake, copy the style of, \"zrób 1:1\", \"reverse engineering\", \"taki sam film tylko z naszą felgą/produktem\", or wants a product launch video in the style of an existing brand (Vossen, HRE, BBS, ...), even if they don't mention AI, Higgsfield or Blender. Also use it for follow-ups on such a project: swapping the product, fixing frames where the old design shows, changing the title or end card, re-assembling, sharper inserts, Black Friday or sale promos with offer typography, and 720p/1080p deliverables."
---

# Promo remake: reference ad → our product, 1:1

The Turismo Forged C19R promo (Nov 2026) was made this way. The client's verdict was "genialny efekt końcowy". The
playbook below is that project generalised. `references/case-turismo-c19r.md` holds every number, prompt and ID from
it; read it when you need a worked example.

Two patterns exist; pick by the reference:

- **Guide pattern** (C19R, `references/case-turismo-c19r.md`): a few long product shots with camera moves. Use a
  Blender guide, then Seedance `video_edit`.
- **Compositor pattern** (Black Friday, `references/case-turismo-black-friday.md`): a fast montage of many short
  shots with heavy typography. Use a Python frame compositor with real footage at master quality, generated 2K
  stills with 2D moves, a few Seedance clips and 2D type. See section 6.

The guide pattern has four layers. Each one can be redone without touching the others:

1. **Reverse engineering** gives a frame-accurate shot map, the typography and the sound map of the reference.
2. **CGI motion guide**: a Blender film with the reference's exact cut, camera moves and timing, using a simple stand-in
   product. It is never shown to anyone. Its only job is to tell the AI where the camera goes.
3. **AI video**: Seedance 2.5 `video_edit` repaints each guide segment as photoreal footage of *our* product from the
   client's product photos. Short `omni_reference` patch shots replace the frames where the guide's design leaks through.
4. **2D and assembly**: our title and end card, the white bridges, the synthesised score, and the assembly in the Higgsfield
   sandbox, which also hosts the deliverable.

## Before you start: intake

Ask only for what blocks the work. Usually that is:

- **The reference video.** A phone capture of a screen is fine; the forensics strip it.
- **Product photos.** At least two clean renders or photos on white: a 3/4 view, and a second finish or angle.
  Without them the AI invents a product, so do not start generation without them. Also ask for the exact product name.
- **Brand assets.** Logo (the largest copy available), brand colours, and a contact or end card if they have one.
- **Copy.** Ask for the title and tagline. Claims such as "6 EXCLUSIVE FINISHES", "ALL-NEW" or "FORGED" are product
  claims: mirror the reference's layout, but list the claim as *to confirm* in the report.
- **Every product model to show.** If the reference shows several products at once (a row, a stack), ask
  which models go where. One model repeated three times reads as lazy.
- **Original footage.** For screen-recorded clips, find the masters (the client's YouTube channel or site)
  before generating anything. Real footage beats AI re-creations, and the client will reject a blurry insert.
- **The exact cut of the reference.** Ask for its true start and end. References are often caught mid-loop.
- **Budget and resolution.** Check `balance`. 720p costs about 7.6 credits per second of `video_edit`; 1080p is about 2.3× that.

## 1. Reverse engineering (about 20 min)

Read `references/reverse-engineering.md`. In short:

- Contact sheets at 2 fps for the whole video, then 10 fps around every cut, with burned-in timecodes
  (`scripts/ref_sheets.sh`).
- A brightness and motion trace (`analyze_motion.py` from the youtube-edit skill) finds fades, flashes and whips.
- Note what belongs to the player or the phone rather than the film: play icons, progress bars, the bezel and the room.
- Crop the title and end card at full resolution to read their layout: label box, bar, solid and outline words,
  brackets, the small mark, and the type-on animation.
- Audio: loudness, spectrogram and onsets (`scripts/audio_map.py`). Mark the impacts, whooshes, montage ticks and
  breakdowns against the cuts.
- Write the shot map as a table (time → shot → our rebuild) into the project README. Every later step keys off it.

## 2. CGI motion guide (Blender via `pip install bpy`)

Read `references/cgi-motion-guide.md`. Bootstrap a project with `scripts/new_project.sh <project-dir>`, which copies
`scripts/cgi/*` into `<project>/cgi/` and the fonts into `<project>/assets/fonts/`.

- `cgi/scene.py` holds the procedural wheel (stand-in product), the white studio, and the render settings.
  `cgi/shots.py` holds one entry per shot: camera, target, roll, lens, f-stop, spin and yaw as functions of t.
  `cgi/post.py` holds the timeline, the studio-white composite, the fades and the 2D cards.
- **Iterate at previz quality**: `--res 216 --spp 4`. That is about 1.6 s per frame and about 18 min for 670 frames.
  Compare it side by side with the reference using `cgi/compare.sh`, and fix framing until each shot matches.
  The reference is usually much tighter (macro) than you first guess.
- The guide only needs readable motion and composition. 720p at 16 spp worked; it took about 3 h on the 4-core
  cloud CPU, so start it in the background with `nohup setsid … &` and report progress with `cgi/progress.sh`.
  A lower-resolution guide was not tested. Try 432p first next time and check that the AI output stays sharp.

## 3. Higgsfield AI pass

Read `references/higgsfield-pipeline.md` before the first call. Key facts:

- **Getting files in.** This cloud environment blocks `upload.higgsfield.ai` and the Higgsfield CDN, but
  the Higgsfield sandbox reaches both, and GitHub too.
  - Files that may be public: commit and push, `curl` the raw file at the commit SHA in `sandbox_exec`, then
    `media_upload` → PUT from the sandbox with `If-None-Match: *` → `media_confirm` (`type` plus `media_ids`).
  - Private files: use `media_upload_widget`, as the only tool in its turn. It takes images in batches but **only one video per
  widget**; one video plus one audio file together is allowed. Send the user the files to upload with
  `SendUserFile` first. Record every media_id in `cgi/higgsfield_media.json`.
- **Segments.** Cut the guide into segments of about 6–8.5 s at natural breaks (white fades). Run Seedance 2.5 in
  `mode: video_edit` at 720p with `generate_audio: false`, the guide as `video_references`, and the product photos
  as `image_references`.
  - The prompt describes the product's exact design, bans the stand-in's design explicitly ("no five-pointed star,
    no hexagonal nuts, not even in 2–3-frame flash cuts"), and names the finish of each shot in order. Without
    that the AI recolours shots, for example a bronze hero turned black.
  - Decline the "IN THE DARK" preset suggestion with `declined_preset_id`.
- **Test one segment first** (the hero segment). Show it to the user, then batch the rest with `generate_video_batch`.
  Jobs take 6–15 min.
- **Leak QC.** Download every result in `sandbox_exec`, make fps-5 tile sheets (256 px tiles, under 512 KiB per
  call) and look at them with `image_paths`. Leaks cluster in a few predictable places:
  - very short montage cuts,
  - hub and cap close-ups,
  - a row of many products,
  - whips,
  - high-key "ghost" shots.

  Pin each leak to film frames with a 12-fps timecoded sheet.
- **Patches.** For each leaking shot, generate a 4–5 s Seedance clip in `omni_reference` mode from the product
  photos only, with no guide (28 credits per 4 s at 720p). Describe the shot, the motion, the finish and any whip
  at the end. Map patch frames onto film frames in the plan.

## 4. 2D, score and assembly

- **Title and end card.** Use `cgi/post.py` `TitleCard`: a red label, a navy bar of solid/outline/solid words,
  brackets and the brand mark, with a wipe, a type-on cursor and glitch blocks.
  - Use the brand's own typeface or its closest open match. Turismo uses **Orbitron**, which has no `·` or `®`
    glyphs; the code draws the dot and uses the logo artwork instead.
  - The end card uses a faint blue line drawing from a product render on white.
  - `cgi/bookends.py --label … --product …` writes the title, the white bridges and the end card into one file
    for upload.
- **Score.** `cgi/sound.py` synthesises impacts, whooshes, risers, a 120 BPM pulse, montage ticks and a shimmer
  from the timeline's cue points, and normalises to −14 LUFS with a −1.5 dBTP ceiling. It is licence-free.
  Higgsfield has no standalone music model here, and Epidemic needs connector auth.
- **Assembly** happens in the Higgsfield sandbox with `scripts/hf_assemble.py plan.json`. Write the plan from
  `templates/hf_plan_turismo_c19r.json`, then:
  1. Download the results with curl inside the sandbox (an uploaded WAV is served under `<id>.mp3`).
  2. Run `--extract`.
  3. Check transitions with `--stills`.
  4. Encode with `--out`; it takes about 75 s.

  Code is text, so write the scripts into the sandbox with a heredoc. Never relay media bytes as text.
- **Deliver.**
  1. Call `media_upload` *before* the producing command.
  2. Run `curl -X PUT … --upload-file` inside the sandbox.
  3. Call `media_confirm`.
  4. Give the user the CDN link.

## 5. Motion match and finishing (reels, after "it looks artificial" feedback)

- **Measure the reference camera, do not guess it.** Run
  `scripts/camera_motion.py ref.mp4 ref_motion.csv --window 0.25`. It gives pan, zoom, roll and motion energy
  per window: where the camera is locked, where it pushes, where it whips, where it rolls. Write those moves
  into the Seedance prompts (start and end keyframes plus "locked camera" or "fast pull-back, then locked")
  and check ours with `--compare ours.csv`.
- **Copy only what the reference does.** If its cuts are clean, use no whip, zoom or impact effects and no
  added shake. Effects the reference lacks are what make a cut look "touched by AI".
- **Read the opening at 10–25 fps, never at 2 fps.** The first 3 s carry the hook, and coarse sheets hide it. In
  the VANTA reel they hid three things:
  - the wheel lies flat on a mirror floor;
  - its spoke centre settles into the barrel and loops with the end shot;
  - the cut at 1.0 s is a match cut into an FPV take that starts rolled 90°.
- **Rolled FPV openers:** generate the first frame in 16:9 with a level horizon, rotate it 90° in the sandbox,
  so it fills 9:16 exactly, and upload it as Seedance `start_image`. Use the next shot's first frame as
  `end_image` and describe the barrel roll back to level. One 4 s clip does it.
- **Exploded 2PC loops:** keyframe A shows the wheel assembled; keyframe B is A edited so the centre floats above
  the barrel. A Seedance clip (start B, end A, "descend, seat, spin") feeds both the end shot and the opening, for
  a seamless loop.
- **Retime to beats:** with `keys: [[film_t, src_t], ...]` in a `reel_finish.py` shot, a monotone cubic carries
  each measured beat (roll 90°, 45°, level) to the reference time.
- **Before/after colour change for free:** `scripts/recolor_car.py` repaints the car body in existing clips.
  It uses a CLIPSeg car mask, a wheel-rim guard and a shading-preserving tint. The VANTA reference's WOW is the
  car changing colour through the "dive into the paint"; we reproduced it as yellow → white without new
  generations. Check `--stills` first, because each shot needs its own settings.
- **Compare the whole film side by side before reporting:** 4 fps sheets of the reference and ours in the
  same layout. Name the gaps honestly (light, removal beat, hero presentation, colour change, mechanical beats
  such as a rising wing) and price the ones that need regeneration.
- **Car reels: a motion guide in minutes, not hours** (VANTA reel v6):
  1. Build the car mesh with `generate_3d` `hunyuan3d_v3_image_to_3d`, `generate_type: Geometry`, from 3
     studio photos (side, front 3/4, rear 3/4). It costs 11 credits and gave about 500k triangles at the right
     proportions; scale it to the real length.
  2. Split the parts by geometry (bonnet, wing, wheels): `scripts/cgi/guide_car_reel.py`.
  3. Render in the Higgsfield sandbox with the Blender 4.5 tarball (download.blender.org) and
     BLENDER_WORKBENCH, which has EGL there.
     - About 1–2 s a frame at 360×640 per process; 6 parallel processes on XL rendered 296 frames in about
       4 min.
     - EEVEE on CPU is 4–50 s a frame; the C19R Cycles guide was about 20 s a frame.
  4. Feed the guide to Seedance `video_edit` (the industry "Playblast2Render" pattern).

  This cloud session cannot download Higgsfield CDN files, so build and render everything in the sandbox.
- **Count beats, not cuts.** The VANTA reel has 5 hard cuts but 14 beats: 1.04–13.3 s is one continuous camera
  move through a metamorphosis and a world change. Key frames for those beats live in
  `projects/turismo-transformation-reel/analysis/ref_keys_seg*.jpg`.
- **Analyse the technical "back end" before finishing** (`projects/turismo-transformation-reel/TECH_ANALYSIS.md`
  is the template):
  1. The true content fps: a phone capture runs at 60 fps VFR, but frame diffs that change every 2nd frame
     mean 30 fps.
  2. Shutter and motion blur, DOF and lens.
  3. The speed profile from `camera_motion.py` at 0.2 s: ease curves, ramp-in, holds, ramp-out.
  4. The transition types (match cut, push-through/object wipe with a colour hold, reverse whip, hard cuts
     at rest on the beat, seamless loop).
  5. Drop sync: a dip and riser into the transition, the bass drop on the reveal.
  6. The grade fingerprint from `scripts/grade_stats.py` (luma percentiles, saturation, RGB, sharpness).

  Then carry the measured speed profile into the guide (`WARP` beta-shaped ramps in `guide_car_reel.py`). Add
  motion blur by temporal supersampling: minterpolate to 4× fps, `tmix=frames=3` (a 270° shutter), back to the
  delivery fps. Grade to the measured stats: AI output is typically about 1 stop darker, oversaturated and 2–3×
  too sharp.
- **When Higgsfield credits run out, check the other connectors.** Tella's `generate_video` (Seedance) worked:
  - 2.0 Fast with an image reference; references must be landscape, so pad a 9:16 frame onto a blurred 16:9
    canvas and crop the centre afterwards.
  - Seedance 2.5 with a reference failed, and text-only 2.5 cost about 3,000 credits.
  - Download with `get_source_thumbnail(format mp4, width 1280/1920)` and fetch the URL in the sandbox.
- **Editing effects that sell the reference's motion:** use `scripts/reel_v6_compositor.py`.
  - Real slow motion from 96 fps interpolation.
  - PCHIP speed ramps.
  - An exponential digital push-in with zoom blur into a flat-paint hold (push-through transition).
  - An explosive zoom-out reveal.
  - Hue-selective sky neutralising, to match worlds without touching the paint.
- **Finishing** uses `scripts/reel_finish.py plan.json` (template `templates/reel_finish_turismo_msp02.json`).
  1. Interpolate every clip to 96 fps with minterpolate (one job per clip, in parallel on an XL sandbox,
     about 4 min).
  2. Sample 30 fps output with eased speed ramps; split a shot into two entries when its speed must change
     (a fast pull-back, then a calm drive-away).
  3. Use `cam` for small digital moves the reference has: `{zoom: [a, b], pan: [[x0, y0], [x1, y1]],
     roll: [r0, r1], ease}`.
  4. Apply one filmic grade across all clips.

## 6. Compositor remakes (montage references: sales, launches, "Shorts")

Read `references/case-turismo-black-friday.md`. Copy `scripts/compositor/bf_draft.py` and `bf_sound.py` into
the project and edit them:

- `SHOTS` holds `(g_start, g_end, kind, params)`. The kinds are clip, clip2 (master footage with focus, push,
  whip, fit band and plate cover), still, gen (Seedance clip), photo_split, img_mirror, myst (lit 2D wheel
  scene), collage, swap and white.
- The typography blocks follow the reference layout. Beat effects key off the measured kick onsets.

Rules learned the hard way:

1. **Draft at 0 credits first** (screen-recorded footage and renders). Get the cut and the type approved, then
   spend.
2. **Inserts of real cars and places must be real footage at master quality.**
   - Download the original with yt-dlp in the sandbox; the flags for embed-only videos are in the case file.
   - Find each moment with `scripts/compositor/frame_match.py`.
   - Cut with `-ss`/`-t` *before* `-i`.
   - Never AI-sharpen or re-imagine real footage: it moves geometry, for example a wheel no longer sits on its
     car.
3. **Generated product stills.**
   - Use gpt_image_2_6 at 2k, with the reference frame first and the product renders after it.
   - State the pose ("lying flat", "standing on the lip, turned 30° so the barrel shows, not flat discs").
   - Use different models per position, and describe the floor and light from the reference.
   - Make two variants.
4. **Motion that cannot be faked in 2D** (a person walking past, a drift): make a gpt keyframe, a Seedance
   **draft** at 480p (12 credits), then `draft_job_id` at 1080p (64), so it is the same take. For a locked-off
   shot, take the person's matte from a temporal-median plate, so text can sit behind them.
5. **Third-party adverts in footage** (plate frames, sponsor boards): ask the client, then cover them with a
   template-tracked, feathered fill.
6. **Feedback by second.** Map second → film frame → shot. Make a strip of ours against the reference at the
   same frames *before* changing anything.
7. **Every final ships with a side-by-side against the reference.** Answer "does every frame match?" with
   timing and cuts (1:1) plus a table of every content deviation and why it exists.
8. **Deliverables.** A 1080×1920 CRF 16 master plus a 720×1280 version encoded from the same PNG frames
   (Lanczos, CRF 17). Publish to TikTok only after explicit approval.

## QC before reporting

Run these in the sandbox:

- Frame count, duration and fps from `ffprobe`.
- `blackdetect` must report 0.
- `ebur128` should read about −14 LUFS with true peak at or below −1 dBTP.
- A full-film fps-2 tile sheet: look at every tile for any trace of the stand-in design.
- The last seconds at fps 10: the whip should land on the end card.

- In the Higgsfield sandbox, check the IEND trailer of every PNG before encoding. Never copy frame folders
  while a render writes to them.

Report the credits spent from `balance` before and after.

## Report to the user (in their language)

Lead with the result and the link. Then cover:

- what changed against the reference,
- the QC numbers,
- the credits spent and left,
- open decisions: claims to confirm, 1080p cost, any shot that deviates from the reference (for example a
  perspective line-up instead of a flat row).

Keep jargon out. The client cares about the product looking right and the cut matching.

## Files

| Path | Use |
|---|---|
| `references/reverse-engineering.md` | Forensics, shot map, typography and sound map methods |
| `references/cgi-motion-guide.md` | Blender guide: modelling a stand-in, studio, shots, render budget, gotchas |
| `references/higgsfield-pipeline.md` | Uploads, prompts, costs, leak patching, sandbox assembly, gotchas |
| `references/case-turismo-c19r.md` | The complete C19R project: timeline, prompts, leak map, IDs, costs |
| `references/case-turismo-black-friday.md` | The Black Friday compositor remake: client rounds, master footage, wheel-row prompts, sandbox gotchas |
| `scripts/compositor/` | `bf_draft.py` (frame compositor and typography), `bf_sound.py` (score on onsets), `frame_match.py` |
| `scripts/ref_sheets.sh`, `scripts/audio_map.py` | Reference forensics |
| `scripts/new_project.sh` | Copy the CGI and 2D toolkit and fonts into a new project |
| `scripts/cgi/` | scene, shots, post, sound, bookends, qc, compare, progress, render_sheet, build |
| `scripts/hf_assemble.py` + `templates/hf_plan_turismo_c19r.json` | Plan-driven assembly |
| `scripts/recolor_car.py` | Repaint the car body (before/after colour change) without new generations |
| `scripts/camera_motion.py`, `scripts/reel_finish.py` | Reference camera fingerprint; 96 fps ramps, camera moves, grade |
| `assets/fonts/` | Orbitron (Turismo) and Archivo Expanded (wide grotesk), both OFL |

Brand tokens for Turismo live in the youtube-edit skill: `references/BRAND-TURISMO.md`.
