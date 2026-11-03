---
name: youtube-edit-brand-turismo
description: "Turismo Wheels brand tokens, assets and rules for edits."
---

# Turismo Wheels: brand notes

| Token | Value | Use |
|---|---|---|
| Primary ink (navy) | `#0A1B2B` | Logo body, tagline text on white |
| Accent (red) | `#C7222A` | The logo's square, the accent word (e.g. STYLE), thin rules |
| Background | White `#FFFFFF` | Intro logo card and end card |
| Typeface for added copy | DM Sans 700, tracking +16 % (tagline); 500/700 for titles | |
| In-film title accent | Cyan `#0AF0F0` hairline only (house style); the brand red stays on the white cards | |

- **Logo:**
  - The supplied logo file is only 280×280 px and heavily compressed. The contact/end card contains the same logo at about 2× the pixels (box `[190, 70, 600, 312]` in the 768×1376 card).
  - Use that copy, re-inked in the two colours above (`bookends.py` `clean_logo`). Never recolour or redraw it beyond that.
- **Tagline approved by the client:** **UNLOCK YOUR STYLE**, with STYLE in red. Earlier copy also approved: "One detail. / A whole new character."
- **Model naming in titles:** `AUDI S8 D4` / `TURISMO WHEELS · INVENTA`. Don't add horsepower figures, wheel sizes, prices or performance claims unless the client supplies and verifies them.
- **End card** (`assets/brand/turismo_end_card_gemini.jpg`, 768×1376, AI-generated):
  - It shows a **different multi-spoke wheel, not the Inventa**. Flag this whenever the film is about a specific model, and offer to swap in a model-matched card.
  - Its contact details are baked into the image.
  - Wheel centre and radius in card pixels: `[383, 633.5, 262]`.
- **Language:** the card's call to action is in Polish ("SKONTAKTUJ SIĘ Z NAMI DLA INDYWIDUALNEJ WYCENY"). Keep the added copy in English unless asked.

## Additions from the C19R promo (Nov 2026)

- **Typeface for title cards: Orbitron** (OFL, `assets/fonts/Orbitron-500/700/900.ttf`). It is the closest open
  match to the TURISMO wordmark: wide, rounded-rectangle letters. It replaced the Vossen-like wide grotesk at the
  client's request.
  - Orbitron has no `·` or `®` glyphs. Draw the middle dot as a small square, and use the logo artwork instead of
    typing ®.
- **Title-card system** (from the Vossen HF reference): red label (`#C7222A`), navy bar (`#0A1B2B`) with the
  words solid / outline / solid, thin corner brackets, and the GT logo mark under the bar's right end. The copy
  used was "TURISMO WHEELS · C19R" / UNLOCK YOUR STYLE.
- **Products with client renders** (`assets/product/`):

  | Product | Renders | Design |
  |---|---|---|
  | Turismo Forged C19R | Neodyme bronze, G-SR silver | Five Y-split spokes with webbed branches, windowed outer lip (about 24 pockets), silver cap with engraved dark GT logo, five open lug holes |
  | Turismo Inventa | Seen only on the client's Audi S8 film | Five-point star of ten blades |
- **Claims still unconfirmed:** "6 EXCLUSIVE FINISHES" (mirrors the reference). Ask before reusing it.
- **For AI or CGI promo remakes of a reference ad**, use the `promo-remake` skill.
