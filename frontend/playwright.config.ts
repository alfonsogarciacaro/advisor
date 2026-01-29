import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : 2,
    reporter: 'html',
    use: {
        baseURL: 'http://localhost:3001',
        trace: 'on-first-retry',
    },
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
    webServer: {
        command: 'npm run dev -- --port 3001',
        url: 'http://localhost:3001',
        reuseExistingServer: true,
        env: {
            NEXT_PUBLIC_API_URL: 'http://localhost:8001',
            NEXT_PUBLIC_FAST_OPTIMIZE: 'true',
        },
    },
});
