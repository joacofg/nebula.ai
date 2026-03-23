import { expect, test } from "@playwright/test";

test("trust-boundary page is reachable without authentication", async ({
  page,
}) => {
  await page.goto("/trust-boundary");

  await expect(
    page.getByRole("heading", { name: "Hosted trust boundary" })
  ).toBeVisible();

  await expect(
    page.getByText("Hosted freshness is not local runtime authority.")
  ).toBeVisible();

  await expect(
    page.getByText(
      "Nebula's hosted control plane is not in the request-serving path."
    )
  ).toBeVisible();

  await expect(page.getByText("Metadata-only by default")).toBeVisible();
  await expect(page.getByText("Excluded by default")).toBeVisible();
});

test("login page links to trust-boundary before auth", async ({ page }) => {
  await page.goto("/");

  const link = page.getByRole("link", {
    name: "Review hosted trust boundary",
  });
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute("href", "/trust-boundary");

  await link.click();
  await expect(page).toHaveURL(/\/trust-boundary$/);

  await expect(
    page.getByText("Hosted freshness is not local runtime authority.")
  ).toBeVisible();

  await expect(
    page.getByText(
      "Nebula's hosted control plane is not in the request-serving path."
    )
  ).toBeVisible();
});
