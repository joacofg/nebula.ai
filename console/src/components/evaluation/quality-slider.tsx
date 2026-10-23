import { TARGET_MAX, TARGET_MIN, TARGET_STEP, formatTarget, snapTarget } from "@/lib/quality-target";

type QualitySliderProps = {
  value: number;
  onChange: (value: number) => void;
  /** Locked while a save is in flight, so its confirmation describes the value on screen. */
  disabled?: boolean;
};

export function QualitySlider({ value, onChange, disabled = false }: QualitySliderProps) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <label htmlFor="quality-target" className="text-lg font-semibold text-ink">
          Calidad objetivo
        </label>
        <output htmlFor="quality-target" className="text-[44px] font-semibold leading-none tracking-[-0.02em] text-ink">
          {formatTarget(value)}
        </output>
      </div>
      <input
        id="quality-target"
        type="range"
        min={TARGET_MIN}
        max={TARGET_MAX}
        step={TARGET_STEP}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(snapTarget(Number(event.target.value)))}
        className="mt-3 w-full cursor-pointer accent-mark disabled:cursor-not-allowed disabled:accent-ink-3"
      />
      <div className="mt-1 flex justify-between font-mono text-xs text-ink-3">
        <span>{formatTarget(TARGET_MIN)}</span>
        <span>{formatTarget(TARGET_MAX)}</span>
      </div>
    </div>
  );
}
