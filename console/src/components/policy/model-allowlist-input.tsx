"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";

type ModelAllowlistInputProps = {
  knownModels: string[];
  value: string[];
  onChange: (nextValue: string[]) => void;
};

export function ModelAllowlistInput({ knownModels, value, onChange }: ModelAllowlistInputProps) {
  const [draftModel, setDraftModel] = useState("");

  function addModel(model: string) {
    const normalized = model.trim();
    if (!normalized || value.includes(normalized)) {
      setDraftModel("");
      return;
    }
    onChange([...value, normalized]);
    setDraftModel("");
  }

  function removeModel(model: string) {
    onChange(value.filter((entry) => entry !== model));
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {value.map((model) => (
          <button
            key={model}
            type="button"
            className="inline-flex items-center gap-2 rounded-full bg-ink px-3 py-1.5 text-xs font-semibold text-mark-soft"
            onClick={() => removeModel(model)}
          >
            {model}
            <X className="h-3.5 w-3.5" />
          </button>
        ))}
      </div>

      <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
        <input
          className="field-input font-(--font-fira-code) text-xs"
          placeholder="Add model"
          value={draftModel}
          onChange={(event) => setDraftModel(event.target.value)}
        />
        <button type="button" className="secondary-button gap-2" onClick={() => addModel(draftModel)}>
          <Plus className="h-4 w-4" />
          Add model
        </button>
      </div>

      <div className="grid gap-2 rounded-2xl border border-line bg-canvas p-3 sm:grid-cols-2">
        {knownModels.map((model) => {
          const selected = value.includes(model);
          return (
            <button
              key={model}
              type="button"
              className={[
                "rounded-xl border px-3 py-2 text-left text-sm transition",
                selected
                  ? "border-mark-line bg-mark-soft text-mark"
                  : "border-surface bg-surface text-ink-2 hover:border-line",
              ].join(" ")}
              onClick={() => (selected ? removeModel(model) : addModel(model))}
            >
              {model}
            </button>
          );
        })}
      </div>
    </div>
  );
}
