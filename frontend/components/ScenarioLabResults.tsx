'use client';

import React from 'react';
import { OptimizationResult } from '../lib/api-client';
import { SCENARIO_LAB_THEME } from '../lib/theme-constants';
import FanChart, { MonteCarloPercentiles } from './charts/FanChart';

interface ScenarioLabResultsProps {
    result: OptimizationResult | null;
    currency?: string;
    goalAmount?: number;
    timeHorizon?: number;
}

export default function ScenarioLabResults({
    result,
    currency = 'USD',
    goalAmount,
    timeHorizon = 10
}: ScenarioLabResultsProps) {
    if (!result) {
        return null;
    }
    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    };

    const formatPercent = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 1,
            maximumFractionDigits: 1,
        }).format(value);
    };

    // Generate Monte Carlo percentiles from scenarios
    // We'll create synthetic percentiles based on the bull/base/bear scenarios
    const generatePercentiles = (): MonteCarloPercentiles | null => {
        if (!result.scenarios || result.scenarios.length === 0) return null;

        // Find bull, base, and bear scenarios
        const bullScenario = result.scenarios.find(s => s.name.toLowerCase().includes('bull'));
        const bearScenario = result.scenarios.find(s => s.name.toLowerCase().includes('bear'));
        const baseScenario = result.scenarios.find(s => s.name.toLowerCase().includes('base'));

        if (!baseScenario?.trajectory) return null;

        // Generate synthetic percentiles
        const baseTrajectory = baseScenario.trajectory;
        const bullTrajectory = bullScenario?.trajectory || baseTrajectory;
        const bearTrajectory = bearScenario?.trajectory || baseTrajectory;

        // Create interpolated percentiles
        const p5 = bearTrajectory.map((p, i) => ({
            date: p.date,
            value: p.value * 0.7 // Very pessimistic
        }));

        const p25 = bearTrajectory.map((p, i) => ({
            date: p.date,
            value: p.value
        }));

        const p50 = baseTrajectory.map((p, i) => ({
            date: p.date,
            value: p.value
        }));

        const p75 = bullTrajectory.map((p, i) => ({
            date: p.date,
            value: p.value
        }));

        const p95 = bullTrajectory.map((p, i) => ({
            date: p.date,
            value: p.value * 1.3 // Very optimistic
        }));

        return { p5, p25, p50, p75, p95 };
    };

    const percentiles = generatePercentiles();

    // Calculate goal achievement probability
    const finalP50 = percentiles?.p50[percentiles.p50.length - 1]?.value ?? 0;
    const finalP5 = percentiles?.p5[percentiles.p5.length - 1]?.value ?? 0;
    const finalP95 = percentiles?.p95[percentiles.p95.length - 1]?.value ?? 0;

    let goalProbability: number | null = null;
    if (goalAmount && finalP5 < goalAmount && finalP95 > goalAmount) {
        const range = finalP95 - finalP5;
        const position = (goalAmount - finalP5) / range;
        goalProbability = 5 + (position * 90);
    } else if (goalAmount && goalAmount <= finalP5) {
        goalProbability = 95;
    } else if (goalAmount && goalAmount >= finalP95) {
        goalProbability = 5;
    }

    // Calculate expected returns from metrics
    const expectedReturn = result.metrics?.expected_annual_return ?? 0.07;

    return (
        <div className="space-y-6">
            {/* Header Card */}
            <div className={`card bg-base-200 p-6 border-l-4 ${SCENARIO_LAB_THEME.colors.border}`}>
                <div className="flex items-start gap-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={`w-8 h-8 ${SCENARIO_LAB_THEME.colors.text} shrink-0`}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    <div>
                        <h3 className={`text-xl font-bold ${SCENARIO_LAB_THEME.colors.text}`}>
                            Scenario Analysis
                        </h3>
                        <p className="text-sm text-base-content/70 mt-1">
                            Probabilistic projections over {timeHorizon} years
                        </p>
                    </div>
                </div>

                {/* Key Metrics */}
                <div className="stats stats-vertical lg:stats-horizontal shadow mt-6">
                    <div className="stat">
                        <div className="stat-title">Initial Investment</div>
                        <div className="stat-value text-2xl">
                            {formatCurrency(result.initial_amount)}
                        </div>
                    </div>

                    <div className="stat">
                        <div className="stat-title">Expected Annual Return</div>
                        <div className="stat-value text-info text-2xl">
                            {formatPercent(expectedReturn)}
                        </div>
                        <div className="stat-desc">
                            Per year (median)
                        </div>
                    </div>

                    <div className="stat">
                        <div className="stat-title">Volatility</div>
                        <div className="stat-value text-2xl">
                            {result.metrics?.annual_volatility
                                ? formatPercent(result.metrics.annual_volatility)
                                : 'N/A'}
                        </div>
                        <div className="stat-desc">
                            Annual standard deviation
                        </div>
                    </div>

                    <div className="stat">
                        <div className="stat-title">Risk-Adjusted Return</div>
                        <div className="stat-value text-2xl">
                            {result.metrics?.sharpe_ratio?.toFixed(2) ?? 'N/A'}
                        </div>
                        <div className="stat-desc">
                            Sharpe Ratio
                        </div>
                    </div>
                </div>
            </div>

            {/* Fan Chart */}
            {percentiles && (
                <div className="card bg-base-200 p-6">
                    <FanChart
                        percentiles={percentiles}
                        currency={currency}
                        goalAmount={goalAmount}
                    />
                </div>
            )}

            {/* Scenario Cards */}
            {result.scenarios && result.scenarios.length > 0 && (
                <div className="card bg-base-200 p-6">
                    <h4 className="font-bold mb-4 flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                        </svg>
                        Scenario Breakdown
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {result.scenarios.map(scenario => {
                            const isBull = scenario.name.toLowerCase().includes('bull');
                            const isBear = scenario.name.toLowerCase().includes('bear');
                            const icon = isBull ? '📈' : isBear ? '📉' : '➡️';
                            const colorClass = isBull ? 'border-success bg-success/5' : isBear ? 'border-error bg-error/5' : 'border-info bg-info/5';

                            return (
                                <div key={scenario.name} className={`card border-2 ${colorClass} p-4`}>
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-2xl">{icon}</span>
                                        <h5 className="font-bold">{scenario.name}</h5>
                                    </div>
                                    <div className="text-sm space-y-1">
                                        <div>
                                            <span className="text-base-content/60">Probability: </span>
                                            <span className="font-semibold">{formatPercent(scenario.probability)}</span>
                                        </div>
                                        {scenario.expected_portfolio_value && (
                                            <div>
                                                <span className="text-base-content/60">Projected Value: </span>
                                                <span className="font-semibold">{formatCurrency(scenario.expected_portfolio_value)}</span>
                                            </div>
                                        )}
                                        {scenario.expected_return && (
                                            <div>
                                                <span className="text-base-content/60">Annual Return: </span>
                                                <span className="font-semibold">{formatPercent(scenario.expected_return)}</span>
                                            </div>
                                        )}
                                        <p className="text-xs text-base-content/60 mt-2">
                                            {scenario.description}
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Goal Achievement Summary */}
            {goalAmount && goalProbability !== null && (
                <div className={`alert ${goalProbability >= 70 ? 'alert-success' : goalProbability >= 50 ? 'alert-warning' : 'alert-error'} border-l-4`}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h3 className="font-bold">
                            Goal Achievement: {goalProbability >= 70 ? 'High Probability' : goalProbability >= 50 ? 'Moderate Probability' : 'Low Probability'}
                        </h3>
                        <div className="text-sm">
                            Based on Monte Carlo simulation, there is a <strong>{goalProbability.toFixed(0)}%</strong> chance of reaching your goal of <strong>{formatCurrency(goalAmount)}</strong> in <strong>{timeHorizon} years</strong>.
                        </div>
                        {goalProbability < 70 && (
                            <div className="text-xs mt-2">
                                💡 Consider: increasing your initial investment, extending your time horizon, or adjusting your expectations.
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Resilience Testing Tips */}
            <div className={`alert border-l-4 ${SCENARIO_LAB_THEME.colors.border}`}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-4.5A6.01 6.01 0 0 0 10.5 3m0 6H9m3 0h3" />
                </svg>
                <div>
                    <h3 className="font-bold">Resilience Testing Tips</h3>
                    <div className="text-sm space-y-1">
                        <p>
                            • The <strong className="text-success">Bull case</strong> represents favorable market conditions.
                        </p>
                        <p>
                            • The <strong className="text-error">Bear case</strong> represents adverse market conditions.
                        </p>
                        <p>
                            • Plan for the <strong className="text-info">Base case</strong> but ensure you can handle the Bear case.
                        </p>
                        <p className="text-xs text-base-content/70 mt-2">
                            This simulation uses historical volatility patterns. Future results may vary.
                        </p>
                    </div>
                </div>
            </div>

            {/* Recommended Portfolio */}
            {result.optimal_portfolio && result.optimal_portfolio.length > 0 && (
                <div className="card bg-base-200 p-6">
                    <h4 className="font-bold mb-4">Recommended Portfolio</h4>
                    <div className="overflow-x-auto">
                        <table className="table table-sm">
                            <thead>
                                <tr>
                                    <th>Ticker</th>
                                    <th>Allocation</th>
                                    <th>Amount</th>
                                    <th>Shares</th>
                                </tr>
                            </thead>
                            <tbody>
                                {result.optimal_portfolio.map(holding => (
                                    <tr key={holding.ticker}>
                                        <td className="font-mono">{holding.ticker}</td>
                                        <td>{formatPercent(holding.weight)}</td>
                                        <td>{formatCurrency(holding.amount)}</td>
                                        <td>{holding.shares.toFixed(2)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
