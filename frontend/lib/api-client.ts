const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== Authentication ====================

let accessToken: string | null = null;
let refreshToken: string | null = null;

if (typeof window !== 'undefined') {
    accessToken = localStorage.getItem('accessToken');
    refreshToken = localStorage.getItem('refreshToken');
}

export function setAuth(access: string, refresh: string) {
    accessToken = access;
    refreshToken = refresh;
    if (typeof window !== 'undefined') {
        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);
    }
}

export function logout() {
    accessToken = null;
    refreshToken = null;
    if (typeof window !== 'undefined') {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
    }
}

export function getAuthToken() {
    return accessToken;
}

export async function login(username: string, password: string): Promise<boolean> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });

        if (response.ok) {
            const data = await response.json();
            setAuth(data.access_token, data.refresh_token);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Login error:', error);
        return false;
    }
}

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = new Headers(options.headers || {});

    if (accessToken) {
        headers.set('Authorization', `Bearer ${accessToken}`);
    }

    const authOptions = {
        ...options,
        headers,
    };

    let response = await fetch(url, authOptions);

    if (response.status === 401 && refreshToken) {
        // Attempt to refresh token
        try {
            const refreshResponse = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (refreshResponse.ok) {
                const data = await refreshResponse.json();
                setAuth(data.access_token, data.refresh_token);

                // Retry original request with new token
                headers.set('Authorization', `Bearer ${data.access_token}`);
                response = await fetch(url, { ...options, headers });
            } else {
                logout();
            }
        } catch (e) {
            logout();
        }
    }

    return response;
}

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
        const response = await fetchWithAuth(`${API_BASE_URL}/api/news`);
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
    const response = await fetchWithAuth(`${API_BASE_URL}/api/agents/${agentName}/run`, {
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
    const response = await fetchWithAuth(`${API_BASE_URL}/api/agents/runs/${runId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get run status');
    }

    return response.json();
}

export async function getRunLogs(runId: string): Promise<AgentLog[]> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/agents/runs/${runId}/logs`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get run logs');
    }

    return response.json();
}

// Portfolio API

export interface BacktestResult {
    trajectory: Array<{ date: string; value: number; pre_tax_value?: number }>;
    benchmark_trajectory: Array<{ date: string; value: number }>;
    metrics: {
        total_return: number;
        pre_tax_total_return?: number;
        final_value: number;
        volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
        recovery_days: number | null;
        cagr: number;
        capital_gains_tax?: number;
        tax_rate?: number;
        tax_impact?: number;
    };
    start_date?: string;
    end_date?: string;
    account_type?: string;
    capital_gains_tax?: number;
}

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
    backtest_result?: BacktestResult | null;
}

export async function optimizePortfolio(
    amount: number,
    currency: string,
    fast: boolean = false,
    historicalDate?: string,
    useStrategy?: string,
    accountType?: string
): Promise<{ job_id: string; status: string }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/portfolio/optimize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            amount,
            currency,
            fast,
            historical_date: historicalDate,
            use_strategy: useStrategy,
            account_type: accountType
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to start optimization');
    }

    return response.json();
}

export async function getOptimizationStatus(jobId: string): Promise<OptimizationResult> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/portfolio/optimize/${jobId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get optimization status');
    }

    return response.json();
}

export async function clearOptimizationCache(jobId?: string): Promise<{ message: string; jobs_cleared: number }> {
    const url = jobId ? `${API_BASE_URL}/api/portfolio/optimize/cache?job_id=${jobId}` : `${API_BASE_URL}/api/portfolio/optimize/cache`;
    const response = await fetchWithAuth(url, {
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
    base_currency?: string;
    risk_preference: RiskProfile;
    initial_portfolio?: AssetHolding[] | null;
    initial_amount?: number | null;
    optimization_result?: OptimizationResult | null;
    recurring_investment?: RecurringInvestment | null;
    tax_accounts?: TaxAccount[] | null;
    research_history: ResearchRun[];
    notes?: string | null;
}

export interface AssetHolding {
    ticker: string;
    account_type: TaxAccountType;
    monetary_value: number;
    // No currency field - always in plan's base_currency
}

export interface ValidationError {
    account_type: string;
    message: string;
    total?: number;
    limit?: number;
}

export interface ValidationResult {
    valid: boolean;
    errors: ValidationError[];
    warnings: Array<{ ticker?: string; message: string }>;
}

export interface EtfInfo {
    symbol: string;
    name: string;
    eligible_accounts: TaxAccountType[];
    market: string;
    native_currency: string;  // For info display
    current_price_base: number;  // Converted to base currency
}

export interface AccountLimitInfo {
    annual_limit: number;
    used_space: number;
    available_space: number;
}

export interface AvailableEtfsResponse {
    etfs: EtfInfo[];
    account_limits: Record<string, AccountLimitInfo>;
    base_currency: string;
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
    const response = await fetchWithAuth(`${API_BASE_URL}/api/plans`, {
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
    const response = await fetchWithAuth(`${API_BASE_URL}/api/plans?user_id=${encodeURIComponent(userId)}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to list plans');
    }

    return response.json();
}

export async function getPlan(planId: string): Promise<Plan> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/plans/${planId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to get plan');
    }

    return response.json();
}

export async function updatePlan(planId: string, request: PlanUpdateRequest): Promise<{ plan_id: string; status: string }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/plans/${planId}`, {
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
    const response = await fetchWithAuth(`${API_BASE_URL}/api/plans/${planId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to delete plan');
    }

    return response.json();
}

export async function runResearchOnPlan(planId: string, request: ResearchOnPlanRequest): Promise<ResearchOnPlanResponse> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/plans/${planId}/research`, {
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

// ==================== Portfolio Management API ====================

export async function getAvailableEtfs(planId: string): Promise<AvailableEtfsResponse> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/portfolio/etfs/available?plan_id=${encodeURIComponent(planId)}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to fetch available ETFs');
    }

    return response.json();
}

export async function validatePortfolioHoldings(
    planId: string,
    holdings: AssetHolding[]
): Promise<ValidationResult> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/portfolio/validate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            plan_id: planId,
            holdings: holdings
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to validate portfolio holdings');
    }

    return response.json();
}

export async function updatePlanPortfolio(
    planId: string,
    holdings: AssetHolding[]
): Promise<{ plan_id: string; status: string }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/plans/${planId}/portfolio`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            initial_portfolio: holdings
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Failed to update portfolio');
    }

    return response.json();
}

// ==================== Strategy Templates API ====================

export interface StrategyTemplate {
    strategy_id: string;
    name: string;
    description: string;
    risk_level: 'conservative' | 'moderate' | 'aggressive';
    icon: string;
    tags: string[];
    constraints: any;
}

export async function listStrategies(riskLevel?: string): Promise<StrategyTemplate[]> {
    const url = riskLevel
        ? `${API_BASE_URL}/api/strategies?risk_level=${encodeURIComponent(riskLevel)}`
        : `${API_BASE_URL}/api/strategies`;

    const response = await fetchWithAuth(url);
    if (!response.ok) {
        throw new Error('Failed to fetch strategies');
    }
    return response.json();
}

export async function getStrategy(strategyId: string): Promise<StrategyTemplate> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/strategies/${strategyId}`);
    if (!response.ok) {
        throw new Error('Failed to fetch strategy');
    }
    return response.json();
}

// ==================== Admin API ====================

export interface AdminConfig {
    etfs: any;
    forecasting: any;
}

export interface CacheStats {
    [key: string]: {
        count: number;
        collection: string;
        error?: string;
    };
}

export async function getAdminConfig(): Promise<AdminConfig> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/admin/config`);
    return response.json();
}

export async function updateETFConfig(config: any): Promise<{ status: string; config_type: string }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/admin/config/etfs`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
    });
    return response.json();
}

export async function updateForecastingConfig(config: any): Promise<{ status: string; config_type: string }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/admin/config/forecasting`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
    });
    return response.json();
}

export async function resetConfig(): Promise<{ status: string; message: string }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/admin/config/reset`, {
        method: 'POST',
    });
    return response.json();
}

export async function getCacheStats(): Promise<CacheStats> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/admin/cache/stats`);
    return response.json();
}

export async function clearCache(cacheType: string): Promise<{ status: string; cache_type: string; items_deleted: number }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/admin/cache/${cacheType}`, {
        method: 'DELETE',
    });
    return response.json();
}
