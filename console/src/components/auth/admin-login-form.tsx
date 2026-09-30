"use client";

import { LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/system/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAdminSession } from "@/lib/admin-session-provider";
import { Alert, AlertDescription } from "@/components/ui/alert";

const REAUTH_MESSAGES: Record<string, string> = {
  "session-expired": "La sesión se cerró. Ingresar la clave de admin otra vez.",
  signed_out: "Sesión cerrada.",
};

type AdminLoginFormProps = {
  reason?: string | null;
};

export function AdminLoginForm({ reason }: AdminLoginFormProps) {
  const router = useRouter();
  const { signIn, isAuthenticated, isSigningIn } = useAdminSession();
  const [adminKey, setAdminKey] = useState("");
  const [touched, setTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validationError = touched && adminKey.trim().length === 0 ? "Falta la clave de admin." : null;
  const helperMessage = useMemo(() => (reason ? REAUTH_MESSAGES[reason] ?? null : null), [reason]);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/evaluacion");
    }
  }, [isAuthenticated, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTouched(true);
    if (adminKey.trim().length === 0) {
      return;
    }
    setError(null);
    try {
      await signIn(adminKey.trim());
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "No se pudo validar la clave de admin.");
    }
  }

  return (
    <div className="w-full max-w-[440px] border border-line-strong bg-surface">
      <PageHeader title="Nebula" cells={[{ label: "Consola", value: "gateway local" }]} />

      {/* method="post" keeps the admin key out of the URL if the form ever
          submits natively (e.g. before hydration), instead of a GET query string. */}
      <form className="flex flex-col gap-4 px-6 py-6" method="post" onSubmit={handleSubmit}>
        {helperMessage ? (
          <Alert>
            <AlertDescription>{helperMessage}</AlertDescription>
          </Alert>
        ) : null}

        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <div>
          <Label htmlFor="admin-key" className="mb-1.5 font-label text-[13px] font-medium text-ink-2">
            Clave de admin
          </Label>
          <Input
            id="admin-key"
            name="admin-key"
            type="password"
            autoComplete="off"
            placeholder="nb-admin-…"
            value={adminKey}
            onBlur={() => setTouched(true)}
            onChange={(event) => setAdminKey(event.target.value)}
            aria-invalid={validationError ? "true" : "false"}
            aria-describedby="admin-key-help"
          />
          {validationError ? (
            <p id="admin-key-help" className="mt-1.5 text-sm text-danger" role="alert">
              {validationError}
            </p>
          ) : (
            <p id="admin-key-help" className="mt-1.5 text-sm text-ink-3">
              Se guarda solo en memoria: al recargar se cierra la sesión.
            </p>
          )}
        </div>

        <Button type="submit" size="lg" disabled={isSigningIn} className="w-full">
          {isSigningIn ? <LoaderCircle aria-hidden className="size-4 animate-spin" /> : null}
          {isSigningIn ? "Entrando…" : "Entrar"}
        </Button>
      </form>
    </div>
  );
}
