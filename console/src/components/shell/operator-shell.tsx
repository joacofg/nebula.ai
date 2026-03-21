"use client";

import type { ReactNode } from "react";

import { Activity, FlaskConical, KeyRound, LogOut, Orbit, Server, ShieldEllipsis } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAdminSession } from "@/lib/admin-session-provider";

type OperatorShellProps = {
  children: ReactNode;
};

const NAV_ITEMS = [
  { href: "/tenants", label: "Tenants", icon: Orbit },
  { href: "/api-keys", label: "API Keys", icon: KeyRound },
  { href: "/policy", label: "Policy", icon: ShieldEllipsis },
  { href: "/playground", label: "Playground", icon: FlaskConical },
  { href: "/observability", label: "Observability", icon: Activity },
  { href: "/deployments", label: "Deployments", icon: Server },
];

export function OperatorShell({ children }: OperatorShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { signOut } = useAdminSession();

  return (
    <div className="grid min-h-screen lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="bg-panel px-4 py-4 text-slate-100 sm:px-6 lg:px-5 lg:py-6">
        <div className="flex items-start justify-between gap-4 lg:block">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.28em] text-sky-200">
              Nebula operator
            </div>
            <h1 className="mt-3 font-[var(--font-fira-code)] text-xl font-semibold">Control Plane</h1>
            <p className="mt-2 max-w-xs text-sm text-slate-300">
              Compact governance workflows for the self-hosted runtime.
            </p>
          </div>

          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
            onClick={() => {
              signOut();
              router.push("/?reason=signed_out");
            }}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>

        <nav className="mt-8 grid gap-2" aria-label="Primary">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={[
                  "group inline-flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition",
                  active
                    ? "bg-sky-500/15 text-white ring-1 ring-inset ring-sky-300/30"
                    : "text-slate-300 hover:bg-white/5 hover:text-white",
                ].join(" ")}
              >
                <span
                  className={[
                    "inline-flex h-9 w-9 items-center justify-center rounded-xl transition",
                    active ? "bg-sky-400/20 text-sky-200" : "bg-white/5 text-slate-400 group-hover:text-sky-200",
                  ].join(" ")}
                >
                  <Icon className="h-4 w-4" />
                </span>
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="min-w-0 bg-transparent px-4 py-4 sm:px-6 lg:px-8 lg:py-8">
        <div className="overflow-x-auto">{children}</div>
      </main>
    </div>
  );
}
