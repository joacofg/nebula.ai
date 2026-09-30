import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundResponse } from "@/components/playground/playground-response";
import { renderWithProviders } from "@/test/render";

describe("playground-response", () => {
  it("renders the assistant content", () => {
    renderWithProviders(<PlaygroundResponse content="Nebula routed this prompt." />);

    expect(screen.getByText("Nebula routed this prompt.")).toBeInTheDocument();
  });
});

describe("PlaygroundResponse long content", () => {
  it("wraps a 2000-character unbroken answer instead of overflowing", () => {
    const long = "x".repeat(2000);
    renderWithProviders(<PlaygroundResponse content={long} />);
    expect(screen.getByText(long).className).toContain("[overflow-wrap:anywhere]");
  });
});
