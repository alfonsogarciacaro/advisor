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
import DrawdownChart from './charts/DrawdownChart';

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
        <div className="card bg-base-200 p-6 border-l-4 border-error">
            <div className="flex items-start gap-4 mb-6">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-error shrink-0">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <div>
                    <h3 className="text-xl font-bold text-error">Fear Test Results</h3>
                    <p className="text-sm text-base-content/70 mt-1">
                        Would you have sold? Be honest with yourself.
                    </p>
                </div>
            </div>

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

            {/* Key Metrics - Max Drawdown First */}
            <div className="stats stats-vertical lg:stats-horizontal shadow mb-6">
                {/* Max Drawdown - Primary Metric for Fear Testing */}
                <div className="stat">
                    <div className="stat-title text-error font-semibold">Max Drawdown (Fear Test)</div>
                    <div className="stat-value text-error text-3xl">
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

            {/* Drawdown Chart - Fear Testing */}
            <div className="mb-6">
                <DrawdownChart result={result} currency={currency} />
            </div>

            {/* Portfolio Value Chart */}
            <div className="h-80 mb-6">
                <h4 className="font-bold mb-4 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
                    </svg>
                    Portfolio Value Over Time
                </h4>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            tickFormatter={(value) => formatCurrency(value ?? 0)}
                        />
                        <Tooltip
                            formatter={(value: number | undefined) => formatCurrency(value ?? 0)}
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

            {/* Educational Insights - Fear Testing Focus */}
            <div className={`alert border-l-4 border-error`}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                    <h3 className="font-bold">Fear Testing Analysis</h3>
                    <div className="text-sm space-y-1">
                        <p>
                            If you invested on <strong>
                                {result.start_date && new Date(result.start_date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                            </strong>, your portfolio would have dropped <strong className="text-error">{formatPercent(Math.abs(result.metrics.max_drawdown))}</strong> at its worst point.
                        </p>
                        <p className="text-error font-semibold">
                            ⚠️ Would you have sold?
                        </p>
                        <p className="text-xs text-base-content/70">
                            Most investors panic and sell at the bottom. If you would have sold during this drawdown, you may need to reduce your risk exposure.
                        </p>
                        <p>
                            {result.metrics.recovery_days
                                ? `It took ${Math.floor(result.metrics.recovery_days / 30)} months to recover from the worst drop.`
                                : 'The portfolio never fully recovered from its worst drop.'}
                        </p>
                        {result.metrics.total_return >= 0 ? (
                            <p className="text-success font-semibold">
                                ✅ Despite the drawdowns, this strategy would have grown your wealth over this period.
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
