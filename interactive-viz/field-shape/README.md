# Field Shape Viewer

An interactive HTML illustration of pressing and defensive shape for the Menomonie Mustangs 4-3-3 with a sweeper/libero defensive system.

## Features

**Unit toggles** — independently show or hide each group of players:
- **Defense** — LB · Stopper · RB · Libero
- **Midfield** — CM-L · CM-C · CM-R
- **Forwards** — LW · ST · RW

**Zone selector** — sets which third of the field the ball is in:
- Attacking · Midfield · Defensive

**Lane selector** — sets the horizontal position of the ball:
- Wide Left · Left Central · Central · Right Central · Wide Right

All 15 zone/lane combinations have unique player positions per unit. Players animate smoothly when switching lanes or zones. Switching units snaps instantly.

**Overlays** — toggleable field guides:
- Field Lanes — vertical channels (wide areas, halfspaces, center)
- Field Zones — horizontal thirds (attacking, midfield, defensive)

**Drag** — the ball and any player can be dragged freely around the pitch. The press arrow updates live as you drag.

**Description box** — updates for every unit/zone/lane combination with a short coaching description and cue for each active unit.

## Coaching concepts illustrated

| Situation | What to look for |
|-----------|-----------------|
| Defense · Attacking zone | Back four compress toward the ball. Stopper steps or shifts. Libero holds central — never steps. |
| Defense · Midfield zone | Unit pushes up to stay compact with midfield. Same compression principles apply. |
| Defense · Defensive zone | Very compact, tight to goal. Libero is last line — goal-side at all times. |
| Midfield · Any zone | Near mid presses or contests. Center mid covers. Far mid tucks to deny the switch. |
| Forwards · Attacking zone | High press. Ball-near winger presses. Striker cuts central lane. Ball-far winger drops and tucks. |
| Forwards · Midfield zone | Drop to midfield line. First line of defensive pressure from deeper. |
| Forwards · Defensive zone | Full tracking run back into defensive third. Everyone behind the ball. |

## Key coaching cues

- **"Ball near, squeeze in. Libero — hold center."**
- **"Stopper stepping — Libero cover."**
- **"Near presses, center covers, far tucks."**
- **"Ball near, press. Ball far, drop."**
- **"Track every runner — we defend together."**

## Usage

Open `index.html` in any modern browser. No build step, no dependencies — everything is self-contained except Google Fonts (loaded via CDN).
