import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ModelAllowlistInput } from "@/components/policy/model-allowlist-input";
import { renderWithProviders } from "@/test/render";

describe("model-allowlist-input", () => {
  it("adds and removes manual model entries", async () => {
    const onChange = vi.fn();
    renderWithProviders(
      <ModelAllowlistInput
        knownModels={["openai/gpt-4o-mini"]}
        value={["openai/gpt-4o-mini"]}
        onChange={onChange}
      />,
    );

    await userEvent.type(screen.getByPlaceholderText("Add model"), "openai/gpt-4.1-mini");
    await userEvent.click(screen.getByRole("button", { name: "Add model" }));

    expect(onChange).toHaveBeenCalledWith(["openai/gpt-4o-mini", "openai/gpt-4.1-mini"]);
  });
});
