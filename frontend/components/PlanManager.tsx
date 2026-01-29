'use client';

import React, { useState, useEffect } from 'react';
import {
    createPlan,
    listPlans,
    getPlan,
    deletePlan,
    updatePlan,
    Plan,
    RiskProfile,
} from '../lib/api-client';

interface PlanManagerProps {
    onPlanSelect: (plan: Plan) => void;
    currentPlanId?: string | null;
}

const RISK_LABELS: Record<RiskProfile, string> = {
    very_conservative: 'Very Conservative',
    conservative: 'Conservative',
    moderate: 'Moderate',
    growth: 'Growth',
    aggressive: 'Aggressive',
};

export default function PlanManager({ onPlanSelect, currentPlanId }: PlanManagerProps) {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newPlanName, setNewPlanName] = useState('');
    const [newPlanDescription, setNewPlanDescription] = useState('');
    const [newPlanRisk, setNewPlanRisk] = useState<RiskProfile>('moderate');
    const [error, setError] = useState<string | null>(null);

    const loadPlans = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await listPlans('default');
            setPlans(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load plans');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPlans();
    }, []);

    const handleCreatePlan = async () => {
        if (!newPlanName.trim()) {
            setError('Please enter a plan name');
            return;
        }

        try {
            setError(null);
            const result = await createPlan({
                name: newPlanName.trim(),
                description: newPlanDescription.trim() || undefined,
                risk_preference: newPlanRisk,
                user_id: 'default',
            });

            // Load the created plan
            const plan = await getPlan(result.plan_id);
            setPlans([plan, ...plans]);
            setShowCreateModal(false);
            setNewPlanName('');
            setNewPlanDescription('');
            setNewPlanRisk('moderate');
            // Navigate to the newly created plan
            onPlanSelect(plan);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create plan');
        }
    };

    const handleDeletePlan = async (planId: string, planName: string) => {
        if (!confirm(`Are you sure you want to delete "${planName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            setError(null);
            await deletePlan(planId);
            setPlans(plans.filter((p) => p.plan_id !== planId));

            // If the deleted plan was selected, clear selection
            if (currentPlanId === planId) {
                // Notify parent to clear selection
                window.location.reload();
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete plan');
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div className="card bg-base-100 shadow-xl border border-base-200">
            <div className="card-body">
                <div className="flex justify-between items-center">
                    <h2 className="card-title">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44l-2.12-2.12z" />
                        </svg>
                        Investment Plans
                    </h2>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="btn btn-primary btn-sm"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                        </svg>
                        New Plan
                    </button>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="alert alert-error mt-4">
                        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>{error}</span>
                        <button onClick={() => setError(null)} className="btn btn-ghost btn-xs">✕</button>
                    </div>
                )}

                {/* Loading State */}
                {loading ? (
                    <div className="flex flex-col items-center justify-center p-12">
                        <span className="loading loading-spinner loading-lg"></span>
                        <p className="mt-4 text-base-content/60">Loading plans...</p>
                    </div>
                ) : plans.length === 0 ? (
                    /* Empty State */
                    <div className="flex flex-col items-center justify-center p-12 text-center">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-16 h-16 text-base-content/20">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44l-2.12-2.12z" />
                        </svg>
                        <h3 className="mt-4 text-lg font-semibold">No plans yet</h3>
                        <p className="text-base-content/60 mt-2">Create your first investment plan to get started</p>
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="btn btn-primary mt-4"
                        >
                            Create Your First Plan
                        </button>
                    </div>
                ) : (
                    /* Plans List */
                    <div className="space-y-3 mt-4">
                        {plans.map((plan) => (
                            <button
                                key={plan.plan_id}
                                className={`card bg-base-200 border cursor-pointer transition-all text-left ${currentPlanId === plan.plan_id
                                        ? 'border-primary shadow-md'
                                        : 'border-base-300 hover:border-base-content/20'
                                    }`}
                                onClick={() => onPlanSelect(plan)}
                                aria-label={`Plan: ${plan.name}`}
                            >
                                <div className="card-body p-4">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <h3 className="font-bold text-lg">{plan.name}</h3>
                                            {plan.description && (
                                                <p className="text-sm text-base-content/60 mt-1">{plan.description}</p>
                                            )}
                                            <div className="flex gap-2 mt-2">
                                                <span className="badge badge-ghost">{RISK_LABELS[plan.risk_preference]}</span>
                                                {plan.optimization_result && (
                                                    <span className="badge badge-success">Optimized</span>
                                                )}
                                                {plan.research_history.length > 0 && (
                                                    <span className="badge badge-info">{plan.research_history.length} Research</span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end gap-2">
                                            <span className="text-xs text-base-content/40">{formatDate(plan.updated_at)}</span>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeletePlan(plan.plan_id, plan.name);
                                                }}
                                                className="btn btn-ghost btn-xs btn-circle text-error hover:bg-error/10"
                                                title="Delete plan"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                )}

                {/* Create Plan Modal */}
                {showCreateModal && (
                    <dialog className="modal modal-open">
                        <div className="modal-box">
                            <h3 className="font-bold text-lg">Create New Investment Plan</h3>

                            <div className="py-4 space-y-4">
                                <div className="form-control">
                                    <label className="label" htmlFor="plan-name">
                                        <span className="label-text">Plan Name</span>
                                    </label>
                                    <input
                                        id="plan-name"
                                        type="text"
                                        value={newPlanName}
                                        onChange={(e) => setNewPlanName(e.target.value)}
                                        className="input input-bordered"
                                        placeholder="e.g., Retirement Portfolio"
                                        autoFocus
                                    />
                                </div>

                                <div className="form-control">
                                    <label className="label" htmlFor="plan-description">
                                        <span className="label-text">Description (optional)</span>
                                    </label>
                                    <textarea
                                        id="plan-description"
                                        value={newPlanDescription}
                                        onChange={(e) => setNewPlanDescription(e.target.value)}
                                        className="textarea textarea-bordered"
                                        placeholder="Describe your investment goals..."
                                        rows={3}
                                    />
                                </div>

                                <div className="form-control">
                                    <label className="label" htmlFor="plan-risk">
                                        <span className="label-text">Risk Preference</span>
                                    </label>
                                    <select
                                        id="plan-risk"
                                        value={newPlanRisk}
                                        onChange={(e) => setNewPlanRisk(e.target.value as RiskProfile)}
                                        className="select select-bordered"
                                    >
                                        <option value="very_conservative">Very Conservative - Max capital preservation</option>
                                        <option value="conservative">Conservative - Focus on stability</option>
                                        <option value="moderate">Moderate - Balanced approach</option>
                                        <option value="growth">Growth - Accept higher volatility</option>
                                        <option value="aggressive">Aggressive - Maximum growth</option>
                                    </select>
                                </div>
                            </div>

                            <div className="modal-action">
                                <button
                                    onClick={() => {
                                        setShowCreateModal(false);
                                        setNewPlanName('');
                                        setNewPlanDescription('');
                                        setNewPlanRisk('moderate');
                                    }}
                                    className="btn btn-ghost"
                                >
                                    Cancel
                                </button>
                                <button onClick={handleCreatePlan} className="btn btn-primary">
                                    Create Plan
                                </button>
                            </div>
                        </div>
                        <form method="dialog" className="modal-backdrop">
                            <button onClick={() => setShowCreateModal(false)}>close</button>
                        </form>
                    </dialog>
                )}
            </div>
        </div>
    );
}
