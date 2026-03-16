"use client";

import type { ReactNode } from "react";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { OperatorShell } from "@/components/shell/operator-shell";
import { useAdminSession } from "@/lib/admin-session-provider";

export default function ConsoleLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const router = useRouter();
  const { adminKey } = useAdminSession();

  useEffect(() => {
    if (!adminKey) {
      router.replace("/?reason=session-expired");
    }
  }, [adminKey, router]);

  if (!adminKey) {
    return null;
  }

  return <OperatorShell>{children}</OperatorShell>;
}
