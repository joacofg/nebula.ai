import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundMetadata } from "@/components/playground/playground-metadata";
import { renderWithProviders } from "@/test/render";

describe("playground-metadata", () => {
  it("renders the immediate routing, tenant, and policy evidence", () => {
    renderWithProviders(
      <PlaygroundMetadata
        requestId="req-play-001"
        tenantId="tenant-alpha"
        routeTarget="premium"
        routeReason="complex_prompt"
        routeTier="economy"
        provider="openai-compatible"
        cacheHit={false}
        fallbackUsed
        latencyMs={187}
        policyMode="auto"
        policyOutcome="allowed"
      />,
    );

    expect(screen.getByText("Detalle de la respuesta")).toBeInTheDocument();
    for (const label of ["Request ID", "Tenant", "Ruta", "Motivo", "Nivel", "Proveedor", "Modo de política", "Resultado de política", "Caché", "Fallback", "Latencia"]) {
      expect(screen.getByRole("group", { name: label })).toBeInTheDocument();
    }
    expect(screen.getByText("req-play-001")).toBeInTheDocument();
    expect(screen.getByText("tenant-alpha")).toBeInTheDocument();
    expect(screen.getByText("premium")).toBeInTheDocument();
    expect(screen.getByText("complex_prompt")).toBeInTheDocument();
    expect(screen.getByText("openai-compatible")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Caché" })).toHaveTextContent("no");
    expect(screen.getByRole("group", { name: "Fallback" })).toHaveTextContent("sí");
    expect(screen.getByText("187 ms")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Nivel" })).toHaveTextContent("economy");
  });
});
