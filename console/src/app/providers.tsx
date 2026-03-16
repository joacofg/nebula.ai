"use client";

import type { ReactNode } from "react";

import { AdminSessionProvider } from "@/lib/admin-session-provider";
import { QueryProvider } from "@/lib/query-provider";

type ProvidersProps = {
  children: ReactNode;
};

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryProvider>
      <AdminSessionProvider>{children}</AdminSessionProvider>
    </QueryProvider>
  );
}
