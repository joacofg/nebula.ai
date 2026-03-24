import { defineConfig, devices } from "@playwright/test";

const webServerCommand =
  "npm run build && cp -R .next/static .next/standalone/.next/static && PORT=3001 HOSTNAME=127.0.0.1 node .next/standalone/server.js";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3001",
    trace: "retain-on-failure",
  },
  webServer: {
    command: webServerCommand,
    port: 3001,
    reuseExistingServer: false,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
