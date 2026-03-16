type PolicyAdvancedSectionProps = {
  maxPremiumCostPerRequest: string;
  softBudgetUsd: string;
  promptCaptureEnabled: boolean;
  responseCaptureEnabled: boolean;
  onFieldChange: (field: "maxPremiumCostPerRequest" | "softBudgetUsd", value: string) => void;
  onToggleChange: (
    field: "promptCaptureEnabled" | "responseCaptureEnabled",
    value: boolean,
  ) => void;
};

export function PolicyAdvancedSection({
  maxPremiumCostPerRequest,
  softBudgetUsd,
  promptCaptureEnabled,
  responseCaptureEnabled,
  onFieldChange,
  onToggleChange,
}: PolicyAdvancedSectionProps) {
  return (
    <details className="rounded-2xl border border-border bg-slate-50 px-4 py-4" open>
      <summary className="cursor-pointer text-sm font-semibold text-slate-900">Advanced settings</summary>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <label className="field-label" htmlFor="max-premium-cost">
            Max premium cost per request
          </label>
          <input
            id="max-premium-cost"
            className="field-input"
            inputMode="decimal"
            value={maxPremiumCostPerRequest}
            onChange={(event) => onFieldChange("maxPremiumCostPerRequest", event.target.value)}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="soft-budget-usd">
            Soft budget USD
          </label>
          <input
            id="soft-budget-usd"
            className="field-input"
            inputMode="decimal"
            value={softBudgetUsd}
            onChange={(event) => onFieldChange("softBudgetUsd", event.target.value)}
          />
        </div>
      </div>

      <div className="mt-4 space-y-3">
        <label className="flex items-center gap-3 rounded-xl border border-border bg-white px-4 py-3 text-sm font-medium text-slate-800">
          <input
            type="checkbox"
            checked={promptCaptureEnabled}
            onChange={(event) => onToggleChange("promptCaptureEnabled", event.target.checked)}
          />
          Prompt capture enabled
        </label>

        <label className="flex items-center gap-3 rounded-xl border border-border bg-white px-4 py-3 text-sm font-medium text-slate-800">
          <input
            type="checkbox"
            checked={responseCaptureEnabled}
            onChange={(event) => onToggleChange("responseCaptureEnabled", event.target.checked)}
          />
          Response capture enabled
        </label>
      </div>

      <p className="mt-4 text-sm text-slate-500">
        Stored for future governance hardening; not yet enforced at runtime.
      </p>
    </details>
  );
}
