"use client";

import type { ReactNode } from "react";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

import { OperatorShell } from "@/components/shell/operator-shell";
import { useAdminSession } from "@/lib/admin-session-provider";
import { SelectedTenantProvider } from "@/lib/selected-tenant";

export default function ConsoleLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const router = useRouter();
  const { adminKey, signOut } = useAdminSession();
  const signedOutByOperator = useRef(false);

  // The one place that leaves the console when the key goes away, so the login is told why exactly once.
  useEffect(() => {
    if (!adminKey) {
      router.replace(signedOutByOperator.current ? "/?reason=signed_out" : "/?reason=session-expired");
    }
  }, [adminKey, router]);

  if (!adminKey) {
    return null;
  }

  return (
    <SelectedTenantProvider>
      <OperatorShell
        onSignOut={() => {
          signedOutByOperator.current = true;
          signOut();
        }}
      >
        {children}
      </OperatorShell>
    </SelectedTenantProvider>
  );
}
