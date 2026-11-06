# Music for the production version

The reference uses **NEXT! (Slowed) by NCTS**, a Brazilian phonk track (cowbell lead, distorted 808). It is a
commercial release, so we cannot use it. We are looking for a licensable track with the same character on
Epidemic Sound.

## How the candidates were chosen
The session's network does not reach epidemicsound.com, so the work ran in the Higgsfield sandbox.

1. Read the public genre pages: drift phonk, phonk, funk carioca, plus the search pages. That gave 60 tracks, of
   which 26 fit the style.
2. Downloaded the low-quality previews (for internal comparison only).
3. Compared each preview, with `librosa`, to the reference soundtrack at 1.2–17 s:
   - **Reference profile:** about 123 BPM; spectral centroid about 1.9 kHz; a tonal cowbell peak around 1.46 kHz;
     a strong sub-bass.
   - **Score weights:** timbre (mean mel spectrum) 35%, harmony (chroma) 25%, tempo 25%, cowbell 15%.
   - **Slowed variants:** each track was also tested slowed ×0.92, ×0.85 and ×0.8 (pitch drops with it), because
     the reference is a slowed edit.

## Top candidates
| # | Track | Artist | BPM | Best version | Score |
|---|---|---|---|---|---|
| 1 | Montagem Samba | Daniel Löfgren | 132 | slowed ×0.92, about 123 BPM, which matches the reference exactly | 0.955 |
| 2 | BXDY COUNT | Robin Sherpa | 122 | original speed | 0.953 |
| 3 | STYLE | David Halsey | 118 | original speed | 0.946 |
| 4 | Machi | Azucares | 130 | original speed | 0.945 |
| 5 | GET IT DONE | Robin Sherpa | 104 | slowed ×0.85 | 0.942 |

Track links:
- Montagem Samba: https://www.epidemicsound.com/music/tracks/2e9fd206-eccb-4fd7-9363-f8ffa377039c/
- BXDY COUNT: https://www.epidemicsound.com/music/tracks/1aa71359-6774-4de7-bf69-121175c5060c/
- STYLE: https://www.epidemicsound.com/music/tracks/03e71f7f-ad6f-4845-9fbd-9fce110cfa5e/
- Machi: https://www.epidemicsound.com/music/tracks/ecee7c3f-2b30-40d6-98b0-7021cafda2d8/
- GET IT DONE: https://www.epidemicsound.com/music/tracks/dc0ca7e8-72dc-4bc4-8bb1-dff132d86f80/

## Demo edits (internal, built from the previews)
`cutmusic.py` cuts a track to the reel's sound map:
- the strongest drop in the track lands on 9.4 s;
- intro without bass until the 1.04 cut;
- break 7.6–8.3, with bass and lead out;
- stutter at 8.4–9.3 (sixteenth-note gates);
- hard stop at 17.0 with a reverb tail.

The demos are laid over previs v7.4. The media IDs are in `higgsfield_media.json` under the `music_demo_*` keys.

## Production
- Licence the chosen track with an Epidemic Sound subscription. Monetised and commercial use needs a valid licence.
- Download the full-quality WAV (or stems, so the break and stutter can be built from the stems rather than with
  filters).
- Re-run `cutmusic.py` on it.
