/**
 * The quality target range of the console: the Evaluación slider and the Policy form share it.
 * The artifact's lowest operating point is 0.7544, so lower targets pick the same point; the
 * API keeps accepting 0.5 to 1.0. The step is a hundredth so every reachable target is shown
 * exactly by `formatTarget`.
 */
export const TARGET_MIN = 0.75;
export const TARGET_MAX = 1;
export const TARGET_STEP = 0.01;

/** A target as the thesis writes it, always with two decimals: 0.9 → "0.90". */
export function formatTarget(target: number): string {
  return target.toFixed(2);
}

/** Slider values are floats: clamp them to the range and snap them to the step grid. */
export function snapTarget(target: number): number {
  const clamped = Math.min(TARGET_MAX, Math.max(TARGET_MIN, target));
  return Math.round(Math.round(clamped / TARGET_STEP) * TARGET_STEP * 1000) / 1000;
}
