import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();
const push = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/policy",
  useRouter: () => ({ replace, push }),
}));

import ConsoleLayout from "@/app/(console)/layout";
import { AdminLoginForm } from "@/components/auth/admin-login-form";
import { AdminSessionProvider } from "@/lib/admin-session-provider";
import { useSelectedTenant } from "@/lib/selected-tenant";

/** The layout alone: it must bring the selected-tenant provider itself. */
function renderLayout(children: ReactNode, adminKey: string | null) {
  return render(
    <AdminSessionProvider initialAdminKey={adminKey}>
      <ConsoleLayout>{children}</ConsoleLayout>
    </AdminSessionProvider>,
  );
}

function reasonOf(url: string) {
  return new URL(url, "http://console.test").searchParams.get("reason");
}

beforeEach(() => {
  replace.mockReset();
  push.mockReset();
});

describe("console layout", () => {
  it("sends a visitor without a session to the login as an expired session", () => {
    renderLayout("contenido", null);

    expect(replace).toHaveBeenCalledTimes(1);
    expect(replace).toHaveBeenCalledWith("/?reason=session-expired");
    expect(screen.queryByText("contenido")).not.toBeInTheDocument();
  });

  it("signs out once, to the login with Sesión cerrada., and not as an expired session", async () => {
    const user = userEvent.setup();
    renderLayout("contenido", "admin-key");
    expect(screen.getByText("contenido")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(replace).toHaveBeenCalledTimes(1);
    expect(replace).toHaveBeenCalledWith("/?reason=signed_out");
    expect(push).not.toHaveBeenCalled();
    expect(screen.queryByText("contenido")).not.toBeInTheDocument();

    // And that is what the login shows for it.
    const { unmount } = render(
      <AdminSessionProvider>
        <AdminLoginForm reason={reasonOf(replace.mock.calls[0][0])} />
      </AdminSessionProvider>,
    );
    expect(screen.getByText("Sesión cerrada.")).toBeInTheDocument();
    expect(screen.queryByText(/La sesión se cerró/)).not.toBeInTheDocument();
    unmount();
  });

  it("gives its pages the selected tenant", () => {
    function Page() {
      const { tenantId } = useSelectedTenant([
        {
          id: "tenant-a",
          name: "Tenant A",
          description: null,
          metadata: {},
          active: true,
          created_at: "2026-03-16T12:00:00Z",
          updated_at: "2026-03-16T12:00:00Z",
        },
      ]);
      return <p>{`tenant: ${tenantId}`}</p>;
    }
    renderLayout(<Page />, "admin-key");
    expect(screen.getByText("tenant: tenant-a")).toBeInTheDocument();
  });
});
