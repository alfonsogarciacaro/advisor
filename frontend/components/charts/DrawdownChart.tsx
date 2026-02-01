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
    ReferenceLine,
} from 'recharts';
import { BacktestResult } from '../../lib/api-client';

interface DrawdownChartProps {
    result: BacktestResult;
    currency?: string;
}

export default function DrawdownChart({ result, currency = 'USD' }: DrawdownChartProps) {
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

    // Calculate drawdown from peak for each point
    const drawdownData = result.trajectory.map((t, index) => {
        const peakSoFar = Math.max(...result.trajectory.slice(0, index + 1).map(p => p.value));
        const drawdown = (peakSoFar - t.value) / peakSoFar;
        return {
            date: new Date(t.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
            value: t.value,
            peak: peakSoFar,
            drawdown: drawdown * 100, // Convert to percentage
        };
    });

    // Find the bottom point (maximum drawdown)
    const bottomPoint = drawdownData.reduce((max, point) =>
        point.drawdown > max.drawdown ? point : max, drawdownData[0]);

    // Find recovery point (next time we hit the peak after the bottom)
    const bottomIndex = drawdownData.findIndex(d => d.date === bottomPoint.date);
    const bottomPeak = bottomPoint.peak;
    let recoveryIndex = drawdownData.findIndex((d, i) =>
        i > bottomIndex && d.value >= bottomPeak);

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h4 className="font-bold text-error flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
                    </svg>
                    Drawdown Timeline
                </h4>
                <span className="text-sm text-base-content/70">
                    Peak to trough decline
                </span>
            </div>

            {/* Chart */}
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={drawdownData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            dataKey="date"
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            tickFormatter={(value) => formatPercent(value / 100)}
                            domain={[0, 'dataMax']}
                        />
                        <Tooltip
                            formatter={(value: any, name: any) => {
                                if (name === 'drawdown') {
                                    return [formatPercent((value ?? 0) / 100), 'Drawdown'];
                                }
                                return [formatCurrency(value ?? 0), name];
                            }}
                            labelFormatter={(label) => `Date: ${label}`}
                        />

                        {/* Drawdown area - red fill */}
                        <Area
                            type="monotone"
                            dataKey="drawdown"
                            stroke="#ef4444"
                            fill="#ef4444"
                            fillOpacity={0.3}
                            name="drawdown"
                        />

                        {/* Zero reference line */}
                        <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" />

                        {/* Maximum drawdown marker */}
                        <ReferenceLine
                            y={bottomPoint.drawdown}
                            stroke="#dc2626"
                            strokeWidth={2}
                            label={`Max: ${formatPercent(bottomPoint.drawdown / 100)}`}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Fear Testing Question */}
            {bottomPoint.drawdown > 10 && (
                <div className="alert alert-error border-l-4 border-error">
                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                        <h3 className="font-bold">Would you have sold?</h3>
                        <div className="text-sm">
                            At the bottom, your portfolio dropped <strong>{formatPercent(bottomPoint.drawdown / 100)}</strong>.
                            {recoveryIndex >= 0 ? (
                                <span> It took <strong>{Math.floor((recoveryIndex - bottomIndex) / 12)} years</strong> to recover.</span>
                            ) : (
                                <span> The portfolio never fully recovered.</span>
                            )}
                        </div>
                        <div className="text-xs mt-2 opacity-80">
                            This is the fear test. Be honest with yourself.
                        </div>
                    </div>
                </div>
            )}

            {/* Recovery Info */}
            {recoveryIndex >= 0 && (
                <div className="flex items-center gap-2 text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-success">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                    </svg>
                    <span>
                        Recovery took <strong>{recoveryIndex - bottomIndex} months</strong> from peak
                    </span>
                </div>
            )}
        </div>
    );
}
