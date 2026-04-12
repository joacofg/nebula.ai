import { TrustBoundaryCard } from "@/components/hosted/trust-boundary-card";
import { getHostedContractContent } from "@/lib/hosted-contract";

export const metadata = {
  title: "Hosted Trust Boundary - Nebula",
};

export default function TrustBoundaryPage() {
  const { copy, reinforcement } = getHostedContractContent();

  return (
    <main className="min-h-screen px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6">
          <h1 className="font-[var(--font-fira-code)] text-2xl font-semibold text-slate-900">
            Hosted trust boundary
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            {reinforcement.allowedDescriptiveClaims[3]}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            {reinforcement.allowedDescriptiveClaims[1]}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            {copy.outageBody}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            Below is the default data contract between your deployment and the
            hosted plane.
          </p>
        </div>

        <TrustBoundaryCard />

        <section className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-white/70 px-6 py-5">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              {copy.onboardingHeading}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              {copy.onboardingBody}
            </p>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              Hosted fleet posture guidance
            </h2>
            <ul className="mt-2 grid gap-2">
              {reinforcement.operatorReadingGuidance.map((guidance) => (
                <li
                  key={guidance}
                  className="flex items-start gap-2 text-sm leading-relaxed text-slate-600"
                >
                  <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
                  <span>{guidance}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              Shared evidence vocabulary
            </h2>
            <ul className="mt-2 grid gap-2">
              <li className="flex items-start gap-2 text-sm leading-relaxed text-slate-600">
                <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sky-500" />
                <span>{reinforcement.evidenceBoundaryVocabulary.retained}</span>
              </li>
              <li className="flex items-start gap-2 text-sm leading-relaxed text-slate-600">
                <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sky-500" />
                <span>{reinforcement.evidenceBoundaryVocabulary.suppressed}</span>
              </li>
              <li className="flex items-start gap-2 text-sm leading-relaxed text-slate-600">
                <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sky-500" />
                <span>{reinforcement.evidenceBoundaryVocabulary.deleted}</span>
              </li>
              <li className="flex items-start gap-2 text-sm leading-relaxed text-slate-600">
                <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sky-500" />
                <span>{reinforcement.evidenceBoundaryVocabulary.notHosted}</span>
              </li>
              <li className="flex items-start gap-2 text-sm leading-relaxed text-slate-600">
                <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-sky-500" />
                <span>{copy.hostedExportExclusion}</span>
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              Hosted outage behavior
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              {copy.outageBody}
            </p>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              Reinforcement guardrails
            </h2>
            <ul className="mt-2 grid gap-2">
              {reinforcement.prohibitedAuthorityClaims.map((claim) => (
                <li
                  key={claim}
                  className="flex items-start gap-2 text-sm leading-relaxed text-slate-600"
                >
                  <span className="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-rose-500" />
                  <span>{claim}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              {copy.remoteLimitsHeading}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              {copy.remoteLimitsBody}
            </p>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              {reinforcement.boundedActionPhrasing.description}
            </p>
          </div>
        </section>

        <p className="mt-6 text-center text-xs text-slate-400">
          This page is public and accessible before authentication.
        </p>
      </div>
    </main>
  );
}
