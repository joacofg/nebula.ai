"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { AdminLoginForm } from "@/components/auth/admin-login-form";
import { useAdminSession } from "@/lib/admin-session-provider";

export function LoginPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAdminSession();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/evaluacion");
    }
  }, [isAuthenticated, router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-rail px-4 py-10">
      <AdminLoginForm reason={searchParams.get("reason")} />
    </main>
  );
}
