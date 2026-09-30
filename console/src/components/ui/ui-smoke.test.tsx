import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

describe("ui primitives", () => {
  it("opens a dialog, keeps focus inside and closes with Escape", async () => {
    const user = userEvent.setup();
    render(
      <>
        <button type="button">Fuera</button>
        <Dialog>
          <DialogTrigger>Abrir</DialogTrigger>
          <DialogContent>
            <DialogTitle>Título</DialogTitle>
            <DialogDescription>Descripción</DialogDescription>
            <button type="button">Dentro</button>
          </DialogContent>
        </Dialog>
      </>,
    );

    await user.click(screen.getByText("Abrir"));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();

    for (let i = 0; i < 4; i += 1) {
      await user.tab();
      expect(dialog).toContainElement(document.activeElement as HTMLElement);
    }

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
