# Audio: what's blocked and the files needed

## Why the audio isn't in yet

Epidemic Sound is connected and search works, but no audio could be fetched:

1. **The account can't download.** `DownloadRecording` and `DownloadSoundEffect` both return `FORBIDDEN – You don't have permission to download this asset`.
2. **The network blocks the audio host.** The environment's network policy denies `audiocdn.epidemicsound.com` (403 at the proxy). That host serves the previews, the downloads and the server-side track edits, so I couldn't even audition the previews.

The track-edit route did work server-side: an 18 s edit of *Invictus* was generated (job `043e4813-15df-4976-9f01-5b32c81f4875`, edit `a87bd42f-f0e3-45cb-8334-134a4a9acded`, 20.0 s). Its file lives on the same blocked host, so I couldn't fetch it.

**I have not listened to any of the candidates below.** They were shortlisted from Epidemic's catalogue metadata only (tags, BPM, "no vocals"). No track has been "chosen", and nothing in the edit claims to use one.

## Two ways to unblock (either works)

- **A. Fix access.** Add `audiocdn.epidemicsound.com` under *Allowed domains* in the cloud environment's network settings. Then I can audition previews and fetch track edits. Full downloads also need an Epidemic plan or connector with download rights.
- **B. Send the files.** Download the WAVs below yourself and drop them into `assets/audio/` with these exact names.

## Files needed (`assets/audio/`)

| Slot | Purpose in the edit | Epidemic Sound item (ID) |
|---|---|---|
| `music.wav` | Main bed (≥ 23 s usable): pulse in the build, bass entrance on the reveal cut (6.9 s in the final video) | Pick **one** after auditioning (shortlist below) |
| `sfx_impact.wav` | Short low impact on frame 1 (the logo card); reused at −15 dB under the signature shot | "Designed, Boom, Impact, Dark, Cinematic, Low HIt" `d106e784-e06e-4673-ae48-a36e145a715d` (4.3 s) |
| `sfx_riser.wav` | Subtle build that **ends** on the reveal cut | "Designed, Riser, Metal Hit, Reverse, Build, Crescendo" `0e565244-d80e-4d88-801e-5183a6335937` (1.6 s, fits the 1.5 s build) |
| `sfx_subdrop.wav` | Deeper accent on the main reveal | "Designed, Bass Dive, Bass Drop, Deep Sub, 50Hz" `91b28e95-2a6b-4233-86fa-f1715f23ab75` |
| `sfx_shimmer.wav` | Very quiet metallic/glass texture under the TURISMO lettering, and again softly as the end card opens (optional) | "Glass, Tonal, Glass Shimmering Texture" `0e854415-f21b-46c9-b22e-2d633967f666` |

No tyre or engine sounds: the car is stationary in nearly every shot, and none of the catalogue hits matched a real car rolling.

### Music shortlist (instrumental, metadata only, not yet auditioned)

| Track | Artist | BPM | Tags | ID |
|---|---|---|---|---|
| Invictus | Lennon Hutton | 135 | dark, electronic, epic, orchestral hybrid | `813d605d-7943-4a33-958b-12a5fc8d7968` |
| The Pursuit | Henry Miles | 130 | dark, pulses, suspense, cinematic | `6bc54a08-a664-40b8-ae55-fe7611eecae3` |
| Odd Shaped Face | Ava Low | 120 | dark, electronic, IDM, beats | `c627cf32-77c6-408a-9031-dc34ee7f8bb6` |
| Hogarth | Lupus Nocte | 148 | dark, dark wave | `246c1bb8-439d-4a97-bf93-14a21b27703c` |
| Eclipse | Henry Miles | 150 | dark, pulses, main title, cinematic | `32c1fe25-d55a-4c53-9d33-7abfba0a8ff5` |

What to listen for: a clear pulse, restrained bass, a short build and a distinct drop or bass entrance. Note the time of that entrance in the file.

## Finishing (one command)

```bash
scripts/finish.sh <seconds_of_the_drop_inside_music.wav> <track_bpm>
# e.g. scripts/finish.sh 31.6 120
```

The script does four things:

- Re-times every cut to the track's beat grid. Shot lengths are stored in beats; use BPM ≥ 120, since 135 BPM gives a 16.0 s film.
- Puts the drop exactly on the reveal cut.
- Mixes the SFX: impact on frame 1, riser ending on the reveal, sub accent on the reveal, quiet shimmer and the signature hit.
- Shapes the last 0.55 s so the loop restarts into the opening impact. The two masters are written to `renders/Audi_S8_D4_Inventa_Hero_9x16.mp4` and `renders/Audi_S8_D4_Inventa_AltOpen_9x16.mp4`.

The mixer targets −14 LUFS with a true-peak ceiling below −1 dBTP. It prints loudness, true peak, a phone-speaker band reading and the level below 120 Hz, and it warns if the mix leans on sub-bass that phone speakers can't play.
