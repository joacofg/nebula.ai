export const QUALITY_MIN = 0.75;
export const QUALITY_MAX = 1;
export const QUALITY_STEP = 0.005;

/** Slider values are floats: snap them to the 0.005 grid, three decimals. */
export function snapTarget(value: number) {
  const clamped = Math.min(QUALITY_MAX, Math.max(QUALITY_MIN, value));
  return Math.round(Math.round(clamped / QUALITY_STEP) * QUALITY_STEP * 1000) / 1000;
}

type QualitySliderProps = {
  value: number;
  onChange: (value: number) => void;
};

export function QualitySlider({ value, onChange }: QualitySliderProps) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <label htmlFor="quality-target" className="field-label mb-0">
          Calidad objetivo
        </label>
        <output htmlFor="quality-target" className="font-mono text-2xl font-semibold text-slate-950">
          {value.toFixed(3)}
        </output>
      </div>
      <input
        id="quality-target"
        type="range"
        min={QUALITY_MIN}
        max={QUALITY_MAX}
        step={QUALITY_STEP}
        value={value}
        onChange={(event) => onChange(snapTarget(Number(event.target.value)))}
        className="mt-3 w-full accent-sky-700"
      />
      <div className="mt-1 flex justify-between font-mono text-xs text-slate-500">
        <span>{QUALITY_MIN.toFixed(2)}</span>
        <span>{QUALITY_MAX.toFixed(2)}</span>
      </div>
    </div>
  );
}
