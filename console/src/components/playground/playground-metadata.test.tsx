import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundMetadata } from "@/components/playground/playground-metadata";
import { renderWithProviders } from "@/test/render";

const RESPONSE_FACTS = ["Ruta", "Motivo", "Nivel", "Proveedor", "Caché", "Fallback"];

const response = {
  routeTarget: "premium",
  routeReason: "learned_router",
  routeTier: "economy",
  provider: "openai-compatible",
  cacheHit: false,
  fallbackUsed: true,
};

describe("playground-metadata", () => {
  it("renders the request and policy evidence the ledger block does not carry", () => {
    renderWithProviders(
      <PlaygroundMetadata requestId="req-play-001" tenantId="tenant-alpha" policyMode="auto" policyOutcome="default" />,
    );

    expect(screen.getByText("Detalle de la respuesta")).toBeInTheDocument();
    for (const label of ["Request ID", "Tenant", "Modo de política", "Resultado de política"]) {
      expect(screen.getByRole("group", { name: label })).toBeInTheDocument();
    }
    expect(screen.getByText("req-play-001")).toBeInTheDocument();
    expect(screen.getByText("tenant-alpha")).toBeInTheDocument();
  });

  it("writes the policy mode and outcome as labels, never as the gateway's codes", () => {
    renderWithProviders(
      <PlaygroundMetadata
        requestId="req-play-001"
        tenantId="tenant-alpha"
        policyMode="premium_only"
        policyOutcome="routing_mode=premium_only;denied=Request exceeds the tenant premium spend guardrail.;outcome_evidence=sufficient(eligible=3)"
      />,
    );

    expect(screen.getByRole("group", { name: "Modo de política" })).toHaveTextContent("Solo premium");
    expect(screen.getByRole("group", { name: "Resultado de política" })).toHaveTextContent("Solo premium, denegado");
    expect(screen.queryByText(/routing_mode|denied=|premium_only|outcome_evidence/)).not.toBeInTheDocument();
  });

  it("reads an outcome without a routing mode as Automático, since the gateway omits it for auto", () => {
    renderWithProviders(
      <PlaygroundMetadata requestId="req-1" tenantId="default" policyMode="auto" policyOutcome="soft_budget=exceeded" />,
    );

    expect(screen.getByRole("group", { name: "Modo de política" })).toHaveTextContent("Automático");
    expect(screen.getByRole("group", { name: "Resultado de política" })).toHaveTextContent("Automático");
    expect(screen.queryByText(/soft_budget|exceeded/)).not.toBeInTheDocument();
  });

  it("does not repeat what the ledger block already says when it has the ledger record", () => {
    renderWithProviders(
      <PlaygroundMetadata requestId="req-play-001" tenantId="tenant-alpha" policyMode="auto" policyOutcome="default" />,
    );

    for (const label of [...RESPONSE_FACTS, "Latencia"]) {
      expect(screen.queryByRole("group", { name: label })).not.toBeInTheDocument();
    }
  });

  it("carries the facts of the response headers when there is no ledger record, once each", () => {
    renderWithProviders(
      <PlaygroundMetadata
        requestId="req-play-001"
        tenantId="tenant-alpha"
        policyMode="auto"
        policyOutcome="default"
        response={response}
      />,
    );

    for (const label of RESPONSE_FACTS) {
      expect(screen.getAllByRole("group", { name: label }), label).toHaveLength(1);
    }
    expect(screen.getByRole("group", { name: "Ruta" })).toHaveTextContent("Premium");
    expect(screen.getByRole("group", { name: "Motivo" })).toHaveTextContent("router aprendido");
    expect(screen.getByRole("group", { name: "Nivel" })).toHaveTextContent("economy");
    expect(screen.getByRole("group", { name: "Proveedor" })).toHaveTextContent("openai-compatible");
    expect(screen.getByRole("group", { name: "Caché" })).toHaveTextContent("no");
    expect(screen.getByRole("group", { name: "Fallback" })).toHaveTextContent("sí");
    // The headers carry no latency, and the client's own clock is not the gateway's.
    expect(screen.queryByRole("group", { name: "Latencia" })).not.toBeInTheDocument();
    expect(screen.queryByText(/routing_mode|premium_only|learned_router/)).not.toBeInTheDocument();
  });

  it("shows a dash for evidence the gateway did not send", () => {
    renderWithProviders(
      <PlaygroundMetadata
        requestId=""
        tenantId=""
        policyMode=""
        policyOutcome=""
        response={{ routeTarget: "", routeReason: "", routeTier: "", provider: "", cacheHit: null, fallbackUsed: null }}
      />,
    );

    for (const label of RESPONSE_FACTS) {
      expect(screen.getByRole("group", { name: label }), label).toHaveTextContent("—");
    }
    for (const label of ["Request ID", "Tenant", "Modo de política", "Resultado de política"]) {
      expect(screen.getByRole("group", { name: label }), label).toHaveTextContent("—");
    }
  });

  it("keeps sí and no for a cache or fallback header the gateway did send", () => {
    renderWithProviders(
      <PlaygroundMetadata
        requestId="req-1"
        tenantId="default"
        policyMode="auto"
        policyOutcome="default"
        response={{ ...response, cacheHit: false, fallbackUsed: true }}
      />,
    );

    expect(screen.getByRole("group", { name: "Caché" })).toHaveTextContent("no");
    expect(screen.getByRole("group", { name: "Fallback" })).toHaveTextContent("sí");
  });
});
