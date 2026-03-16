import { Suspense } from "react";

import { LoginPageClient } from "@/components/auth/login-page-client";

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-slate-50" />}>
      <LoginPageClient />
    </Suspense>
  );
}
