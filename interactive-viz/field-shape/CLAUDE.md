# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Interactive soccer tactical visualization for the Menomonie Mustangs. No build step, no dependencies — open `index.html` in a browser to test. Google Fonts loaded via CDN.

## Architecture

Three files:

- **`index.html`** — Slim shell with static SVG pitch (viewBox 300×420), overlays, ball/attacker elements, and a `<g id="dynamic-layer">` where players/lines/arrows are injected. Contains selector containers populated by JS.
- **`formations.js`** — Data-only formation registry (`FORMATIONS` global). Each formation (e.g. `433`) contains phases (e.g. `defensive`, `attacking`). Each phase is a self-contained config: units, players, positions (zone×lane grid), shape lines, descriptions, legend, and defaults.
- **`app.js`** — Rendering engine. Reads from `FORMATIONS`, dynamically generates SVG player groups, shape lines, compress zones, and press arrows. Handles animation (380ms lerp), drag, and all UI state.

## Adding a New Formation or Phase

1. In `formations.js`, add a new entry: `FORMATIONS['442'] = {}; FORMATIONS['442']['defensive'] = { ... }` following the existing shape.
2. Each phase needs: `label`, `subtitle`, `units` (with players), `positions` (per unit/zone/lane), `ballPos`, `descriptions`, `legend`, `shapeLines`, `defaults`.
3. The UI auto-generates formation/phase selectors when multiple options exist.

## Key Data Shape

```
positions[unitId][zone][lane] = { playerId: {x,y}, ..., pressFrom: 'playerId' }
```

Zones: `attacking`, `midfield`, `defensive`
Lanes: `left`, `left-center`, `center`, `right-center`, `right`

Every unit × zone × lane combination must have an entry (15 combos per unit).
