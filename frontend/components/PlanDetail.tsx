'use client';

import React, { useState } from 'react';
import { Plan, OptimizationResult, TaxAccount, AssetHolding, updatePlanPortfolio, optimizePortfolio } from '../lib/api-client';
import PortfolioOptimizer from './PortfolioOptimizer';
import ResearchPanel from './ResearchPanel';
import AccountManager from './AccountManager';
import Playground from './Playground';
import PortfolioEditor from './PortfolioEditor';
import HoldingsByAccount from './HoldingsByAccount';
import PlanSettingsModal from './PlanSettingsModal';

interface PlanDetailProps {
    plan: Plan;
    onBack: () => void;
    onPlanUpdate?: (plan: Plan) => void;
}

export default function PlanDetail({ plan, onBack, onPlanUpdate }: PlanDetailProps) {
    const [localPlan, setLocalPlan] = useState<Plan>(plan);
    const [showPortfolioEditor, setShowPortfolioEditor] = useState(false);
    const [showSettingsModal, setShowSettingsModal] = useState(false);
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const [isStartingOptimization, setIsStartingOptimization] = useState(false);

    const handleOptimize = async () => {
        const totalValue = localPlan.initial_portfolio?.reduce((sum, h) => sum + h.monetary_value, 0) || 0;

        if (totalValue <= 0) {
            alert("Please add assets (or cash) to your portfolio before optimizing.");
            return;
        }

        setIsStartingOptimization(true);
        try {
            // Start optimization with total portfolio value
            const response = await optimizePortfolio(totalValue, localPlan.base_currency || 'USD');
            setActiveJobId(response.job_id);
        } catch (error) {
            console.error('Failed to start optimization:', error);
            alert('Failed to start optimization. Please try again.');
        } finally {
            setIsStartingOptimization(false);
        }
    };

    const handleSettingsSave = async (updatedPlan: Plan) => {
        // In a real app, we would save to backend here. 
        // Assuming the parent or a context handles the actual API call updates via onPlanUpdate,
        // or we recall an API. For now, we update local state and notify parent.
        // If PlanSettingsModal calls an API, we just need to update local state.

        // Actually PlanSettingsModal prop onSave expects a Promise.
        // We can simulate saving or assume the modal passed a plan that is ready to be saved.
        // Since we don't have a direct "updatePlan" API exported in api-client (only create and specific updates),
        // we might leave the implementation hole or assume onPlanUpdate handles persistence if we pass it up.
        // However, based on implementation plan, we should probably just update local state if backend update isn't ready.
        // Wait, AccountManager inside PlanSettingsModal updates accounts.
        // PlanSettingsModal updates name/desc/etc.

        // Let's assume for now we update local state and call onPlanUpdate.
        // If there's an API to update plan details (name, etc), we should use it.
        // Checking api-client.ts... I don't see `updatePlan`. 
        // I'll update local stat and parent.

        setLocalPlan(updatedPlan);
        onPlanUpdate?.(updatedPlan);
        setShowSettingsModal(false);
    };

    return (
        <div className="space-y-6 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center gap-4 border-b border-base-200 pb-4">
                <div className="flex items-center gap-2">
                    <button onClick={onBack} className="btn btn-ghost btn-sm px-2">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
                        </svg>
                    </button>
                    <div>
                        <h1 className="text-xl md:text-2xl font-bold truncate max-w-md">{localPlan.name}</h1>
                        <p className="text-xs text-base-content/60">{localPlan.risk_preference.replace('_', ' ')} Strategy</p>
                    </div>
                </div>

                <div className="flex-1"></div>

                <div className="flex gap-2 flex-wrap">
                    <button
                        onClick={() => setShowSettingsModal(true)}
                        className="btn btn-ghost btn-sm"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M10.34 15.84c-.688-.06-1.386-.09-2.09-.09H7.5a4.5 4.5 0 110-9h.75c.704 0 1.402-.03 2.09-.09m0 9.18c.253.962.584 1.892.985 2.783.247.55.06 1.21-.463 1.511l-.657.38c-.551.318-1.26.117-1.527-.461a20.845 20.845 0 01-1.44-4.282m3.102.069a18.03 18.03 0 01-.59-4.59c0-1.586.205-3.124.59-4.59m0 9.18a23.848 23.848 0 018.835 2.535M10.34 6.66a23.847 23.847 0 018.835-2.535m0 0A23.74 23.74 0 0018.795 3m.38 1.125a23.91 23.91 0 011.014 5.395m-1.014 8.855c-.118.38-.245.754-.38 1.125m.38-1.125a23.91 23.91 0 001.014-5.395m0-3.46c.495.413.811 1.035.811 1.73 0 .695-.316 1.317-.811 1.73m0-3.46a24.347 24.347 0 010 3.46" />
                        </svg>
                        Settings
                    </button>
                    <button
                        onClick={() => setShowPortfolioEditor(true)}
                        className="btn btn-outline btn-sm"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" />
                        </svg>
                        Edit Portfolio
                    </button>
                    <button
                        onClick={handleOptimize}
                        disabled={isStartingOptimization || !!activeJobId}
                        className="btn btn-primary btn-sm"
                    >
                        {isStartingOptimization ? <span className="loading loading-spinner loading-xs"></span> : (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                            </svg>
                        )}
                        Optimize Portfolio
                    </button>
                </div>
            </div>

            {/* Research History Summary */}
            {localPlan.research_history.length > 0 && (
                <div className="alert alert-info py-2 text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>
                        Latest research: {new Date(localPlan.research_history[localPlan.research_history.length - 1].timestamp).toLocaleDateString()}
                    </span>
                </div>
            )}

            {/* Current Holdings Display */}
            <div className="card bg-base-100 shadow-sm border border-base-200">
                <div className="card-body p-6">
                    <h2 className="card-title text-base mb-4">Current Holdings</h2>
                    {(localPlan.initial_portfolio && localPlan.initial_portfolio.length > 0) ? (
                        <HoldingsByAccount
                            holdings={localPlan.initial_portfolio}
                            baseCurrency={localPlan.base_currency}
                            accountLimits={localPlan.tax_accounts?.reduce((acc, account) => {
                                if (account.annual_limit) {
                                    acc[account.account_type] = {
                                        annual_limit: account.annual_limit,
                                        used_space: account.annual_limit - account.available_space,
                                        available_space: account.available_space
                                    };
                                }
                                return acc;
                            }, {} as Record<string, { annual_limit: number; used_space: number; available_space: number }>)}
                        />
                    ) : (
                        <div className="text-center py-8 bg-base-200/50 rounded-lg border-2 border-dashed border-base-300">
                            <p className="text-base-content/60 mb-3">No assets registered yet.</p>
                            <button
                                className="btn btn-sm btn-outline"
                                onClick={() => setShowPortfolioEditor(true)}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                                </svg>
                                Add Assets
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Optimization Results (if available or running) */}
            {(localPlan.optimization_result || activeJobId) && (
                <div className="card bg-base-100 shadow-sm border border-base-200">
                    <div className="card-body p-0">
                        <PortfolioOptimizer
                            jobId={activeJobId}
                            initialResult={localPlan.optimization_result}
                            onComplete={(result) => {
                                const updated = { ...localPlan, optimization_result: result, updated_at: new Date().toISOString() };
                                setLocalPlan(updated);
                                onPlanUpdate?.(updated);
                                setActiveJobId(null);
                            }}
                        />
                    </div>
                </div>
            )}

            {/* Playground */}
            <div className="card bg-base-100 shadow-sm border border-base-200">
                <div className="card-body p-6">
                    <h2 className="card-title text-base mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                        </svg>
                        Analysis Playground
                    </h2>
                    <Playground
                        initialAmount={localPlan.initial_amount || 10000}
                        currency={localPlan.base_currency}
                    />
                </div>
            </div>

            {/* Research Panel */}
            <div id="research-panel">
                <ResearchPanel
                    planId={localPlan.plan_id}
                    planName={localPlan.name}
                    followUpSuggestions={localPlan.optimization_result?.metrics?.follow_up_suggestions as string[] | null}
                    onResearchComplete={(result) => {
                        onPlanUpdate?.(localPlan);
                    }}
                />
            </div>

            {/* Modals */}
            {showPortfolioEditor && (
                <PortfolioEditor
                    planId={localPlan.plan_id}
                    initialPortfolio={localPlan.initial_portfolio || undefined}
                    baseCurrency={localPlan.base_currency}
                    onSave={async (holdings) => {
                        await updatePlanPortfolio(localPlan.plan_id, holdings);
                        const updated = { ...localPlan, initial_portfolio: holdings, updated_at: new Date().toISOString() };
                        setLocalPlan(updated);
                        onPlanUpdate?.(updated);
                        setShowPortfolioEditor(false);
                    }}
                    onCancel={() => setShowPortfolioEditor(false)}
                />
            )}

            {showSettingsModal && (
                <PlanSettingsModal
                    plan={localPlan}
                    onSave={async (updatedPlan) => handleSettingsSave(updatedPlan)}
                    onCancel={() => setShowSettingsModal(false)}
                />
            )}
        </div>
    );
}
