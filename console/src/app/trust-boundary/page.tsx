import { TrustBoundaryCard } from "@/components/hosted/trust-boundary-card";

export const metadata = {
  title: "Hosted Trust Boundary - Nebula",
};

export default function TrustBoundaryPage() {
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
            enforcement. Below is the default data contract between your
            deployment and the hosted plane.
          </p>
        </div>

        <TrustBoundaryCard />

        <p className="mt-6 text-center text-xs text-slate-400">
          This page is public and accessible before authentication.
        </p>
      </div>
    </main>
  );
}
