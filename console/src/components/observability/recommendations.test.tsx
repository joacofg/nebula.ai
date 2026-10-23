import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Recommendations } from "@/components/observability/recommendations";
import type { RecommendationBundle, RecommendationCard } from "@/lib/admin-api";

function bundle(recommendations: RecommendationCard[]) {
  return { window_requests_evaluated: 56, recommendations } as unknown as RecommendationBundle;
}

const tuneCache = {
  code: "tune_semantic_cache_threshold",
  title: "Review semantic cache tuning",
  category: "cache",
  priority: 2,
  summary: "The cache is enabled but recent hit rate is low for the observed request window.",
  recommended_action: "Review the maximum entry age first.",
  evidence: [
    { label: "cache_hit_rate", value: "16%" },
    { label: "similarity_threshold", value: "0.90" },
  ],
} as unknown as RecommendationCard;

describe("Recommendations", () => {
  it("renders the gateway's known recommendations in Spanish", () => {
    render(<Recommendations bundle={bundle([tuneCache])} />);

    expect(screen.getByRole("heading", { name: "Revisar el ajuste de la caché semántica" })).toBeInTheDocument();
    expect(screen.queryByText(/Review semantic cache tuning/)).not.toBeInTheDocument();
    expect(screen.queryByText(/The cache is enabled/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Review the maximum entry age/)).not.toBeInTheDocument();
    // The gateway writes "16%"; the console writes numbers like the thesis ("31 %").
    expect(screen.getByRole("group", { name: "Tasa de aciertos" })).toHaveTextContent("16 %");
    expect(screen.getByRole("group", { name: "Umbral de similitud" })).toHaveTextContent("0.90");
  });

  it("points the low hit rate card to entry age first and gives the cost of a lower threshold", () => {
    render(<Recommendations bundle={bundle([tuneCache])} />);

    expect(
      screen.getByText(
        "Revisar primero la antigüedad máxima de las entradas. Bajar el umbral de similitud da más " +
          "aciertos, pero con una precisión que la medición encontró por debajo de 0.95.",
      ),
    ).toBeInTheDocument();
  });

  it("words the cache's runtime status on the restore card in Spanish, keeping a status it does not know", () => {
    const restore = {
      code: "restore_semantic_cache_runtime",
      title: "Restore semantic cache runtime",
      category: "cache",
      priority: 1,
      summary: "Semantic cache is unavailable.",
      recommended_action: "Recover the cache dependency.",
      evidence: [
        { label: "cache_runtime_status", value: "degraded" },
        { label: "cache_runtime_detail", value: "Qdrant is unreachable." },
      ],
    } as unknown as RecommendationCard;
    const { unmount } = render(<Recommendations bundle={bundle([restore])} />);

    expect(screen.getByRole("heading", { name: "Restaurar la caché semántica" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Estado de la caché" })).toHaveTextContent("Degradado");
    expect(screen.getByRole("group", { name: "Estado de la caché" })).not.toHaveTextContent("degraded");
    expect(screen.getByRole("group", { name: "Detalle" })).toHaveTextContent("Qdrant is unreachable.");
    unmount();

    const unknownStatus = { ...restore, evidence: [{ label: "cache_runtime_status", value: "melting" }] };
    render(<Recommendations bundle={bundle([unknownStatus as RecommendationCard])} />);
    expect(screen.getByRole("group", { name: "Estado de la caché" })).toHaveTextContent("melting");
  });

  it("words the default routing mode on the pressure card in Spanish, keeping a mode it does not know", () => {
    const pressure = {
      code: "review_premium_routing_pressure",
      title: "Review premium routing pressure",
      category: "policy",
      priority: 2,
      summary: "Premium share is high.",
      recommended_action: "Review routing.",
      evidence: [{ label: "routing_mode_default", value: "auto" }],
    } as unknown as RecommendationCard;
    const { unmount } = render(<Recommendations bundle={bundle([pressure])} />);

    expect(screen.getByRole("group", { name: "Modo de ruteo" })).toHaveTextContent("Automático");
    expect(screen.getByRole("group", { name: "Modo de ruteo" })).not.toHaveTextContent("auto");
    unmount();

    const unknownMode = { ...pressure, evidence: [{ label: "routing_mode_default", value: "round_robin" }] };
    render(<Recommendations bundle={bundle([unknownMode as RecommendationCard])} />);
    expect(screen.getByRole("group", { name: "Modo de ruteo" })).toHaveTextContent("round_robin");
  });

  it("words the category in Spanish and keeps one it does not know as sent", () => {
    const { unmount } = render(<Recommendations bundle={bundle([tuneCache])} />);
    expect(screen.getByText(/^caché · prioridad 2$/)).toBeInTheDocument();
    unmount();

    render(<Recommendations bundle={bundle([{ ...tuneCache, category: "billing" } as unknown as RecommendationCard])} />);
    expect(screen.getByText(/^billing · prioridad 2$/)).toBeInTheDocument();
  });

  it("falls back to the gateway's text for a code it does not know", () => {
    const unknown = { ...tuneCache, code: "new_code", title: "Something new", evidence: [{ label: "raw_label", value: "1" }] };
    render(<Recommendations bundle={bundle([unknown as RecommendationCard])} />);

    expect(screen.getByRole("heading", { name: "Something new" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "raw_label" })).toHaveTextContent("1");
  });
});
