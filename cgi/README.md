# Turismo Inventa: CGI promo (rebuild of the Vossen Hybrid Forged Series spot)

The client supplied a phone recording of a laptop playing Vossen's *Hybrid Forged Series* promo
(`source/Vossen_HF_reference_phone-capture.mp4`). The brief: reverse-engineer it shot by shot and rebuild it 1:1
for Turismo Wheels.

The Vossen spot is 100 % CGI (wheels on a white studio cyclorama, no car, no people), so this rebuild is CGI too.
No Vossen footage, design or audio is reused. Everything here is generated:

- **Wheel:** a procedural Blender model of the Turismo Inventa. It has a five-point star of ten blades, a concave
  face, a polished lip engraved TURISMO / INVENTA, five lugs and a GT centre cap. It is approximated from the client's
  Audi film; it is not CAD data.
- **Finishes:** six, like the reference line-up: gloss black (polished lip), satin black, hyper silver,
  brushed/polished, gunmetal and bronze.
- **Graphics:** in Turismo colours. The labels use red `#C7222A` and the bars use navy `#0A1B2B`; the reference's
  red label and dark bar map onto them directly. Set in Archivo Expanded (OFL), the closest open match to the
  reference's wide grotesk.
- **Sound:** a synthesised score and sound design (`sound.py`), using no samples and no licensed music.

## Reverse engineering: the reference

**The file:** 848×478, about 60 fps VFR, 34.68 s. It is a handheld phone shot of a laptop screen, and the audio is
the laptop speakers recorded through the phone mic (−36.8 LUFS).

**Player and room artefacts:** a YouTube play/pause icon (1.3–2.0 s), the progress bar, the screen bezel and the
room. None of these belong to the film, so they are not reproduced.

**Look:**
- Background: a near-white studio cyclorama with a soft vignette. The ghost sections are high-key and cool.
- Light: large soft studio light with dark flags. Metal reads through dark reflections.
- Lenses: macro lenses with shallow depth of field.
- Motion: slow pushes and turntable rotations, plus fast "whip" spins with heavy motion blur as transitions.
- Typography:
  - A red label box of letter-spaced caps sits over a dark bar.
  - The bar's three words run solid / outline / solid (`HYBRID` `FORGED` `SERIES`).
  - Corner brackets frame the bar, and a tiny mark sits under its right end.
  - The bar wipes open from the centre, the letters type on behind a block cursor, and dark glitch blocks flicker.

**Sound:** a trailer-style design rather than a song:
- Low impacts on the section cuts: 2.6, 10.55, 16.65, 24.6, 28.55 and 33.05 s.
- Whooshes on the whips.
- A pulsing bass bed.
- A transient on each montage cut, about every 0.25 s.
- Quiet breakdowns under the white fades.

### Shot map (reference time = our time, 25 fps)

| Time (s) | Reference | Turismo rebuild (shot id) |
|---|---|---|
| 0.00–2.56 | Title card: VOSSEN'S ALL-NEW / HYBRID FORGED SERIES | `TURISMO WHEELS · INVENTA` / `UNLOCK YOUR STYLE` (YOUR in outline) |
| 2.56–4.80 | Line-up of 6 finishes whips in from the right, drifts, fades to white (4.0–4.6) | S02: 7 Inventas in 6 finishes, same whip and fade |
| 4.80–6.16 | Low macro on the lower rim, fades in from white | S03 satin black |
| 6.16–6.76 | Whip spin into the hub | S04 |
| 6.76–7.56 | Silver face, 3/4, slow push | S05 hyper silver |
| 7.56–7.76 | Gloss-black 3/4 flash | S06 |
| 7.76–8.52 | Wheel lying flat at a low angle, whip | S07 gunmetal |
| 8.52–10.40 | Full wheel on the turntable turns to the front, fades to white | S08 brushed |
| 10.56–14.30 | Macro along the rim and barrel, tilting onto the lip, fade | S09 gunmetal, lip lettering |
| 14.80–16.64 | Ghost hub fades in from white, trucking left | S10 (55 % opacity, cool high-key) |
| 16.64–20.60 | Finish montage A (16 cuts, 0.08–0.72 s each) | A1–A12 |
| 20.60–24.40 | Dark wheel close-up, slow spin, light sweep, slow fade to white | S11 gunmetal, moving strip light |
| 24.60–28.56 | Finish montage B (the same shots re-cut, plus one dissolve at 27.0) | A*, B5, B7, B12 |
| 28.56–32.72 | Bronze hero, 3/4 turning to the front, slow push | S12 bronze |
| 32.72–33.04 | Whip zoom into the centre cap | S13 |
| 33.04–34.72 | End card: faint blue line drawing of the wheel, AVAILABLE IN / 6 EXCLUSIVE FINISHES | Same; line art from the LINE render |

The exact frames are in `post.py` → `TIMELINE`. The montage cut points drive the ticks in `sound.py`.

## Build

```bash
pip install bpy numpy opencv-python-headless pillow scipy      # bpy = Blender 5.2 as a Python module
cgi/build.sh 720 16          # CGI at 1280x720 (upscaled to 1080p) -> composite -> score -> mux into renders/
cgi/build.sh 1080 24         # full-resolution master (about 2.5x the render time)
```

The steps one at a time:

```bash
python3 cgi/make_textures.py                                  # logo, cap and lip textures -> work/tex
python3 cgi/shots.py -- --res 216 --spp 4 --only S12          # quick previz of one shot
python3 cgi/shots.py -- --res 720 --spp 16 --skip-existing    # all shots -> work/cgi/720/<shot>/f####.png
python3 cgi/post.py --res 720 --out work/film_720.mp4         # composite + titles, writes .timeline.json
python3 cgi/sound.py work/film_720.timeline.json work/score.wav
cgi/compare.sh renders/<film>.mp4 work/compare.mp4     # side-by-side QC against the reference
```

Render cost on the 4-core cloud CPU: about 12–22 s per frame at 720p and 16 spp (denoised). There are 671 CGI
frames, about 3 hours in all. The title and end cards are 2D and render instantly.

## Copy and claims to confirm with Turismo

- **Title:** `TURISMO WHEELS · INVENTA` / `UNLOCK YOUR STYLE`. Both are client-approved copy from the Audi project.
- **End card:** `AVAILABLE IN / 6 EXCLUSIVE FINISHES` mirrors the reference. **The number of finishes is a product
  claim:** confirm that Turismo really offers six finishes for the Inventa, or change `COPY["end_words"]` in
  `post.py` (one line).
- **Finishes shown:** gloss black, satin black, hyper silver, brushed, gunmetal and bronze are illustrative. Swap
  their values in `scene.py` → `FINISHES` for the real catalogue finishes.

## Version 2: AI video of the Turismo Forged C19R (Higgsfield)

At the client's request the wheel became the **Turismo Forged C19R** and the footage became AI-generated video.
The CGI film above is now only the motion guide.

1. **Motion guide:** `work/film_720.mp4` cut into four segments: 2.56–10.40, 10.56–16.64, 16.64–24.40 and
   24.60–33.04 s. They were uploaded to Higgsfield through the upload widget, because this cloud session's
   network policy blocks the Higgsfield hosts.
2. **Video edit:** Seedance 2.5 in `video_edit` mode, 720p. Each segment was edited with the two client renders
   of the C19R (`assets/product/`) as image references and a per-segment prompt naming the shots and finishes.
   This keeps the reference cut, camera moves and timing.
3. **Patches:** a few shots kept the old CGI design (the line-up, the flat wheel, the ghost hub, cap close-ups and
   the cap whip). Those frames were replaced by four short Seedance `omni_reference` clips generated from the C19R
   photos only, with no CGI guide.
4. **2D pieces:** `cgi/bookends_c19r.py` renders the title ("TURISMO WHEELS · C19R" / UNLOCK YOUR STYLE), the
   white bridges, and the end card with a line drawing of the C19R, all in Orbitron.
5. **Assembly:** `cgi/hf_assemble.py` runs in the Higgsfield sandbox. It takes frames at 25 fps and 1920×1080
   (each AI clip re-timed to its source length), adds the patches, the ghost and fade treatments, and the bookends,
   and muxes the score from `cgi/sound.py`. The run takes about 75 s.

Media and job ids are in `cgi/higgsfield_media.json`. The deliverable is in the client's Higgsfield library as
`Turismo_C19R_Promo_16x9.mp4` (media `f226a2a0-4b97-4123-8728-c01e53802d48`): 868 frames, 34.72 s, −14.3 LUFS,
true peak −1.7 dBTP, no black frames.
