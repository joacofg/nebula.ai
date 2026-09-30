"use client";

import { LoaderCircle, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAdminSession } from "@/lib/admin-session-provider";

const REAUTH_MESSAGES: Record<string, string> = {
  "session-expired": "Your in-memory admin session is gone. Enter the Nebula admin key again.",
  signed_out: "You signed out of the operator console.",
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

  const validationError = touched && adminKey.trim().length === 0 ? "Nebula admin key is required." : null;
  const helperMessage = useMemo(() => (reason ? REAUTH_MESSAGES[reason] ?? null : null), [reason]);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/tenants");
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
      setError(nextError instanceof Error ? nextError.message : "Unable to validate the admin key.");
    }
  }

  return (
    <div className="panel w-full max-w-md overflow-hidden">
      <div className="bg-panel px-6 py-5 text-surface">
        <div className="inline-flex items-center gap-2 rounded-full border border-surface/10 bg-surface/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-mark-line">
          <ShieldCheck className="h-3.5 w-3.5" />
          Nebula control plane
        </div>
        <h1 className="mt-4 font-(--font-fira-code) text-2xl font-semibold text-surface">
          Operator Console
        </h1>
        <p className="mt-2 text-sm text-on-panel-2">
          Paste the deployment admin key to open the focused governance surface for tenants, API keys,
          and policy management.
        </p>
      </div>

      {/* method="post" keeps the admin key out of the URL if the form ever
          submits natively (e.g. before hydration), instead of a GET query string. */}
      <form className="space-y-5 px-6 py-6" method="post" onSubmit={handleSubmit}>
        {helperMessage ? (
          <div className="rounded-xl border border-mark-line bg-mark-soft px-4 py-3 text-sm text-mark">
            {helperMessage}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-xl border border-danger-line bg-danger-soft px-4 py-3 text-sm text-danger">
            {error}
          </div>
        ) : null}

        <div>
          <label className="field-label" htmlFor="admin-key">
            Nebula admin key
          </label>
          <input
            id="admin-key"
            name="admin-key"
            type="password"
            autoComplete="off"
            className="field-input"
            placeholder="nb-admin-live-..."
            value={adminKey}
            onBlur={() => setTouched(true)}
            onChange={(event) => setAdminKey(event.target.value)}
            aria-invalid={validationError ? "true" : "false"}
          />
          {validationError ? (
            <p className="mt-2 text-sm text-danger" role="alert">
              {validationError}
            </p>
          ) : (
            <p className="mt-2 text-sm text-ink-4">
              Stored in browser memory only. Refreshing or closing the tab clears this session.
            </p>
          )}
        </div>

        <button className="action-button w-full gap-2" disabled={isSigningIn} type="submit">
          {isSigningIn ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
          Enter console
        </button>
      </form>
    </div>
  );
}
