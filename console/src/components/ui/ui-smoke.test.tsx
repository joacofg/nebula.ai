import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

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

  it("closes a dialog with a button named Cerrar", async () => {
    const user = userEvent.setup();
    render(
      <Dialog>
        <DialogTrigger>Abrir</DialogTrigger>
        <DialogContent>
          <DialogTitle>Título</DialogTitle>
          <DialogDescription>Descripción</DialogDescription>
        </DialogContent>
      </Dialog>,
    );

    await user.click(screen.getByText("Abrir"));
    expect(screen.queryByRole("button", { name: "Close" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("names the dialog footer's close button Cerrar", async () => {
    const user = userEvent.setup();
    render(
      <Dialog>
        <DialogTrigger>Abrir</DialogTrigger>
        <DialogContent showCloseButton={false}>
          <DialogTitle>Título</DialogTitle>
          <DialogDescription>Descripción</DialogDescription>
          <DialogFooter showCloseButton />
        </DialogContent>
      </Dialog>,
    );

    await user.click(screen.getByText("Abrir"));
    expect(screen.queryByRole("button", { name: "Close" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes a sheet with a button named Cerrar", async () => {
    const user = userEvent.setup();
    render(
      <Sheet>
        <SheetTrigger>Abrir</SheetTrigger>
        <SheetContent>
          <SheetTitle>Título</SheetTitle>
          <SheetDescription>Descripción</SheetDescription>
        </SheetContent>
      </Sheet>,
    );

    await user.click(screen.getByText("Abrir"));
    expect(screen.queryByRole("button", { name: "Close" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
