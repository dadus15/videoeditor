# Turismo Forged MSP02 2PC: design spec for generation

Measured on the client's front render (`assets/msp02_2pc_front.png`, 1280 px, centre (639, 639), wheel radius
R = 455 px) and checked against the 3/4 render. Paste the **prompt DNA** below into every image and video prompt
where the wheel is visible.

## Geometry (radii as a fraction of the wheel radius R)

| Zone | Radius | Details |
|---|---|---|
| Centre cap | 0–0.23 R | Gold, two tiers. Outer ring of **20 trapezoidal radial facets** (turbine / sunburst, a "rotor" look). Inner flat disc with the **embossed Turismo GT logo**, tone-on-tone gold. Thin dark seam around the cap. |
| Hub dish | 0.23–0.32 R | Raised gold ring around the cap, engraved tone-on-tone **TURISMO** (upper arc) and **FORGED** (lower arc). **No visible lug nuts.** |
| Spokes | 0.32–0.72 R | **10 spokes** leave the hub, each about 18° wide. At about 0.45 R each spoke **forks into a Y**, so **20 slim legs** meet the outer ring, one every 18°. Edges softly rounded, smooth fillets at the fork and at the ring. |
| Windows | 0.32–0.72 R | **10 large tapered windows** between neighbouring Y-spokes, starting right at the hub (about 17–20° wide) and widening outward. **10 small narrow triangles** inside each Y fork (about 4° at 0.5 R, 12° at 0.7 R). 20 openings in total. |
| Bolt ring | 0.72–0.86 R | Raised gold ring with a **notched, machined inner edge** ("TR59 rotor" style), with **20 small silver rivets** evenly spaced (every 18°) at 0.80 R. |
| Lip | 0.86–1.00 R | **Wide, deep, mirror-polished chrome stepped lip** (two steps), chrome barrel, valve stem on the lip at about 6:30. |
| Depth | | Moderately concave face; deep lip visible in 3/4 views. |

**Finish:**
- Centre: satin champagne gold (measured #B49B79 on the cap, #A1896A on the ring).
- Lip and barrel: polished chrome.
- Rivets: silver.

**Not to be confused with** a BBS LM / RS mesh, which has 20 straight thin spokes from the hub and a cross-lace
pattern. MSP02 has 10 thick spokes that split into Ys.

## Prompt DNA (English, paste as-is)

> Turismo Forged MSP02 2PC wheel, exact design: two-piece wheel with a satin champagne-gold centre and a
> mirror-polished chrome stepped lip. TEN spokes leave the hub; each spoke forks halfway out into a Y with two slim
> legs, giving twenty legs that meet a raised gold outer bolt ring. Between neighbouring spokes are ten large tapered
> windows that start right at the hub, and inside every Y fork is one small narrow triangular window. The gold bolt
> ring has a notched machined inner edge and exactly twenty small silver rivets evenly spaced around it. Wide deep
> polished chrome lip. Raised gold hub dish engraved TURISMO above and FORGED below. Gold centre cap with an outer
> ring of twenty radial trapezoid facets like a turbine and an embossed tone-on-tone GT logo in the middle. No
> visible lug nuts. NOT a BBS-style mesh of twenty straight thin spokes.

## Keyframe check (3 Nov 2026)

The first keyframes (GPT Image 2.5, low quality, 1k):
- **Correct:** the cap and the 2PC chrome lip with rivets.
- **Wrong:** the spokes came out as a BBS-like mesh of about 20 straight spokes instead of 10 Y-forks.

The keyframes with a visible wheel are being regenerated at high quality (2k) with the DNA above:
- K1: as an edit of the client's render, wheel kept unchanged;
- K4, K5, K6, K8, K9: regenerated with the DNA.
