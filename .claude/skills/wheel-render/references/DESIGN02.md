# DESIGN 02: Y-spoke aero ring (approved October 2026)

The client's verdict was "wow, ja jestem pod wrażeniem, wyszło perfekcyjnie". This is the house example of a **precise sketch-to-render pass**.

## Source

- Design marked ② on a 4-design pencil sheet (bottom row: frontal and 3/4 drawings).
- The first attempts used the whole sheet and were not precise enough. The client asked for "ultra dokładny" (ultra-precise).

## What made it precise

1. **Analyse an enlarged crop** before prompting. Crop the design out of the sheet with PIL into the scratchpad, upscale it about 2.5× and look at it with Read. Count the spokes, forks, slots, windows, lugs and band widths.
2. **Crop each view separately** (front and 3/4). Send the crops to the user with SendUserFile, then ask them to upload the crops through `media_upload_widget`.
3. **Give the generator only the crop and the logo.** No other designs and no earlier renders, so nothing bleeds in.
4. **Prompt it as a trace.** "Convert the pencil drawing … with IDENTICAL geometry, as if the drawing were traced … change nothing in the design; only turn pencil into real materials", followed by a list of materials for each part.
5. Add a **technical frontal** render with even light on a mid-grey background, so the client can compare it with the drawing.

## Spec from outside to inside

1. **Lip:** thin, mirror-polished and seamless, with no bolts.
2. **Outer face ring:** wide, in brushed light-gunmetal aluminium, with about 20 rectangular windows with rounded corners. The windows are gloss black pockets separated by narrow bridges.
3. **Aero band:** narrower, in candy-violet, with a dashed row of small dark slots along its middle.
4. **Spokes:** 10 slender light-gunmetal spokes with diamond-cut edges. Each has a narrow gloss black lancet slot near the hub and forks into a Y at about 60 % of the radius. The branches land on the bridges of the outer ring.
5. **Barrel:** gloss black behind the spokes and outside.
6. **Lug nuts:** 5, in gloss black. One sits at 12 o'clock, inside the V formed by two spokes.
7. **Center cap:** a thick candy-violet ring around a polished silver cap. The logo is in its **original file colours**: a black T, the red square and black TURISMO. This gave the most faithful logo so far.

## Higgsfield IDs

| What | ID |
|---|---|
| Full sheet (designs 1–4) | `8c1b9920-36bc-4d1c-9e57-a77a648468f6` |
| Crop: design 2, front | `e58f4c78-17be-4fd9-a5e4-ecfb80d59ccc` |
| Crop: design 2, 3/4 | `6f5b91f6-a7b2-461f-a377-732c9748ac81` |
| **APPROVED** front 4:5 | `76fed42e-ab7a-416d-a5a9-ebe3bae96afe` |
| **APPROVED** 3/4 with caption | `43ec586b-d9be-4ddc-97fa-f48b6d1bea8e` |
| **APPROVED** technical front | `f625fb38-ca7c-4f33-b6ba-16615df064cd` |
| RS6 C7 hero scene, 2 variants | `4138b5a0-5637-4256-b418-4a80335ec160`, `c42c1ea9-1184-4a4c-aaff-4b4a88d8316b` |

## Standard car framing ("jak zawsze")

- Edit the approved RS6 scene `8b964fda…`: a low front 3/4 view of a Nardo grey RS6 C7 in a night industrial hall, with violet and white neons, wet asphalt and purple calipers.
- Change only the wheels.
- References, in this order:
  1. the scene;
  2. the approved 3/4 wheel render;
  3. the approved front wheel render;
  4. the logo.
