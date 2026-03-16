"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

let inMemoryAdminKey: string | null = null;

type AdminSessionContextValue = {
  adminKey: string | null;
  isAuthenticated: boolean;
  isSigningIn: boolean;
  signIn: (nextAdminKey: string) => Promise<void>;
  signOut: () => void;
  clearSession: () => void;
};

const AdminSessionContext = createContext<AdminSessionContextValue | null>(null);

type AdminSessionProviderProps = {
  children: ReactNode;
  initialAdminKey?: string | null;
};

export function AdminSessionProvider({
  children,
  initialAdminKey = null,
}: AdminSessionProviderProps) {
  const [adminKey, setAdminKey] = useState<string | null>(initialAdminKey ?? inMemoryAdminKey);
  const [isSigningIn, setIsSigningIn] = useState(false);

  const value = useMemo<AdminSessionContextValue>(
    () => ({
      adminKey,
      isAuthenticated: adminKey !== null,
      isSigningIn,
      async signIn(nextAdminKey: string) {
        setIsSigningIn(true);
        try {
          const response = await fetch("/api/admin/session", {
            headers: {
              "X-Nebula-Admin-Key": nextAdminKey,
            },
          });
          if (!response.ok) {
            const body = (await response.json().catch(() => ({}))) as { detail?: string };
            throw new Error(body.detail ?? "Unable to validate the Nebula admin key.");
          }
          inMemoryAdminKey = nextAdminKey;
          setAdminKey(nextAdminKey);
        } finally {
          setIsSigningIn(false);
        }
      },
      signOut() {
        inMemoryAdminKey = null;
        setAdminKey(null);
      },
      clearSession() {
        inMemoryAdminKey = null;
        setAdminKey(null);
      },
    }),
    [adminKey, isSigningIn],
  );

  return <AdminSessionContext.Provider value={value}>{children}</AdminSessionContext.Provider>;
}

export function useAdminSession() {
  const context = useContext(AdminSessionContext);
  if (!context) {
    throw new Error("useAdminSession must be used inside AdminSessionProvider.");
  }
  return context;
}
