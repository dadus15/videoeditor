# Turismo BF "Kute felgi w 48h": audio needed

The picture is locked: `renders/Turismo_BF_KuteFelgi48h_Hook_9x16_PICTURE-LOCK.mp4` (14.56 s, **no audio**).

## Why there's no music yet

The **Epidemic Sound connector isn't authorized** in this session, so I couldn't search, audition or download anything. Authorize it in claude.ai under Settings → Connectors → Epidemic Sound. Downloads also need:

- an Epidemic plan with download rights;
- `audiocdn.epidemicsound.com` allowed in this environment's network settings. That host serves the previews, downloads and track edits.

**I have not listened to any track.** The shortlist below comes from catalogue metadata seen in the earlier Audi × Inventa session (tags, BPM, no vocals). Nothing has been "chosen".

## Files needed (`assets/audio/`)

| Slot | Where it lands in this edit | Epidemic Sound item (ID) |
|---|---|---|
| `music.wav` | Main bed, at least 15 s usable. Pulse under the detail shots (0–4.5 s), **drop or bass entrance on the reveal at 4.52 s** | Choose **one** after auditioning (see below) |
| `sfx_impact.wav` | Frame 1 (hook), and again at −15 dB at 8.52 s (BLACK FRIDAY shot) | "Designed, Boom, Impact, Dark, Cinematic, Low HIt" `d106e784-e06e-4673-ae48-a36e145a715d` |
| `sfx_riser.wav` | Ends exactly on the reveal (4.52 s); about 1–1.6 s long | "Designed, Riser, Metal Hit, Reverse, Build, Crescendo" `0e565244-d80e-4d88-801e-5183a6335937` (1.6 s) |
| `sfx_subdrop.wav` | On the reveal (4.52 s) | "Designed, Bass Dive, Bass Drop, Deep Sub, 50Hz" `91b28e95-2a6b-4233-86fa-f1715f23ab75` |
| `sfx_shimmer.wav` (optional) | Very quiet under the FORGED lettering (1.52 s) and as the end card opens (11.05 s) | "Glass, Tonal, Glass Shimmering Texture" `0e854415-f21b-46c9-b22e-2d633967f666` |

### Music shortlist (instrumental; metadata only, NOT auditioned)

| Track | Artist | BPM | Tags | ID |
|---|---|---|---|---|
| The Pursuit | Henry Miles | 130 | dark, pulses, suspense, cinematic | `6bc54a08-a664-40b8-ae55-fe7611eecae3` |
| Invictus | Lennon Hutton | 135 | dark, electronic, epic, orchestral hybrid | `813d605d-7943-4a33-958b-12a5fc8d7968` |
| Odd Shaped Face | Ava Low | 120 | dark, electronic, IDM, beats | `c627cf32-77c6-408a-9031-dc34ee7f8bb6` |
| Eclipse | Henry Miles | 150 | dark, pulses, main title, cinematic | `32c1fe25-d55a-4c53-9d33-7abfba0a8ff5` |

Once the connector works, also search for: "dark cinematic bass pulse automotive", "dark industrial electronic build drop", "minimal dark electronic pulse" (no vocals). What to listen for: a clear pulse from bar 1, restrained bass, a short build and a distinct drop. Write down when the drop happens in the file.

## Finishing (one command)

```bash
EDLS=edit/stills_turismo_bf.json .claude/skills/youtube-edit/scripts/finish.sh <drop_seconds_in_music.wav> <track_bpm>
```

- Shot lengths are stored in beats, so `<track_bpm>` re-times every cut to the track. Use 120–135 BPM: at 135 BPM the film runs about 10.2 s plus the 3.1 s end card.
- The drop lands on the reveal, and the SFX land on their cue points.
- The mix targets −14 LUFS with true peak ≤ −1 dBTP and prints a phone-speaker check.
- Output: `renders/Turismo_BF_KuteFelgi48h_Hook_9x16.mp4`.
