"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import { QueryClient, QueryClientProvider, type DefaultOptions } from "@tanstack/react-query";

type QueryProviderProps = {
  children: ReactNode;
};

/**
 * The defaults every query and mutation of the console runs with; the tests' client builds on
 * the same object.
 *
 * `networkMode: "always"`: the gateway is self-hosted and reached through the console's own
 * proxies, so what the browser reports about internet access says nothing about it. With the
 * default ("online"), a laptop without wifi would pause every request and the console would
 * never fetch from a gateway on localhost. A gateway that is really down fails fast instead.
 */
export const queryClientDefaultOptions = {
  queries: {
    retry: 1,
    refetchOnWindowFocus: false,
    networkMode: "always",
  },
  mutations: {
    networkMode: "always",
  },
} satisfies DefaultOptions;

export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(() => new QueryClient({ defaultOptions: queryClientDefaultOptions }));

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
