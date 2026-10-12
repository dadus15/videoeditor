---
name: youtube-edit-style-guide
description: "Visual, motion, camera, audio, and editing preferences for the YouTube editing workflow."
---

# Style guide

This is my look, the one the skill is set to. Fill in the "Yours" column, then tell Claude: "Here's my style guide. Update the youtube-edit skill to match it." Leave a row empty and it keeps mine.

Where it lives: the colours and font are at the top of `youtube-edit/scripts/compose.py` (the `:root` colour tokens and the font files). Every rule below is written into `youtube-edit/SKILL.md`. You don't need to open either; Claude does it.

## Colours

| Role | Mine | Yours |
|---|---|---|
| Highlight (key words, ticks, bars) | Cyan `#0AF0F0` | |
| Deep anchor (gradient end, a word-highlight block with white text) | Blue `#0005EE` | |
| Punchline (the payoff word, the last step of a diagram) | Magenta `#CD00EE` | |
| Money and stakes (dollar figures, warnings) | Amber `#FFB904` | |
| Text | White `#FFFFFF` | |

Two rules I learned the hard way: highlighted words are never dark blue (it disappears on dark footage), and only one gradient per frame.

## Font

| | Mine | Yours |
|---|---|---|
| Font | DM Sans, weights 400, 500 and 700 (in `youtube-edit/assets/fonts`) | |
| Headlines | 700, with a thin stroke in the same colour to make it heavier | |
| Big numbers | Every digit written out (`$207,000,000`, never `$207M`), white, counting up | |

## Cards and text on screen

| | Mine | Yours |
|---|---|---|
| Card style | Frosted glass: light glass on dark scenes, dark glass on a bright room | |
| Default for words | One line at the bottom, key words in the highlight colour | |
| Lists | Never a list panel. Each item becomes its own thing: pills next to my head, a diagram, one animation per number | |
| My face | Not the default background. 40% or more of a talking section is full-screen animation | |
| A person or job I mention | 3 seconds of B-roll of that person doing it | |
| An app I name | A clean, designed window of it, not a screenshot | |
| A website or post I name | The real page, in a browser window, scrolling | |

## Motion

| | Mine | Yours |
|---|---|---|
| Things coming in | 0.4 s, soft ease out. No bounces, no flips | |
| Things leaving | 0.35 s | |
| Timing | Every animation lands on the word it belongs to, a beat before I say it | |
| Variety | Never the same type of animation twice in a row | |
| Busy check | About 7 animations and 7 camera moves per 90 seconds | |

## Camera

| | Mine | Yours |
|---|---|---|
| Zoom anchor | The top of the frame, so my head never gets cropped | |
| Punch-in on a key word | 118 to 125%, a third of a second | |
| Slow creep across a thought | 110 to 112% over 5 to 10 seconds | |
| At every cut | Back to 100% | |

## Sound

| | Mine | Yours |
|---|---|---|
| Default | Silence. A sound has to earn its place | |
| Allowed | A pop when a logo lands, a light click when a cursor clicks, typing only when someone types, a cha-ching at very low volume for money | |
| Never | A whoosh under text | |
| Music | Something tense under the hook, then lo-fi, very low, ducked under my voice | |

## Cuts

| | Mine | Yours |
|---|---|---|
| Retakes | Keep the last take of every line | |
| Pauses | Nothing longer than about 0.4 s after a sentence | |
| Live demos | Show the result, not the waiting | |
| Flash cuts | Never | |

## Product and automotive shorts (approved on the Audi S8 D4 × Turismo project, October 2026)

These rows apply when there is no speaker, and they override the talking-head rows above for that kind of video. Full detail is in `AUTOMOTIVE-SHORTS.md`.

| | Mine |
|---|---|
| Length | 15–20 s film, plus about 2.5 s brand intro and about 3.5 s end card when the client supplies them |
| Frame 1 | The product (the strongest clear wheel), never a black frame. With a brand intro, the logo is already partly visible on frame 1 |
| Framing on low-res sources | Square 1080×1080 for details, full-width 1080×646 for wides, over a dark blurred duplicate. Never stretched, never forced to full 9:16 |
| Zoom anchor | The product (wheel hub), not the top of frame. Pushes of 100→107.5 %, sub-pixel |
| The big moment | Square → wide "aperture" reveal anchored on the wheel, on the music's drop, held about 2 s |
| Rhythm | Pair shots by motion direction; include one relaxed shot; don't cut mechanically on every beat |
| Titles | `AUDI S8 D4` in DM Sans 700 with tracking; a sub-line in 500; the model name in a masked rise; a cyan hairline |
| Brand intro | White card, logo plus a two-colour tagline rising out of a mask, push-slide into the film |
| Ending | Iris from the product's wheel, zooming through the card's hub into the end card, one light sweep, hold; loops white to white |
| Frame rate | The source film's native rate (25 fps here), one film frame per output frame |
| Music | Dark electronic, cinematic bass or minimal industrial, with the drop on the reveal. SFX: impact on frame 1, a riser ending on the reveal, a sub accent, quiet textures only. No engine sound on a stationary car |
