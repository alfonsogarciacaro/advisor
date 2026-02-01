'use client';

import React, { useState, useEffect } from 'react';
import { optimizePortfolio, getOptimizationStatus, OptimizationResult } from '../lib/api-client';
import { listStrategies, StrategyTemplate } from '../lib/api-client';
import { SCENARIO_LAB_THEME } from '../lib/theme-constants';
import ScenarioLabResults from './ScenarioLabResults';
import { ACCOUNT_TYPES } from '../lib/historical-events';

interface ScenarioLabProps {
    initialAmount?: number;
    currency?: string;
}

export default function ScenarioLab({
    initialAmount = 10000,
    currency = 'USD'
}: ScenarioLabProps) {
    const [amount, setAmount] = useState(initialAmount);
    const [timeHorizon, setTimeHorizon] = useState(10); // years
    const [goalAmount, setGoalAmount] = useState<number | undefined>();
    const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
    const [accountType, setAccountType] = useState('taxable');
    const [loading, setLoading] = useState(false);
    const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
    const [strategies, setStrategies] = useState<StrategyTemplate[]>([]);
    const [strategiesLoading, setStrategiesLoading] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

    // Load strategies on mount
    useEffect(() => {
        setStrategiesLoading(true);
        listStrategies()
            .then(setStrategies)
            .catch(err => console.error('Failed to load strategies:', err))
            .finally(() => setStrategiesLoading(false));
    }, []);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        };
    }, [pollInterval]);

    // Update goal amount suggestion based on amount and time horizon
    useEffect(() => {
        // Suggest a goal (e.g., double the money over the time period)
        const annualReturn = 0.07; // 7% assumption
        const suggestedGoal = amount * Math.pow(1 + annualReturn, timeHorizon);
        if (!goalAmount) {
            setGoalAmount(Math.round(suggestedGoal / 1000) * 1000); // Round to nearest 1000
        }
    }, [amount, timeHorizon]);

    const runSimulation = async () => {
        setLoading(true);
        setOptimizationResult(null);

        try {
            // For future simulation, we don't pass historical_date
            const response = await optimizePortfolio(
                amount,
                currency,
                undefined, // No historical_date for future simulation
                selectedStrategy || undefined,
                accountType
            );

            setJobId(response.job_id);

            // Poll for result
            const interval = setInterval(async () => {
                try {
                    const status = await getOptimizationStatus(response.job_id);

                    if (status.status === 'completed' || status.status === 'failed') {
                        clearInterval(interval);
                        setPollInterval(null);
                        setLoading(false);

                        if (status.status === 'completed') {
                            setOptimizationResult(status);
                        } else if (status.error) {
                            console.error('Simulation failed:', status.error);
                        }
                    }
                } catch (err) {
                    console.error('Polling error:', err);
                    clearInterval(interval);
                    setPollInterval(null);
                    setLoading(false);
                }
            }, 2000);

            setPollInterval(interval);
        } catch (error) {
            console.error('Failed to start simulation:', error);
            setLoading(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
        }).format(value);
    };

    const selectedStrategyData = strategies.find(s => s.strategy_id === selectedStrategy);

    return (
        <div className="space-y-6">
            <div className={`card bg-base-200 p-6 border-l-4 ${SCENARIO_LAB_THEME.colors.border}`}>
                <div className="flex items-start gap-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={`w-8 h-8 ${SCENARIO_LAB_THEME.colors.text} shrink-0`}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    <div className="flex-1">
                        <h3 className={`text-xl font-bold mb-1 ${SCENARIO_LAB_THEME.colors.text}`}>
                            {SCENARIO_LAB_THEME.heading}
                        </h3>
                        <p className={`text-sm font-semibold ${SCENARIO_LAB_THEME.colors.text}`}>
                            {SCENARIO_LAB_THEME.subheading}
                        </p>
                        <p className="text-sm text-base-content/70 mt-2">
                            {SCENARIO_LAB_THEME.description}
                        </p>
                    </div>
                </div>

                {/* Investment Amount */}
                <div className="form-control mt-6">
                    <label htmlFor="investment-amount" className="label">Investment Amount</label>
                    <input
                        id="investment-amount"
                        type="number"
                        className="input input-bordered"
                        value={amount}
                        onChange={(e) => setAmount(Number(e.target.value))}
                        min={100}
                    />
                </div>

                {/* Time Horizon Slider */}
                <div className="form-control mt-4">
                    <label className="label">
                        <span className="label-text font-semibold">Time Horizon</span>
                        <span className="label-text-alt">{timeHorizon} years</span>
                    </label>
                    <input
                        type="range"
                        min="1"
                        max="30"
                        value={timeHorizon}
                        onChange={(e) => setTimeHorizon(Number(e.target.value))}
                        className="range range-info"
                    />
                    <div className="flex justify-between text-xs text-base-content/60 px-2 mt-1">
                        <span>1 year</span>
                        <span>10 years</span>
                        <span>30 years</span>
                    </div>
                </div>

                {/* Goal Amount (Optional) */}
                <div className="form-control mt-4">
                    <label htmlFor="goal-amount" className="label">
                        Goal Amount (Optional)
                        <span className="label-text-alt">For probability calculation</span>
                    </label>
                    <input
                        id="goal-amount"
                        type="number"
                        className="input input-bordered"
                        value={goalAmount || ''}
                        onChange={(e) => setGoalAmount(e.target.value ? Number(e.target.value) : undefined)}
                        placeholder="e.g., 20000"
                    />
                    <label className="label">
                        <span className="label-text-alt text-info">
                            💡 We'll calculate the probability of reaching this goal
                        </span>
                    </label>
                </div>

                {/* Account Type Selector */}
                <div className="form-control mt-4">
                    <label className="label">Account Type (affects taxes)</label>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                        {ACCOUNT_TYPES.map(account => (
                            <button
                                key={account.value}
                                className={`btn btn-sm ${accountType === account.value ? 'btn-info' : 'btn-outline'}`}
                                onClick={() => setAccountType(account.value)}
                            >
                                <span className="text-lg mr-1">{account.icon}</span>
                                <span className="text-xs">{account.label}</span>
                            </button>
                        ))}
                    </div>
                    <label className="label">
                        <span className="label-text-alt text-info">
                            💡 NISA accounts have 0% capital gains tax
                        </span>
                    </label>
                </div>

                {/* Strategy Selector */}
                <div className="form-control mt-4">
                    <label className="label">Strategy Template (Optional)</label>
                    {strategiesLoading ? (
                        <div className="flex items-center gap-2">
                            <span className="loading loading-spinner loading-sm"></span>
                            <span className="text-sm">Loading strategies...</span>
                        </div>
                    ) : (
                        <div className="flex gap-2">
                            <select
                                className="select select-bordered flex-1"
                                value={selectedStrategy || ''}
                                onChange={(e) => setSelectedStrategy(e.target.value || null)}
                            >
                                <option value="">Custom Constraints (None)</option>
                                {strategies.map(strategy => (
                                    <option key={strategy.strategy_id} value={strategy.strategy_id}>
                                        {strategy.icon} {strategy.name} ({strategy.risk_level})
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                    {selectedStrategyData && (
                        <label className="label">
                            <span className="label-text-alt">
                                📋 {selectedStrategyData.description}
                            </span>
                        </label>
                    )}
                </div>

                {/* Selected Strategy Summary */}
                {selectedStrategyData && (
                    <div className={`alert mt-4 border-l-4 ${SCENARIO_LAB_THEME.colors.border}`}>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                            <h3 className="font-bold">Selected: {selectedStrategyData.name}</h3>
                            <p className="text-sm">{selectedStrategyData.description}</p>
                        </div>
                    </div>
                )}

                {/* Run Button */}
                <button
                    className="btn btn-info btn-block mt-6"
                    onClick={runSimulation}
                    disabled={loading}
                    aria-label="Run Simulation"
                >
                    {loading ? (
                        <>
                            <span className="loading loading-spinner"></span>
                            Running Simulation...
                        </>
                    ) : (
                        <>
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                            </svg>
                            Run Simulation
                        </>
                    )}
                </button>
            </div>

            {/* Results */}
            {optimizationResult && (
                <ScenarioLabResults
                    result={optimizationResult}
                    currency={currency}
                    goalAmount={goalAmount}
                    timeHorizon={timeHorizon}
                />
            )}
        </div>
    );
}
