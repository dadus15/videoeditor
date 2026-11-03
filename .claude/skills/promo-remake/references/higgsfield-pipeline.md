# Higgsfield pipeline (Seedance 2.5 video edit + patches + sandbox assembly)

Everything here was verified on the Turismo C19R project in November 2026. Load the tools with ToolSearch
(`mcp__Higgsfield__*`). Check `balance` first and tell the user the expected spend.

## Network reality in this cloud environment

The session's egress proxy blocks `upload.higgsfield.ai`, `d2ol7oe51mr4n9.cloudfront.net` (inputs) and
`d8j0ntlcm91z4.cloudfront.net` (results). So:

- **Inputs:**
  1. `SendUserFile` the files to the user.
  2. Open `media_upload_widget` as the **only** tool call in that turn.
  3. The user uploads the files and replies with media_ids.

  The widget limits: images in batches; **one video per widget**; one video plus one audio together is fine
  (`type: auto`). `media_upload` + curl PUT from this container fails with 403.
- **Results** cannot be downloaded here. Do all downloading, inspection and assembly in `sandbox_exec`: the
  Higgsfield sandbox has internet, ffmpeg, numpy and Pillow. It has 1 CPU and 8 GB RAM, foreground commands time
  out at 120 s, and background jobs at 15 min.
- **Cleaner alternative:** the user adds those three hosts under the environment's Network access → Allowed
  domains (`read_documentation` topic `environment.network`). Then upload with `media_upload` + PUT from here and
  download with curl. A new session may be needed before the change applies.
- **Uploaded file URLs** inside the sandbox: `https://d2ol7oe51mr4n9.cloudfront.net/<user>/<media_id>.mp4`. Images
  are `<id>_resize.jpg`. An uploaded **WAV is served as `<id>.mp3`** (still PCM inside; ffprobe confirms).

## Models and costs (720p, Nov 2026)

| Use | Model / mode | Cost | Time |
|---|---|---|---|
| Repaint a guide segment with our product | `seedance_2_5`, `mode: video_edit` | billed by source length, about 7.6 credits/s (8.44 s = 64) | 6–15 min |
| Patch shot from photos only | `seedance_2_5`, `mode: omni_reference`, 4–5 s | 28 credits per 4 s, 35 per 5 s | 6–16 min |
| Same at 1080p | | about 16 credits/s | |

There is no standalone music model here: `sonilo_music` is for the game pipeline only, and Suno was not in the
catalogue. Use `cgi/sound.py`.

`video_edit` output is 24 fps and about 0.8 % shorter than the guide. Re-time it to the guide length in the
assembly plan (`retime_to`), and the frame counts come out exact.

## Segment plan

- **Cut points:** cut the guide at natural breaks, white fades or section cuts, into 6–8.5 s pieces. The C19R film
  used 2.56–10.40, 10.56–16.64, 16.64–24.40 and 24.60–33.04 s. Title, end card and white bridges are 2D and never
  go through the AI.
- **Encoding:** CRF 16, at the guide's own resolution.
- **Test first:** run the hero segment as the first test and show the user before batching the rest.

## Prompt template for `video_edit`

Keep the wording close to this; it worked.

```
Video edit. Every wheel in every frame becomes the <BRAND PRODUCT> wheel from the reference images: <exact design in
plain words: spoke layout, face concavity, lip details, centre cap + logo, lug holes>. The original wheel design must
never appear: no <stand-in features: five-pointed star spokes, plain smooth lip, black centre cap with text, hexagonal
nuts>, not even in the shortest flash cuts of two or three frames or motion-blurred frames. Keep every source cut point,
camera move, framing, timing, spin direction and motion blur exactly. Shots: <ordered list of the segment's shots with
the finish of each: "a bronze C19R standing on the floor", "gunmetal close-up", ...>. <Hero finish rule, e.g. "The hero
wheel must stay bronze, not black.">. Seamless white studio cyclorama, soft vignette and contact shadow, soft
product-studio light with dark reflections in the metal. Photoreal high-end product CGI commercial, crisp machined
metal, no text overlays, no car, no tyre.
```

**Request settings:** `medias` = the guide as `video_references` plus product photos as `image_references`, and
`generate_audio: false`. Pass `declined_preset_id` when the server suggests a preset (it suggested "IN THE DARK",
which is wrong for a white studio).

## Leak QC (the step that makes it "Top")

`video_edit` keeps the guide's geometry wherever the guide is detailed and the shot is short. In the C19R run, about
20 % of the frames showed the old design:

- **Line-up of seven wheels:** the whole 2.2 s.
- **Gloss-black flash and lying-flat wheel:** 1 s.
- **High-key ghost hub:** 1.8 s.
- **Cap close-ups in the montage:** 0.25 s each, showing the old cap with text and the hex nuts.
- **First 0.65 s of the dark hero.**
- **Last 0.6 s of the whip into the cap.**

Everything else was a clean C19R, including complex macros of the windowed lip.

Workflow in the sandbox:

```bash
ffmpeg -i aiN.mp4 -vf "fps=5,scale=256:-1,tile=8x5" -frames:v 1 -q:v 5 aiN_sheet.jpg      # pass via image_paths
ffmpeg -ss S -t D -i aiN.mp4 -vf "fps=12,scale=200:-1,drawtext=...:text='%{pts\:flt}',tile=8x2" ... # pin ranges
```

- **Size limit:** keep each `image_paths` call under 512 KiB in total. Two 2048-px-wide sheets is the limit, so
  send three or more in separate calls.
- **Converting times:** a sheet time inside a segment maps to film time as `seg_start + t × guide_len / ai_len`.

## Patches

- **What to generate:** one `omni_reference` clip per leaking *type* of shot, not per leak. One hub macro clip
  served four slots.
- **Prompt:** describe framing, motion, finish and any whip at the end ("in the last second it spins very fast
  with strong motion blur"), and give the product photos only.
- **Using them:** take the needed frames in the plan (`in`, `speed` for whips, `span` to slow a clip). Re-apply
  fades and ghost treatment in the assembly rather than asking the AI for them.
- **Trimming instead:** if the first part of a long shot leaks, start the clip later and stretch it (`span`) rather
  than regenerating.
- **Line-ups:** the AI generated a line-up in perspective rather than a flat row. That was accepted, but flag it.

## Assembly and delivery (sandbox)

1. **Download.** Inside the sandbox, `curl` the results (`result_url`) and the uploaded bookends and score into a
   workdir.
2. **Install the script.** Write `hf_assemble.py` there with a heredoc. Code is text and fine to paste; media bytes
   are never relayed as text.
3. **Write the plan.** Copy `templates/hf_plan_turismo_c19r.json` and edit the sources and timeline.
4. **Build.** Run `python3 hf_assemble.py plan.json --extract`, then `--stills a,b,c --sheet check.jpg` (inspect
   it), then `--out Master.mp4` in the background. The encode takes about 75 s for 35 s at 1080p.
5. **QC:** ffprobe, `blackdetect`, `ebur128`, a full fps-2 sheet and an fps-10 sheet of the ending.
6. **Deliver:**
   1. Call `media_upload` (filename `<Name>.mp4`) *before* the PUT.
   2. In the sandbox, run `curl -X PUT -H "Content-Type: video/mp4" -H "If-None-Match: *" --upload-file Master.mp4
      '<upload_url>'` and expect 200.
   3. Call `media_confirm`.
   4. Share the returned `url`. The file is also in the user's Higgsfield library.
7. **Record ids.** Put every media_id and job_id in the project's `cgi/higgsfield_media.json` and commit it.

## Gotchas

- **Polling:** `jobs_wait` waits at most 15 s. To poll without spamming, run a background `sleep 120` with Bash and
  check again when it completes.
- **Sandbox persistence:** the sandbox can be replaced (`sandbox_id` changes). The Modal workspace keeps
  `/home/user` files, but running processes die. If `sandbox_created: true`, re-download the inputs.
- **Session restarts:** after a worker restart the Higgsfield MCP reconnects after a moment. Re-load the tools with
  ToolSearch.
- **Finish drift:** the AI swaps finishes when a segment mixes several. Name each shot's finish in the prompt.
