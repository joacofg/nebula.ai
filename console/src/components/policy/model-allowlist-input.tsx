"use client";

import { useState } from "react";
import { Check, Plus, X } from "lucide-react";

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

      {knownModels.length ? (
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-label text-[13px] font-medium text-ink-3">Conocidos</span>
          {knownModels.map((model) => {
            const selected = value.includes(model);
            return (
              <button
                key={model}
                type="button"
                aria-pressed={selected}
                className={[
                  "inline-flex h-8 items-center gap-1.5 border px-2.5 font-mono text-[12px] transition-colors",
                  selected ? "border-ink bg-canvas text-ink" : "border-line bg-surface text-ink-2 hover:border-ink",
                ].join(" ")}
                onClick={() => (selected ? removeModel(model) : addModel(model))}
              >
                {selected ? <Check aria-hidden className="size-3.5" /> : null}
                {model}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
