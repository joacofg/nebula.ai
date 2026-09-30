// A TypeScript port of the learned router's selection rule, run over the
// out-of-fold replay exported by `scripts.router.train`. It must agree with
// `src/nebula/services/learned_router.py` and `scripts/router/frontier.py`:
// the golden test checks it against every operating point of the real file.

export type Tier = "local" | "economy" | "frontier";

export const TIERS: readonly Tier[] = ["local", "economy", "frontier"];

export type ReplayRow = {
  key: string;
  lang: string;
  task: string;
  text: string;
  p_local: number;
  p_economy: number;
  local_ok: boolean;
  economy_ok: boolean;
  cost_economy: number;
  cost_frontier: number;
};

export type ReplayOperatingPoint = {
  tau_local: number;
  tau_economy: number;
  quality: number;
  cost_per_prompt: number;
};

export type CostQuality = { cost: number; quality: number };

export type ReplayBaselines = {
  all_local: CostQuality;
  all_economy: CostQuality;
  all_frontier: CostQuality;
  oracle: CostQuality;
  heuristic_premium_frontier: CostQuality;
  heuristic_premium_economy: CostQuality;
};

export type TierShare = Record<Tier, number>;

export type NestedFigure = {
  quality: number;
  cost: number;
  vs_all_frontier: number;
  vs_all_frontier_ci95: [number, number];
  vs_random: number;
  vs_random_ci95: [number, number];
  share: TierShare;
  by_lang: Record<string, CostQuality>;
};

export type LatencyFigure = {
  model: string;
  median_s: number;
  p90_s: number;
  mean_s: number;
  n: number;
};

export type RouterReplay = {
  version: number;
  router_label: string;
  rows: ReplayRow[];
  operating_points: ReplayOperatingPoint[];
  baselines: ReplayBaselines;
  nested: Record<string, NestedFigure>;
  latency: Record<string, LatencyFigure>;
};

export type LangFigure = { n: number; costPerPrompt: number; quality: number };

export type Evaluation = {
  costPerPrompt: number;
  quality: number;
  share: TierShare;
  byLang: Record<string, LangFigure>;
};

// A target no measured point reaches: every prompt goes to the frontier model.
export const ALL_FRONTIER: ReplayOperatingPoint = {
  tau_local: Number.POSITIVE_INFINITY,
  tau_economy: Number.POSITIVE_INFINITY,
  quality: 1,
  cost_per_prompt: Number.NaN,
};

export function isAllFrontier(point: ReplayOperatingPoint) {
  return point.tau_local === Number.POSITIVE_INFINITY && point.tau_economy === Number.POSITIVE_INFINITY;
}

export function operatingPoint(points: readonly ReplayOperatingPoint[], target: number) {
  // A measured quality of 1.0 means no cheap pick failed out of fold, not that
  // none can: a target of perfection gets the reference model.
  if (target >= 1.0) {
    return ALL_FRONTIER;
  }
  const ordered = [...points].sort(
    (a, b) => a.cost_per_prompt - b.cost_per_prompt || b.quality - a.quality,
  );
  return ordered.find((p) => p.quality >= target) ?? ALL_FRONTIER;
}

export function routeRow(row: ReplayRow, point: ReplayOperatingPoint): Tier {
  if (row.p_local >= point.tau_local) {
    return "local";
  }
  if (row.p_economy >= point.tau_economy) {
    return "economy";
  }
  return "frontier";
}

export function tierOutcome(row: ReplayRow, tier: Tier) {
  if (tier === "local") {
    return { cost: 0, ok: row.local_ok };
  }
  if (tier === "economy") {
    return { cost: row.cost_economy, ok: row.economy_ok };
  }
  // The frontier tier is the reference, so it counts as sufficient by definition.
  return { cost: row.cost_frontier, ok: true };
}

export function evaluate(rows: readonly ReplayRow[], point: ReplayOperatingPoint): Evaluation {
  const counts: TierShare = { local: 0, economy: 0, frontier: 0 };
  const langs: Record<string, { n: number; cost: number; ok: number }> = {};
  let cost = 0;
  let ok = 0;
  for (const r of rows) {
    const tier = routeRow(r, point);
    const outcome = tierOutcome(r, tier);
    counts[tier] += 1;
    cost += outcome.cost;
    ok += outcome.ok ? 1 : 0;
    const lang = (langs[r.lang] ??= { n: 0, cost: 0, ok: 0 });
    lang.n += 1;
    lang.cost += outcome.cost;
    lang.ok += outcome.ok ? 1 : 0;
  }
  const n = rows.length;
  if (n === 0) {
    return { costPerPrompt: 0, quality: 0, share: counts, byLang: {} };
  }
  const byLang: Record<string, LangFigure> = {};
  for (const [lang, v] of Object.entries(langs)) {
    byLang[lang] = { n: v.n, costPerPrompt: v.cost / v.n, quality: v.ok / v.n };
  }
  return {
    costPerPrompt: cost / n,
    quality: ok / n,
    share: { local: counts.local / n, economy: counts.economy / n, frontier: counts.frontier / n },
    byLang,
  };
}

function randomCorners(baselines: ReplayBaselines): CostQuality[] {
  return [baselines.all_local, baselines.all_economy, baselines.all_frontier];
}

/** Cheapest random mixture of the three single-tier policies reaching q. */
export function randomCostAtQuality(baselines: ReplayBaselines, q: number): number | null {
  const corners = randomCorners(baselines);
  let best: number | null = null;
  for (const c of corners) {
    if (c.quality >= q) {
      best = best === null ? c.cost : Math.min(best, c.cost);
    }
  }
  for (let i = 0; i < corners.length; i += 1) {
    for (let j = i + 1; j < corners.length; j += 1) {
      const [a, b] = [corners[i], corners[j]].sort((x, y) => x.quality - y.quality);
      if (a.quality < q && q <= b.quality) {
        const t = (q - a.quality) / (b.quality - a.quality);
        const mix = (1 - t) * a.cost + t * b.cost;
        best = best === null ? mix : Math.min(best, mix);
      }
    }
  }
  return best;
}

/** The lower-right hull of the three corners: the cheapest random mix at each quality. */
export function randomFrontier(baselines: ReplayBaselines): CostQuality[] {
  const corners = [...randomCorners(baselines)].sort((a, b) => a.quality - b.quality);
  const qualities = Array.from(new Set(corners.map((c) => c.quality)));
  return qualities
    .map((quality) => ({ quality, cost: randomCostAtQuality(baselines, quality) }))
    .filter((p): p is CostQuality => p.cost !== null);
}

export function paretoFront(points: readonly ReplayOperatingPoint[]) {
  const ordered = [...points].sort(
    (a, b) => a.cost_per_prompt - b.cost_per_prompt || b.quality - a.quality,
  );
  const front: ReplayOperatingPoint[] = [];
  let best = Number.NEGATIVE_INFINITY;
  for (const p of ordered) {
    if (p.quality > best) {
      front.push(p);
      best = p.quality;
    }
  }
  return front;
}

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Row indices in a fixed, seeded order (Fisher–Yates over mulberry32). */
export function replayOrder(rows: readonly unknown[], seed: number) {
  const order = rows.map((_, i) => i);
  const random = mulberry32(seed);
  for (let i = order.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return order;
}
