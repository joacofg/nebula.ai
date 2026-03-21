"use client";

import { useEffect } from "react";
import { ArrowRight, LockKeyhole, ServerCrash, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { AdminLoginForm } from "@/components/auth/admin-login-form";
import { useAdminSession } from "@/lib/admin-session-provider";

export function LoginPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAdminSession();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/tenants");
    }
  }, [isAuthenticated, router]);

  return (
    <main className="min-h-screen px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <section className="rounded-[2rem] border border-slate-200/80 bg-slate-950 px-6 py-8 text-white shadow-panel sm:px-8 sm:py-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-sky-200">
            Self-hosted governance
          </div>
          <h2 className="mt-6 max-w-2xl font-[var(--font-fira-code)] text-3xl font-semibold leading-tight sm:text-4xl">
            Precise tenant control without dropping into raw admin calls.
          </h2>
          <p className="mt-4 max-w-xl text-base text-slate-300">
            Nebula&apos;s operator console wraps the existing admin-key trust model in a compact,
            technical UI tuned for self-hosted governance work.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <div className="shell-card px-4 py-4">
              <LockKeyhole className="h-5 w-5 text-sky-300" />
              <h3 className="mt-3 text-sm font-semibold">Memory-only access</h3>
              <p className="mt-2 text-sm text-slate-300">
                The admin key stays in React state only. Refresh ends the session by design.
              </p>
            </div>
            <div className="shell-card px-4 py-4">
              <ArrowRight className="h-5 w-5 text-sky-300" />
              <h3 className="mt-3 text-sm font-semibold">Direct to tenants</h3>
              <p className="mt-2 text-sm text-slate-300">
                Successful sign-in lands on the tenant management surface immediately.
              </p>
            </div>
            <div className="shell-card px-4 py-4">
              <ServerCrash className="h-5 w-5 text-sky-300" />
              <h3 className="mt-3 text-sm font-semibold">Proxy boundary</h3>
              <p className="mt-2 text-sm text-slate-300">
                Browser requests stay same-origin while the console forwards them to the FastAPI admin API.
              </p>
            </div>
          </div>
        </section>

        <div className="flex flex-col gap-6">
          <AdminLoginForm reason={searchParams.get("reason")} />

          <Link
            href="/trust-boundary"
            className="inline-flex items-center gap-2 self-center text-sm font-medium text-slate-500 transition hover:text-sky-700"
          >
            <ShieldCheck className="h-4 w-4" />
            Review hosted trust boundary
          </Link>
        </div>
      </div>
    </main>
  );
}
