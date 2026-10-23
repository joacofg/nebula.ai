import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundMetadata } from "@/components/playground/playground-metadata";
import { renderWithProviders } from "@/test/render";

describe("playground-metadata", () => {
  it("renders the request and policy evidence the ledger block does not carry", () => {
    renderWithProviders(
      <PlaygroundMetadata requestId="req-play-001" tenantId="tenant-alpha" policyMode="auto" policyOutcome="allowed" />,
    );

    expect(screen.getByText("Detalle de la respuesta")).toBeInTheDocument();
    for (const label of ["Request ID", "Tenant", "Modo de política", "Resultado de política"]) {
      expect(screen.getByRole("group", { name: label })).toBeInTheDocument();
    }
    expect(screen.getByText("req-play-001")).toBeInTheDocument();
    expect(screen.getByText("tenant-alpha")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Modo de política" })).toHaveTextContent("auto");
    expect(screen.getByRole("group", { name: "Resultado de política" })).toHaveTextContent("allowed");
  });

  it("does not repeat what the ledger block already says", () => {
    renderWithProviders(
      <PlaygroundMetadata requestId="req-play-001" tenantId="tenant-alpha" policyMode="auto" policyOutcome="allowed" />,
    );

    for (const label of ["Ruta", "Motivo", "Nivel", "Proveedor", "Caché", "Fallback", "Latencia"]) {
      expect(screen.queryByRole("group", { name: label })).not.toBeInTheDocument();
    }
  });

  it("shows a dash for evidence the gateway did not send", () => {
    renderWithProviders(<PlaygroundMetadata requestId="" tenantId="" policyMode="" policyOutcome="" />);

    for (const label of ["Request ID", "Tenant", "Modo de política", "Resultado de política"]) {
      expect(screen.getByRole("group", { name: label })).toHaveTextContent("—");
    }
  });
});
