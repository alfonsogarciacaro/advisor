'use client';

import React, { useState } from 'react';
import HistoricalReplay from './HistoricalReplay';

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
                    Test different investment strategies using historical data and see how they would have performed.
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
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0v-4.5M4.5 15l7.5-7.5M12 21V9m6 0l6-6M6 15H7.5a4.5 4.5 0 01-.48-3.937A4.502 4.502 0 014.5 15v1" />
                    </svg>
                    Historical Replay
                </button>
                <button
                    role="tab"
                    className={`tab ${mode === 'future' ? 'tab-active' : ''}`}
                    onClick={() => setMode('future')}
                    disabled
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 mr-2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    Future Simulation
                    <span className="badge badge-xs badge-neutral ml-2">Coming Soon</span>
                </button>
            </div>

            {/* Content */}
            {mode === 'historical' ? (
                <HistoricalReplay initialAmount={initialAmount} currency={currency} />
            ) : (
                <div className="alert alert-info">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Future simulation coming soon! For now, try historical replay to see how strategies would have performed.</span>
                </div>
            )}
        </div>
    );
}
