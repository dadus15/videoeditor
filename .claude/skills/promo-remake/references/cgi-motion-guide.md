# CGI motion guide (Blender, headless)

The guide film carries the reference's exact cut, camera moves and timing into the AI pass. It needs readable
geometry and composition, not beauty. The stand-in product should have roughly the right silhouette (a wheel: rim,
lip, spokes, hub, cap). Its *design* will be repainted, and anything distinctive in it, such as hex nuts, a black
cap with text or a star pattern, is what leaks into the AI output. Keep the stand-in plain where you can.

## Setup

```bash
pip install bpy numpy opencv-python-headless pillow scipy    # bpy 5.x = Blender as a Python module, CPU Cycles
scripts/new_project.sh /path/to/project                      # copies cgi/ and fonts
python3 cgi/make_textures.py                                 # logo/cap/lip textures from assets/brand
```

`make_textures.py` expects `assets/brand/turismo_end_card_gemini.jpg`; change `CARD` and the crop boxes for
another brand.

## scene.py essentials (lessons)

- **World:** use a white studio with a dark horizon band and dark side flags in the world shader, so metal reads
  through dark reflections.
- **Lights:** a key softbox, a side strip and a kick light. **Never** put a big fill panel behind the camera: every
  finish turns into chrome.
- **Floor:** a shadow catcher with `visible_glossy = visible_diffuse = False`. Otherwise the 30 m white plane
  reflects into the metal and washes out every finish. This was the cause of "everything looks silver".
- **Background:** use `film_transparent` and composite the studio white, vignette, fades and ghosts in 2D
  (`post.py`). That is cheaper and fully controllable.
- **Animation:** keyframe every frame with LINEAR interpolation (set
  `preferences.edit.keyframe_new_interpolation_type`). Keep the camera in quaternions with sign continuity, so
  motion blur doesn't flip.
- **Sharp edges:** use `mesh.set_sharp_from_angle()` (Blender 4.1+), plus a Bevel modifier (angle limit) and a
  Weighted Normal modifier on spokes and nuts.
- **Text on curved parts** (lip engraving): use a polar UV in the shader (atan2 → U, radius → V) on an image strip.
  Turn the words in the lower half 180° so they read upright.

## shots.py

Each shot has a frame count, a finish and `cam(t)`, returning loc, target, roll, lens, spin, optional fstop
(enables DOF) and yaw. Use `blur` for whips (Cycles motion blur, shutter 0.5–1.0) and `floor` for standing wheels.

**Framing lessons from the Vossen rebuild:** the reference was much tighter than the first guess. Low macros put the
camera about 0.3 m from a 0.52 m wheel with a 22–28 mm lens, the hub just out of frame. "Hero" shots fill the frame.
Full-wheel montage shots sit at 1.25–1.3 m with a 50 mm lens. Line-ups have a flat row and a small yaw (−12°).

## Render budget (4-core cloud CPU, Cycles + OIDN)

| Pass | Settings | Time |
|---|---|---|
| Previz | 216p, 4 spp | about 1.6 s/frame, about 18 min for the film |
| Guide / CGI master | 720p, 16 spp | 17–25 s/frame, about 3 h for 679 frames |

Most of the cost is per-frame overhead and denoising, so lower spp alone doesn't help much.

- Run long renders detached (`nohup setsid python3 cgi/shots.py -- --res 720 --spp 16 --skip-existing &`).
- Report progress with `cgi/progress.sh`, which shows a bar, the current shot and an ETA.
- `--skip-existing` resumes after an interruption, but a half-rendered shot restarts from frame 1.
- The client said 3–4 h is too long. Next time render the guide at the lowest resolution that keeps the AI output
  sharp (test 432p), or skip the 720p CGI master entirely when the deliverable is the AI version.

## QC of the guide

Compare against the reference with `cgi/compare.sh film.mp4 compare.mp4`, a side-by-side with timecodes.
Grab 8 stills per sheet at the same timestamps from both and fix framing shot by shot.

## Gotchas

- `pgrep -f pattern` inside a loop, or `pkill -f`, matches its own shell. Wait on the real python PID
  (`ps -eo pid,cmd | grep "[p]ython3 cgi/shots.py"`).
- **AgX view transform:** keep `AgX - Medium High Contrast`. Standard clips the highlights.
- **Previz vs final:** only the resolution and spp change, so framing approved in previz holds.
