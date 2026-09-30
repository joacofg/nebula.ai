// Shared logic for the three direction mockups: same numbers as the console's
// router-replay.ts, drawn by each direction's own CSS.
(function () {
  const R = window.REPLAY;
  const ops = R.ops
    .map(([tl, te, q, c]) => ({ tl, te, q, c }))
    .sort((a, b) => a.c - b.c || b.q - a.q);

  function point(target) {
    if (target >= 1) return { tl: Infinity, te: Infinity, q: 1, c: R.baselines.all_frontier[0] / 1000 };
    return ops.find((p) => p.q >= target) || { tl: Infinity, te: Infinity };
  }

  function evaluate(p) {
    const share = { local: 0, economy: 0, frontier: 0 };
    let cost = 0, ok = 0;
    for (const [pl, pe, lok, eok, ce, cf] of R.rows) {
      if (pl >= p.tl) { share.local++; ok += lok; }
      else if (pe >= p.te) { share.economy++; cost += ce; ok += eok; }
      else { share.frontier++; cost += cf; ok += 1; }
    }
    const n = R.rows.length;
    return {
      cost1000: (cost / n) * 1000,
      quality: ok / n,
      share: { local: share.local / n, economy: share.economy / n, frontier: share.frontier / n },
    };
  }

  const X = { min: 0, max: 2.5 }, Y = { min: 0.74, max: 1.0 };

  // opts: { svg, w, h, pad:{l,r,t,b}, grid:'graticule'|'datasheet'|'minimal', labels:bool }
  function drawChart(opts, current) {
    const { svg, w, h, pad } = opts;
    const iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
    const sx = (v) => pad.l + ((v - X.min) / (X.max - X.min)) * iw;
    const sy = (v) => pad.t + (1 - (v - Y.min) / (Y.max - Y.min)) * ih;
    const el = [];
    // grid
    if (opts.grid === "graticule") {
      for (let i = 0; i <= 10; i++) {
        const x = pad.l + (iw * i) / 10, y = pad.t + (ih * i) / 10;
        el.push(`<line class="g-major" x1="${x}" y1="${pad.t}" x2="${x}" y2="${pad.t + ih}"/>`);
        el.push(`<line class="g-major" x1="${pad.l}" y1="${y}" x2="${pad.l + iw}" y2="${y}"/>`);
        if (i < 10) for (let k = 1; k < 5; k++) {
          const mx = x + (iw / 50) * k, my = y + (ih / 50) * k;
          el.push(`<line class="g-minor" x1="${mx}" y1="${pad.t + ih / 2 - 3}" x2="${mx}" y2="${pad.t + ih / 2 + 3}"/>`);
          el.push(`<line class="g-minor" x1="${pad.l + iw / 2 - 3}" y1="${my}" x2="${pad.l + iw / 2 + 3}" y2="${my}"/>`);
        }
      }
    } else {
      const yt = opts.grid === "datasheet" ? [0.75, 0.8, 0.85, 0.9, 0.95, 1.0] : [0.8, 0.9, 1.0];
      for (const v of yt) el.push(`<line class="g-major" x1="${pad.l}" y1="${sy(v)}" x2="${pad.l + iw}" y2="${sy(v)}"/>`);
      if (opts.grid === "datasheet") for (const v of [0.5, 1, 1.5, 2, 2.5]) el.push(`<line class="g-major" x1="${sx(v)}" y1="${pad.t}" x2="${sx(v)}" y2="${pad.t + ih}"/>`);
      el.push(`<rect class="g-frame" x="${pad.l}" y="${pad.t}" width="${iw}" height="${ih}" fill="none"/>`);
    }
    // ticks
    for (const v of [0, 0.5, 1, 1.5, 2, 2.5]) el.push(`<text class="tick" x="${sx(v)}" y="${pad.t + ih + 16}" text-anchor="middle">${v.toFixed(1)}</text>`);
    for (const v of [0.75, 0.8, 0.85, 0.9, 0.95, 1.0]) el.push(`<text class="tick" x="${pad.l - 8}" y="${sy(v) + 4}" text-anchor="end">${v.toFixed(2)}</text>`);
    el.push(`<text class="axis" x="${pad.l + iw}" y="${h - 4}" text-anchor="end">costo · USD / 1000 pedidos</text>`);
    el.push(`<text class="axis" x="${pad.l}" y="${pad.t - 10}">calidad</text>`);
    // random mix
    const b = R.baselines;
    el.push(`<line class="s-random" x1="${sx(b.all_local[0])}" y1="${sy(b.all_local[1])}" x2="${sx(b.all_frontier[0])}" y2="${sy(b.all_frontier[1])}"/>`);
    // router front (step)
    let d = "";
    R.front.forEach(([c, q], i) => {
      d += i === 0 ? `M${sx(c)},${sy(q)}` : `H${sx(c)}V${sy(q)}`;
    });
    el.push(`<path class="s-router" d="${d}" fill="none"/>`);
    // baselines
    const marks = [
      ["all_local", "todo local", "start", 8, 14],
      ["all_economy", "todo economy", "start", 8, 4],
      ["all_frontier", "todo frontier", "end", -8, -8],
      ["oracle", "oráculo", "start", 8, 4],
      ["heuristic_premium_frontier", "heurística v0", "start", 8, 16],
    ];
    for (const [k, label, anchor, dx, dy] of marks) {
      const [c, q] = b[k];
      el.push(`<circle class="m-base" cx="${sx(c)}" cy="${sy(q)}" r="3.5"/>`);
      el.push(`<text class="m-label" x="${sx(c) + dx}" y="${sy(q) + dy}" text-anchor="${anchor}">${label}</text>`);
    }
    // current point
    const cx = sx(current.cost1000), cy = sy(current.quality);
    el.push(`<line class="m-cross" x1="${cx}" y1="${pad.t}" x2="${cx}" y2="${pad.t + ih}"/>`);
    el.push(`<line class="m-cross" x1="${pad.l}" y1="${cy}" x2="${pad.l + iw}" y2="${cy}"/>`);
    el.push(`<circle class="m-current-ring" cx="${cx}" cy="${cy}" r="9"/>`);
    el.push(`<circle class="m-current" cx="${cx}" cy="${cy}" r="5"/>`);
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.innerHTML = el.join("");
  }

  function fmtPct(v) { return `${Math.round(v * 100)} %`; }
  function fmtUsd(v) { return `USD ${v.toFixed(2)}`; }
  function fmtTau(v) { return Number.isFinite(v) ? v.toFixed(2) : "∞"; }

  // Wires [data-bind] nodes, the slider and the chart.
  function mount(opts) {
    const slider = document.querySelector("[data-slider]");
    const frontierCost = R.baselines.all_frontier[0];
    function update() {
      const target = Number(slider.value) / 100;
      const p = point(target);
      const r = evaluate(p);
      const set = (k, v) => document.querySelectorAll(`[data-bind="${k}"]`).forEach((n) => (n.textContent = v));
      set("target", target.toFixed(2));
      set("cost", fmtUsd(r.cost1000));
      set("quality", r.quality.toFixed(3));
      set("saving", `−${Math.round((1 - r.cost1000 / frontierCost) * 100)} %`);
      set("tl", fmtTau(p.tl));
      set("te", fmtTau(p.te));
      for (const t of ["local", "economy", "frontier"]) {
        set(`share-${t}`, fmtPct(r.share[t]));
        document.querySelectorAll(`[data-share="${t}"]`).forEach((n) => (n.style.flexGrow = String(Math.max(r.share[t], 0.0001))));
      }
      document.querySelectorAll("[data-chart]").forEach((svg) => drawChart({ ...opts.chart, svg }, r));
    }
    slider.addEventListener("input", update);
    update();
  }

  window.Nebula = { mount, R };
})();
