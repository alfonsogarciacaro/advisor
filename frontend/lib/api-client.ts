export interface NewsItem {
    title: string;
    summary: string;
    url: string;
    source: string;
    time_published: string;
}

// Agent types
export interface AgentRunResponse {
    run_id: string;
    status: string;
}

export interface AgentLog {
    run_id: string;
    step: string;
    status: string;
    details?: any;
    timestamp: string;
}

export interface AgentRunStatus {
    agent: string;
    status: string;
    input: any;
    result?: any;
    error?: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
}

// News API
export async function getLatestNews(): Promise<NewsItem[]> {
    try {
        const response = await fetch('/api/news');
        if (!response.ok) {
            throw new Error('Failed to fetch news');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching news:', error);
        return [];
    }
}

// Agent API
export async function runAgent(agentName: string, input: any): Promise<AgentRunResponse> {
    const response = await fetch(`/api/agents/${agentName}/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to start agent');
    }

    return response.json();
}

export async function getRunStatus(runId: string): Promise<AgentRunStatus> {
    const response = await fetch(`/api/agents/runs/${runId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get run status');
    }

    return response.json();
}

export async function getRunLogs(runId: string): Promise<AgentLog[]> {
    const response = await fetch(`/api/agents/runs/${runId}/logs`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get run logs');
    }

    return response.json();
}

// Portfolio API
export interface OptimizationResult {
    job_id: string;
    status: string;
    initial_amount: number;
    currency: string;
    optimal_portfolio?: Array<{
        ticker: string;
        weight: number;
        amount: number;
        expected_return: number;
        shares: number;
        price: number;
    }>;
    efficient_frontier?: Array<{
        annual_volatility: number;
        annual_return: number;
        sharpe_ratio: number;
    }>;
    metrics?: {
        net_investment: number;
        total_commission: number;
        expected_annual_return: number;
        annual_volatility: number;
        sharpe_ratio: number;
    };
    error?: string;
}

export async function optimizePortfolio(amount: number, currency: string): Promise<{ job_id: string; status: string }> {
    const response = await fetch('/api/portfolio/optimize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount, currency }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to start optimization');
    }

    return response.json();
}

export async function getOptimizationStatus(jobId: string): Promise<OptimizationResult> {
    const response = await fetch(`/api/portfolio/${jobId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get optimization status');
    }

    return response.json();
}
