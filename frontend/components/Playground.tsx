'use client';

import React, { useState } from 'react';
import HistoricalAudit from './HistoricalAudit';
import ScenarioLab from './ScenarioLab';

type Mode = 'historical' | 'future';

interface PlaygroundProps {
    initialAmount?: number;
    currency?: string;
}

export default function Playground({
    initialAmount = 10000,
    currency = 'USD'
}: PlaygroundProps) {
    const [mode, setMode] = useState<Mode>('historical');

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold mb-2">🎮 Strategy Playground</h2>
                <p className="text-base-content/70">
                    Test investment strategies through historical fear testing and future scenario planning.
                </p>
            </div>

            {/* Mode Selector */}
            <div role="tablist" className="tabs tabs-boxed bg-base-200">
                <button
                    role="tab"
                    className={`tab ${mode === 'historical' ? 'tab-active' : ''}`}
                    onClick={() => setMode('historical')}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>
                    Historical Audit
                </button>
                <button
                    role="tab"
                    className={`tab ${mode === 'future' ? 'tab-active' : ''}`}
                    onClick={() => setMode('future')}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    Scenario Lab
                </button>
            </div>

            {/* Content */}
            {mode === 'historical' ? (
                <HistoricalAudit initialAmount={initialAmount} currency={currency} />
            ) : (
                <ScenarioLab initialAmount={initialAmount} currency={currency} />
            )}
        </div>
    );
}
