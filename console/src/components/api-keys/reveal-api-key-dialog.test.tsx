import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RevealApiKeyDialog } from "@/components/api-keys/reveal-api-key-dialog";
import { renderWithProviders } from "@/test/render";

describe("reveal-api-key-dialog", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  it("renders the reveal-once warning and copies the raw key", async () => {
    renderWithProviders(<RevealApiKeyDialog apiKey="nbk_secret" open onClose={vi.fn()} />);

    expect(screen.getByText("This key will not be shown again.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Copy key" }));

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("nbk_secret");
    });
  });
});
