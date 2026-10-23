import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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

  describe("copy confirmation", () => {
    afterEach(() => {
      vi.useRealTimers();
    });

    // fireEvent, not userEvent: user-event waits on timers, which the fake clock holds back.
    async function copyKey() {
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Copiar" }));
      });
    }

    it("goes back from Copiada to Copiar after 2 s", async () => {
      vi.useFakeTimers();
      renderWithProviders(<RevealApiKeyDialog apiKey="nbk_secret" open onClose={vi.fn()} />);

      await copyKey();
      expect(screen.getByRole("button", { name: "Copiada" })).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(1999);
      });
      expect(screen.getByRole("button", { name: "Copiada" })).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(1);
      });
      expect(screen.getByRole("button", { name: "Copiar" })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Copiada" })).not.toBeInTheDocument();
    });

    it("shows Copiar again when the dialog is reopened with another key", async () => {
      vi.useFakeTimers();
      const { rerender } = renderWithProviders(<RevealApiKeyDialog apiKey="nbk_first" open onClose={vi.fn()} />);

      await copyKey();
      expect(screen.getByRole("button", { name: "Copiada" })).toBeInTheDocument();

      rerender(<RevealApiKeyDialog apiKey={null} open={false} onClose={vi.fn()} />);
      rerender(<RevealApiKeyDialog apiKey="nbk_second" open onClose={vi.fn()} />);

      expect(screen.getByText("nbk_second")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Copiar" })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Copiada" })).not.toBeInTheDocument();
    });

    it("does not cut a later copy short with the timer of an earlier one", async () => {
      vi.useFakeTimers();
      const { rerender } = renderWithProviders(<RevealApiKeyDialog apiKey="nbk_first" open onClose={vi.fn()} />);

      await copyKey();
      act(() => {
        vi.advanceTimersByTime(1500);
      });
      rerender(<RevealApiKeyDialog apiKey={null} open={false} onClose={vi.fn()} />);
      rerender(<RevealApiKeyDialog apiKey="nbk_second" open onClose={vi.fn()} />);

      await copyKey();
      act(() => {
        vi.advanceTimersByTime(1000);
      });
      expect(screen.getByRole("button", { name: "Copiada" })).toBeInTheDocument();
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
