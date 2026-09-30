import { describe, expect, it } from "vitest";

import { plural, reasonLabel, statusLabel } from "@/components/system/labels";

describe("labels", () => {
  it("maps known codes and passes unknown ones through", () => {
    expect(reasonLabel("learned_router")).toBe("router aprendido");
    expect(reasonLabel("something_new")).toBe("something_new");
    expect(reasonLabel(null)).toBe("—");
    expect(statusLabel("provider_error")).toBe("error del proveedor");
    expect(statusLabel("fallback_completed")).toBe("completado con fallback");
  });

  it("pluralizes", () => {
    expect(plural(1, "recomendación", "recomendaciones")).toBe("1 recomendación");
    expect(plural(3, "recomendación", "recomendaciones")).toBe("3 recomendaciones");
  });
});
