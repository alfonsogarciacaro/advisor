'use client';

import React, { useState, useEffect } from 'react';
import { optimizePortfolio, getOptimizationStatus, clearOptimizationCache, OptimizationResult } from '../lib/api-client';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    ComposedChart, Scatter, ReferenceDot
} from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface PortfolioOptimizerProps {
    initialAmount?: number;
    initialCurrency?: string;
    fast?: boolean;  // Fast mode for testing (skip forecasting/LLM, reduce simulations)
}

export default function PortfolioOptimizer({ initialAmount = 10000, initialCurrency = 'USD', fast = false }: PortfolioOptimizerProps) {
    const [amount, setAmount] = useState<number>(initialAmount);
    const [currency, setCurrency] = useState<string>(initialCurrency);
    const [jobId, setJobId] = useState<string | null>(null);
    const [result, setResult] = useState<OptimizationResult | null>(null);
    const [isRunning, setIsRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showDebug, setShowDebug] = useState(false);

    const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD'];

    const startOptimization = async () => {
        if (amount <= 0) {
            setError('Please enter a valid investment amount');
            return;
        }

        setIsRunning(true);
        setError(null);
        setResult(null);

        try {
            const response = await optimizePortfolio(amount, currency, fast);
            setJobId(response.job_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start optimization');
            setIsRunning(false);
        }
    };

    useEffect(() => {
        if (!jobId) return;

        let interval: NodeJS.Timeout | null = null;

        const pollStatus = async () => {
            try {
                const status = await getOptimizationStatus(jobId);
                console.log('Optimization status:', status);
                console.log('Efficient frontier length:', status.efficient_frontier?.length);
                console.log('Scenarios length:', status.scenarios?.length);
                console.log('Scenarios:', status.scenarios);
                setResult(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    setIsRunning(false);
                    if (status.error) {
                        setError(status.error);
                    }
                    // Clear the interval when job completes
                    if (interval) {
                        clearInterval(interval);
                        interval = null;
                    }
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch status');
                setIsRunning(false);
                // Clear the interval on error
                if (interval) {
                    clearInterval(interval);
                    interval = null;
                }
            }
        };

        pollStatus();
        interval = setInterval(pollStatus, 2000);

        return () => {
            if (interval) {
                clearInterval(interval);
            }
        };
    }, [jobId]);

    const formatCurrency = (value: number) => {
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

    const getStatusBadge = () => {
        if (!result) return null;

        const statusMap = {
            queued: 'badge-ghost',
            fetching_data: 'badge-info',
            forecasting: 'badge-info animate-pulse',
            optimizing: 'badge-warning animate-pulse',
            generating_analysis: 'badge-primary animate-pulse',
            completed: 'badge-success',
            failed: 'badge-error',
        };

        return (
            <span className={`badge ${statusMap[result.status as keyof typeof statusMap] || 'badge-ghost'}`}>
                {result.status.replace('_', ' ').toUpperCase()}
            </span>
        );
    };

    return (
        <div className="card bg-base-100 shadow-xl border border-base-200">
            <div className="card-body">
                <h2 className="card-title">
                    Portfolio Optimizer
                    {result && getStatusBadge()}
                </h2>

                {/* Input Form */}
                <div className="flex flex-wrap gap-4 mt-4">
                    <div className="form-control">
                        <label className="label" htmlFor="investment-amount">
                            <span className="label-text">Investment Amount</span>
                        </label>
                        <input
                            id="investment-amount"
                            type="number"
                            min="100"
                            step="100"
                            value={amount}
                            onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                            className="input input-bordered w-48"
                            disabled={isRunning}
                        />
                    </div>

                    <div className="form-control">
                        <label className="label" htmlFor="currency">
                            <span className="label-text">Currency</span>
                        </label>
                        <select
                            id="currency"
                            value={currency}
                            onChange={(e) => setCurrency(e.target.value)}
                            className="select select-bordered w-32"
                            disabled={isRunning}
                        >
                            {currencies.map((c) => (
                                <option key={c} value={c}>
                                    {c}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-control">
                        <label className="label">
                            <span className="label-text opacity-0">Action</span>
                        </label>
                        <button
                            onClick={startOptimization}
                            disabled={isRunning}
                            className="btn btn-primary"
                        >
                            {isRunning ? (
                                <>
                                    <span className="loading loading-spinner loading-sm"></span>
                                    Optimizing...
                                </>
                            ) : (
                                'Optimize Portfolio'
                            )}
                        </button>
                    </div>

                    <div className="form-control">
                        <label className="label">
                            <span className="label-text opacity-0">Debug</span>
                        </label>
                        <button
                            onClick={() => setShowDebug(!showDebug)}
                            className="btn btn-ghost btn-sm"
                        >
                            {showDebug ? 'Hide Debug' : 'Show Debug'}
                        </button>
                    </div>

                    <div className="form-control">
                        <label className="label">
                            <span className="label-text opacity-0">Cache</span>
                        </label>
                        <button
                            onClick={async () => {
                                if (jobId) {
                                    try {
                                        await clearOptimizationCache(jobId);
                                        alert(`Cleared cache for job ${jobId}`);
                                        setJobId(null);
                                        setResult(null);
                                    } catch (err) {
                                        alert(err instanceof Error ? err.message : 'Failed to clear cache');
                                    }
                                } else if (result?.job_id) {
                                    try {
                                        await clearOptimizationCache(result.job_id);
                                        alert(`Cleared cache for job ${result.job_id}`);
                                        setJobId(null);
                                        setResult(null);
                                    } catch (err) {
                                        alert(err instanceof Error ? err.message : 'Failed to clear cache');
                                    }
                                } else {
                                    alert('No job to clear');
                                }
                            }}
                            disabled={isRunning}
                            className="btn btn-warning btn-sm"
                        >
                            Clear Cache
                        </button>
                    </div>
                </div>

                {/* Debug Info */}
                {showDebug && (
                    <div className="alert alert-info mt-4">
                        <div className="flex-1">
                            <h3 className="font-bold">Debug Info</h3>
                            <div className="text-xs mt-2 space-y-1">
                                <div>Job ID: {jobId || result?.job_id || 'None'}</div>
                                <div>Status: {result?.status || 'No result'}</div>
                                <div>Efficient Frontier Points: {result?.efficient_frontier?.length || 0}</div>
                                <div>Scenarios Count: {result?.scenarios?.length || 0}</div>
                                {result?.scenarios && result.scenarios.length > 0 && (
                                    <div>Scenario Names: {result.scenarios.map(s => s.name).join(', ')}</div>
                                )}
                                {result?.scenarios && result.scenarios.length > 0 && result.scenarios[0]?.trajectory && (
                                    <div>First Scenario Trajectory Points: {result.scenarios[0].trajectory.length}</div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Error Display */}
                {error && (
                    <div className="alert alert-error mt-4">
                        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>{error}</span>
                    </div>
                )}

                {/* Results Display */}
                {result && (result.status === 'completed' || result.status === 'generating_analysis') && (
                    <div className="mt-6 space-y-6">
                        {/* Key Metrics */}
                        {result.metrics && (
                            <div className="stats stats-vertical lg:stats-horizontal shadow w-full bg-base-200">
                                <div className="stat">
                                    <div className="stat-title">Initial Investment</div>
                                    <div className="stat-value text-lg">
                                        {formatCurrency(result.initial_amount)}
                                    </div>
                                </div>
                                <div className="stat">
                                    <div className="stat-title">Net Investment</div>
                                    <div className="stat-value text-lg text-primary">
                                        {formatCurrency(result.metrics.net_investment)}
                                    </div>
                                    <div className="stat-desc">
                                        Commission: {formatCurrency(result.metrics.total_commission)}
                                    </div>
                                </div>
                                <div className="stat">
                                    <div className="stat-title">Expected Annual Return</div>
                                    <div className="stat-value text-lg text-success">
                                        {formatPercent(result.metrics.expected_annual_return)}
                                    </div>
                                </div>
                                <div className="stat">
                                    <div className="stat-title">Annual Volatility</div>
                                    <div className="stat-value text-lg text-warning">
                                        {formatPercent(result.metrics.annual_volatility)}
                                    </div>
                                </div>
                                <div className="stat">
                                    <div className="stat-title">Sharpe Ratio</div>
                                    <div className="stat-value text-lg">
                                        {result.metrics.sharpe_ratio !== undefined && result.metrics.sharpe_ratio !== null
                                            ? typeof result.metrics.sharpe_ratio === 'number'
                                                ? result.metrics.sharpe_ratio.toFixed(2)
                                                : result.metrics.sharpe_ratio
                                            : 'N/A'}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Optimal Portfolio Table */}
                        {result.optimal_portfolio && result.optimal_portfolio.length > 0 && (
                            <div className="overflow-x-auto">
                                <h3 className="text-lg font-bold mb-3">Optimal Portfolio Allocation</h3>
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
                                        {result.optimal_portfolio.map((asset, idx) => (
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

                        {/* Efficient Frontier */}
                        {result.efficient_frontier && result.efficient_frontier.length > 0 && (
                            <div className="space-y-6">
                                <h3 className="text-lg font-bold">Efficient Frontier</h3>
                                <div className="h-96 w-full bg-white dark:bg-zinc-900 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <ComposedChart
                                            margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-700" />
                                            <XAxis
                                                type="number"
                                                dataKey="annual_volatility"
                                                name="Volatility"
                                                unit="%"
                                                tickFormatter={(value) => (value * 100).toFixed(0)}
                                                label={{ value: 'Expected Risk (Volatility)', position: 'bottom', offset: 0 }}
                                            />
                                            <YAxis
                                                type="number"
                                                dataKey="annual_return"
                                                name="Return"
                                                unit="%"
                                                tickFormatter={(value) => (value * 100).toFixed(0)}
                                                label={{ value: 'Expected Return', angle: -90, position: 'insideLeft' }}
                                            />
                                            <Tooltip
                                                formatter={(value: number | undefined) => value !== undefined ? [(value * 100).toFixed(2) + '%', ''] : ['', '']}
                                                labelFormatter={(value) => `Volatility: ${(Number(value) * 100).toFixed(2)}%`}
                                            />
                                            <Legend />
                                            <Line
                                                data={result.efficient_frontier}
                                                type="monotone"
                                                dataKey="annual_return"
                                                stroke="#2563eb"
                                                strokeWidth={3}
                                                dot={false}
                                                name="Efficient Frontier"
                                                isAnimationActive={true}
                                            />
                                            {/* Current Optimal Portfolio Point */}
                                            {result.metrics && result.metrics.annual_volatility !== null && result.metrics.annual_volatility !== undefined && (
                                                <ReferenceDot
                                                    x={result.metrics.annual_volatility}
                                                    y={result.metrics.expected_annual_return ?? 0}
                                                    r={6}
                                                    fill="#dc2626"
                                                    stroke="none"
                                                />
                                            )}
                                        </ComposedChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="collapse collapse-arrow border border-base-300 bg-base-100 rounded-box">
                                    <input type="checkbox" />
                                    <div className="collapse-title text-sm font-medium">
                                        View Detailed Frontier Data
                                    </div>
                                    <div className="collapse-content">
                                        <div className="overflow-x-auto">
                                            <table className="table table-compact table-pin-rows">
                                                <thead>
                                                    <tr>
                                                        <th>Volatility</th>
                                                        <th>Return</th>
                                                        <th>Sharpe Ratio</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {result.efficient_frontier.map((point, idx) => (
                                                        <tr key={idx}>
                                                            <td>{formatPercent(point.annual_volatility ?? null)}</td>
                                                            <td className={(point.annual_return ?? 0) >= 0 ? 'text-success' : 'text-error'}>
                                                                {formatPercent(point.annual_return ?? null)}
                                                            </td>
                                                            <td>
                                                                <span className={`badge badge-sm ${(point.sharpe_ratio ?? 0) > 1 ? 'badge-success' : (point.sharpe_ratio ?? 0) > 0.5 ? 'badge-warning' : 'badge-error'}`}>
                                                                    {typeof point.sharpe_ratio === 'number' ? point.sharpe_ratio.toFixed(2) : 'N/A'}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Scenario Forecasts */}
                        {result.scenarios && result.scenarios.length > 0 && (
                            <div className="space-y-6">
                                <h3 className="text-lg font-bold">Scenario Forecasts</h3>

                                <div className="h-96 w-full bg-white dark:bg-zinc-900 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart
                                            data={(() => {
                                                if (!result.scenarios || result.scenarios.length === 0) return [];
                                                const firstTrajectory = result.scenarios[0].trajectory;
                                                if (!firstTrajectory) return [];

                                                return firstTrajectory.map((pt, idx) => {
                                                    const item: any = { date: new Date(pt.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) };
                                                    result.scenarios?.forEach(s => {
                                                        if (s.trajectory && s.trajectory[idx]) {
                                                            item[s.name] = s.trajectory[idx].value;
                                                        }
                                                    });
                                                    return item;
                                                });
                                            })()}
                                            margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-700" />
                                            <XAxis dataKey="date" />
                                            <YAxis
                                                tickFormatter={(value: number | undefined) => value !== undefined ? new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(value) : ''}
                                            />
                                            <Tooltip formatter={(value: number | undefined) => value !== undefined ? formatCurrency(value) : ''} />
                                            <Legend />
                                            {result.scenarios.map((scenario) => (
                                                <Line
                                                    key={scenario.name}
                                                    type="monotone"
                                                    dataKey={scenario.name}
                                                    stroke={scenario.name.includes('Bull') ? '#22c55e' : scenario.name.includes('Bear') ? '#ef4444' : '#3b82f6'}
                                                    strokeWidth={2}
                                                    dot={false}
                                                />
                                            ))}
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {result.scenarios.map((scenario, idx) => (
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
                            </div>
                        )}

                        {/* LLM Report */}
                        <div className="card bg-base-200 border border-base-300">
                            <div className="card-body">
                                <h3 className="card-title mb-4 flex items-center gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                                    </svg>
                                    AI Analysis Report
                                    {result.status === 'generating_analysis' && (
                                        <span className="loading loading-spinner loading-sm text-primary"></span>
                                    )}
                                </h3>

                                {result.llm_report ? (
                                    <div className="prose prose-sm max-w-none">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {result.llm_report}
                                        </ReactMarkdown>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center p-8 text-center text-base-content/60">
                                        {result.status === 'generating_analysis' ? (
                                            <>
                                                <span className="loading loading-dots loading-lg mb-2"></span>
                                                <p>Generative models are analyzing your portfolio...</p>
                                                <p className="text-xs mt-1">This usually takes 10-20 seconds</p>
                                            </>
                                        ) : (
                                            <p>No analysis report generated.</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
