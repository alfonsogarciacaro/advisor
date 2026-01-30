'use client';

import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import { BacktestResult } from '../lib/api-client';
import { getHistoricalEvents } from '../lib/historical-events';

interface BacktestResultsProps {
    result: BacktestResult;
    currency?: string;
}

export default function BacktestResults({ result, currency = 'USD' }: BacktestResultsProps) {
    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    };

    const formatPercent = (value: number | null | undefined) => {
        if (value === null || value === undefined) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 1,
            maximumFractionDigits: 1,
        }).format(value);
    };

    // Prepare chart data
    const chartData = result.trajectory.map(t => {
        const benchmarkPoint = result.benchmark_trajectory.find(b => b.date === t.date);
        return {
            date: new Date(t.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
            portfolio: t.value,
            benchmark: benchmarkPoint?.value || null
        };
    });

    const historicalEvents = result.start_date && result.end_date
        ? getHistoricalEvents(result.start_date, result.end_date)
        : [];

    return (
        <div className="card bg-base-200 p-6">
            <h3 className="text-xl font-bold mb-6">📊 Backtest Results</h3>

            {/* Tax Alert if applicable */}
            {result.capital_gains_tax && result.capital_gains_tax > 0 && (
                <div className="alert alert-warning mb-6">
                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                        <h3 className="font-bold">Tax Impact Applied</h3>
                        <div className="text-sm">
                            {result.account_type && result.account_type !== 'taxable'
                                ? `Using ${result.account_type.replace('_', ' ')} account with ${formatPercent(result.metrics.tax_rate || 0)} tax rate`
                                : `${formatPercent(result.metrics.tax_rate || 0)} capital gains tax applied`
                            }
                        </div>
                        <div className="text-xs mt-1">
                            Consider tax-advantaged accounts (NISA/iDeCo) for better after-tax returns.
                        </div>
                    </div>
                </div>
            )}

            {/* Key Metrics */}
            <div className="stats stats-vertical lg:stats-horizontal shadow mb-6">
                <div className="stat">
                    <div className="stat-title">Final Value</div>
                    <div className="stat-value text-primary text-2xl">
                        {formatCurrency(result.metrics.final_value)}
                    </div>
                    <div className="stat-desc">
                        {formatPercent(result.metrics.total_return)} total return
                    </div>
                    {result.metrics.pre_tax_total_return !== undefined &&
                         result.metrics.pre_tax_total_return !== result.metrics.total_return && (
                        <div className="stat-desc text-error">
                            {formatPercent(result.metrics.pre_tax_total_return)} pre-tax
                        </div>
                    )}
                </div>

                <div className="stat">
                    <div className="stat-title">Worst Case (Max Drawdown)</div>
                    <div className="stat-value text-error text-2xl">
                        {formatPercent(result.metrics.max_drawdown)}
                    </div>
                    <div className="stat-desc">
                        {result.metrics.recovery_days
                            ? `Recovered in ${Math.floor(result.metrics.recovery_days / 30)} months`
                            : 'Never fully recovered'
                        }
                    </div>
                </div>

                <div className="stat">
                    <div className="stat-title">Annualized Return</div>
                    <div className="stat-value text-2xl">
                        {formatPercent(result.metrics.cagr)}
                    </div>
                    <div className="stat-desc">
                        Per year (CAGR)
                    </div>
                </div>

                <div className="stat">
                    <div className="stat-title">Risk-Adjusted Return</div>
                    <div className="stat-value text-2xl">
                        {result.metrics.sharpe_ratio.toFixed(2)}
                    </div>
                    <div className="stat-desc">
                        Sharpe Ratio
                    </div>
                </div>
            </div>

            {/* Chart */}
            <div className="h-96 mb-6">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            tickFormatter={(value) => formatCurrency(value)}
                        />
                        <Tooltip
                            formatter={(value: number) => formatCurrency(value)}
                            labelFormatter={(label) => `Date: ${label}`}
                        />
                        <Legend />

                        {/* Portfolio */}
                        <Line
                            type="monotone"
                            dataKey="portfolio"
                            stroke="#2563eb"
                            strokeWidth={2}
                            name="Your Portfolio"
                            dot={false}
                        />

                        {/* Benchmark */}
                        <Line
                            type="monotone"
                            dataKey="benchmark"
                            stroke="#94a3b8"
                            strokeDasharray="5 5"
                            strokeWidth={2}
                            name="Benchmark (60/40)"
                            dot={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Historical Event Markers */}
            {historicalEvents.length > 0 && (
                <div className="mb-6">
                    <h4 className="font-bold mb-2">📌 Key Historical Events</h4>
                    <div className="flex flex-wrap gap-2">
                        {historicalEvents.map(event => (
                            <div key={event.date} className="badge badge-outline badge-lg p-4">
                                <span className="text-xl mr-2">{event.icon}</span>
                                <div className="text-left">
                                    <div className="font-semibold">{event.name}</div>
                                    <div className="text-xs">{new Date(event.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Educational Insights */}
            <div className="alert alert-info">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                    <h3 className="font-bold">How to Interpret This</h3>
                    <div className="text-sm space-y-1">
                        <p>
                            • If you invested on <strong>
                                {result.start_date && new Date(result.start_date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                            </strong>, you would have{' '}
                            <strong className={result.metrics.total_return >= 0 ? 'text-success' : 'text-error'}>
                                {result.metrics.total_return >= 0 ? 'gained' : 'lost'}
                                {formatPercent(Math.abs(result.metrics.total_return))}
                            </strong> by today.
                        </p>
                        <p>
                            • The worst drop was <strong>{formatPercent(Math.abs(result.metrics.max_drawdown))}</strong>.
                        </p>
                        <p>
                            • {result.metrics.recovery_days
                                ? `It took ${Math.floor(result.metrics.recovery_days / 30)} months to recover from the worst drop.`
                                : 'The portfolio never fully recovered from its worst drop.'}
                        </p>
                        {result.metrics.total_return >= 0 ? (
                            <p className="text-success font-semibold">
                                ✅ This strategy would have grown your wealth over this period.
                            </p>
                        ) : (
                            <p className="text-warning">
                                ⚠️ Past performance doesn't guarantee future results. Consider extending the time period.
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
