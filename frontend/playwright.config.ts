import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : 2,
    reporter: 'line',
    timeout: process.env.CI ? 60000 : 30000,
    expect: {
        timeout: process.env.CI ? 10000 : 5000,
    },
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
        reuseExistingServer: false,
        stderr: 'pipe',
        timeout: 120 * 1000,
        wait: {
            stdout: /ready/i
        },
        env: {
            NEXT_PUBLIC_API_URL: 'http://localhost:8001',
        },
    },
});
