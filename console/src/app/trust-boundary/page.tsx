import { TrustBoundaryCard } from "@/components/hosted/trust-boundary-card";
import { getHostedContractContent } from "@/lib/hosted-contract";

export const metadata = {
  title: "Hosted Trust Boundary - Nebula",
};

export default function TrustBoundaryPage() {
  const { copy } = getHostedContractContent();

  return (
    <main className="min-h-screen px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6">
          <h1 className="font-[var(--font-fira-code)] text-2xl font-semibold text-slate-900">
            Hosted trust boundary
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            The hosted control plane is optional for self-hosted Nebula and
            recommended for pilots because it improves onboarding and fleet
            visibility without becoming authoritative for local runtime
            enforcement.
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            Hosted-control-plane outages degrade visibility only; they do not
            break the self-hosted serving path.
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-600">
            Below is the default data contract between your deployment and the
            hosted plane.
          </p>
        </div>

        <TrustBoundaryCard />

        <section className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-white/70 px-6 py-5">
          <p className="text-sm leading-relaxed text-slate-600">
            {copy.pilotIntro}
          </p>

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
              {copy.outageHeading}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              {copy.outageBody}
            </p>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-slate-900">
              {copy.remoteLimitsHeading}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              {copy.remoteLimitsBody}
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
