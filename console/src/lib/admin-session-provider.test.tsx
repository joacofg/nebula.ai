import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
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

  it("clears the in-memory session without local storage support", async () => {
    renderWithProviders(<SessionConsumer />, { adminKey: "existing-admin-key" });

    expect(screen.queryByText("localStorage")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "clear session" }));

    await waitFor(() => expect(screen.getByText("empty")).toBeInTheDocument());
  });
});
