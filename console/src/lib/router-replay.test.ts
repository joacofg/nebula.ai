import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

import {
  ALL_FRONTIER,
  evaluate,
  isAllFrontier,
  operatingPoint,
  paretoFront,
  randomCostAtQuality,
  randomFrontier,
  replayOrder,
  routeRow,
  type ReplayBaselines,
  type ReplayOperatingPoint,
  type ReplayRow,
  type RouterReplay,
} from "@/lib/router-replay";

const REPLAY_PATH = path.resolve(__dirname, "../../../src/nebula/data/router_replay_v1.json");
const replay = JSON.parse(readFileSync(REPLAY_PATH, "utf-8")) as RouterReplay;

function row(overrides: Partial<ReplayRow> = {}): ReplayRow {
  return {
    key: "en:qa-0000",
    lang: "en",
    task: "qa",
    text: "prompt",
    p_local: 0.5,
    p_economy: 0.5,
    local_ok: true,
    economy_ok: true,
    cost_economy: 0.001,
    cost_frontier: 0.002,
    ...overrides,
  };
}

function point(overrides: Partial<ReplayOperatingPoint> = {}): ReplayOperatingPoint {
  return { tau_local: 0.5, tau_economy: 0.5, quality: 0.9, cost_per_prompt: 0.001, ...overrides };
}

describe("router replay golden test (real file)", () => {
  it("reproduces Python's cost and quality for every operating point", () => {
    expect(replay.rows).toHaveLength(1250);
    expect(replay.operating_points.length).toBeGreaterThan(0);
    for (const p of replay.operating_points) {
      const result = evaluate(replay.rows, p);
      expect(Math.abs(result.quality - p.quality)).toBeLessThan(1e-9);
      expect(Math.abs(result.costPerPrompt - p.cost_per_prompt)).toBeLessThan(1e-9);
    }
  });

  it("reproduces the nested 0.95 share and all-frontier baseline", () => {
    const allFrontier = evaluate(replay.rows, ALL_FRONTIER);
    expect(allFrontier.quality).toBe(1);
    expect(Math.abs(allFrontier.costPerPrompt - replay.baselines.all_frontier.cost)).toBeLessThan(1e-9);
    expect(allFrontier.share).toEqual({ local: 0, economy: 0, frontier: 1 });
  });
});

describe("operatingPoint", () => {
  const points = [
    point({ quality: 0.8, cost_per_prompt: 0.0005 }),
    point({ quality: 0.95, cost_per_prompt: 0.002, tau_local: 0.9 }),
    point({ quality: 0.95, cost_per_prompt: 0.0015, tau_local: 0.8 }),
    point({ quality: 0.97, cost_per_prompt: 0.0015, tau_local: 0.85 }),
  ];

  it("takes the cheapest point meeting the target, ties broken by higher quality", () => {
    expect(operatingPoint(points, 0.9)).toEqual(points[3]);
    expect(operatingPoint(points, 0.8)).toEqual(points[0]);
  });

  it("returns all frontier for a target of 1.0", () => {
    expect(isAllFrontier(operatingPoint([...points, point({ quality: 1 })], 1.0))).toBe(true);
  });

  it("returns all frontier when no point reaches the target", () => {
    const chosen = operatingPoint(points, 0.99);
    expect(isAllFrontier(chosen)).toBe(true);
    expect(chosen.quality).toBe(1);
  });

  it("returns all frontier when there are no points", () => {
    expect(isAllFrontier(operatingPoint([], 0.8))).toBe(true);
  });
});

describe("routeRow", () => {
  it("cascades local, then economy, then frontier", () => {
    const p = point({ tau_local: 0.7, tau_economy: 0.9 });
    expect(routeRow(row({ p_local: 0.7 }), p)).toBe("local");
    expect(routeRow(row({ p_local: 0.69, p_economy: 0.9 }), p)).toBe("economy");
    expect(routeRow(row({ p_local: 0.69, p_economy: 0.89 }), p)).toBe("frontier");
  });

  it("sends everything to frontier at the all-frontier point", () => {
    expect(routeRow(row({ p_local: 1, p_economy: 1 }), ALL_FRONTIER)).toBe("frontier");
  });
});

describe("evaluate", () => {
  it("averages cost, quality, share and per-language figures", () => {
    const rows = [
      row({ lang: "es", p_local: 0.9, local_ok: false }),
      row({ lang: "es", p_local: 0.1, p_economy: 0.9, economy_ok: true, cost_economy: 0.004 }),
      row({ lang: "en", p_local: 0.1, p_economy: 0.1, cost_frontier: 0.008 }),
      row({ lang: "en", p_local: 0.9, local_ok: true }),
    ];
    const result = evaluate(rows, point({ tau_local: 0.5, tau_economy: 0.5 }));
    expect(result.costPerPrompt).toBeCloseTo(0.003, 12);
    expect(result.quality).toBeCloseTo(0.75, 12);
    expect(result.share).toEqual({ local: 0.5, economy: 0.25, frontier: 0.25 });
    expect(result.byLang.es).toEqual({ n: 2, costPerPrompt: 0.002, quality: 0.5 });
    expect(result.byLang.en).toEqual({ n: 2, costPerPrompt: 0.004, quality: 1 });
  });

  it("returns zeros, not NaN, for an empty set", () => {
    const result = evaluate([], point());
    expect(result).toEqual({
      costPerPrompt: 0,
      quality: 0,
      share: { local: 0, economy: 0, frontier: 0 },
      byLang: {},
    });
  });
});

describe("randomCostAtQuality", () => {
  const baselines: ReplayBaselines = {
    all_local: { cost: 0, quality: 0.75 },
    all_economy: { cost: 0.0018, quality: 0.88 },
    all_frontier: { cost: 0.0025, quality: 1 },
    oracle: { cost: 0.0005, quality: 1 },
    heuristic_premium_frontier: { cost: 0.0002, quality: 0.76 },
    heuristic_premium_economy: { cost: 0.0001, quality: 0.756 },
  };

  it("is zero when all-local already reaches the target", () => {
    expect(randomCostAtQuality(baselines, 0.7)).toBe(0);
  });

  it("takes the cheapest mixture over corners and pair segments", () => {
    // local↔frontier at 0.95: t = 0.2/0.25 = 0.8 → 0.002; local↔economy cannot reach it;
    // economy↔frontier: t = 0.07/0.12 → 0.0018 + t*0.0007 ≈ 0.0022083.
    expect(randomCostAtQuality(baselines, 0.95)).toBeCloseTo(0.002, 12);
  });

  it("is null when no mixture reaches the target", () => {
    expect(randomCostAtQuality(baselines, 1.01)).toBeNull();
  });

  it("matches the real file's nested vs_random figure", () => {
    const nested = replay.nested["0.95"];
    const random = randomCostAtQuality(replay.baselines, nested.quality);
    expect(random).not.toBeNull();
    expect(Math.abs(1 - nested.cost / (random as number) - nested.vs_random)).toBeLessThan(1e-9);
  });
});

describe("randomFrontier", () => {
  it("traces the cheapest mix at each corner quality, skipping dominated corners", () => {
    const frontier = randomFrontier({
      all_local: { cost: 0, quality: 0.75 },
      all_economy: { cost: 0.0024, quality: 0.8 },
      all_frontier: { cost: 0.0025, quality: 1 },
      oracle: { cost: 0.0005, quality: 1 },
      heuristic_premium_frontier: { cost: 0.0002, quality: 0.76 },
      heuristic_premium_economy: { cost: 0.0001, quality: 0.756 },
    });
    // Economy is dominated by the local↔frontier mix at 0.8 (0.0005 < 0.0024).
    expect(frontier.map((p) => p.quality)).toEqual([0.75, 0.8, 1]);
    expect(frontier[0].cost).toBe(0);
    expect(frontier[1].cost).toBeCloseTo(0.0005, 12);
    expect(frontier[2].cost).toBe(0.0025);
  });
});

describe("paretoFront", () => {
  it("keeps points sorted by cost with strictly increasing quality", () => {
    const front = paretoFront([
      point({ cost_per_prompt: 0.002, quality: 0.9 }),
      point({ cost_per_prompt: 0.001, quality: 0.9 }),
      point({ cost_per_prompt: 0.0015, quality: 0.85 }),
      point({ cost_per_prompt: 0, quality: 0.75 }),
    ]);
    expect(front.map((p) => [p.cost_per_prompt, p.quality])).toEqual([
      [0, 0.75],
      [0.001, 0.9],
    ]);
  });
});

describe("replayOrder", () => {
  it("is a deterministic permutation for a seed", () => {
    const rows = Array.from({ length: 50 }, (_, i) => row({ key: `k${i}` }));
    const a = replayOrder(rows, 7);
    expect(a).toEqual(replayOrder(rows, 7));
    expect([...a].sort((x, y) => x - y)).toEqual(rows.map((_, i) => i));
    expect(a).not.toEqual(rows.map((_, i) => i));
    expect(replayOrder(rows, 8)).not.toEqual(a);
  });
});
