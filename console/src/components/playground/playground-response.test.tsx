import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundResponse } from "@/components/playground/playground-response";
import { renderWithProviders } from "@/test/render";

describe("playground-response", () => {
  it("renders the assistant content and request id", () => {
    renderWithProviders(<PlaygroundResponse content="Nebula routed this prompt." requestId="req-play-001" />);

    expect(screen.getByText("Nebula routed this prompt.")).toBeInTheDocument();
    expect(screen.getByText("Request ID")).toBeInTheDocument();
    expect(screen.getByText("req-play-001")).toBeInTheDocument();
  });
});
