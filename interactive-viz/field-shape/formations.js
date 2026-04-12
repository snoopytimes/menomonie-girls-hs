/**
 * Formation Registry
 *
 * Each formation is a top-level key. Within it, each "phase" (defensive, attacking,
 * set-pieces, etc.) is a separate entry. To add a new formation or phase, just add
 * another object following the same shape.
 *
 * Structure:
 *   FORMATIONS[formationId][phaseId] = {
 *     label:       "Human-readable name",
 *     subtitle:    "Subtitle shown under the heading",
 *     units:       { unitId: { label, players: [{ id, label, fill, stroke, strokeWidth }] } },
 *     positions:   { unitId: { [zone]: { [lane]: { <playerId>: {x,y}, pressFrom } } } },
 *     ballPos:     { [zone]: { [lane]: {x,y} } },
 *     descriptions:{ unitId: { [zone]: { [lane]: "HTML string" } } },
 *     legend:      { unitId: [{ color, border, label }] },
 *     shapeLines:  { unitId: [ [fromId, toId, style] ] },   // style: "primary" | "secondary"
 *     defaults:    { zone, lane, units: [unitId, ...] }
 *   }
 */

const FORMATIONS = {};

// ═══════════════════════════════════════════════════════════════════════════════
// 4-3-3  ·  Defensive Shape
// ═══════════════════════════════════════════════════════════════════════════════

FORMATIONS['433'] = FORMATIONS['433'] || {};
FORMATIONS['433']['defensive'] = {
  label: 'Pressing & Defensive Shape',
  subtitle: 'Menomonie Mustangs · 4-3-3 · Sweeper / Libero System',

  units: {
    defense: {
      label: 'Defense',
      players: [
        { id: 'dA', label: 'LB',  fill: '#1a3a8f', stroke: 'white',   strokeWidth: 2 },
        { id: 'dB', label: 'STP', fill: '#8f1a1a', stroke: '#c8a84b', strokeWidth: 2.5 },
        { id: 'dC', label: 'RB',  fill: '#1a3a8f', stroke: 'white',   strokeWidth: 2 },
        { id: 'dD', label: 'LIB', fill: '#1a5c3a', stroke: 'rgba(255,255,255,.9)', strokeWidth: 2 },
      ],
    },
    midfield: {
      label: 'Midfield',
      players: [
        { id: 'mA', label: 'CM-L', fill: '#1a3a8f', stroke: 'white', strokeWidth: 2 },
        { id: 'mB', label: 'CM-C', fill: '#1a3a8f', stroke: 'white', strokeWidth: 2 },
        { id: 'mC', label: 'CM-R', fill: '#1a3a8f', stroke: 'white', strokeWidth: 2 },
      ],
    },
    forwards: {
      label: 'Forwards',
      players: [
        { id: 'fA', label: 'LW', fill: '#b8860b', stroke: '#c8a84b', strokeWidth: 2 },
        { id: 'fB', label: 'ST', fill: '#b8860b', stroke: '#c8a84b', strokeWidth: 2 },
        { id: 'fC', label: 'RW', fill: '#b8860b', stroke: '#c8a84b', strokeWidth: 2 },
      ],
    },
  },

  shapeLines: {
    defense: [
      ['dA', 'dB', 'primary'],
      ['dB', 'dC', 'primary'],
      ['dA', 'dD', 'secondary'],
      ['dC', 'dD', 'secondary'],
      ['dB', 'dD', 'secondary'],
    ],
    midfield: [
      ['mA', 'mB', 'primary'],
      ['mB', 'mC', 'primary'],
    ],
    forwards: [
      ['fA', 'fB', 'primary'],
      ['fB', 'fC', 'primary'],
    ],
  },

  legend: {
    defense:  [
      { color: '#8f1a1a', border: '2.5px solid #c8a84b', label: 'Stopper' },
      { color: '#1a5c3a', border: '2px solid white',      label: 'Libero' },
      { color: '#1a3a8f', border: '2px solid white',      label: 'Outside Back' },
    ],
    midfield: [{ color: '#1a3a8f', border: '2px solid white', label: 'Central Mid' }],
    forwards: [{ color: '#b8860b', border: '2px solid #c8a84b', label: 'Forward' }],
  },

  ballPos: {
    attacking: {
      'left': {x:28,y:65}, 'left-center': {x:90,y:70}, 'center': {x:150,y:80},
      'right-center': {x:210,y:70}, 'right': {x:272,y:65},
    },
    midfield: {
      'left': {x:28,y:200}, 'left-center': {x:90,y:210}, 'center': {x:150,y:205},
      'right-center': {x:210,y:210}, 'right': {x:272,y:200},
    },
    defensive: {
      'left': {x:28,y:300}, 'left-center': {x:90,y:300}, 'center': {x:150,y:300},
      'right-center': {x:210,y:300}, 'right': {x:272,y:300},
    },
  },

  positions: {
    defense: {
      attacking: {
        'left':         { dA:{x:45,y:210},  dB:{x:100,y:200}, dC:{x:160,y:210}, dD:{x:100,y:250}, pressFrom:'dA' },
        'left-center':  { dA:{x:60,y:210},  dB:{x:110,y:200}, dC:{x:160,y:210}, dD:{x:110,y:250}, pressFrom:'dB' },
        'center':       { dA:{x:90,y:210},  dB:{x:150,y:210}, dC:{x:210,y:210}, dD:{x:150,y:250}, pressFrom:'dB' },
        'right-center': { dA:{x:145,y:210}, dB:{x:200,y:200}, dC:{x:240,y:210}, dD:{x:200,y:250}, pressFrom:'dB' },
        'right':        { dA:{x:155,y:210}, dB:{x:210,y:200}, dC:{x:255,y:210}, dD:{x:210,y:250}, pressFrom:'dC' },
      },
      midfield: {
        'left':         { dA:{x:35,y:280},  dB:{x:90,y:290},  dC:{x:160,y:320}, dD:{x:70,y:325},  pressFrom:'dA' },
        'left-center':  { dA:{x:58,y:295},  dB:{x:105,y:285}, dC:{x:180,y:290}, dD:{x:110,y:320}, pressFrom:'dB' },
        'center':       { dA:{x:90,y:290},  dB:{x:150,y:285}, dC:{x:205,y:290}, dD:{x:150,y:320}, pressFrom:'dB' },
        'right-center': { dA:{x:130,y:295}, dB:{x:200,y:280}, dC:{x:250,y:290}, dD:{x:200,y:320}, pressFrom:'dB' },
        'right':        { dA:{x:150,y:320}, dB:{x:210,y:285}, dC:{x:270,y:260}, dD:{x:225,y:320}, pressFrom:'dC' },
      },
      defensive: {
        'left':         { dA:{x:60,y:355},  dB:{x:90,y:355},  dC:{x:150,y:375}, dD:{x:90,y:385},  pressFrom:'dA' },
        'left-center':  { dA:{x:70,y:360},  dB:{x:100,y:350}, dC:{x:155,y:375}, dD:{x:115,y:375}, pressFrom:'dB' },
        'center':       { dA:{x:120,y:360}, dB:{x:150,y:350}, dC:{x:180,y:360}, dD:{x:150,y:380}, pressFrom:'dB' },
        'right-center': { dA:{x:140,y:375}, dB:{x:205,y:350}, dC:{x:240,y:360}, dD:{x:200,y:380}, pressFrom:'dB' },
        'right':        { dA:{x:150,y:375}, dB:{x:220,y:355}, dC:{x:260,y:335}, dD:{x:230,y:385}, pressFrom:'dC' },
      },
    },
    midfield: {
      attacking: {
        'left':         { mA:{x:95,y:125},  mB:{x:120,y:170}, mC:{x:170,y:170}, pressFrom:'mA' },
        'left-center':  { mA:{x:90,y:130},  mB:{x:125,y:170}, mC:{x:180,y:170}, pressFrom:'mA' },
        'center':       { mA:{x:105,y:145}, mB:{x:150,y:170}, mC:{x:195,y:145}, pressFrom:'mB' },
        'right-center': { mA:{x:120,y:170}, mB:{x:175,y:170}, mC:{x:210,y:130}, pressFrom:'mC' },
        'right':        { mA:{x:130,y:170}, mB:{x:180,y:170}, mC:{x:210,y:125}, pressFrom:'mC' },
      },
      midfield: {
        'left':         { mA:{x:60,y:250},  mB:{x:138,y:268}, mC:{x:205,y:275}, pressFrom:'mA' },
        'left-center':  { mA:{x:72,y:250},  mB:{x:135,y:260}, mC:{x:210,y:250}, pressFrom:'mA' },
        'center':       { mA:{x:90,y:230},  mB:{x:150,y:250}, mC:{x:205,y:228}, pressFrom:'mB' },
        'right-center': { mA:{x:90,y:245},  mB:{x:165,y:255}, mC:{x:228,y:250}, pressFrom:'mC' },
        'right':        { mA:{x:110,y:260}, mB:{x:180,y:255}, mC:{x:228,y:240}, pressFrom:'mC' },
      },
      defensive: {
        'left':         { mA:{x:70,y:330},  mB:{x:130,y:335}, mC:{x:180,y:345}, pressFrom:'mA' },
        'left-center':  { mA:{x:110,y:335}, mB:{x:130,y:350}, mC:{x:170,y:345}, pressFrom:'mA' },
        'center':       { mA:{x:100,y:335}, mB:{x:135,y:340}, mC:{x:195,y:335}, pressFrom:'mB' },
        'right-center': { mA:{x:125,y:345}, mB:{x:175,y:345}, mC:{x:228,y:330}, pressFrom:'mC' },
        'right':        { mA:{x:140,y:335}, mB:{x:200,y:335}, mC:{x:240,y:320}, pressFrom:'mC' },
      },
    },
    forwards: {
      attacking: {
        'left':         { fA:{x:40,y:120},  fB:{x:110,y:68},  fC:{x:158,y:120}, pressFrom:'fA' },
        'left-center':  { fA:{x:50,y:120},  fB:{x:135,y:85},  fC:{x:190,y:104}, pressFrom:'fA' },
        'center':       { fA:{x:72,y:108},  fB:{x:150,y:120}, fC:{x:228,y:108}, pressFrom:'fB' },
        'right-center': { fA:{x:95,y:110},  fB:{x:165,y:84},  fC:{x:255,y:110}, pressFrom:'fC' },
        'right':        { fA:{x:125,y:120}, fB:{x:190,y:68},  fC:{x:260,y:120}, pressFrom:'fC' },
      },
      midfield: {
        'left':         { fA:{x:42,y:178},  fB:{x:110,y:150}, fC:{x:195,y:182}, pressFrom:'fA' },
        'left-center':  { fA:{x:65,y:178},  fB:{x:135,y:155}, fC:{x:225,y:202}, pressFrom:'fA' },
        'center':       { fA:{x:85,y:178},  fB:{x:150,y:140}, fC:{x:220,y:178}, pressFrom:'fB' },
        'right-center': { fA:{x:75,y:202},  fB:{x:165,y:175}, fC:{x:235,y:178}, pressFrom:'fC' },
        'right':        { fA:{x:85,y:190},  fB:{x:165,y:150}, fC:{x:225,y:168}, pressFrom:'fC' },
      },
      defensive: {
        'left':         { fA:{x:50,y:270},  fB:{x:120,y:250}, fC:{x:210,y:298}, pressFrom:'fA' },
        'left-center':  { fA:{x:50,y:280},  fB:{x:140,y:245}, fC:{x:225,y:310}, pressFrom:'fA' },
        'center':       { fA:{x:72,y:290},  fB:{x:150,y:245}, fC:{x:228,y:290}, pressFrom:'fB' },
        'right-center': { fA:{x:75,y:298},  fB:{x:160,y:255}, fC:{x:232,y:280}, pressFrom:'fC' },
        'right':        { fA:{x:80,y:290},  fB:{x:160,y:250}, fC:{x:248,y:270}, pressFrom:'fC' },
      },
    },
  },

  descriptions: {
    defense: {
      attacking: {
        'left':         '<strong>LB closes the ball</strong> high in the opponent\'s half. Stopper shifts left — second defender, covering the inside. RB pinches in. <strong>Libero holds central behind all three.</strong> Cue: <strong>"Ball near, squeeze in. Libero — hold center."</strong>',
        'left-center':  '<strong>Stopper steps to pressure</strong> in the left channel. LB holds her width. RB tucks in. <strong>Libero covers centrally behind the stopper.</strong> Cue: <strong>"Stopper stepping — Libero cover."</strong>',
        'center':       '<strong>Stopper steps straight up, central.</strong> LB and RB hold their width. <strong>Libero sits directly behind, central.</strong> Cue: <strong>"Everyone in their lane."</strong>',
        'right-center': '<strong>Stopper steps to pressure</strong> in the right channel. RB holds her width. LB tucks in. <strong>Libero covers centrally behind the stopper.</strong> Cue: <strong>"Stopper stepping — Libero cover."</strong>',
        'right':        '<strong>RB closes the ball</strong> high in the opponent\'s half. Stopper shifts right — second defender. LB pinches in. <strong>Libero holds central behind all three.</strong> Cue: <strong>"Ball near, squeeze in. Libero — hold center."</strong>',
      },
      midfield: {
        'left':         '<strong>LB pushes up to close the ball wide</strong> in the middle third. Stopper shifts left — second defender. RB tucks in. <strong>Libero holds central behind the three.</strong> Cue: <strong>"Push up and hold shape. Libero — read the space."</strong>',
        'left-center':  '<strong>Stopper steps to pressure</strong> in the left-central midfield channel. LB holds width. RB compresses. <strong>Libero sits centrally behind the stopper.</strong> Cue: <strong>"Stopper on it — Libero cover behind."</strong>',
        'center':       '<strong>Stopper steps to contest centrally</strong> in midfield. LB and RB hold their width. <strong>Libero holds directly behind, central.</strong> Cue: <strong>"Hold the diamond — everyone in their lane."</strong>',
        'right-center': '<strong>Stopper steps to pressure</strong> in the right-central midfield channel. RB holds width. LB compresses. <strong>Libero sits centrally behind the stopper.</strong> Cue: <strong>"Stopper on it — Libero cover behind."</strong>',
        'right':        '<strong>RB pushes up to close the ball wide</strong> in the middle third. Stopper shifts right — second defender. LB tucks in. <strong>Libero holds central behind the three.</strong> Cue: <strong>"Push up and hold shape. Libero — read the space."</strong>',
      },
      defensive: {
        'left':         '<strong>LB is first defender on the ball</strong> in our defensive third. Stopper covers inside — no pass through. RB pinches in tight. <strong>Libero is goal-side, protecting space behind all three.</strong> Cue: <strong>"No space behind. Libero — protect the goal."</strong>',
        'left-center':  '<strong>Stopper steps to challenge</strong> in our defensive third. LB stays tight. RB closes the gap. <strong>Libero is last defender — goal-side, nothing gets through.</strong> Cue: <strong>"Stopper step — Libero, no space behind."</strong>',
        'center':       '<strong>Stopper challenges the ball centrally</strong> in our third. LB and RB are tight — no space wide. <strong>Libero is directly behind, last line of defense.</strong> Cue: <strong>"Compact. No gaps. Libero anchors."</strong>',
        'right-center': '<strong>Stopper steps to challenge</strong> in our defensive third. RB stays tight. LB closes. <strong>Libero is last defender — goal-side.</strong> Cue: <strong>"Stopper step — Libero, no space behind."</strong>',
        'right':        '<strong>RB is first defender on the ball</strong> in our defensive third. Stopper covers inside. LB pinches in tight. <strong>Libero is goal-side, protecting space behind all three.</strong> Cue: <strong>"No space behind. Libero — protect the goal."</strong>',
      },
    },
    midfield: {
      attacking: {
        'left':         '<strong>CM-L presses aggressively</strong> toward the ball. CM-C shifts to cover the central lane. <strong>CM-R tucks in sharply</strong> — denies the switch. Cue: <strong>"Near presses, center covers, far tucks."</strong>',
        'left-center':  '<strong>CM-L steps up to press.</strong> CM-C covers centrally. <strong>CM-R tucks in</strong> to deny the switch right. Cue: <strong>"Near presses, center covers, far tucks."</strong>',
        'center':       '<strong>CM-C steps up to pressure.</strong> CM-L and CM-R hold even width — flat line, all lanes closed. Cue: <strong>"Hold shape, CM-C leads, wings connected."</strong>',
        'right-center': '<strong>CM-R steps up to press.</strong> CM-C covers centrally. <strong>CM-L tucks in</strong> to deny the switch left. Cue: <strong>"Near presses, center covers, far tucks."</strong>',
        'right':        '<strong>CM-R presses aggressively</strong> toward the ball. CM-C shifts to cover the central lane. <strong>CM-L tucks in sharply</strong> — denies the switch. Cue: <strong>"Near presses, center covers, far tucks."</strong>',
      },
      midfield: {
        'left':         '<strong>CM-L battles for the ball wide in midfield.</strong> CM-C shifts left to cover the center. <strong>CM-R tucks in</strong> — deny the switch. Contest everything in the middle third. Cue: <strong>"Win it in midfield — near battles, far tucks."</strong>',
        'left-center':  '<strong>CM-L steps to contest</strong> in the left-central channel. CM-C covers the center. <strong>CM-R tucks in.</strong> Cue: <strong>"Near battles, center covers, far tucks."</strong>',
        'center':       '<strong>CM-C steps to contest centrally.</strong> CM-L and CM-R hold even width — flat line. <strong>Compete for every ball in the middle third.</strong> Cue: <strong>"CM-C wins it — wings hold width."</strong>',
        'right-center': '<strong>CM-R steps to contest</strong> in the right-central channel. CM-C covers the center. <strong>CM-L tucks in.</strong> Cue: <strong>"Near battles, center covers, far tucks."</strong>',
        'right':        '<strong>CM-R battles for the ball wide in midfield.</strong> CM-C shifts right to cover the center. <strong>CM-L tucks in</strong> — deny the switch. Cue: <strong>"Win it in midfield — near battles, far tucks."</strong>',
      },
      defensive: {
        'left':         '<strong>CM-L drops to track the wide runner</strong> into our defensive third. CM-C covers the center. <strong>CM-R tucks in tight.</strong> Mids form a wall in front of the defense. Cue: <strong>"Drop and cover — no gaps in front of the defense."</strong>',
        'left-center':  '<strong>CM-L drops to block the left-central lane.</strong> CM-C covers centrally. <strong>CM-R tucks in.</strong> Compact block — protect the space in front of the back four. Cue: <strong>"Get behind the ball — no space to exploit."</strong>',
        'center':       '<strong>CM-C drops to block centrally.</strong> CM-L and CM-R hold wide — no gaps. <strong>Tight wall in front of the defense.</strong> Cue: <strong>"Compact. No gaps. Wall in front of defense."</strong>',
        'right-center': '<strong>CM-R drops to block the right-central lane.</strong> CM-C covers centrally. <strong>CM-L tucks in.</strong> Protect the space in front of the back four. Cue: <strong>"Get behind the ball — no space to exploit."</strong>',
        'right':        '<strong>CM-R drops to track the wide runner</strong> into our defensive third. CM-C covers the center. <strong>CM-L tucks in tight.</strong> Mids form a wall in front of the defense. Cue: <strong>"Drop and cover — no gaps in front of the defense."</strong>',
      },
    },
    forwards: {
      attacking: {
        'left':         '<strong>LW presses the ball</strong> high in the opponent\'s half. ST shifts to cut the central lane. <strong>RW drops and tucks in</strong> — denies the switch. Cue: <strong>"Ball near, press. Ball far, drop."</strong>',
        'left-center':  '<strong>LW presses.</strong> ST narrows to close the central pass. <strong>RW tucks in</strong> — denies the switch, forces play backward. Cue: <strong>"Ball near, press. Ball far, drop."</strong>',
        'center':       '<strong>ST leads the press centrally.</strong> LW and RW narrow symmetrically — no space in the middle. Cue: <strong>"ST leads, wings narrow, force it back."</strong>',
        'right-center': '<strong>RW presses.</strong> ST narrows to close the central pass. <strong>LW tucks in</strong> — denies the switch. Cue: <strong>"Ball near, press. Ball far, drop."</strong>',
        'right':        '<strong>RW presses the ball</strong> high in the opponent\'s half. ST shifts to cut the central lane. <strong>LW drops and tucks in</strong> — denies the switch. Cue: <strong>"Ball near, press. Ball far, drop."</strong>',
      },
      midfield: {
        'left':         '<strong>LW drops to the midfield line</strong> and presses the ball. ST drops central — deny the pass through. <strong>RW tucks in.</strong> First line of defensive pressure from midfield. Cue: <strong>"Drop to the line — near presses, far tucks."</strong>',
        'left-center':  '<strong>LW drops and presses</strong> in the left-central channel from the midfield line. ST closes the central lane. <strong>RW tucks in.</strong> Cue: <strong>"Drop to the line — near presses, far tucks."</strong>',
        'center':       '<strong>ST drops to the midfield line</strong> and contests centrally. LW and RW tuck in — compact line. <strong>No space through the center.</strong> Cue: <strong>"Drop to the line — ST leads, wings narrow."</strong>',
        'right-center': '<strong>RW drops and presses</strong> in the right-central channel from the midfield line. ST closes the central lane. <strong>LW tucks in.</strong> Cue: <strong>"Drop to the line — near presses, far tucks."</strong>',
        'right':        '<strong>RW drops to the midfield line</strong> and presses the ball. ST drops central. <strong>LW tucks in.</strong> First line of defensive pressure from midfield. Cue: <strong>"Drop to the line — near presses, far tucks."</strong>',
      },
      defensive: {
        'left':         '<strong>LW tracks all the way back</strong> into the defensive third — goal-side of her runner. ST drops to block central passes. <strong>RW tracks back on the right side.</strong> Full team behind the ball. Cue: <strong>"Track every runner — we defend together."</strong>',
        'left-center':  '<strong>LW tracks the ball-side runner</strong> deep into our defensive third. ST drops to block the central pass. <strong>RW tucks in</strong> to deny the switch. Cue: <strong>"All the way back — no free runners."</strong>',
        'center':       '<strong>ST drops centrally</strong> in our defensive third to block passing lanes. LW and RW track their runners. <strong>Compact unit in front of the midfield.</strong> Cue: <strong>"Track every runner — we defend together."</strong>',
        'right-center': '<strong>RW tracks the ball-side runner</strong> deep into our defensive third. ST drops to block the central pass. <strong>LW tucks in.</strong> Cue: <strong>"All the way back — no free runners."</strong>',
        'right':        '<strong>RW tracks all the way back</strong> into the defensive third — goal-side of her runner. ST drops centrally. <strong>LW tracks back on the left side.</strong> Full team behind the ball. Cue: <strong>"Track every runner — we defend together."</strong>',
      },
    },
  },

  defaults: { zone: 'attacking', lane: 'center', units: ['defense', 'midfield', 'forwards'] },
};
