// ══════════════════════════════════════════════════════════════════════════════
// Field Shape Viewer — Engine
// Reads from the FORMATIONS registry (formations.js) and renders dynamically.
// ══════════════════════════════════════════════════════════════════════════════

// ── STATE ────────────────────────────────────────
let currentFormation = '433';
let currentPhase     = 'defensive';
let activeUnits      = new Set();
let currentZone      = 'attacking';
let currentLane      = 'center';
let animFrame        = null;
let startTime        = null;
let livePos          = null;
const DUR            = 380;

// ── HELPERS ──────────────────────────────────────
function lerp(a, b, t) { return a + (b - a) * t; }

function setEl(id, attr, val) {
  const e = document.getElementById(id);
  if (e) e.setAttribute(attr, val);
}

function getConfig() {
  return FORMATIONS[currentFormation][currentPhase];
}

// ── DYNAMIC SVG GENERATION ───────────────────────
function buildPlayerGroups() {
  const svg = document.querySelector('svg.field');
  // Remove old dynamic groups
  svg.querySelectorAll('[data-dynamic]').forEach(el => el.remove());

  const cfg = getConfig();
  const ns = 'http://www.w3.org/2000/svg';

  // Create compress-zone rects
  for (const unitId of Object.keys(cfg.units)) {
    const rect = document.createElementNS(ns, 'rect');
    rect.id = `cz-${unitId}`;
    rect.setAttribute('data-dynamic', '');
    rect.setAttribute('width', 0);
    rect.setAttribute('height', 0);
    rect.setAttribute('rx', 4);
    rect.setAttribute('fill', unitId === 'forwards' ? 'rgba(184,134,11,.12)' : 'rgba(26,58,143,.12)');
    svg.querySelector('#dynamic-layer').appendChild(rect);
  }

  // Create shape lines
  for (const [unitId, lines] of Object.entries(cfg.shapeLines)) {
    const g = document.createElementNS(ns, 'g');
    g.id = `lines-${unitId}`;
    g.setAttribute('data-dynamic', '');
    lines.forEach((lineDef, i) => {
      const line = document.createElementNS(ns, 'line');
      line.id = `sl-${unitId}-${i}`;
      line.setAttribute('x1', 0); line.setAttribute('y1', 0);
      line.setAttribute('x2', 0); line.setAttribute('y2', 0);
      if (lineDef[2] === 'primary') {
        line.setAttribute('stroke', 'rgba(255,255,255,.22)');
        line.setAttribute('stroke-width', '1.2');
        line.setAttribute('stroke-dasharray', '5 4');
      } else {
        line.setAttribute('stroke', 'rgba(255,255,255,.14)');
        line.setAttribute('stroke-width', '1');
        line.setAttribute('stroke-dasharray', '3 5');
      }
      g.appendChild(line);
    });
    svg.querySelector('#dynamic-layer').appendChild(g);
  }

  // Create press arrows
  for (const unitId of Object.keys(cfg.units)) {
    const line = document.createElementNS(ns, 'line');
    line.id = `press-${unitId}`;
    line.setAttribute('data-dynamic', '');
    line.setAttribute('x1', 0); line.setAttribute('y1', 0);
    line.setAttribute('x2', 0); line.setAttribute('y2', 0);
    line.setAttribute('stroke', '#c8a84b');
    line.setAttribute('stroke-width', '1.8');
    line.setAttribute('stroke-dasharray', '4 3');
    line.setAttribute('marker-end', 'url(#arrow-gold)');
    line.setAttribute('opacity', '.85');
    svg.querySelector('#dynamic-layer').appendChild(line);
  }

  // Create player groups
  for (const [unitId, unit] of Object.entries(cfg.units)) {
    for (const p of unit.players) {
      const g = document.createElementNS(ns, 'g');
      g.id = `grp-${p.id}`;
      g.setAttribute('data-dynamic', '');
      g.setAttribute('data-unit', unitId);

      const shadow = document.createElementNS(ns, 'circle');
      shadow.id = `${p.id}-shadow`;
      shadow.setAttribute('r', 14);
      shadow.setAttribute('fill', 'rgba(0,0,0,.3)');
      g.appendChild(shadow);

      const circle = document.createElementNS(ns, 'circle');
      circle.id = p.id;
      circle.setAttribute('r', 12);
      circle.setAttribute('fill', p.fill);
      circle.setAttribute('stroke', p.stroke);
      circle.setAttribute('stroke-width', p.strokeWidth);
      circle.classList.add('draggable');
      circle.dataset.drag = p.id;
      g.appendChild(circle);

      const text = document.createElementNS(ns, 'text');
      text.id = `${p.id}-lbl`;
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('font-family', 'DM Sans,sans-serif');
      text.setAttribute('font-size', p.label.length > 3 ? '7' : '8');
      text.setAttribute('font-weight', '600');
      text.setAttribute('fill', 'white');
      text.textContent = p.label;
      g.appendChild(text);

      svg.querySelector('#dynamic-layer').appendChild(g);
    }
  }
}

// ── BUILD UI CONTROLS ────────────────────────────
function buildFormationSelector() {
  const container = document.getElementById('formation-selector');
  const formationIds = Object.keys(FORMATIONS);
  // Only show formation selector if there are multiple formations
  if (formationIds.length <= 1) {
    container.style.display = 'none';
  } else {
    container.style.display = '';
    container.innerHTML = formationIds.map(id => {
      // Use the first phase's label as a display name, or just the id
      const firstPhase = Object.keys(FORMATIONS[id])[0];
      const displayName = id.replace(/(\d)(\d)(\d)/, '$1-$2-$3');
      return `<button class="formation-btn${id === currentFormation ? ' active' : ''}" data-formation="${id}">${displayName}</button>`;
    }).join('');
    container.querySelectorAll('.formation-btn').forEach(btn => {
      btn.addEventListener('click', () => setFormation(btn.dataset.formation));
    });
  }
}

function buildPhaseSelector() {
  const container = document.getElementById('phase-selector');
  const phases = Object.keys(FORMATIONS[currentFormation]);
  if (phases.length <= 1) {
    container.style.display = 'none';
  } else {
    container.style.display = '';
    container.innerHTML = phases.map(id => {
      const label = FORMATIONS[currentFormation][id].label || id;
      return `<button class="phase-btn${id === currentPhase ? ' active' : ''}" data-phase="${id}">${label}</button>`;
    }).join('');
    container.querySelectorAll('.phase-btn').forEach(btn => {
      btn.addEventListener('click', () => setPhase(btn.dataset.phase));
    });
  }
}

function buildUnitSelector() {
  const container = document.getElementById('unit-selector');
  const cfg = getConfig();
  container.innerHTML = Object.entries(cfg.units).map(([id, unit]) =>
    `<button class="unit-btn${activeUnits.has(id) ? ' active' : ''}" data-unit="${id}">${unit.label}</button>`
  ).join('');
  container.querySelectorAll('.unit-btn').forEach(btn => {
    btn.addEventListener('click', () => toggleUnit(btn.dataset.unit));
  });
}

function buildZoneTabs() {
  const container = document.getElementById('zone-tabs');
  const zones = ['attacking', 'midfield', 'defensive'];
  container.innerHTML = zones.map(z =>
    `<button class="tab${z === currentZone ? ' active' : ''}" data-zone="${z}">${z.charAt(0).toUpperCase() + z.slice(1)}</button>`
  ).join('');
  container.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => setZone(btn.dataset.zone));
  });
}

function buildLaneTabs() {
  const container = document.getElementById('lane-tabs');
  const lanes = [
    { id: 'left', label: 'Wide Left' },
    { id: 'left-center', label: 'Left Central' },
    { id: 'center', label: 'Central' },
    { id: 'right-center', label: 'Right Central' },
    { id: 'right', label: 'Wide Right' },
  ];
  container.innerHTML = lanes.map(l =>
    `<button class="tab${l.id === currentLane ? ' active' : ''}" data-lane="${l.id}">${l.label}</button>`
  ).join('');
  container.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => setLane(btn.dataset.lane));
  });
}

// ── POSITION ASSEMBLY ────────────────────────────
function getAllPlayerIds() {
  const cfg = getConfig();
  const ids = [];
  for (const unit of Object.values(cfg.units)) {
    for (const p of unit.players) ids.push(p.id);
  }
  return ids;
}

function getFullPos(zone, lane) {
  const cfg = getConfig();
  const pos = { ball: { ...cfg.ballPos[zone][lane] } };
  for (const [unitId, unit] of Object.entries(cfg.units)) {
    const unitPos = cfg.positions[unitId][zone][lane];
    for (const p of unit.players) {
      pos[p.id] = { ...unitPos[p.id] };
    }
  }
  return pos;
}

// ── RENDERING ────────────────────────────────────
function setPlayer(k, p) {
  setEl(k + '-shadow', 'cx', p.x + 1);
  setEl(k + '-shadow', 'cy', p.y + 1);
  setEl(k, 'cx', p.x);
  setEl(k, 'cy', p.y);
  setEl(k + '-lbl', 'x', p.x);
  setEl(k + '-lbl', 'y', p.y + 3.5);
}

function drawArrow(id, from, to) {
  const dx = to.x - from.x, dy = to.y - from.y, d = Math.sqrt(dx * dx + dy * dy);
  if (d > 22) {
    setEl(id, 'x1', from.x + dx * 14 / d);
    setEl(id, 'y1', from.y + dy * 14 / d);
    setEl(id, 'x2', from.x + dx * (d - 16) / d);
    setEl(id, 'y2', from.y + dy * (d - 16) / d);
  } else {
    clearArrow(id);
  }
}

function clearArrow(id) {
  setEl(id, 'x1', 0); setEl(id, 'y1', 0);
  setEl(id, 'x2', 0); setEl(id, 'y2', 0);
}

function updateCompressZone(id, pts, on) {
  if (!on) { setEl(id, 'width', 0); setEl(id, 'height', 0); return; }
  const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
  setEl(id, 'x', Math.min(...xs) - 14);
  setEl(id, 'y', Math.min(...ys) - 13);
  setEl(id, 'width', Math.max(...xs) - Math.min(...xs) + 28);
  setEl(id, 'height', Math.max(...ys) - Math.min(...ys) + 28);
}

function applyPos(pos) {
  livePos = JSON.parse(JSON.stringify(pos));
  const cfg = getConfig();
  const b = pos.ball;

  // Ball + attacker
  ['ball', 'ball-inner', 'att-ring'].forEach(id => { setEl(id, 'cx', b.x); setEl(id, 'cy', b.y); });
  setEl('att', 'cx', b.x); setEl('att', 'cy', b.y);
  setEl('att-lbl', 'x', b.x); setEl('att-lbl', 'y', b.y + 3.5);

  // Players
  for (const id of getAllPlayerIds()) setPlayer(id, pos[id]);

  // Unit visibility
  for (const [unitId, unit] of Object.entries(cfg.units)) {
    const on = activeUnits.has(unitId);
    for (const p of unit.players) {
      const grp = document.getElementById(`grp-${p.id}`);
      if (grp) grp.style.display = on ? '' : 'none';
    }
    const linesGrp = document.getElementById(`lines-${unitId}`);
    if (linesGrp) linesGrp.style.display = on ? '' : 'none';

    // Compress zone
    const pts = unit.players.map(p => pos[p.id]);
    updateCompressZone(`cz-${unitId}`, pts, on);

    // Shape lines
    if (on && cfg.shapeLines[unitId]) {
      cfg.shapeLines[unitId].forEach((lineDef, i) => {
        const [fromId, toId] = lineDef;
        const lineId = `sl-${unitId}-${i}`;
        setEl(lineId, 'x1', pos[fromId].x); setEl(lineId, 'y1', pos[fromId].y);
        setEl(lineId, 'x2', pos[toId].x);   setEl(lineId, 'y2', pos[toId].y);
      });
    }

    // Press arrow
    if (on) {
      const pressFrom = cfg.positions[unitId][currentZone][currentLane].pressFrom;
      drawArrow(`press-${unitId}`, pos[pressFrom], b);
    } else {
      clearArrow(`press-${unitId}`);
    }
  }
}

// ── LEGEND & DESCRIPTION ─────────────────────────
function renderLegend() {
  const cfg = getConfig();
  const items = [];
  for (const unitId of Object.keys(cfg.units)) {
    if (activeUnits.has(unitId) && cfg.legend[unitId]) {
      items.push(...cfg.legend[unitId]);
    }
  }
  items.push({ color: 'rgba(224,92,92,.85)', border: '1px solid white', label: 'Attacker' });
  document.getElementById('legend').innerHTML = items.map(i =>
    `<div class="legend-item"><div class="legend-dot" style="background:${i.color};border:${i.border}"></div>${i.label}</div>`
  ).join('');
}

function updateDescription() {
  const cfg = getConfig();
  const unitOrder = Object.keys(cfg.units).reverse();
  const active = unitOrder.filter(u => activeUnits.has(u));
  const box = document.getElementById('desc-box');
  if (active.length === 0) {
    box.innerHTML = '<div class="desc-unit"><p style="color:#555">Select a unit above.</p></div>';
    return;
  }
  box.innerHTML = active.map(u => {
    const text = cfg.descriptions[u]?.[currentZone]?.[currentLane] || '';
    const label = cfg.units[u].label;
    return `<div class="desc-unit"><h3>${label}</h3><p>${text}</p></div>`;
  }).join('');
}

// ── ANIMATION ────────────────────────────────────
function animateTo(zone, lane) {
  if (animFrame) cancelAnimationFrame(animFrame);
  const playerIds = getAllPlayerIds();
  const from = livePos || getFullPos(currentZone, currentLane);
  const to = getFullPos(zone, lane);
  startTime = performance.now();

  function step(now) {
    const t = Math.min((now - startTime) / DUR, 1);
    const e = t < .5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    const pos = { ball: { x: lerp(from.ball.x, to.ball.x, e), y: lerp(from.ball.y, to.ball.y, e) } };
    for (const k of playerIds) {
      pos[k] = { x: lerp(from[k].x, to[k].x, e), y: lerp(from[k].y, to[k].y, e) };
    }
    applyPos(pos);
    if (t < 1) animFrame = requestAnimationFrame(step);
    else { applyPos(to); animFrame = null; }
  }
  animFrame = requestAnimationFrame(step);
}

// ── PUBLIC SETTERS ───────────────────────────────
function setFormation(id) {
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
  currentFormation = id;
  // If current phase doesn't exist in new formation, pick the first available
  if (!FORMATIONS[id][currentPhase]) {
    currentPhase = Object.keys(FORMATIONS[id])[0];
  }
  loadPhase();
}

function setPhase(id) {
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
  currentPhase = id;
  loadPhase();
}

function loadPhase() {
  const cfg = getConfig();
  const defaults = cfg.defaults || { zone: 'attacking', lane: 'center', units: Object.keys(cfg.units) };
  activeUnits = new Set(defaults.units);
  currentZone = defaults.zone;
  currentLane = defaults.lane;
  livePos = null;

  // Update title
  document.getElementById('page-title').textContent = cfg.label || 'Field Shape';
  document.getElementById('page-subtitle').textContent = cfg.subtitle || '';

  // Rebuild all dynamic elements
  buildFormationSelector();
  buildPhaseSelector();
  buildUnitSelector();
  buildZoneTabs();
  buildLaneTabs();
  buildPlayerGroups();
  initDrag();

  applyPos(getFullPos(currentZone, currentLane));
  renderLegend();
  updateDescription();
}

function toggleUnit(unit) {
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
  activeUnits.has(unit) ? activeUnits.delete(unit) : activeUnits.add(unit);
  document.querySelectorAll('.unit-btn').forEach(btn => {
    btn.classList.toggle('active', activeUnits.has(btn.dataset.unit));
  });
  applyPos(livePos || getFullPos(currentZone, currentLane));
  renderLegend();
  updateDescription();
}

function setZone(zone) {
  document.querySelectorAll('#zone-tabs .tab').forEach(t => {
    t.classList.toggle('active', t.dataset.zone === zone);
  });
  currentZone = zone;
  updateDescription();
  animateTo(zone, currentLane);
}

function setLane(lane) {
  document.querySelectorAll('#lane-tabs .tab').forEach(t => {
    t.classList.toggle('active', t.dataset.lane === lane);
  });
  currentLane = lane;
  updateDescription();
  animateTo(currentZone, lane);
}

// ── OVERLAYS ─────────────────────────────────────
function toggleOverlay(id, on) {
  document.getElementById(id).setAttribute('display', on ? '' : 'none');
}

// ── CONTROLS TOGGLE ──────────────────────────────
function toggleControls() {
  const wrap = document.getElementById('controls-wrap');
  const btn = document.getElementById('controls-toggle');
  const hidden = wrap.classList.toggle('hidden');
  btn.textContent = (hidden ? '▸' : '▾') + ' Controls';
}

// ── RESET ────────────────────────────────────────
function resetToDefault() {
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
  const cfg = getConfig();
  const defaults = cfg.defaults || { zone: 'attacking', lane: 'center', units: Object.keys(cfg.units) };
  activeUnits = new Set(defaults.units);
  livePos = null;

  buildUnitSelector();
  renderLegend();
  setZone(defaults.zone);
  setLane(defaults.lane);
}

// ── DRAG ─────────────────────────────────────────
let dragKey = null, dragOffset = { x: 0, y: 0 };

function svgPoint(e) {
  const svg = document.querySelector('svg.field');
  const pt = svg.createSVGPoint();
  const src = e.touches ? e.touches[0] : e;
  pt.x = src.clientX;
  pt.y = src.clientY;
  return pt.matrixTransform(svg.getScreenCTM().inverse());
}

function initDrag() {
  const svg = document.querySelector('svg.field');
  // Remove old listeners by cloning (simple approach for re-init)
  // Instead, use a single persistent listener and just rebind pointerdown on new elements
  if (!svg._dragInitialized) {
    svg._dragInitialized = true;
    svg.addEventListener('pointermove', e => {
      if (!dragKey) return;
      e.preventDefault();
      const pt = svgPoint(e);
      const pos = JSON.parse(JSON.stringify(livePos || getFullPos(currentZone, currentLane)));
      const nx = Math.max(12, Math.min(288, pt.x - dragOffset.x));
      const ny = Math.max(12, Math.min(408, pt.y - dragOffset.y));
      if (dragKey === 'ball') pos.ball = { x: nx, y: ny };
      else pos[dragKey] = { x: nx, y: ny };
      applyPos(pos);
    }, { passive: false });
    svg.addEventListener('pointerup', () => dragKey = null);
    svg.addEventListener('pointercancel', () => dragKey = null);
  }

  // Bind pointerdown on all new draggable elements
  svg.querySelectorAll('[data-drag]').forEach(el => {
    el.addEventListener('touchstart', e => e.preventDefault(), { passive: false });
    el.addEventListener('pointerdown', e => {
      if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
      e.preventDefault();
      svg.setPointerCapture(e.pointerId);
      dragKey = e.currentTarget.dataset.drag;
      const pt = svgPoint(e);
      const cur = livePos || getFullPos(currentZone, currentLane);
      const ref = dragKey === 'ball' ? cur.ball : cur[dragKey];
      dragOffset = { x: pt.x - ref.x, y: pt.y - ref.y };
    }, { passive: false });
  });
}

// ── INIT ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadPhase();
});
