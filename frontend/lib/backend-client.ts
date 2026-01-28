const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

/**
 * Backend client for Next.js API routes to communicate with Python backend.
 * Centralizes all backend HTTP calls.
 */

// News
export async function fetchNewsFromBackend() {
    const response = await fetch(`${BACKEND_URL}/api/news`);
    if (!response.ok) {
        throw new Error(`Backend news fetch failed: ${response.status}`);
    }
    return response.json();
}

// Agents
export async function createAgentRun(agentName: string, input: any) {
    const response = await fetch(`${BACKEND_URL}/api/agents/${agentName}/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend agent run failed: ${errorText}`);
    }

    return response.json();
}

export async function fetchAgentRunStatus(runId: string) {
    const response = await fetch(`${BACKEND_URL}/api/agents/runs/${runId}`);
    if (!response.ok) {
        throw new Error(`Backend run status fetch failed: ${response.status}`);
    }
    return response.json();
}

export async function fetchAgentRunLogs(runId: string) {
    const response = await fetch(`${BACKEND_URL}/api/agents/runs/${runId}/logs`);
    if (!response.ok) {
        throw new Error(`Backend run logs fetch failed: ${response.status}`);
    }
    return response.json();
}

// Portfolio
export async function startOptimization(amount: number, currency: string) {
    const response = await fetch(`${BACKEND_URL}/api/portfolio/optimize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount, currency }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend optimization start failed: ${errorText}`);
    }

    return response.json();
}

export async function fetchOptimizationStatus(jobId: string) {
    const response = await fetch(`${BACKEND_URL}/api/portfolio/optimize/${jobId}`);
    if (!response.ok) {
        throw new Error(`Backend optimization status fetch failed: ${response.status}`);
    }
    return response.json();
}
