import type { ReactElement, ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";

import { AdminSessionProvider } from "@/lib/admin-session-provider";
import { queryClientDefaultOptions } from "@/lib/query-provider";
import { SelectedTenantProvider } from "@/lib/selected-tenant";

type WrapperProps = {
  children: ReactNode;
};

type RenderOptions = {
  adminKey?: string | null;
  /** A client the test prepared (with data already cached, say); a fresh one otherwise. */
  queryClient?: QueryClient;
};

/**
 * The query client the tests render with: the console's own defaults (its network mode too),
 * but no retries, so a failure shows at once.
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      ...queryClientDefaultOptions,
      queries: { ...queryClientDefaultOptions.queries, retry: false },
    },
  });
}

export function renderWithProviders(ui: ReactElement, options: RenderOptions = {}) {
  const queryClient = options.queryClient ?? createTestQueryClient();

  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <AdminSessionProvider initialAdminKey={options.adminKey ?? null}>
          <SelectedTenantProvider>{children}</SelectedTenantProvider>
        </AdminSessionProvider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper });
}
