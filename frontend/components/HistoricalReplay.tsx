'use client';

import React, { useState, useEffect } from 'react';
import { optimizePortfolio, getOptimizationStatus, BacktestResult, OptimizationResult } from '../lib/api-client';
import { listStrategies, StrategyTemplate } from '../lib/api-client';
import { PRESET_PERIODS, ACCOUNT_TYPES } from '../lib/historical-events';
import BacktestResults from './BacktestResults';

interface HistoricalReplayProps {
    initialAmount?: number;
    currency?: string;
}

export default function HistoricalReplay({
    initialAmount = 10000,
    currency = 'USD'
}: HistoricalReplayProps) {
    const [startDate, setStartDate] = useState('2020-01-01');
    const [amount, setAmount] = useState(initialAmount);
    const [loading, setLoading] = useState(false);
    const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
    const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
    const [accountType, setAccountType] = useState('taxable');
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

    const runBacktest = async () => {
        setLoading(true);
        setBacktestResult(null);

        try {
            const response = await optimizePortfolio(
                amount,
                currency,
                false, // fast mode
                startDate,
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

                        if (status.backtest_result) {
                            setBacktestResult(status.backtest_result);
                        } else if (status.status === 'failed' && status.error) {
                            console.error('Backtest failed:', status.error);
                        } else {
                            console.warn('Backtest completed but no backtest_result found');
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
            console.error('Failed to start backtest:', error);
            setLoading(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
        }).format(value);
    };

    const generateRandomPortfolio = () => {
        if (strategies.length === 0) return;

        // Random strategy
        const randomIndex = Math.floor(Math.random() * strategies.length);
        const randomStrategy = strategies[randomIndex];
        setSelectedStrategy(randomStrategy.strategy_id);

        // Random account type
        const accountTypes = ['taxable', 'nisa_growth', 'nisa_general', 'ideco'];
        setAccountType(accountTypes[Math.floor(Math.random() * accountTypes.length)]);

        // Random amount
        const amounts = [10000, 50000, 100000, 500000, 1000000];
        setAmount(amounts[Math.floor(Math.random() * amounts.length)]);
    };

    const selectedStrategyData = strategies.find(s => s.strategy_id === selectedStrategy);

    return (
        <div className="space-y-6">
            <div className="card bg-base-200 p-6">
                <h3 className="text-xl font-bold mb-4">🕰️ Historical Replay</h3>
                <p className="text-sm text-base-content/70 mb-6">
                    See how this strategy would have performed starting from a specific date in the past.
                </p>

                {/* Preset Periods */}
                <div className="mb-4">
                    <label className="label">Quick Select Historical Period</label>
                    <div className="flex flex-wrap gap-2">
                        {PRESET_PERIODS.map(preset => (
                            <button
                                key={preset.date}
                                className={`btn btn-sm ${startDate === preset.date ? 'btn-primary' : 'btn-outline'}`}
                                onClick={() => setStartDate(preset.date)}
                                title={preset.description}
                            >
                                <span className="text-lg mr-1">{preset.icon}</span>
                                {preset.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Custom Date Picker */}
                <div className="form-control mb-4">
                    <label htmlFor="start-date" className="label">Or Pick Custom Start Date</label>
                    <input
                        id="start-date"
                        type="date"
                        className="input input-bordered"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        max={new Date().toISOString().split('T')[0]}
                    />
                </div>

                {/* Amount Input */}
                <div className="form-control mb-4">
                    <label htmlFor="investment-amount" className="label">Investment Amount</label>
                    <input
                        id="investment-amount"
                        type="number"
                        className="input input-bordered"
                        value={amount}
                        onChange={(e) => setAmount(Number(e.target.value))}
                        min={100}
                    />
                    <label className="label">
                        <span className="label-text-alt text-info">
                            💡 Starting amount on {new Date(startDate).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                        </span>
                    </label>
                </div>

                {/* Account Type Selector */}
                <div className="form-control mb-4">
                    <label className="label">Account Type (affects taxes)</label>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                        {ACCOUNT_TYPES.map(account => (
                            <button
                                key={account.value}
                                className={`btn btn-sm ${accountType === account.value ? 'btn-primary' : 'btn-outline'}`}
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
                <div className="form-control mb-6">
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
                            <button
                                onClick={generateRandomPortfolio}
                                className="btn btn-outline"
                                disabled={loading || strategies.length === 0}
                                title="Generate a random portfolio for exploration"
                            >
                                🎲 Random
                            </button>
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
                    <div className="alert alert-info mb-6">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                            <h3 className="font-bold">Selected: {selectedStrategyData.name}</h3>
                            <p className="text-sm">{selectedStrategyData.description}</p>
                            <p className="text-xs mt-1">
                                Risk Level: <span className="badge badge-neutral">{selectedStrategyData.risk_level}</span>
                            </p>
                        </div>
                    </div>
                )}

                {/* Tax Impact Info */}
                {accountType !== 'taxable' && (
                    <div className="alert alert-success mb-6">
                        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                            <h3 className="font-bold">Tax-Advantaged Account Selected</h3>
                            <p className="text-sm">
                                Using <strong>{accountType.replace('_', ' ')}</strong> means <strong>0% capital gains tax</strong>!
                                This could save you thousands compared to a taxable account.
                            </p>
                        </div>
                    </div>
                )}

                {/* Run Button */}
                <button
                    className="btn btn-primary btn-block"
                    onClick={runBacktest}
                    disabled={loading}
                    aria-label="Run Backtest"
                >
                    {loading ? (
                        <>
                            <span className="loading loading-spinner"></span>
                            Running Backtest...
                        </>
                    ) : (
                        <>
                            <span className="text-lg mr-2">▶️</span>
                            Run Backtest
                        </>
                    )}
                </button>
            </div>

            {/* Results */}
            {backtestResult && (
                <BacktestResults result={backtestResult} currency={currency} />
            )}
        </div>
    );
}
