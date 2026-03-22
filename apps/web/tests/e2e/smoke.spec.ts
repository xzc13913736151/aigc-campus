import { expect, test } from "@playwright/test";


test("home page renders the hero content", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "把校园里的找对象、找队友和经验交流收进同一个协作平台。" })).toBeVisible();
});
