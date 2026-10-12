---
name: youtube-edit-prompts
description: "Reusable prompts for installing, building, using, reviewing, and updating the YouTube editing workflow."
---

# The prompts I type

Copy them, then change the parts in [brackets].

## Install this kit

> Install the youtube-edit skill from the WeAreNoCode-YouTube-Editor folder into this project's .claude/skills folder. Then check everything it needs, install what's missing, and run its tests.

## Or build your own from scratch

The prompt I started with:

> Could you please create a video editing system for me? I'd like to use HyperFrames, FFmpeg, Tella, and Epidemic Sound for this system. Run me through how to set it up step by step.

When it works:

> Save everything we set up as a skill called youtube-edit, so I can run it in any new thread.

## Edit a hook

> Please use my YouTube editing skill to edit this hook for my YouTube video.

Then add what you know about the clip. Mine, from the video:

> When I say things like zoom, show a zoom. When I talk about a sound effect, add the sound effect. When I talk about the different animations, show three of the most impressive animations from the library inside the skill.

## Edit a full video

> Please use my YouTube editing skill to edit this full video. The raw clips are [file names], in this order. I also recorded [number] screen recordings in Tella called [names].

With Tella connected, give it the names. It opens them directly, no upload.

## Give notes

Watch the whole thing first, then go through it with timestamps. Plain words work:

> At second 22 you did this. I'd like it to be like that.

> Around second 14 there's a quick flash. That's a mistake. Please take it out.

> This is way too busy, and most of these sounds make no sense.

> Could you please make this a little bit better?

## Make it learn

This is the one that matters. After every round of notes:

> Can you learn from what we did and add it to the skill?

Or short:

> Save this to the skill.

## Make it yours

> Here's my style guide [paste or attach STYLE-GUIDE.md]. Update the youtube-edit skill to match it.

## Edit a product or automotive short

The brief that produced the approved Audi S8 D4 × Turismo film, condensed:

> Use my youtube-edit skill to edit [file] into a striking [15–20] s short for Reels, TikTok and Shorts. The subject is [car] on [wheel brand and model]; make the [wheels] the main point of interest. Analyse the footage and the available tools first (black bars, player messages, baked cuts and music). Open on the strongest [wheel] shot, build with 2–3 details, reveal the full car on the drop, end with a title and a loop. No voiceover. At most three treatments. Source music and SFX from Epidemic Sound and list their IDs. 9:16, no stretching, and say honestly what the source quality allows. Deliver a main version, an alternative opening, the audio list and short notes.

## Add brand bookends

> Add the [brand] logo photo on the first scene with the text [UNLOCK YOUR STYLE], then slide into the whole video, and put [the contact card file] at the end with a good ending effect.

## Finish once the audio arrives

> The Epidemic files are in assets/audio. The drop in music.wav is at [31.6] s and the track is [120] BPM. Finish the edit.

Claude runs `.claude/skills/youtube-edit/scripts/finish.sh 31.6 120` from the project root.
