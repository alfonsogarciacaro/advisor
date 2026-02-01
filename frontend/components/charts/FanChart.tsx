'use client';

import React from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';

export interface MonteCarloPercentiles {
    p5: Array<{ date: string; value: number }>;
    p25: Array<{ date: string; value: number }>;
    p50: Array<{ date: string; value: number }>;
    p75: Array<{ date: string; value: number }>;
    p95: Array<{ date: string; value: number }>;
}

interface FanChartProps {
    percentiles: MonteCarloPercentiles;
    currency?: string;
    goalAmount?: number;
}

export default function FanChart({ percentiles, currency = 'USD', goalAmount }: FanChartProps) {
    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    };

    // Merge all percentile data into a single array
    const chartData = percentiles.p5.map((point, index) => ({
        date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        p5: point.value,
        p25: percentiles.p25[index]?.value ?? point.value,
        p50: percentiles.p50[index]?.value ?? point.value,
        p75: percentiles.p75[index]?.value ?? point.value,
        p95: percentiles.p95[index]?.value ?? point.value,
    }));

    // Calculate probability of reaching goal
    const finalP50 = percentiles.p50[percentiles.p50.length - 1]?.value ?? 0;
    const finalP5 = percentiles.p5[percentiles.p5.length - 1]?.value ?? 0;
    const finalP95 = percentiles.p95[percentiles.p95.length - 1]?.value ?? 0;

    // Estimate probability using normal distribution approximation
    // If goal is at p50, probability is ~50%
    let goalProbability: number | null = null;
    if (goalAmount && finalP5 < goalAmount && finalP95 > goalAmount) {
        // Linear interpolation between p5 and p95
        const range = finalP95 - finalP5;
        const position = (goalAmount - finalP5) / range;
        goalProbability = 5 + (position * 90); // p5=5%, p95=95%
    } else if (goalAmount && goalAmount <= finalP5) {
        goalProbability = 95;
    } else if (goalAmount && goalAmount >= finalP95) {
        goalProbability = 5;
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h4 className="font-bold text-info flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    Probabilistic Projection
                </h4>
                <span className="text-sm text-base-content/70">
                    Monte Carlo simulation (1000 runs)
                </span>
            </div>

            {/* Chart */}
            <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            tickFormatter={(value) => formatCurrency(value)}
                        />
                        <Tooltip
                            formatter={(value: any, name: any) => {
                                const labels: Record<string, string> = {
                                    'p95': '95th percentile (optimistic)',
                                    'p75': '75th percentile',
                                    'p50': '50th percentile (median)',
                                    'p25': '25th percentile',
                                    'p5': '5th percentile (pessimistic)',
                                };
                                return [formatCurrency(value ?? 0), labels[name] || name];
                            }}
                            labelFormatter={(label) => `Date: ${label}`}
                        />
                        <Legend />

                        {/* Goal line if provided */}
                        {goalAmount && (
                            <Area
                                type="monotone"
                                dataKey={() => goalAmount}
                                stroke="#fbbf24"
                                fill="none"
                                strokeDasharray="5 5"
                                name={`Goal: ${formatCurrency(goalAmount)}`}
                            />
                        )}

                        {/* Outer cone (5th-95th percentile) - lightest */}
                        <Area
                            type="monotone"
                            dataKey="p95"
                            stroke="#3b82f6"
                            fill="#3b82f6"
                            fillOpacity={0.05}
                            name="95th percentile"
                        />

                        {/* Second cone (25th-75th percentile) - medium */}
                        <Area
                            type="monotone"
                            dataKey="p75"
                            stroke="#3b82f6"
                            fill="#3b82f6"
                            fillOpacity={0.15}
                            name="75th percentile"
                        />

                        {/* Median line (50th percentile) - darkest */}
                        <Area
                            type="monotone"
                            dataKey="p50"
                            stroke="#2563eb"
                            fill="#2563eb"
                            fillOpacity={0.3}
                            name="50th percentile (median)"
                            strokeWidth={2}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Goal Achievement Probability */}
            {goalAmount && goalProbability !== null && (
                <div className={`alert ${goalProbability >= 70 ? 'alert-success' : goalProbability >= 50 ? 'alert-warning' : 'alert-error'}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h3 className="font-bold">
                            {goalProbability >= 70 ? 'High Confidence' : goalProbability >= 50 ? 'Moderate Confidence' : 'Low Confidence'}
                        </h3>
                        <div className="text-sm">
                            Probability of reaching <strong>{formatCurrency(goalAmount)}</strong>: <strong>{goalProbability.toFixed(0)}%</strong>
                        </div>
                        <div className="text-xs mt-1">
                            Based on Monte Carlo simulation with historical volatility
                        </div>
                    </div>
                </div>
            )}

            {/* Percentile Explanation */}
            <div className="text-xs text-base-content/60 space-y-1">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500/30 rounded"></div>
                    <span>95th percentile: Best 5% of outcomes</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500/50 rounded"></div>
                    <span>75th percentile: Better than 75% of outcomes</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-600 rounded"></div>
                    <span>50th percentile: Median outcome (most likely)</span>
                </div>
            </div>
        </div>
    );
}
