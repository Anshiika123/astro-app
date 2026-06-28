/* chart-wheel.js
   SVG natal chart wheel renderer.
   Entry point: drawChartWheel(containerId, chartData, mode)
   chartData = full /api/chart response JSON.
   mode = 'sidereal' or 'tropical'
*/

(function () {

// ── Constants ────────────────────────────────────────────────────────────────

const SIGNS   = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                 'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
const SIGN_SYM = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓'];
const ELEM    = ['fire','earth','air','water',
                 'fire','earth','air','water',
                 'fire','earth','air','water'];
const ELEM_COLOR = { fire:'#c8553a', earth:'#9a844a', air:'#4a86a8', water:'#3a5f9a' };
const ELEM_FILL  = { fire:'#c8553a22', earth:'#9a844a22', air:'#4a86a822', water:'#3a5f9a22' };

const PLANET_GLYPH = {
  Sun:'☉', Moon:'☽', Mercury:'☿', Venus:'♀', Mars:'♂',
  Jupiter:'♃', Saturn:'♄', Rahu:'☊', Ketu:'☋'
};
const PLANET_COLOR = {
  Sun:'#ffd060', Moon:'#c0d8ff', Mercury:'#a0ffb0', Venus:'#ffb0e0',
  Mars:'#ff7060', Jupiter:'#ffaa44', Saturn:'#b0b0e0',
  Rahu:'#9090c0', Ketu:'#a0907a'
};

const ASPECT_COLOR = {
  Conjunction:'#ffd700', Sextile:'#4caf50',
  Square:'#e53935', Trine:'#1e88e5', Opposition:'#9c27b0'
};

// SVG dimensions
const W = 500, H = 500, CX = 250, CY = 250;
const RO  = 238;   // zodiac outer
const RI  = 200;   // zodiac inner / house outer
const RP  = 168;   // planet ring
const RHI = 118;   // house inner
const RA  = 98;    // aspect circle
const RC  = 28;    // centre

// ── Helpers ──────────────────────────────────────────────────────────────────

function NS(tag, attrs, text) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k,v] of Object.entries(attrs||{})) el.setAttribute(k, String(v));
  if (text !== undefined) el.textContent = text;
  return el;
}

/** Convert ecliptic longitude to SVG angle in radians.
 *  ASC lands at 180° (left), zodiac runs counter-clockwise.
 *  Formula: svgDeg = (180 - (lon - ascLon)) mod 360
 */
function lonToRad(lon, ascLon) {
  const rel = ((lon - ascLon) % 360 + 360) % 360;
  const deg = ((180 - rel) % 360 + 360) % 360;
  return deg * Math.PI / 180;
}

function polar(r, rad) {
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) };
}

// ── Drawing functions ─────────────────────────────────────────────────────────

function drawZodiacRing(svg, ascLon) {
  for (let i = 0; i < 12; i++) {
    const a1 = lonToRad(i * 30,      ascLon);
    const a2 = lonToRad(i * 30 + 30, ascLon);
    const o1 = polar(RO, a1), o2 = polar(RO, a2);
    const i1 = polar(RI, a1), i2 = polar(RI, a2);
    // Arc from a1→a2 is 30° counter-clockwise (decreasing angle).
    // Outer arc: sweep=0 (CCW), large-arc=0; inner arc: sweep=1 (CW), large-arc=0.
    const d = `M${o1.x} ${o1.y} A${RO} ${RO} 0 0 0 ${o2.x} ${o2.y}`
            + ` L${i2.x} ${i2.y} A${RI} ${RI} 0 0 1 ${i1.x} ${i1.y} Z`;
    svg.appendChild(NS('path', { d, fill: ELEM_FILL[ELEM[i]], stroke: ELEM_COLOR[ELEM[i]], 'stroke-width':'0.6' }));

    // Sector divider line
    svg.appendChild(NS('line', { x1:o1.x, y1:o1.y, x2:i1.x, y2:i1.y,
      stroke:'#2a2a4a', 'stroke-width':'0.5' }));

    // Sign glyph
    const ma = lonToRad(i * 30 + 15, ascLon);
    const gp = polar((RO + RI) / 2, ma);
    svg.appendChild(NS('text', {
      x: gp.x, y: gp.y,
      'text-anchor':'middle', 'dominant-baseline':'central',
      'font-size':'13', fill: ELEM_COLOR[ELEM[i]], 'font-family':'serif'
    }, SIGN_SYM[i]));
  }
  // Boundary circles
  svg.appendChild(NS('circle', { cx:CX, cy:CY, r:RO, fill:'none', stroke:'#3a3a5a', 'stroke-width':'1' }));
  svg.appendChild(NS('circle', { cx:CX, cy:CY, r:RI, fill:'none', stroke:'#3a3a5a', 'stroke-width':'1' }));
}

function drawHouses(svg, houses, ascLon) {
  const cusps = houses.houses;
  for (let idx = 0; idx < 12; idx++) {
    const h     = cusps[idx];
    const next  = cusps[(idx + 1) % 12];
    const angle = lonToRad(h.cusp, ascLon);
    const isAngular = [1,4,7,10].includes(h.number);

    // Cusp line
    const po = polar(RI, angle), pi = polar(RHI, angle);
    svg.appendChild(NS('line', { x1:po.x, y1:po.y, x2:pi.x, y2:pi.y,
      stroke: isAngular ? '#7070b0' : '#333355',
      'stroke-width': isAngular ? '1.5' : '0.7' }));

    // House number (midpoint between this and next cusp)
    const mid = h.cusp + ((next.cusp - h.cusp + 360) % 360) / 2;
    const ma  = lonToRad(mid, ascLon);
    const np  = polar(RHI + 14, ma);
    svg.appendChild(NS('text', {
      x: np.x, y: np.y,
      'text-anchor':'middle', 'dominant-baseline':'central',
      'font-size':'8.5', fill:'#5555aa', 'font-family':'sans-serif'
    }, h.number));
  }
  svg.appendChild(NS('circle', { cx:CX, cy:CY, r:RHI, fill:'#080814', stroke:'#2a2a4a', 'stroke-width':'0.75' }));
}

function drawAspectLines(svg, planets, aspects, ascLon) {
  const angles = {};
  for (const [name, pos] of Object.entries(planets)) {
    angles[name] = lonToRad(pos.longitude, ascLon);
  }
  for (const a of aspects.slice(0, 20)) {
    const aA = angles[a.planet_a], aB = angles[a.planet_b];
    if (aA === undefined || aB === undefined) continue;
    const pA = polar(RA, aA), pB = polar(RA, aB);
    const op = Math.max(0.15, 1 - Math.abs(a.orb_diff) / 6);
    svg.appendChild(NS('line', {
      x1:pA.x, y1:pA.y, x2:pB.x, y2:pB.y,
      stroke: ASPECT_COLOR[a.aspect] || '#888',
      'stroke-width':'0.9', opacity: op.toFixed(2)
    }));
  }
}

function drawPlanets(svg, planets, ascLon) {
  // Collect positions to detect crowding
  const placed = [];

  for (const [name, pos] of Object.entries(planets)) {
    let rad = lonToRad(pos.longitude, ascLon);

    // Nudge crowded planets slightly inward
    let r = RP;
    for (const p of placed) {
      const diff = Math.abs(rad - p.rad);
      const gap  = Math.min(diff, 2 * Math.PI - diff);
      if (gap < 0.18) { r -= 16; break; }
    }
    placed.push({ rad });

    const pp = polar(r, rad);

    // Tick line to zodiac ring
    const rp = polar(RI - 2, rad);
    svg.appendChild(NS('line', { x1:pp.x, y1:pp.y, x2:rp.x, y2:rp.y,
      stroke:'#44445a', 'stroke-width':'0.4' }));

    // Glyph
    const glyph = PLANET_GLYPH[name] || name[0];
    const col   = PLANET_COLOR[name] || '#c0c0ff';
    const gEl   = NS('text', {
      x: pp.x, y: pp.y - 5,
      'text-anchor':'middle', 'dominant-baseline':'auto',
      'font-size':'12', fill: pos.retrograde ? '#ff7070' : col,
      'font-family':'serif'
    }, glyph);
    svg.appendChild(gEl);

    // Degree label
    const deg = NS('text', {
      x: pp.x, y: pp.y + 6,
      'text-anchor':'middle', 'dominant-baseline':'hanging',
      'font-size':'6.5', fill:'#888899', 'font-family':'sans-serif'
    }, pos.sign_degree.toFixed(0) + '°');
    svg.appendChild(deg);
  }
}

function drawCenter(svg) {
  svg.appendChild(NS('circle', { cx:CX, cy:CY, r:RC, fill:'#0e0e22', stroke:'#4a4a7a', 'stroke-width':'1' }));
  svg.appendChild(NS('text', { x:CX, y:CY,
    'text-anchor':'middle', 'dominant-baseline':'central',
    'font-size':'15', fill:'#7070bb', 'font-family':'serif' }, '✦'));
}

function drawAscLabel(svg, ascLon) {
  const a   = lonToRad(ascLon, ascLon); // = 180° (left)
  const pOut = polar(RO + 6, a);
  svg.appendChild(NS('text', {
    x: pOut.x - 8, y: pOut.y,
    'text-anchor':'end', 'dominant-baseline':'central',
    'font-size':'8', fill:'#ffffff', 'font-family':'sans-serif',
    'font-weight':'bold'
  }, 'ASC'));
  // Bold line along ASC axis
  const p1 = polar(RI, a), p2 = polar(RO, a);
  svg.appendChild(NS('line', { x1:p1.x, y1:p1.y, x2:p2.x, y2:p2.y,
    stroke:'#ffffff', 'stroke-width':'1.2', opacity:'0.7' }));
}

// ── Public API ────────────────────────────────────────────────────────────────

window.drawChartWheel = function(containerId, chartData, mode) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  const chart   = (mode === 'tropical') ? chartData.tropical : chartData.sidereal;
  const houses  = chart.houses;
  const planets = chart.planets;
  const aspects = chartData.aspects || [];
  const ascLon  = houses.ascendant;

  const svg = NS('svg', {
    viewBox: `0 0 ${W} ${H}`,
    width:'100%', style:'max-width:480px;display:block;margin:0 auto;'
  });

  // Layer order matters: back → front
  svg.appendChild(NS('circle', { cx:CX, cy:CY, r:RO, fill:'#0a0a1a', stroke:'#2a2a4a', 'stroke-width':'1' }));
  drawZodiacRing(svg, ascLon);
  drawHouses(svg, houses, ascLon);
  drawAspectLines(svg, planets, aspects, ascLon);
  drawPlanets(svg, planets, ascLon);
  drawAscLabel(svg, ascLon);
  drawCenter(svg);

  container.appendChild(svg);
};

})();
