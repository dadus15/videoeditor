---
name: youtube-edit
description: Plan, edit, render, review, and refine YouTube videos and short vertical product films (Reels, TikTok, Shorts) from raw or already-edited footage using this project's editing tools and style rules. Use for hook edits, full video edits, automotive or product spots with a brand intro and end card, music and sound-effect sourcing, timestamped revision notes, and updates to the editing workflow or style guide.
---

# YouTube editing

Create a polished first cut from the supplied footage, then revise it from the user's timestamped notes. Treat the project files and available tools as the source of truth: inspect them before editing, and do not claim a render or feature exists until you have verified it.

## Project references

Use the bundled files in `references/` when relevant:

- `STYLE-GUIDE.md` contains the full visual, motion, camera, sound, and cut preferences.
- `PROMPTS.md` contains example prompts for setup, editing, notes, and saving learned preferences.
- `SETUP.md` explains the intended local tool setup.
- `README.md` describes the original kit and its components.
- `AUTOMOTIVE-SHORTS.md` is the detailed playbook for short product or automotive films: source forensics, framing, transitions, brand bookends, audio, QC, and gotchas. Read it before any non-talking-head product edit.
- `BRAND-TURISMO.md` holds the Turismo Wheels brand tokens and asset notes.

## Tools in this skill

These scripts are in `scripts/` and were verified on a real project. Run them from the **project root**: paths in an EDL are relative to the root, and fonts come from this skill's `assets/fonts/` (DM Sans 400/500/700, OFL). Requirements: `ffmpeg`, and Python with `numpy`, `opencv-python-headless` and `pillow`.

| Script | What it does |
|---|---|
| `analyze_motion.py <video> <csv>` | Per-frame brightness and median optical flow. Use it to map shots, baked fades, and motion direction. |
| `unique_frames.py <video>` | Detects the real film frames inside a screen capture or variable-frame-rate file, and reports per-shot frame counts. |
| `compose.py <edl.json> <out.mp4> [--bpm N] [--crf N] [--audio wav]` | The 9:16 compositor. Shot lengths are in beats; it re-times film frames 1:1 at the EDL fps, then renders windows, pushes, aperture moves and titles. It also writes `<out>.timeline.json` with cue points. |
| `bookends.py <edl.json> <film.mp4> <out.mp4>` | Brand intro (logo, tagline, push-slide) and end card (iris from the product, light sweep). Configured by the EDL's `bookends` block. |
| `mix_audio.py <timeline.json> <out.wav> --music-drop S` | Mixes music and SFX to the cue points, targets −14 LUFS with true peak below −1 dBTP, and reports a phone-speaker check. |
| `finish.sh <drop_s> [bpm]` | Runs every `edit/edl_*.json` through film → bookends → mix → mux, naming each output from the EDL's `output` field. |

`templates/edl_automotive_example.json` is a complete, approved EDL to copy and adapt. The original kit's cutting, transcription and HyperFrames tools are **not** included. Check whether they're installed before planning a talking-head edit around them.

## Start each edit

1. Inspect the project for its scripts, dependencies, assets, and prior edits. Use existing project tools when available; don't invent script names or assume a tool is installed.
2. Identify the source clips and their intended order. Ask a focused question only when a missing detail blocks editing; otherwise make a sensible, reversible choice and state it.
3. Review the footage and transcript, if available. Keep the last take of each line. Remove long dead air and waiting in live demos while preserving meaning and natural delivery.
4. For screen recordings, use supplied recordings or open the named Tella recordings if that integration is available. Use real pages and apps when the narration names them; never fabricate screenshots or page details.
5. Build the edit with the project's available HyperFrames and FFmpeg workflow, then render and inspect the output. Confirm the render completed and check for missing media, unintended flashes, bad crops, audio problems, and other visible errors before reporting completion.

For a short hook, prioritize a clear opening, tight pacing, and only the strongest visual moments. For a full video, preserve the supplied clip order unless the user asks for a different structure. Show the result of a demo rather than its waiting time.

## Short product and automotive films

When the footage is a product or car film with no voiceover, follow `references/AUTOMOTIVE-SHORTS.md`. The brief overrides the talking-head defaults below: no 40 % full-screen-animation rule, no lo-fi default, and push-ins anchored on the product instead of the top of frame. The bans on accidental flashes, bounces, flips, and whooshes under text still apply. The essentials, all approved by the client:

- **Forensics first.** Treat any supplied file as possibly already edited or screen-captured:
  - Detect letterboxing per shot, not over the whole file, because a player's zoom mode changes it mid-file.
  - Find player overlays: messages, speed badges, end screens with UI.
  - Find baked fades with a brightness trace, and baked music with a spectrogram.
  - Never layer new music over baked music; drop it.
- **Native cadence.** Count unique frames per shot. If the film is 25 fps inside a ~40 fps capture, deliver at 25 fps with one film frame per output frame. A 30 fps output repeats every 6th frame and stutters.
- **Respect low resolution.** Don't blow every shot up to full 9:16:
  - Detail shots go in a 1080×1080 square window (about 4× the source pixels).
  - Wide shots use the full source width (about 2.4×), so the whole car stays visible.
  - Everything sits on a dark, blurred duplicate at about 17 % brightness, at a uniform scale with no stretching.
  - Say plainly that 1080×1920 is a delivery size, not recovered detail.
- **Structure.** Hook on the strongest detail at frame 1, then 2–3 details in the build, then the hero reveal on the drop, held for about 2 s. Pair shots by motion direction in the rhythm section, include one relaxed shot, then the signature shot with titles. Close with a move that loops back to the opening.
- **Three treatments maximum.** A sub-pixel push anchored on the product; a square-to-wide "aperture" reveal anchored on the product; a masked title reveal with a cubic ease-out over about 0.7 s. No speed ramps or frame interpolation on jittery sources (they warp spokes), and no generated product detail.
- **Brand bookends**, when the client supplies a logo or contact card:
  - Open on a white logo card with a two-colour tagline rising out of a mask.
  - Push-slide into the film in the opener's motion direction.
  - End with an iris centred on the product (the wheel) that zooms *through the hub* into the card, then one light sweep and a hold. The loop runs white card to white card.
  - Take the sharpest copy of the logo available; a contact card often carries a bigger one than the logo file. Re-ink it in the sampled brand colours.

## Visual style

- Use DM Sans at weights 400, 500, and 700 when the bundled font is available. Use white text; cyan `#0AF0F0` for highlights; deep blue `#0005EE` as a gradient end or word block with white text; magenta `#CD00EE` for punchlines; and amber `#FFB904` for money and stakes.
- Never place dark-blue text on a highlight. Use at most one gradient per frame.
- Use a single line of text near the bottom by default. Make key words cyan. Avoid list panels: turn list items into individual visual elements, diagrams, or animations.
- Use frosted-glass cards, choosing a light treatment on dark scenes and a dark treatment in bright rooms.
- Do not use the speaker's face as the default background. Use full-screen animation for at least 40% of a talking section when it supports the narration.
- When narration mentions a person or job, show roughly three seconds of relevant B-roll. When it names an app, show a clean designed window; when it names a website or post, show the actual page in a browser-style window.
- Set headlines in bold with a thin stroke in the same color. Write large numbers in full (for example, `$207,000,000`), in white, and animate counting up when appropriate.
- On brand cards, a brand's own colours replace the palette above. For Turismo: navy text, with red only on the accent word and rule (see `references/BRAND-TURISMO.md`). Keep titles clear of the product and of the Reels/TikTok UI zones: nothing important below y≈1450 or in the right-hand 120 px.

## Motion, camera, and sound

- Bring elements in over about 0.4 seconds with a soft ease-out; remove them over about 0.35 seconds. Avoid bounces and flips.
- Time each animation to its spoken word, landing a beat before the word. Vary animation types; don't repeat the same type twice in a row.
- Keep the overall pace restrained: about seven animations and seven camera moves per 90 seconds. Never use flash cuts.
- Anchor zooms near the top of frame so the speaker's head stays clear. Use 118–125% for a brief key-word punch-in (about a third of a second), or 110–112% over 5–10 seconds for a slow creep. Return to 100% at every cut.
- Default to silence. Use sound only when it fits the action: a light pop for a logo landing, a click for a cursor click, typing only while someone types, and a very quiet cha-ching for money. Never add whooshes under text.
- Use tense, restrained music under a hook, then low lo-fi music ducked under speech when suitable. Respect the user's available licensed music sources; do not imply that music is included with this project.
- For product films: dark electronic, cinematic bass or minimal industrial music, with its drop on the hero reveal. Add a short impact on frame 1, a subtle riser that *ends* on the reveal, a deeper sub accent on the reveal, and at most a few quiet textures on real movement. No engine sound on a stationary car.

## Music and sound sourcing (Epidemic Sound)

- Search works through the connector. Downloads can fail in two separate ways:
  1. The account returns `FORBIDDEN` (no download rights).
  2. The network blocks `audiocdn.epidemicsound.com`. That host serves previews, downloads and track edits, so allow it in the environment's network settings.
- When blocked: finish the picture edit, write an `AUDIO_REQUEST.md` with exact slot filenames, item titles and IDs, and request those files. Name renders `..._PICTURE-LOCK.mp4` so a silent cut isn't posted by mistake.
- **Never name a track as "chosen" or "used" unless you have heard it.** Metadata-based shortlists must be labelled as not auditioned.
- `EditRecording` with `requiredRegionsAtOffsets` can place a track's drop exactly on the reveal and cut the track to length on the server.

## Review and learn from notes

1. Watch the full rendered edit before giving a summary or making a final claim.
2. Apply revision notes at their stated timestamps. Translate plain-language feedback into a specific edit, then re-render and review the affected section and the full result for continuity.
3. Remove accidental flashes and confusing or excessive sounds. If the edit feels busy, reduce motion and sound rather than adding more effects.
4. When the user says to learn from the notes or save them to the skill, add only reusable preferences that are supported by their feedback. Update the relevant project style or editing rules, and preserve existing rules unless the user changes them.
5. When given a replacement style guide, follow its filled-in preferences. Leave blank entries at the project's current defaults. Update relevant style tokens in the actual composition code only if that code exists; verify the changed output.
6. Machine QC on every render (commands are in `AUTOMOTIVE-SHORTS.md`):
   - Frame count and duration; no black frames (`blackdetect`).
   - No single-frame flashes (a frame that differs from both neighbours).
   - Even cadence (no repeated frames on moving shots).
   - Cuts on the planned frames; no player text or badges inside the crops.
   - Frame 1 shows the subject.
   - The last frame and the first frame read as a loop.
   - Audio: true peak ≤ −1 dBTP and a phone-band level check, with the audio padded to the full video length so `-shortest` keeps every frame.
7. Look at transitions as still frames at full resolution, not just as contact sheets. Example: an iris that scaled a white-backed card up from tiny looked like a pasted cut-out until it was changed to zoom through the hub.

## Report

Summarize what was edited, where the rendered file is, and any issues that still affect the result. State which checks you completed. If a required tool or asset is unavailable, explain the concrete blocker and what remains to be done. Files over about 30 MB can't be sent through the chat: keep the full-quality master in `renders/` and send a smaller review copy (CRF 22).
