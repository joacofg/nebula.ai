import type { ReactElement, ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";

import { AdminSessionProvider } from "@/lib/admin-session-provider";

type WrapperProps = {
  children: ReactNode;
};

type RenderOptions = {
  adminKey?: string | null;
};

export function renderWithProviders(ui: ReactElement, options: RenderOptions = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <AdminSessionProvider initialAdminKey={options.adminKey ?? null}>{children}</AdminSessionProvider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper });
}
