'use client';

import React, { useState } from 'react';
import { Plan, TaxAccount } from '../lib/api-client';
import AccountManager from './AccountManager';

interface PlanSettingsModalProps {
    plan: Plan;
    onSave: (updatedPlan: Plan) => Promise<void>;
    onCancel: () => void;
}

type SettingsTab = 'general' | 'accounts';

export default function PlanSettingsModal({ plan, onSave, onCancel }: PlanSettingsModalProps) {
    const [localPlan, setLocalPlan] = useState<Plan>(JSON.parse(JSON.stringify(plan)));
    const [activeTab, setActiveTab] = useState<SettingsTab>('general');
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await onSave(localPlan);
        } catch (error) {
            console.error('Failed to save plan settings:', error);
            // You might want to show an error message here
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="modal modal-open">
            <div className="modal-box max-w-4xl h-[80vh] flex flex-col p-0">
                {/* Header */}
                <div className="p-6 border-b border-base-200 flex justify-between items-center">
                    <h3 className="font-bold text-lg">Plan Settings</h3>
                    <button className="btn btn-sm btn-circle btn-ghost" onClick={onCancel}>✕</button>
                </div>

                {/* Tabs */}
                <div className="px-6 pt-4">
                    <div role="tablist" className="tabs tabs-bordered">
                        <button
                            role="tab"
                            className={`tab ${activeTab === 'general' ? 'tab-active' : ''}`}
                            onClick={() => setActiveTab('general')}
                        >
                            General
                        </button>
                        <button
                            role="tab"
                            className={`tab ${activeTab === 'accounts' ? 'tab-active' : ''}`}
                            onClick={() => setActiveTab('accounts')}
                        >
                            Accounts
                        </button>
                    </div>
                </div>

                {/* Content - Scrollable */}
                <div className="flex-1 overflow-y-auto p-6">
                    {activeTab === 'general' && (
                        <div className="space-y-4 max-w-2xl mx-auto">
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Plan Name</span>
                                </label>
                                <input
                                    type="text"
                                    value={localPlan.name}
                                    onChange={(e) => setLocalPlan({ ...localPlan, name: e.target.value })}
                                    className="input input-bordered"
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Description</span>
                                </label>
                                <textarea
                                    value={localPlan.description || ''}
                                    onChange={(e) => setLocalPlan({ ...localPlan, description: e.target.value })}
                                    className="textarea textarea-bordered"
                                    rows={2}
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Tax Residence</span>
                                </label>
                                <select
                                    className="select select-bordered"
                                    disabled
                                    value="japan"
                                >
                                    <option value="japan">Japan (JPY)</option>
                                </select>
                                <label className="label">
                                    <span className="label-text-alt">Tax residence determines default currency and account types. Currently only Japan is supported.</span>
                                </label>
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Risk Preference</span>
                                </label>
                                <select
                                    value={localPlan.risk_preference}
                                    onChange={(e) => setLocalPlan({ ...localPlan, risk_preference: e.target.value as any })}
                                    className="select select-bordered"
                                >
                                    <option value="very_conservative">Very Conservative - Max capital preservation</option>
                                    <option value="conservative">Conservative - Focus on stability</option>
                                    <option value="moderate">Moderate - Balanced approach</option>
                                    <option value="growth">Growth - Accept higher volatility</option>
                                    <option value="aggressive">Aggressive - Maximum growth</option>
                                </select>
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Notes</span>
                                </label>
                                <textarea
                                    value={localPlan.notes || ''}
                                    onChange={(e) => setLocalPlan({ ...localPlan, notes: e.target.value })}
                                    className="textarea textarea-bordered"
                                    placeholder="Add any notes about this plan..."
                                    rows={4}
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === 'accounts' && (
                        <div>
                            <p className="text-base-content/70 mb-4">
                                Configure your tax-advantaged accounts (NISA, iDeCo) and taxable accounts for optimal tax placement.
                            </p>
                            <AccountManager
                                accounts={localPlan.tax_accounts || []}
                                onUpdate={(accounts) => setLocalPlan({ ...localPlan, tax_accounts: accounts })}
                                currency={localPlan.base_currency}
                            />
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="modal-action p-6 border-t border-base-200 m-0">
                    <button className="btn btn-ghost" onClick={onCancel} disabled={isSaving}>
                        Cancel
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSave}
                        disabled={isSaving}
                    >
                        {isSaving ? <span className="loading loading-spinner"></span> : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
}
