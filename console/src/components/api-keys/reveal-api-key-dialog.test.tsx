import { fireEvent, screen, waitFor } from "@testing-library/react";
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

    expect(screen.getByText("No se vuelve a mostrar.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Copiar" }));

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("nbk_secret");
    });
  });

  it("has exactly one Cerrar button, and it closes the dialog", async () => {
    const onClose = vi.fn();
    renderWithProviders(<RevealApiKeyDialog apiKey="nbk_secret" open onClose={onClose} />);

    const close = screen.getAllByRole("button", { name: "Cerrar" });
    expect(close).toHaveLength(1);

    await userEvent.click(close[0]);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("stays open on a click outside, since the key is shown only once", async () => {
    const onClose = vi.fn();
    renderWithProviders(<RevealApiKeyDialog apiKey="nbk_secret" open onClose={onClose} />);

    // Radix attaches its outside-pointer listener on the next tick.
    await new Promise((resolve) => setTimeout(resolve, 0));
    fireEvent.pointerDown(document.body);

    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByText("nbk_secret")).toBeInTheDocument();
  });
});
