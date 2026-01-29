'use client';

import React, { useState } from 'react';
import { Plan, OptimizationResult, TaxAccount } from '../lib/api-client';
import PortfolioOptimizer from './PortfolioOptimizer';
import ResearchPanel from './ResearchPanel';
import AccountManager from './AccountManager';

interface PlanDetailProps {
    plan: Plan;
    onBack: () => void;
    onPlanUpdate?: (plan: Plan) => void;
}

type ViewMode = 'overview' | 'accounts' | 'settings';

export default function PlanDetail({ plan, onBack, onPlanUpdate }: PlanDetailProps) {
    const [showOptimizer, setShowOptimizer] = useState(!plan.optimization_result);
    const [deepDiveMetric, setDeepDiveMetric] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<ViewMode>('overview');
    const [localPlan, setLocalPlan] = useState<Plan>(plan);

    const handleAccountsUpdate = (accounts: TaxAccount[]) => {
        const updated = { ...localPlan, tax_accounts: accounts, updated_at: new Date().toISOString() };
        setLocalPlan(updated);
        onPlanUpdate?.(updated);
    };

    const formatCurrency = (value: number, currency: string = localPlan.initial_amount ? 'USD' : 'USD') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);
    };

    const formatPercent = (value: number | null | undefined) => {
        if (value === null || value === undefined) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);
    };

    const handleDeepDive = (metric: string) => {
        setDeepDiveMetric(metric);
        // Scroll to research panel
        document.getElementById('research-panel')?.scrollIntoView({ behavior: 'smooth' });
        // Set the research query automatically
        const researchInput = document.querySelector('input[placeholder*="recession"]') as HTMLInputElement;
        if (researchInput) {
            const queries: Record<string, string> = {
                'return': 'Explain the drivers of expected return for this portfolio',
                'volatility': 'Analyze the risk factors and volatility sources in this portfolio',
                'sharpe': 'Evaluate the risk-adjusted performance of this portfolio',
                'allocation': 'Analyze the portfolio allocation and concentration risk',
            };
            researchInput.value = queries[metric] || metric;
            researchInput.focus();
        }
    };

    const DeepDiveButton = ({ metric, label }: { metric: string; label: string }) => (
        <button
            onClick={() => handleDeepDive(metric)}
            className="btn btn-ghost btn-xs text-primary hover:bg-primary/10"
            title="Deep dive into this metric"
        >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {label}
        </button>
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button onClick={onBack} className="btn btn-ghost btn-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
                    </svg>
                    Back to Plans
                </button>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold">{localPlan.name}</h1>
                    {localPlan.description && (
                        <p className="text-base-content/60 text-sm mt-1">{localPlan.description}</p>
                    )}
                </div>
                <div className="flex gap-2">
                    {localPlan.optimization_result && (
                        <button
                            onClick={() => setShowOptimizer(!showOptimizer)}
                            className="btn btn-outline btn-sm"
                        >
                            {showOptimizer ? 'Hide' : 'Show'} Optimizer
                        </button>
                    )}
                    <div className="badge badge-ghost">{localPlan.risk_preference.replace('_', ' ')}</div>
                </div>
            </div>

            {/* Research History Summary */}
            {localPlan.research_history.length > 0 && (
                <div className="alert alert-info">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>
                        This plan has <strong>{localPlan.research_history.length}</strong> research analysi
                        {localPlan.research_history.length !== 1 ? 's' : ''}.
                        Latest: {new Date(localPlan.research_history[localPlan.research_history.length - 1].timestamp).toLocaleDateString()}
                    </span>
                </div>
            )}

            {/* Tab Navigation */}
            <div role="tablist" className="tabs tabs-boxed bg-base-200">
                <button
                    role="tab"
                    className={`tab ${viewMode === 'overview' ? 'tab-active' : ''}`}
                    onClick={() => setViewMode('overview')}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                    </svg>
                    Overview
                </button>
                <button
                    role="tab"
                    className={`tab ${viewMode === 'accounts' ? 'tab-active' : ''}`}
                    onClick={() => setViewMode('accounts')}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v-.75M8.25 2.25h.008v.008H8.25V2.25zm2.25 0h.008v.008h-.008V2.25zm2.25 0h.008v.008h-.008V2.25z" />
                    </svg>
                    Accounts ({localPlan.tax_accounts?.length || 0})
                </button>
                <button
                    role="tab"
                    className={`tab ${viewMode === 'settings' ? 'tab-active' : ''}`}
                    onClick={() => setViewMode('settings')}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.34 15.84c-.688-.06-1.386-.09-2.09-.09H7.5a4.5 4.5 0 110-9h.75c.704 0 1.402-.03 2.09-.09m0 9.18c.253.962.584 1.892.985 2.783.247.55.06 1.21-.463 1.511l-.657.38c-.551.318-1.26.117-1.527-.461a20.845 20.845 0 01-1.44-4.282m3.102.069a18.03 18.03 0 01-.59-4.59c0-1.586.205-3.124.59-4.59m0 9.18a23.848 23.848 0 018.835 2.535M10.34 6.66a23.847 23.847 0 018.835-2.535m0 0A23.74 23.74 0 0018.795 3m.38 1.125a23.91 23.91 0 011.014 5.395m-1.014 8.855c-.118.38-.245.754-.38 1.125m.38-1.125a23.91 23.91 0 001.014-5.395m0-3.46c.495.413.811 1.035.811 1.73 0 .695-.316 1.317-.811 1.73m0-3.46a24.347 24.347 0 010 3.46" />
                    </svg>
                    Settings
                </button>
            </div>

            {/* Content based on view mode */}
            {viewMode === 'accounts' && (
                <div className="card bg-base-100 shadow-xl border border-base-200">
                    <div className="card-body">
                        <h2 className="card-title">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v-.75M8.25 2.25h.008v.008H8.25V2.25zm2.25 0h.008v.008h-.008V2.25zm2.25 0h.008v.008h-.008V2.25z" />
                            </svg>
                            Investment Accounts
                        </h2>
                        <p className="text-base-content/70">
                            Configure your tax-advantaged accounts (NISA, iDeCo) and taxable accounts for optimal tax placement.
                        </p>
                        <AccountManager
                            accounts={localPlan.tax_accounts || []}
                            onUpdate={handleAccountsUpdate}
                            currency="JPY"
                        />
                    </div>
                </div>
            )}

            {viewMode === 'settings' && (
                <div className="card bg-base-100 shadow-xl border border-base-200">
                    <div className="card-body">
                        <h2 className="card-title">Plan Settings</h2>
                        <p className="text-base-content/70">Your investment preferences and profile settings.</p>

                        <div className="space-y-4">
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Plan Name</span>
                                </label>
                                <input
                                    type="text"
                                    value={localPlan.name}
                                    onChange={(e) => setLocalPlan({ ...localPlan, name: e.target.value })}
                                    className="input input-bordered"
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Description</span>
                                </label>
                                <textarea
                                    value={localPlan.description || ''}
                                    onChange={(e) => setLocalPlan({ ...localPlan, description: e.target.value })}
                                    className="textarea textarea-bordered"
                                    rows={2}
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Risk Preference</span>
                                </label>
                                <select
                                    value={localPlan.risk_preference}
                                    onChange={(e) => setLocalPlan({ ...localPlan, risk_preference: e.target.value as any })}
                                    className="select select-bordered"
                                >
                                    <option value="very_conservative">Very Conservative - Max capital preservation</option>
                                    <option value="conservative">Conservative - Focus on stability</option>
                                    <option value="moderate">Moderate - Balanced approach</option>
                                    <option value="growth">Growth - Accept higher volatility</option>
                                    <option value="aggressive">Aggressive - Maximum growth</option>
                                </select>
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Notes</span>
                                </label>
                                <textarea
                                    value={localPlan.notes || ''}
                                    onChange={(e) => setLocalPlan({ ...localPlan, notes: e.target.value })}
                                    className="textarea textarea-bordered"
                                    placeholder="Add any notes about this plan..."
                                    rows={4}
                                />
                            </div>

                            <div className="divider"></div>

                            <div className="alert alert-info">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                                </svg>
                                <span>
                                    <strong>Admin Configuration</strong><br />
                                    Available ETFs, account rules, and tax conditions are configured at the system level.
                                    Contact admin for changes to global configuration.
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {viewMode === 'overview' && (
                <>
                    {/* Original overview content */}

                    {/* Optimization Results */}
                    {showOptimizer && (
                        <>
                            {!localPlan.optimization_result ? (
                                <div className="card bg-base-100 shadow-xl border border-base-200">
                                    <div className="card-body">
                                        <h2 className="card-title">Start Portfolio Optimization</h2>
                                        <p className="text-base-content/70">
                                            Create an optimized portfolio allocation based on your {localPlan.risk_preference.replace('_', ' ')} risk preference.
                                        </p>
                                        <PortfolioOptimizer
                                            initialAmount={localPlan.initial_amount || 10000}
                                            initialCurrency="USD"
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    {/* Key Metrics with Deep-Dive Buttons */}
                                    {localPlan.optimization_result.metrics && (
                                        <div className="stats stats-vertical lg:stats-horizontal shadow w-full bg-base-200">
                                            <div className="stat">
                                                <div className="stat-title">Initial Investment</div>
                                                <div className="stat-value text-lg">
                                                    {formatCurrency(localPlan.optimization_result.initial_amount)}
                                                </div>
                                            </div>
                                            <div className="stat">
                                                <div className="stat-title">Net Investment</div>
                                                <div className="stat-value text-lg text-primary">
                                                    {formatCurrency(localPlan.optimization_result.metrics.net_investment)}
                                                </div>
                                                <div className="stat-desc">
                                                    Commission: {formatCurrency(localPlan.optimization_result.metrics.total_commission)}
                                                </div>
                                            </div>
                                            <div className="stat relative">
                                                <div className="stat-title flex items-center gap-2">
                                                    Expected Annual Return
                                                    <DeepDiveButton metric="return" label="Analyze" />
                                                </div>
                                                <div className="stat-value text-lg text-success">
                                                    {formatPercent(localPlan.optimization_result.metrics.expected_annual_return)}
                                                </div>
                                            </div>
                                            <div className="stat relative">
                                                <div className="stat-title flex items-center gap-2">
                                                    Annual Volatility
                                                    <DeepDiveButton metric="volatility" label="Deep Dive" />
                                                </div>
                                                <div className="stat-value text-lg text-warning">
                                                    {formatPercent(localPlan.optimization_result.metrics.annual_volatility)}
                                                </div>
                                            </div>
                                            <div className="stat relative">
                                                <div className="stat-title flex items-center gap-2">
                                                    Sharpe Ratio
                                                    <DeepDiveButton metric="sharpe" label="Explain" />
                                                </div>
                                                <div className="stat-value text-lg">
                                                    {localPlan.optimization_result.metrics.sharpe_ratio !== undefined && localPlan.optimization_result.metrics.sharpe_ratio !== null
                                                        ? typeof localPlan.optimization_result.metrics.sharpe_ratio === 'number'
                                                            ? localPlan.optimization_result.metrics.sharpe_ratio.toFixed(2)
                                                            : localPlan.optimization_result.metrics.sharpe_ratio
                                                        : 'N/A'}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Optimal Portfolio with Allocation Analysis */}
                                    {localPlan.optimization_result.optimal_portfolio && localPlan.optimization_result.optimal_portfolio.length > 0 && (
                                        <div className="overflow-x-auto">
                                            <div className="flex justify-between items-center mb-3">
                                                <h3 className="text-lg font-bold">Optimal Portfolio Allocation</h3>
                                                <DeepDiveButton metric="allocation" label="Analyze Allocation" />
                                            </div>
                                            <table className="table table-zebra">
                                                <thead>
                                                    <tr>
                                                        <th>Ticker</th>
                                                        <th>Weight</th>
                                                        <th>Amount</th>
                                                        <th>Shares</th>
                                                        <th>Price</th>
                                                        <th>Expected Return</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {localPlan.optimization_result.optimal_portfolio.map((asset, idx) => (
                                                        <tr key={idx}>
                                                            <td className="font-bold">{asset.ticker}</td>
                                                            <td>{formatPercent(asset.weight)}</td>
                                                            <td>{formatCurrency(asset.amount)}</td>
                                                            <td>{asset.shares.toFixed(2)}</td>
                                                            <td>{formatCurrency(asset.price)}</td>
                                                            <td className={(asset.expected_return ?? 0) >= 0 ? 'text-success' : 'text-error'}>
                                                                {formatPercent(asset.expected_return)}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}

                                    {/* LLM Report with Follow-up Suggestions */}
                                    {localPlan.optimization_result.llm_report && (
                                        <div className="card bg-base-200 border border-base-300">
                                            <div className="card-body">
                                                <h3 className="card-title mb-4 flex items-center gap-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                                                    </svg>
                                                    AI Analysis Report
                                                </h3>
                                                <div className="prose prose-sm max-w-none">
                                                    {localPlan.optimization_result.llm_report.split('\n').map((paragraph, idx) => (
                                                        <p key={idx}>{paragraph}</p>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Scenarios */}
                                    {localPlan.optimization_result.scenarios && localPlan.optimization_result.scenarios.length > 0 && (
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            {localPlan.optimization_result.scenarios.map((scenario, idx) => (
                                                <div key={idx} className={`card bg-base-200 ${scenario.name === 'Bull Case' ? 'border-l-4 border-success' :
                                                    scenario.name === 'Bear Case' ? 'border-l-4 border-error' :
                                                        'border-l-4 border-info'
                                                    }`}>
                                                    <div className="card-body p-4">
                                                        <div className="flex justify-between items-start">
                                                            <h4 className="font-bold text-lg">{scenario.name}</h4>
                                                            <span className="badge badge-ghost">{formatPercent(scenario.probability)} probability</span>
                                                        </div>
                                                        <p className="text-sm opacity-70 mt-1">{scenario.description}</p>
                                                        <div className="divider my-2"></div>
                                                        <div className="space-y-1">
                                                            <div className="flex justify-between">
                                                                <span className="text-sm">Expected Value:</span>
                                                                <span className="font-semibold">{formatCurrency(scenario.expected_portfolio_value ?? 0)}</span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-sm">Expected Return:</span>
                                                                <span className={`font-semibold ${(scenario.expected_return ?? 0) >= 0 ? 'text-success' : 'text-error'}`}>
                                                                    {formatPercent(scenario.expected_return)}
                                                                </span>
                                                            </div>
                                                            <div className="flex justify-between">
                                                                <span className="text-sm">Volatility:</span>
                                                                <span className="font-semibold">{formatPercent(scenario.annual_volatility)}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </>
            )}

            {/* Research Panel - Always visible */}
            <div id="research-panel">
                <ResearchPanel
                    planId={localPlan.plan_id}
                    planName={localPlan.name}
                    followUpSuggestions={localPlan.optimization_result?.metrics?.follow_up_suggestions as string[] | null}
                    onResearchComplete={(result) => {
                        // Reload plan to get updated research history
                        onPlanUpdate?.(localPlan);
                    }}
                />
            </div>
        </div>
    );
}
