import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { useAdminSession } from "@/lib/admin-session-provider";
import { renderWithProviders } from "@/test/render";

function SessionConsumer() {
  const session = useAdminSession();

  return (
    <div>
      <span>{session.adminKey ?? "empty"}</span>
      <button type="button" onClick={() => session.signIn("fresh-admin-key")}>
        sign in
      </button>
      <button type="button" onClick={() => session.clearSession()}>
        clear session
      </button>
    </div>
  );
}

describe("AdminSessionProvider", () => {
  it("stores the admin key in memory only after successful validation", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok" }),
      }),
    );

    renderWithProviders(<SessionConsumer />);

    expect(screen.getByText("empty")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "sign in" }));

    await waitFor(() => expect(screen.getByText("fresh-admin-key")).toBeInTheDocument());
  });

  describe("a failed sign in", () => {
    function FailureConsumer() {
      const session = useAdminSession();
      const [message, setMessage] = useState("none");

      return (
        <div>
          <span data-testid="key">{session.adminKey ?? "empty"}</span>
          <span data-testid="failure">{message}</span>
          <button type="button" onClick={() => session.signIn("bad-admin-key").catch((error: Error) => setMessage(error.message))}>
            sign in
          </button>
        </div>
      );
    }

    it.each([
      [
        "a wrong key",
        () => Promise.resolve(new Response(JSON.stringify({ detail: "Missing or invalid admin API key." }), { status: 401 })),
        "La clave de admin no es válida.",
      ],
      [
        "an unreachable gateway",
        () => Promise.resolve(new Response(JSON.stringify({ detail: "gateway_unreachable" }), { status: 503 })),
        "No se pudo conectar con el gateway.",
      ],
      ["a console server that does not answer", () => Promise.reject(new TypeError("Failed to fetch")), "No se pudo conectar con el gateway."],
      [
        "a gateway error",
        () => Promise.resolve(new Response("<html></html>", { status: 500 })),
        "El gateway devolvió un error (500).",
      ],
    ])("rejects with the Spanish message for %s and stores no key", async (_case, answer, message) => {
      vi.stubGlobal("fetch", vi.fn().mockImplementation(answer));

      renderWithProviders(<FailureConsumer />);
      const keyBefore = screen.getByTestId("key").textContent;
      await userEvent.click(screen.getByRole("button", { name: "sign in" }));

      await waitFor(() => expect(screen.getByTestId("failure")).toHaveTextContent(message));
      expect(screen.getByTestId("key").textContent).toBe(keyBefore);
      expect(screen.getByTestId("key")).not.toHaveTextContent("bad-admin-key");
    });
  });

  it("clears the in-memory session without local storage support", async () => {
    renderWithProviders(<SessionConsumer />, { adminKey: "existing-admin-key" });

    expect(screen.queryByText("localStorage")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "clear session" }));

    await waitFor(() => expect(screen.getByText("empty")).toBeInTheDocument());
  });
});
