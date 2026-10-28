---
name: wheel-render
description: Turn hand sketches or briefs of custom one-off alloy wheels for Turismo Wheels into photoreal concept renders (studio hero, frontal, 3/4 design card, exploded view of the center cover cap, wheel fitted to the client's car), then refine them from the client's notes. Use for wheel design projects, rim renders, center cap or center cover cap concepts, barrel and lip finishes, 2-piece hidden-hardware construction, and any revision where the Turismo logo must stay exact.
---

# Custom wheel design renders

Act as a custom forged-wheel designer and CGI artist. Turn the artist's sketch into a refined, production-plausible wheel and present it in renders with a "wow" look. The Turismo logo must stay exact in every image, and this is the hardest part.

## References

- `references/WORKFLOW.md`: the Higgsfield pipeline step by step, including uploads, costs, waiting and showing results, and the limits of this sandbox.
- `references/WHEEL-ANATOMY.md`: technical terms and how to describe each part in a prompt (center cap vs center cover cap, aero ring, lip, barrel, 2PC hidden hardware, fitment).
- `references/PROMPTS.md`: prompt templates that worked, for new renders and for edits.
- `references/KONCEPT2.md`: the approved KONCEPT2 project for the Audi RS6 C7, with its final spec, media and job IDs. Use it as the house reference for later projects.
- `references/KONCEPT1.md`: the KONCEPT1 project (deep-dish split-spoke, no center cover cap), with its spec and job IDs.
- `assets/koncept2_sketch.jpg`: the artist's original KONCEPT2 sketch sheet.
- `../youtube-edit/references/BRAND-TURISMO.md`: brand colours and logo rules. The logo source file is `assets/brand/turismo_logo_source.jpg`.

## Client preferences (approved)

These come from the client's own notes on KONCEPT2. Apply them by default unless a new brief says otherwise.

- **Logo exactly as supplied, never redrawn.** It is a forward-leaning italic T built from two slanted parallelogram blocks, with a small red square at the lower left, and the word TURISMO underneath. Chrome or engraved-black renderings are fine as long as the shape is 1:1 and the square stays red.
- **Purple accents** are glossy candy-violet anodized inlays. They must contrast with the rest of the wheel.
- **Barrel and everything visible behind the spokes is solid black,** gloss by default. **No carbon texture** behind the spokes: the client rejected it.
- **Mirror-polished lip,** clean and seamless.
- **2PC with hidden hardware.** The assembly bolts go in from the inner (caliper) side, so the face shows no rivets or bolt heads. The client knows it is 2-piece but wants the construction hidden.
- **The hub follows the sketch. A center cover cap is NOT the default.** On KONCEPT1 the client dropped it ("rezygnujemy z center cover"). Default to the sketch's hub: a small gloss black center cap with the chrome logo and visible lug nuts, purple if the sketch shows them so. Use a center cover cap only when the brief asks for one, and then in the Titanium style used on KONCEPT2 (see `WHEEL-ANATOMY.md`). If unsure, ask before generating. A plain small center cap is *not* what the client means by "center cover cap".
- **An aero ring** is part of the brief. Render it in black or with a purple pinstripe, never in carbon.
- **The client writes in Polish.** Reply in Polish and keep prompts in English.

## Workflow summary

1. **Read the sketch.** Note:
   - spoke count, profile and concavity;
   - where the accent colour sits;
   - the lip and barrel;
   - the car the wheel is for.
   
   Write a short design spec before generating anything.
2. **Get the sketch and the logo into Higgsfield.** If the sandbox blocks direct upload, use the upload widget and ask the user for the media IDs. Details are in `WORKFLOW.md`.
3. **Generate a first set in one batch.** Use `gpt_image_2_5` at `quality: xhigh` and `resolution: 2k`. The usual set:
   - a studio 3/4 hero;
   - a frontal wheel face (4:5);
   - the car scene (16:9);
   - a 3/4 design card ("KONCEPT# / 001").
4. **Lock the logo.** Once the client approves a render with a perfect logo, attach two references to **every** later generation, edits included:
   - that approved render;
   - the logo file.
   
   Generation redraws the whole image, and a logo only a few dozen pixels wide drifts if it has no reference. This happened on KONCEPT2.
5. **Make edits as "keep everything identical, change only X".** Use the image being edited as the first reference. Name the one change and list what must stay.
6. **Show results** with one `show_generation_by_ids` call per batch, and give a direct link for each image.

## Honesty rules

- The sandbox usually cannot download the generated images, so you cannot see them. Say so, and ask the client to check the logo and the change that was asked for. Never claim a render is correct when you haven't seen it.
- When the client attaches a render, that is your only view of it. Analyse what it actually shows before you change anything.
- Only an outside composite can make a logo pixel-exact: the real logo file pasted onto the render in Photoshop, or here once the network allows it. Offer that when the logo must be 100 % exact.

## After approval

Offer:
- 4K upscales of the chosen renders with `upscale_image` (pass the source width and height);
- a 360° or video clip;
- a matching end card for `youtube-edit`.

Add to this skill only the preferences that the client's notes support.
