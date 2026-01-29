const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
        const response = await fetch(`${API_BASE_URL}/api/news`);
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
    const response = await fetch(`${API_BASE_URL}/api/agents/${agentName}/run`, {
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
    const response = await fetch(`${API_BASE_URL}/api/agents/runs/${runId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get run status');
    }

    return response.json();
}

export async function getRunLogs(runId: string): Promise<AgentLog[]> {
    const response = await fetch(`${API_BASE_URL}/api/agents/runs/${runId}/logs`);

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
        expected_return?: number | null;
        shares: number;
        price: number;
        annual_expense_ratio?: number | null;
        contribution_to_risk?: number | null;
    }>;
    efficient_frontier?: Array<{
        annual_volatility?: number | null;
        annual_return?: number | null;
        sharpe_ratio?: number | null;
    }>;
    metrics?: {
        net_investment: number;
        total_commission: number;
        annual_custody_cost?: number;
        expected_annual_return?: number | null;
        annual_volatility?: number | null;
        sharpe_ratio?: number | null;
        [key: string]: number | string | null | undefined;
    };
    scenarios?: Array<{
        name: string;
        probability: number;
        description: string;
        expected_portfolio_value?: number | null;
        expected_return?: number | null;
        annual_volatility?: number | null;
        trajectory?: Array<{ date: string; value: number }>;
    }>;
    llm_report?: string;
    error?: string;
}

export async function optimizePortfolio(amount: number, currency: string, fast: boolean = false): Promise<{ job_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/portfolio/optimize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount, currency, fast }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to start optimization');
    }

    return response.json();
}

export async function getOptimizationStatus(jobId: string): Promise<OptimizationResult> {
    const response = await fetch(`${API_BASE_URL}/api/portfolio/optimize/${jobId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get optimization status');
    }

    return response.json();
}

export async function clearOptimizationCache(jobId?: string): Promise<{ message: string; jobs_cleared: number }> {
    const url = jobId ? `${API_BASE_URL}/api/portfolio/optimize/cache?job_id=${jobId}` : `${API_BASE_URL}/api/portfolio/optimize/cache`;
    const response = await fetch(url, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to clear cache');
    }

    return response.json();
}

// ==================== Plan Management API ====================

export type RiskProfile = 'very_conservative' | 'conservative' | 'moderate' | 'growth' | 'aggressive';

export type TaxAccountType = 'taxable' | 'nisa_general' | 'nisa_growth' | 'ideco' | 'dc_pension' | 'other';

export interface TaxAccount {
    account_type: TaxAccountType;
    name: string;
    annual_limit?: number | null;
    current_balance: number;
    available_space: number;
    withdrawal_rules?: string | null;
    dividend_tax_rate: number;
    capital_gains_tax_rate: number;
    contribution_deductible: boolean;
}

export interface RecurringInvestment {
    enabled: boolean;
    frequency: 'weekly' | 'biweekly' | 'monthly' | 'quarterly';
    amount: number;
    currency: string;
    dividend_reinvestment: boolean;
    next_investment_date?: string | null;
}

export interface ResearchRun {
    run_id: string;
    timestamp: string;
    query: string;
    result_summary: string;
    scenarios?: any[] | null;
    refined_forecasts?: any | null;
    follow_up_suggestions?: string[] | null;
}

export interface Plan {
    plan_id: string;
    user_id: string;
    name: string;
    description?: string | null;
    created_at: string;
    updated_at: string;
    risk_preference: RiskProfile;
    initial_portfolio?: any[] | null;
    initial_amount?: number | null;
    optimization_result?: OptimizationResult | null;
    recurring_investment?: RecurringInvestment | null;
    tax_accounts?: TaxAccount[] | null;
    research_history: ResearchRun[];
    notes?: string | null;
}

export interface PlanCreateRequest {
    name: string;
    description?: string;
    risk_preference?: RiskProfile;
    initial_portfolio?: any[];
    initial_amount?: number;
    currency?: string;
    user_id?: string;
}

export interface PlanUpdateRequest {
    name?: string;
    description?: string;
    notes?: string;
    risk_preference?: RiskProfile;
}

export interface ResearchOnPlanRequest {
    query: string;
}

export interface ResearchOnPlanResponse {
    run_id: string;
    summary: string;
    scenarios: any[];
    refined_forecasts: any;
    follow_up_suggestions: string[] | null;
}

// Plan API Functions
export async function createPlan(request: PlanCreateRequest): Promise<{ plan_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/plans`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to create plan');
    }

    return response.json();
}

export async function listPlans(userId: string = 'default'): Promise<Plan[]> {
    const response = await fetch(`${API_BASE_URL}/api/plans?user_id=${encodeURIComponent(userId)}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to list plans');
    }

    return response.json();
}

export async function getPlan(planId: string): Promise<Plan> {
    const response = await fetch(`${API_BASE_URL}/api/plans/${planId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to get plan');
    }

    return response.json();
}

export async function updatePlan(planId: string, request: PlanUpdateRequest): Promise<{ plan_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/plans/${planId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to update plan');
    }

    return response.json();
}

export async function deletePlan(planId: string): Promise<{ plan_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/plans/${planId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to delete plan');
    }

    return response.json();
}

export async function runResearchOnPlan(planId: string, request: ResearchOnPlanRequest): Promise<ResearchOnPlanResponse> {
    const response = await fetch(`${API_BASE_URL}/api/plans/${planId}/research`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to run research');
    }

    return response.json();
}
