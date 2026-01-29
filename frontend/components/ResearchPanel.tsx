'use client';

import React, { useState } from 'react';
import { runResearchOnPlan, ResearchOnPlanResponse } from '../lib/api-client';

interface ResearchPanelProps {
    planId: string | null;
    planName: string | null;
    followUpSuggestions?: string[] | null;
    onResearchComplete?: (result: ResearchOnPlanResponse) => void;
}

export default function ResearchPanel({ planId, planName, followUpSuggestions, onResearchComplete }: ResearchPanelProps) {
    const [customQuery, setCustomQuery] = useState('');
    const [isRunning, setIsRunning] = useState(false);
    const [result, setResult] = useState<ResearchOnPlanResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);

    const handleRunResearch = async (query: string) => {
        if (!planId) {
            setError('No plan selected');
            return;
        }

        if (!query.trim()) {
            setError('Please enter a research question');
            return;
        }

        setIsRunning(true);
        setError(null);
        setResult(null);
        setSelectedSuggestion(query);

        try {
            const response = await runResearchOnPlan(planId, { query: query.trim() });
            setResult(response);
            onResearchComplete?.(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to run research');
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <div className="card bg-base-100 shadow-xl border border-base-200">
            <div className="card-body">
                <h2 className="card-title">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                    </svg>
                    Research Agent
                    {planName && <span className="text-sm font-normal text-base-content/60">on {planName}</span>}
                </h2>

                {!planId ? (
                    <div className="flex flex-col items-center justify-center p-8 text-center text-base-content/60">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15.042 21.672L13.684 16.6m0 0l-2.51 2.225.569-9.47 5.227 7.917-3.286-.672zM12 2.25V4.5m5.834.166l-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243l-1.59-1.59" />
                        </svg>
                        <p className="mt-4">Select a plan to run research analysis</p>
                    </div>
                ) : (
                    <>
                        {/* Follow-up Suggestions */}
                        {followUpSuggestions && followUpSuggestions.length > 0 && (
                            <div className="space-y-3">
                                <h3 className="text-sm font-semibold text-base-content/70 uppercase tracking-wide">
                                    Suggested Research
                                </h3>
                                <div className="space-y-2">
                                    {followUpSuggestions.map((suggestion, idx) => (
                                        <div
                                            key={idx}
                                            className={`card bg-base-200 border cursor-pointer transition-all ${
                                                selectedSuggestion === suggestion
                                                    ? 'border-primary'
                                                    : 'border-transparent hover:border-base-content/20'
                                            }`}
                                        >
                                            <div className="card-body p-3">
                                                <div className="flex justify-between items-start gap-2">
                                                    <p className="text-sm flex-1">{suggestion}</p>
                                                    <button
                                                        onClick={() => handleRunResearch(suggestion)}
                                                        disabled={isRunning}
                                                        className="btn btn-primary btn-sm"
                                                    >
                                                        {isRunning && selectedSuggestion === suggestion ? (
                                                            <>
                                                                <span className="loading loading-spinner loading-xs"></span>
                                                                Analyzing...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                                                                </svg>
                                                                Analyze
                                                            </>
                                                        )}
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Custom Query Input */}
                        <div className="divider text-xs">OR ASK A CUSTOM QUESTION</div>

                        <div className="form-control">
                            <label className="label">
                                <span className="label-text">Your Question</span>
                            </label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={customQuery}
                                    onChange={(e) => setCustomQuery(e.target.value)}
                                    className="input input-bordered flex-1"
                                    placeholder="e.g., What happens if there's a recession?"
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter' && !isRunning) {
                                            handleRunResearch(customQuery);
                                        }
                                    }}
                                    disabled={isRunning}
                                />
                                <button
                                    onClick={() => handleRunResearch(customQuery)}
                                    disabled={isRunning || !customQuery.trim()}
                                    className="btn btn-primary"
                                >
                                    {isRunning ? (
                                        <span className="loading loading-spinner loading-sm"></span>
                                    ) : (
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Error Display */}
                        {error && (
                            <div className="alert alert-error">
                                <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{error}</span>
                                <button onClick={() => setError(null)} className="btn btn-ghost btn-xs">✕</button>
                            </div>
                        )}

                        {/* Research Results */}
                        {result && (
                            <div className="space-y-4 mt-4">
                                <div className="alert alert-success">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <span>Research completed! Run ID: {result.run_id}</span>
                                </div>

                                {/* Summary */}
                                <div className="card bg-base-200 border border-base-300">
                                    <div className="card-body p-4">
                                        <h4 className="font-semibold text-sm mb-2">Summary</h4>
                                        <p className="text-sm whitespace-pre-wrap">{result.summary}</p>
                                    </div>
                                </div>

                                {/* New Follow-up Suggestions */}
                                {result.follow_up_suggestions && result.follow_up_suggestions.length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="font-semibold text-sm">Follow-up Questions</h4>
                                        {result.follow_up_suggestions.map((suggestion, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => {
                                                    setCustomQuery(suggestion);
                                                    handleRunResearch(suggestion);
                                                }}
                                                className="w-full text-left btn btn-ghost btn-sm justify-start h-auto py-2 px-3"
                                            >
                                                <span className="text-sm">{suggestion}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
