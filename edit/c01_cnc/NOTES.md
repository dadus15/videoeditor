# Turismo Forged C01: "Wykute. Nie produkowane." (9:16, 30 s, no music)

Render: `renders/Turismo_Forged_C01_CNC_9x16.mp4` (1080×1920, 24 fps, H.264 + AAC, −14.2 LUFS, true peak −2.0 dBTP).
Rebuild: `python3 edit/c01_cnc/assemble.py source/c01_cnc renders/Turismo_Forged_C01_CNC_9x16.mp4`

All footage is AI-generated (Higgsfield). Keyframes: GPT Image 2.6 with the client's C01 photo
(`source/c01_cnc/keyframes/C01_reference_brushed-grey.png`) as the design reference. Motion and sound: Kling 3.0 Pro,
image-to-video, native 24 fps.

| Time | Shot | Clip (source in–out) | Sound |
|---|---|---|---|
| 0.0–5.0 | Billet drops into the CNC chuck, locked camera; impact at 1.64 s | `s1.mp4` 0–5 | impact, ring, hum (−13 LUFS) |
| 5.0–14.0 | Milling the C01 spokes, chips and coolant, tracking shot. Title 7.0–10.6: "Jeden kęs aluminium 6061" | `s2.mp4` 0–9 | spindle whine, cutting (−13) |
| 14.0–18.0 | Pull-back, machine reveal | `s3.mp4` 0.5–4.5 | machine (−14) |
| 18.0–18.5 | Hard cut to black and silence | slate | silence |
| 18.5–26.0 | Finished wheel (matte black spokes, polished lip, Turismo cap) in darkness, slow orbit (shots 4+5 as one move) | `s45.mp4` 0–7.5 | silence |
| 26.0–30.0 | Lowered black CLS 63 widebody on C01, dark garage. Title from 26.9: "TURISMO WHEELS / Wykute. Nie produkowane." | `s6.mp4` 0.5–4.5 | V8 idle (−21) |

Finish: one shared cold-steel grade (colour balance toward blue, saturation 0.82), fine temporal grain, titles in DM Sans
with a soft dark halo, hard cuts only.

Decisions and caveats:
- Shots 2–3 show raw machined aluminium (the wheel is not finished yet). Shots 4–6 use the brief's finish: matte black face,
  polished lip. The client photo is the Brushed Grey version; spoke geometry follows it.
- The car is AI-generated. Its front reads close to a CLS / AMG GT 4-door; it is not a photo of a real customer car.
- The CNC process is AI-rendered and is not a record of Turismo's real machines or cycle.

QC passed: 720 frames, cuts at 5.0 / 14.0 / 18.0 / 26.0 s, black only at 18.0–18.5 (intended), no single-frame flashes, no
repeated frames, no music in any clip (spectrogram check), titles clear of the Reels UI zones.
