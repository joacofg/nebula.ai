"use client";

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { useState } from "react";
import { Activity, ChartLine, FlaskConical, KeyRound, LogOut, Menu, Orbit, ShieldEllipsis } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "cn";

import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useAdminSession } from "@/lib/admin-session-provider";

type NavItem = { href: string; label: string; icon: LucideIcon };

const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "Operar",
    items: [
      { href: "/evaluacion", label: "Evaluación", icon: ChartLine },
      { href: "/playground", label: "Playground", icon: FlaskConical },
      { href: "/observability", label: "Observabilidad", icon: Activity },
    ],
  },
  {
    label: "Configurar",
    items: [
      { href: "/tenants", label: "Tenants", icon: Orbit },
      { href: "/api-keys", label: "Claves de API", icon: KeyRound },
      { href: "/policy", label: "Política", icon: ShieldEllipsis },
    ],
  },
];

function Brand() {
  return (
    <div className="border-b border-line px-5 py-4">
      <div className="text-xl font-bold leading-tight tracking-[-0.01em] text-ink">Nebula</div>
      <div className="font-label text-[13px] font-medium text-ink-3">gateway local</div>
    </div>
  );
}

function NavLinks({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <nav aria-label="Principal" className="flex flex-col gap-5 py-4">
      {NAV_GROUPS.map((group) => (
        <div key={group.label} className="flex flex-col">
          <div className="px-5 pb-1.5 font-label text-[13px] font-medium text-ink-3">{group.label}</div>
          {group.items.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                onClick={onNavigate}
                className={cn(
                  "flex h-10 items-center gap-3 px-5 text-[15px] transition-colors duration-100",
                  active
                    ? "bg-surface font-semibold text-ink shadow-[inset_0_1px_0_var(--color-line),inset_0_-1px_0_var(--color-line)]"
                    : "font-medium text-ink-2 hover:bg-surface/70 hover:text-ink",
                )}
              >
                <Icon aria-hidden className={cn("size-4 shrink-0", active ? "text-mark" : "text-ink-3")} />
                {label}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

function SessionFooter({ onSignOut }: { onSignOut: () => void }) {
  return (
    <div className="mt-auto border-t border-line px-5 py-4">
      <div className="font-label text-[13px] font-medium text-ink-3">Sesión en memoria</div>
      <button
        type="button"
        onClick={onSignOut}
        className="mt-2 inline-flex h-9 items-center gap-2 border border-line bg-surface px-3 text-sm font-semibold text-ink transition-colors hover:border-ink"
      >
        <LogOut aria-hidden className="size-4" />
        Cerrar sesión
      </button>
    </div>
  );
}

export function OperatorShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { signOut } = useAdminSession();
  const [menuOpen, setMenuOpen] = useState(false);

  function handleSignOut() {
    signOut();
    router.push("/?reason=signed_out");
  }

  return (
    <div className="grid min-h-screen bg-surface lg:grid-cols-[216px_minmax(0,1fr)]">
      <aside className="hidden border-r border-line-strong bg-rail lg:block">
        <div className="sticky top-0 flex h-screen flex-col">
          <Brand />
          <NavLinks pathname={pathname} />
          <SessionFooter onSignOut={handleSignOut} />
        </div>
      </aside>

      <div className="min-w-0">
        <div className="flex h-12 items-center justify-between border-b border-line-strong bg-rail px-4 lg:hidden">
          <span className="text-lg font-bold text-ink">Nebula</span>
          <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
            <SheetTrigger
              aria-label="Abrir menú"
              className="inline-flex size-9 items-center justify-center border border-line bg-surface text-ink"
            >
              <Menu aria-hidden className="size-4" />
            </SheetTrigger>
            <SheetContent side="left" className="w-[260px] gap-0 bg-rail p-0">
              <SheetTitle className="sr-only">Menú</SheetTitle>
              <SheetDescription className="sr-only">Navegación de la consola</SheetDescription>
              <Brand />
              <NavLinks pathname={pathname} onNavigate={() => setMenuOpen(false)} />
              <SessionFooter onSignOut={handleSignOut} />
            </SheetContent>
          </Sheet>
        </div>
        {/* Pages stretch to the viewport so the sheet rules of their columns reach the bottom. */}
        <main className="flex min-h-screen min-w-0 flex-col [&>section]:flex [&>section]:flex-1 [&>section]:flex-col [&>section>.grid]:flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
