import { onlineManager, useMutation, useQuery } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { QueryProvider } from "@/lib/query-provider";

afterEach(() => {
  onlineManager.setOnline(true);
});

function ReadsGateway({ read }: { read: () => Promise<string> }) {
  const query = useQuery({ queryKey: ["gateway"], queryFn: read });
  return <p>{query.data ?? "waiting"}</p>;
}

function WritesGateway({ write }: { write: () => Promise<string> }) {
  const mutation = useMutation({ mutationFn: write });
  return (
    <>
      <button type="button" onClick={() => mutation.mutate()}>
        Guardar
      </button>
      <p>{mutation.data ?? "idle"}</p>
    </>
  );
}

// The console talks to a gateway on localhost through its own proxies: whether the browser
// reports internet access says nothing about it, and a laptop without wifi must still load.
describe("query provider", () => {
  it("runs a query while the browser reports no network", async () => {
    onlineManager.setOnline(false);
    const read = vi.fn().mockResolvedValue("tenants arrived");

    render(
      <QueryProvider>
        <ReadsGateway read={read} />
      </QueryProvider>,
    );

    expect(await screen.findByText("tenants arrived")).toBeInTheDocument();
    expect(read).toHaveBeenCalledTimes(1);
  });

  it("runs a mutation while the browser reports no network", async () => {
    onlineManager.setOnline(false);
    const write = vi.fn().mockResolvedValue("policy saved");
    const user = userEvent.setup();

    render(
      <QueryProvider>
        <WritesGateway write={write} />
      </QueryProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText("policy saved")).toBeInTheDocument();
    expect(write).toHaveBeenCalledTimes(1);
  });
});
