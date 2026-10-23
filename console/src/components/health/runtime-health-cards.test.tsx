import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RuntimeHealthCards } from "@/components/health/runtime-health-cards";
import { renderWithProviders } from "@/test/render";

/** One dependency's card, found by the name in its heading. */
function card(name: string) {
  const article = screen.getByRole("heading", { name }).closest("article");
  expect(article).not.toBeNull();
  return within(article as HTMLElement);
}

/** The status written next to a card's name. */
function statusOf(name: string) {
  return screen.getByRole("heading", { name }).nextElementSibling;
}

describe("runtime-health-cards", () => {
  it("renders ready, degraded, and not_ready cards with their status in Spanish", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{
          gateway: {
            status: "ready",
            required: true,
            detail: "FastAPI application is running.",
          },
          semantic_cache: {
            status: "degraded",
            required: false,
            detail: "Qdrant unavailable.",
          },
          premium_provider: {
            status: "not_ready",
            required: false,
            detail: "Premium provider offline.",
          },
        }}
      />,
    );

    expect(screen.getByText("gateway")).toBeInTheDocument();
    expect(statusOf("gateway")).toHaveTextContent("Listo");
    expect(statusOf("semantic_cache")).toHaveTextContent("Degradado");
    expect(statusOf("premium_provider")).toHaveTextContent("No listo");
    expect(screen.queryByText("not ready")).not.toBeInTheDocument();
    expect(screen.queryByText("degraded")).not.toBeInTheDocument();
    expect(
      screen.getByText("Una dependencia opcional degradada no bloquea el gateway."),
    ).toBeInTheDocument();
    // The gateway's own diagnosis stays as written.
    expect(screen.getByText("FastAPI application is running.")).toBeInTheDocument();
  });

  it("keeps a status it does not know as the gateway sent it", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{ postgres: { status: "healthy", required: true, detail: "ready" } }}
      />,
    );

    expect(statusOf("postgres")).toHaveTextContent("healthy");
  });

  it("renders resilience metadata for critical, optional, and recovering dependencies in Spanish", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{
          governance_store: {
            status: "not_ready",
            required: true,
            detail: "Governance queries failed.",
            dependency_class: "serving_critical",
            lifecycle_state: "not_ready",
            serving_effect: "fail_closed",
            reason_code: "governance_query_failed",
            recovering: false,
            enabled: true,
            last_failure_at: "2026-04-12T01:00:00Z",
          },
          semantic_cache: {
            status: "degraded",
            required: false,
            detail: "Semantic cache unavailable; requests continue without cache hits.",
            dependency_class: "serving_optional",
            lifecycle_state: "degraded",
            serving_effect: "continuity_limited",
            reason_code: "semantic_cache_unavailable",
            recovering: false,
            enabled: true,
          },
          premium_provider: {
            status: "recovering",
            required: false,
            detail: "Premium provider connectivity restored; recovery checks are still running.",
            dependency_class: "serving_optional",
            lifecycle_state: "recovering",
            serving_effect: "continuity_limited",
            reason_code: "premium_provider_recovered",
            recovering: true,
            last_failure_at: "2026-04-12T00:55:00Z",
            last_recovery_at: "2026-04-12T01:03:00Z",
          },
        }}
      />,
    );

    const governance = card("governance_store");
    expect(governance.getByRole("group", { name: "Clase" })).toHaveTextContent("crítica para servir");
    expect(governance.getByRole("group", { name: "Ciclo de vida" })).toHaveTextContent("No listo");
    expect(governance.getByRole("group", { name: "Efecto" })).toHaveTextContent("bloquea pedidos");
    expect(governance.getByRole("group", { name: "Código" })).toHaveTextContent("falló la consulta al almacén");
    expect(governance.getByRole("group", { name: "Activada" })).toHaveTextContent("sí");
    expect(governance.getByRole("group", { name: "Recuperándose" })).toHaveTextContent("no");
    expect(governance.getByText("2026-04-12T01:00:00Z")).toBeInTheDocument();
    expect(governance.queryByRole("group", { name: "Última recuperación" })).not.toBeInTheDocument();

    const cache = card("semantic_cache");
    expect(cache.getByRole("group", { name: "Clase" })).toHaveTextContent("opcional");
    expect(cache.getByRole("group", { name: "Ciclo de vida" })).toHaveTextContent("Degradado");
    expect(cache.getByRole("group", { name: "Efecto" })).toHaveTextContent("continuidad limitada");
    expect(cache.getByRole("group", { name: "Código" })).toHaveTextContent("caché no disponible");

    const provider = card("premium_provider");
    expect(statusOf("premium_provider")).toHaveTextContent("Recuperándose");
    expect(provider.getByRole("group", { name: "Ciclo de vida" })).toHaveTextContent("Recuperándose");
    expect(provider.getByRole("group", { name: "Recuperándose" })).toHaveTextContent("sí");
    expect(provider.getByText("2026-04-12T01:03:00Z")).toBeInTheDocument();
    // A reason the console does not know is shown as the gateway sent it, never a blank.
    expect(provider.getByRole("group", { name: "Código" })).toHaveTextContent("premium_provider_recovered");

    for (const english of ["serving critical", "fail closed", "governance query failed", "not ready"]) {
      expect(screen.queryByText(english)).not.toBeInTheDocument();
    }
  });

  it("keeps the gateway's code available as the title of its Spanish label", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{
          local_ollama: {
            status: "ready",
            required: false,
            detail: "Local Ollama endpoint is reachable.",
            dependency_class: "serving_optional",
            serving_effect: "continuity_limited",
            reason_code: "local_ollama_ready",
          },
        }}
      />,
    );

    expect(card("local_ollama").getByText("Ollama alcanzable")).toHaveAttribute("title", "local_ollama_ready");
    expect(card("local_ollama").getByText("opcional")).toHaveAttribute("title", "serving_optional");
    expect(card("local_ollama").getByText("continuidad limitada")).toHaveAttribute("title", "continuity_limited");
  });

  it("renders retention lifecycle runtime metrics without introducing a dedicated dashboard", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{
          retention_lifecycle: {
            status: "degraded",
            required: false,
            detail: "Retention lifecycle cleanup failed on its last attempt.",
            last_status: "failed",
            last_run_at: "2026-04-12T01:02:03Z",
            last_attempted_run_at: "2026-04-12T01:05:00Z",
            last_deleted_count: 4,
            last_eligible_count: 4,
            last_error: "cleanup query timed out",
          },
        }}
      />,
    );

    expect(screen.getByText("retention_lifecycle")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Último estado" })).toHaveTextContent("fallida");
    expect(screen.queryByText("failed")).not.toBeInTheDocument();
    expect(screen.getByText("Filas borradas")).toBeInTheDocument();
    expect(screen.getAllByText("4")).toHaveLength(2);
    expect(screen.getByText("Último error")).toBeInTheDocument();
    expect(screen.getByText("cleanup query timed out")).toBeInTheDocument();
    expect(screen.queryByText(/retention dashboard/i)).not.toBeInTheDocument();
  });

  it("says so when the gateway reports no dependencies", () => {
    renderWithProviders(<RuntimeHealthCards dependencies={{}} isLoading={false} />);
    expect(screen.getByText("El gateway no informó dependencias.")).toBeInTheDocument();
  });
});
