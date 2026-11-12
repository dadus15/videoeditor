# Case: Turismo Black Friday 2026 (1:1 remake of the @VossenWheels Black Friday Short)

Client verdicts: "Jest sztos" for the production cut, then "Wszystko jest genialne" for final v6c (12 Nov 2026).
The project is in `projects/turismo-black-friday/`. Its README has a section per version, and
`higgsfield_media.json` holds every media and job ID.

This was a **compositor remake**, not a Seedance `video_edit` remake. The film is built frame by frame in Python
(`scripts/compositor/bf_draft.py`) from several sources:

- real footage;
- generated 2K stills with 2D moves;
- two Seedance clips;
- 2D typography.

Use this pattern when the reference is a fast montage of many short shots (12–30 frames each) with heavy
typography. A guide film would cost too much, and most shots only need a still with a push.

## Timeline of the job (each step was a client round)

| Round | Client said | What we learned |
|---|---|---|
| Draft v1–v2 | "almost perfect" | Build the whole film at 0 credits first (screen-recorded footage and renders). The client judges the cut and the type, not the pixels. |
| v3 | "use the car-show footage, add our own WOW, look at competitors" | Watch 5–6 competitor promos. Add brand-unique beats: F1 start lights, a wheel that cuts the red line like a blade with sparks, a beat punch and RGB split on kicks, LINK IN BIO. |
| v4 | sent the reference **trimmed** to its real start and end | Always ask for the exact cut. Our clock was 24 frames off and the film loops (the end card runs into frame 0). |
| v5 | "in the reference the wheels lie flat", "Audi R8 in the final shot" | Look at each wheel shot's **pose**: flat, standing, stacked or exploded. Keyframe = reference frame + product render. |
| v6–v8 | specific cars per second, final copy | The client maps scenes by **second**. Convert second → film frame → shot letter, and check with a strip of ours against the reference at the same frames. |
| Final v4 | "inserts are blurry, grainy, pixelated" | Screen recordings (230–370 px) are never good enough for a paid ad. |
| Final v5 | "AI-sharpened inserts look unnatural" (wheel sits beside the car, odd interior) | **Never re-imagine real footage with an image model.** It changes geometry: the wheel moves off the car. Use the real footage. |
| Final v6 | "still poor next to the original's razor sharpness — find it online" | Find the **original masters** (the client's own YouTube channel). Download 4K or 1080p50 and frame-match. |
| Final v6c | "10 s wheels look like flat patterns with no barrel, one model only, the floor is wrong" | Generated wheel rows need: different client models, an explicit barrel, and a floor described from the reference. |

## Real footage at master quality

- **yt-dlp in the Higgsfield sandbox.**
  - Most videos download with the default client.
  - An embed-only video ("not available") needs `--js-runtimes node --remote-components ejs:github --extractor-args "youtube:player_client=web_embedded" --referer https://<client-site>/`.
  - Fetch only what you need with `--download-sections "*0-50"` and the 4K format (313 webm) or 1080p50 (299).
- **Frame match.** `scripts/compositor/frame_match.py clip.mp4 master.mp4 25 <t…>`, at 96×54 grey correlation.
  Scores were 0.89–0.99. Then confirm with a timecoded 10 fps strip.
- **Cutting.**
  - Put `-ss` **and** `-t` *before* `-i` for an exact window. A `-t` after `-i` combined with filters gave 16
    frames instead of 20, so the last frame held.
  - Slow motion: `setpts=PTS/0.62,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1`. Start **after** any
    scene cut in the source; minterpolate blends across a cut and leaves a ghost on the first frame.
  - Count frames with `ffprobe -count_frames` every time.
  - Check for objects crossing the frame (a pole crossed at 13.3 s) and cut before them.
- **Sharpening.** Do not sharpen 4K material, only Lanczos-downscale it. Use an unsharp mask (0.35, σ 1.6) only
  on sources under 1500 px.
- **Removing a third-party advert** (the TENZI plate frame on the R34 rear):
  1. Track a template per frame (`cv2.matchTemplate`, ±300 px search).
  2. Fill the box with the median colour of a ring above and below it, plus matching grain.
  3. Blend with a Gaussian-feathered mask.

  Ask the client whether to cover or keep such a frame; they chose to cover.
- **Public repo.** Excerpts committed to a public repo are public. Tell the client and offer to remove them.

## Generated stills (gpt_image_2_6, high, 2k, 2.75 credits each)

- **References.** First the reference frame (composition, light, floor), then each product render.
  - Say "Recreate exactly the composition, camera and lighting of the first reference image".
  - Then assign every product to a position: "FRONT RIGHT = the wheel from the second reference".
  - Ban copying the reference's text, logos and UI icons.
- **Wheel rows look flat unless you say otherwise.** The prompt that fixed it:
  - "bare forged wheels (no tyres) STANDING upright on their outer lips";
  - "each turned about 30 degrees toward the camera so the full depth is visible: the face, the polished outer
    lip AND the deep cylindrical barrel behind the face, like real solid 3D wheels, not flat discs".
- **Product variety.** If the reference shows three wheels, use three different client models. Ask the client
  for the line-up up front.
- **The floor and light come from the reference, in words.** For example: "wet grey polished concrete with a
  large shallow puddle, mirror-like reflections, droplets, bright grey foreground falling off to black, a thin
  red glow behind the back-left wheel".
- **Variants.** Make 2 for 5.5 credits, for example with two wheels swapped, and keep the other as a free
  alternative.
- **Size.** The 1520×2688 output resizes to 1080×1920 with negligible squash. With a 2D push, start the zoom at
  1.04 or more when panning ±20 px, so no border shows.

## Seedance where real motion matters

- **Final walker shot and title background.** Seedance 2.5 `omni_reference` from a gpt keyframe.
  - First a **draft** (`draft: true`): 480p, 4 s, 12 credits.
  - Then finalise the *same take* with `draft_job_id` at 1080p (64 credits).
- **Person in front of the type.** With a locked-off camera, take the matte from the difference against a
  temporal-median plate, at half resolution. The walker then passes in front of the date card, as in the
  reference.
- **Scene spec.** Write a JSON scene spec before generating (`final_scene_audi_r8.json`), covering camera, lens,
  environment, car, person, wardrobe, action and constraints.

## Typography and copy

- **Reference layout, client copy.** Mirror the reference exactly: a HUD title card, a red label, SAVE UP TO /
  amount / unit, a red square with typed dates, and a © footer. The words come from the client.
- **Prices.** Use plain digits, as the reference does. The "spinning wheel zeros" gimmick was dropped once the
  copy was final.
- **Unconfirmed claims.** Keep a list of claims to confirm, for example "WORLDWIDE SALE", "ON ALL FORGED WHEELS",
  and a single date versus a range.

## Score

`scripts/compositor/bf_sound.py` synthesises a licence-free score on the reference's measured kick onsets:

- the drop at 2.10 s;
- the hard stop on the final shot at 14.10 s;
- an outro bed from 17.2 s that loops into frame 0;
- an F1-light thump per light, a "lights out" sub drop, and grinder sparks for the blade.

It is normalised to −14 LUFS with a −1.5 dBTP ceiling.

## Higgsfield sandbox mechanics (what bit us)

- **Timeouts and background jobs.**
  - Foreground `sandbox_exec` runs for at most 120 s.
  - Renders and encodes go with `background: true`. Poll `/home/user/.bg/<id>.exit` with a loop such as
    `for i in $(seq 22); do [ -f … ] && break; sleep 5; done`.
- **Persistence.** `/home/user` persists across sandbox restarts and between standard and XL sandboxes.
- **Previews.** Pass `image_paths` (≤512 KiB in total) to look at contact sheets. That is the only way to see
  sandbox pixels from this session.
- **Never `cp` frame folders while a render writes to them.** It overwrote fresh frames and truncated PNGs.
  - Render into a fresh folder or with `--frames a,b,c --force`.
  - Check every PNG's IEND trailer before encoding.
- **Code into the sandbox.** Commit, push, then `curl raw.githubusercontent.com/<repo>/<sha>/…` (`sync.sh <sha>`).
  Pinning the SHA avoids a stale CDN cache.
- **Local files to Higgsfield.** This container cannot reach `upload.higgsfield.ai`.
  1. Commit the file (it must be fine to be public).
  2. `curl` it into the sandbox.
  3. `media_upload`, then `curl -X PUT -H "If-None-Match: *" --upload-file` from the sandbox.
  4. `media_confirm` with `type` (`image` or `video`) and `media_ids`.

  Alternatively, use `media_upload_widget` as the only tool in its turn.
- **A bad upload.** Do not confirm a slot that holds a bad file. Request new slots, and record the abandoned IDs.
- **Fetching results.** `jobs_wait` takes `jobs: [{index, job_id}]` with a timeout of at most 15 s. Download
  result PNGs inside the sandbox with curl.

## Deliverables and QC

- **Master.** 1080×1920, 30 fps, H.264 High CRF 16, preset slow, yuv420p, AAC 256k 48 kHz, `+faststart`.
  - 563 frames, 18.77 s.
  - `blackdetect` must report 0.
- **720p.** Encode from the same PNG frames, `scale=720:1280:flags=lanczos`, CRF 17. Do not re-encode the
  1080p MP4.
- **Side-by-side with the reference for every final.**
  - Reference `trim=start_frame=28:end_frame=591`, 540×960 each, `hstack`, with VOSSEN and TURISMO labels.
  - The client's "do all frames match?" is answered with it, plus an honest table of content deviations.
- **TikTok.**
  - `tiktok_connect` links expire in about 10 minutes, so issue one only when the client is ready.
  - Publish only after explicit approval, through `tiktok_prepare_publish`.

## The missed glyph

The footer "© 2026 TURISMO WHEELS" showed "□ 2026" in every version up to v6c, because Orbitron has no ©. It was
caught only by looking at a 720p still. Fix: draw © as a ring plus a C, and run the small-print crop check from
the QC list in SKILL.md.

## Credits

| Stage | Credits |
|---|---|
| Draft | 0 |
| v5 keyframes and draft | ≈40 |
| Production (title + final shot at 1080p, keyframes) | 142.75 |
| Final v4 AI inserts (later rejected) | 16.5 |
| Final v6c wheel row | 5.5 |

The YouTube masters cost nothing. That is the lesson: look for the client's original footage before generating
anything.
