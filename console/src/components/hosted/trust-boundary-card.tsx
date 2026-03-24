import { getHostedContractContent } from "@/lib/hosted-contract";

export function TrustBoundaryCard() {
  const {
    defaultExportedData,
    excludedByDefault,
    freshnessStates,
    copy,
    reinforcement,
  } = getHostedContractContent();

  return (
    <section className="panel mx-auto max-w-2xl px-6 py-6 sm:px-8 sm:py-8">
      <h2 className="text-lg font-semibold text-slate-900">{copy.heading}</h2>

      <p className="mt-1 text-sm font-medium text-sky-700">{copy.metadataOnly}</p>

      <p className="mt-3 text-sm text-slate-600">{copy.notInPath}</p>

      <ul className="mt-4 grid gap-1.5">
        {defaultExportedData.map((field) => (
          <li
            key={field.key}
            className="flex items-baseline gap-2 text-sm text-slate-700"
          >
            <span className="inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sky-500" />
            {field.label}
          </li>
        ))}
      </ul>

      <h3 className="mt-6 text-sm font-semibold text-slate-900">
        Shared reading guidance
      </h3>
      <ul className="mt-2 grid gap-1.5">
        {reinforcement.operatorReadingGuidance.map((guidance) => (
          <li
            key={guidance}
            className="flex items-start gap-2 text-sm text-slate-700"
          >
            <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
            <span>{guidance}</span>
          </li>
        ))}
      </ul>

      <h3 className="mt-6 text-sm font-semibold text-slate-900">
        Freshness states
      </h3>
      <ul className="mt-2 grid gap-1.5">
        {freshnessStates.map((state) => (
          <li key={state.key} className="text-sm text-slate-700">
            <span className="font-medium">{state.key}</span>
            <span className="text-slate-500"> &mdash; {state.description}</span>
          </li>
        ))}
      </ul>

      <h3 className="mt-6 text-sm font-semibold text-slate-900">
        Reinforcement guardrails
      </h3>
      <ul className="mt-2 grid gap-1.5">
        {reinforcement.allowedDescriptiveClaims.map((claim) => (
          <li
            key={claim}
            className="flex items-start gap-2 text-sm text-slate-700"
          >
            <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sky-500" />
            <span>{claim}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 px-4 py-4">
        <p className="text-sm font-semibold text-slate-900">
          {reinforcement.boundedActionPhrasing.label}
        </p>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          {reinforcement.boundedActionPhrasing.description}
        </p>
      </div>

      <h3 className="mt-6 text-sm font-semibold text-slate-900">
        {copy.excludedHeading}
      </h3>
      <ul className="mt-2 grid gap-1.5">
        {excludedByDefault.map((item) => (
          <li
            key={item}
            className="flex items-baseline gap-2 text-sm text-slate-700"
          >
            <span className="inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-pink-500" />
            {item}
          </li>
        ))}
      </ul>

      <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
        <p className="text-sm font-medium text-amber-800">
          {copy.freshnessWarning}
        </p>
      </div>

      <p className="mt-4 text-xs text-slate-500">{copy.footnote}</p>
    </section>
  );
}
