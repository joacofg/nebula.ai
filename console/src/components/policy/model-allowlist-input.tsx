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
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2" aria-label="Modelos permitidos">
        {value.map((model) => (
          <button
            key={model}
            type="button"
            aria-label={`Quitar ${model}`}
            className="inline-flex h-8 items-center gap-2 border border-ink bg-surface px-2.5 font-mono text-[12px] font-medium text-ink transition-colors hover:bg-canvas"
            onClick={() => removeModel(model)}
          >
            {model}
            <X aria-hidden className="size-3.5" />
          </button>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          className="field-input font-mono text-[13px]"
          placeholder="proveedor/modelo"
          aria-label="Agregar modelo"
          value={draftModel}
          onChange={(event) => setDraftModel(event.target.value)}
        />
        <button type="button" className="secondary-button" onClick={() => addModel(draftModel)}>
          <Plus aria-hidden className="size-4" />
          Agregar
        </button>
      </div>

      {knownModels.some((model) => !value.includes(model)) ? (
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-label text-[13px] font-medium text-ink-3">Sugeridos</span>
          {knownModels
            .filter((model) => !value.includes(model))
            .map((model) => (
              <button
                key={model}
                type="button"
                className="inline-flex h-8 items-center gap-1.5 border border-dashed border-line-strong/50 bg-surface px-2.5 font-mono text-[12px] text-ink-2 transition-colors hover:border-ink hover:text-ink"
                onClick={() => addModel(model)}
              >
                <Plus aria-hidden className="size-3.5" />
                {model}
              </button>
            ))}
        </div>
      ) : null}
    </div>
  );
}
