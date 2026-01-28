'use client';

import React, { useState, useEffect } from 'react';
import { optimizePortfolio, getOptimizationStatus, OptimizationResult } from '../lib/api-client';

interface PortfolioOptimizerProps {
    initialAmount?: number;
    initialCurrency?: string;
}

export default function PortfolioOptimizer({ initialAmount = 10000, initialCurrency = 'USD' }: PortfolioOptimizerProps) {
    const [amount, setAmount] = useState<number>(initialAmount);
    const [currency, setCurrency] = useState<string>(initialCurrency);
    const [jobId, setJobId] = useState<string | null>(null);
    const [result, setResult] = useState<OptimizationResult | null>(null);
    const [isRunning, setIsRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);

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
            const response = await optimizePortfolio(amount, currency);
            setJobId(response.job_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start optimization');
            setIsRunning(false);
        }
    };

    useEffect(() => {
        if (!jobId) return;

        const pollStatus = async () => {
            try {
                const status = await getOptimizationStatus(jobId);
                setResult(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    setIsRunning(false);
                    if (status.error) {
                        setError(status.error);
                    }
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch status');
                setIsRunning(false);
            }
        };

        pollStatus();
        const interval = setInterval(pollStatus, 2000);

        return () => clearInterval(interval);
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
                        <label className="label">
                            <span className="label-text">Investment Amount</span>
                        </label>
                        <input
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
                        <label className="label">
                            <span className="label-text">Currency</span>
                        </label>
                        <select
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
                </div>

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
                {result && result.status === 'completed' && (
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
                            <div className="overflow-x-auto">
                                <h3 className="text-lg font-bold mb-3">Efficient Frontier</h3>
                                <div className="overflow-y-auto max-h-64">
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
                                                    <td>{formatPercent(point.annual_volatility)}</td>
                                                    <td className={(point.annual_return ?? 0) >= 0 ? 'text-success' : 'text-error'}>
                                                        {formatPercent(point.annual_return)}
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
                        )}

                        {/* Scenario Forecasts */}
                        {result.scenarios && result.scenarios.length > 0 && (
                            <div className="overflow-x-auto">
                                <h3 className="text-lg font-bold mb-3">Scenario Forecasts</h3>
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
                        {result.llm_report && (
                            <div className="card bg-base-200 border border-base-300">
                                <div className="card-body">
                                    <h3 className="card-title mb-4">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                                        </svg>
                                        AI Analysis Report
                                    </h3>
                                    <div className="prose prose-sm max-w-none">
                                        <div className="whitespace-pre-wrap text-sm leading-relaxed">
                                            {result.llm_report}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
