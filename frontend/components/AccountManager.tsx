'use client';

import React, { useState } from 'react';
import { TaxAccount, TaxAccountType } from '../lib/api-client';

interface AccountManagerProps {
    accounts: TaxAccount[];
    onUpdate: (accounts: TaxAccount[]) => void;
    currency?: string;
}

const ACCOUNT_TYPES: { type: TaxAccountType; name: string; description: string; defaultLimit: number }[] = [
    { type: 'nisa_growth', name: 'NISA Growth', description: 'High-growth investments (¥1.8M/year limit)', defaultLimit: 1800000 },
    { type: 'nisa_general', name: 'NISA General', description: 'Broad market investments (¥1.2M/year limit)', defaultLimit: 1200000 },
    { type: 'ideco', name: 'iDeCo', description: 'Private pension with tax deduction (¥144K-¥816K/year)', defaultLimit: 144000 },
    { type: 'dc_pension', name: 'DC Pension', description: 'Company pension plan', defaultLimit: 0 },
    { type: 'taxable', name: 'Taxable Account', description: 'Standard investment account (20.315% tax)', defaultLimit: 0 },
    { type: 'other', name: 'Other', description: 'Other special account type', defaultLimit: 0 },
];

export default function AccountManager({ accounts, onUpdate, currency = 'JPY' }: AccountManagerProps) {
    const [showAddModal, setShowAddModal] = useState(false);
    const [editingAccount, setEditingAccount] = useState<TaxAccount | null>(null);
    const [newAccountType, setNewAccountType] = useState<TaxAccountType>('taxable');

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('ja-JP', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    };

    const handleAddAccount = () => {
        const template = ACCOUNT_TYPES.find(a => a.type === newAccountType);
        if (!template) return;

        const newAccount: TaxAccount = {
            account_type: template.type,
            name: template.name,
            annual_limit: template.defaultLimit || null,
            current_balance: 0,
            available_space: template.defaultLimit || 0,
            dividend_tax_rate: template.type.includes('nisa') || template.type === 'ideco' ? 0 : 0.20315,
            capital_gains_tax_rate: template.type.includes('nisa') || template.type === 'ideco' ? 0 : 0.20315,
            contribution_deductible: template.type === 'ideco',
            withdrawal_rules: undefined,
        };

        setEditingAccount(newAccount);
        setShowAddModal(false);
    };

    const handleSaveAccount = () => {
        if (!editingAccount) return;

        const existingIndex = accounts.findIndex(a => a.name === editingAccount.name);
        let updatedAccounts: TaxAccount[];

        if (existingIndex >= 0) {
            updatedAccounts = [...accounts];
            updatedAccounts[existingIndex] = editingAccount;
        } else {
            updatedAccounts = [...accounts, editingAccount];
        }

        onUpdate(updatedAccounts);
        setEditingAccount(null);
    };

    const handleDeleteAccount = (accountName: string) => {
        if (!confirm(`Remove "${accountName}" from this plan?`)) return;
        onUpdate(accounts.filter(a => a.name !== accountName));
    };

    const calculateTotalLimit = () => {
        return accounts.reduce((sum, a) => sum + (a.annual_limit || 0), 0);
    };

    const calculateTotalSpace = () => {
        return accounts.reduce((sum, a) => sum + (a.available_space || 0), 0);
    };

    return (
        <div className="space-y-4">
            {/* Summary */}
            <div className="stats stats-vertical lg:stats-horizontal bg-base-200 w-full">
                <div className="stat">
                    <div className="stat-title">Total Accounts</div>
                    <div className="stat-value text-2xl">{accounts.length}</div>
                </div>
                <div className="stat">
                    <div className="stat-title">Annual Limit</div>
                    <div className="stat-value text-2xl text-primary">{formatCurrency(calculateTotalLimit())}</div>
                </div>
                <div className="stat">
                    <div className="stat-title">Available Space</div>
                    <div className="stat-value text-2xl text-success">{formatCurrency(calculateTotalSpace())}</div>
                </div>
            </div>

            {/* Accounts List */}
            <div className="space-y-3">
                {accounts.map((account, idx) => (
                    <div key={idx} className="card bg-base-200 border border-base-300">
                        <div className="card-body p-4">
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <h4 className="font-bold">{account.name}</h4>
                                        <span className="badge badge-ghost text-xs">{account.account_type.replace('_', ' ')}</span>
                                        {account.dividend_tax_rate === 0 && account.capital_gains_tax_rate === 0 && (
                                            <span className="badge badge-success text-xs">Tax-Free</span>
                                        )}
                                        {account.contribution_deductible && (
                                            <span className="badge badge-info text-xs">Deductible</span>
                                        )}
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                                        <div>
                                            <div className="text-xs text-base-content/60">Annual Limit</div>
                                            <div className="font-semibold">{account.annual_limit ? formatCurrency(account.annual_limit) : 'Unlimited'}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-base-content/60">Available Space</div>
                                            <div className="font-semibold text-success">{formatCurrency(account.available_space)}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-base-content/60">Current Balance</div>
                                            <div className="font-semibold">{formatCurrency(account.current_balance)}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-base-content/60">Tax Rate</div>
                                            <div className="font-semibold">{(account.capital_gains_tax_rate * 100).toFixed(1)}%</div>
                                        </div>
                                    </div>

                                    {/* Progress bar */}
                                    {account.annual_limit && account.annual_limit > 0 && (
                                        <div className="mt-3">
                                            <progress
                                                className="progress progress-primary w-full"
                                                value={account.annual_limit - account.available_space}
                                                max={account.annual_limit}
                                            ></progress>
                                            <div className="text-xs text-base-content/60 mt-1">
                                                {formatCurrency(account.annual_limit - account.available_space)} / {formatCurrency(account.annual_limit)} used
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setEditingAccount(account)}
                                        className="btn btn-ghost btn-xs"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                                        </svg>
                                    </button>
                                    <button
                                        onClick={() => handleDeleteAccount(account.name)}
                                        className="btn btn-ghost btn-xs text-error"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Add Account Button */}
            <button
                onClick={() => setShowAddModal(true)}
                className="btn btn-outline btn-sm w-full"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Add Account
            </button>

            {/* Add Account Modal */}
            {showAddModal && (
                <dialog className="modal modal-open">
                    <div className="modal-box">
                        <h3 className="font-bold text-lg">Add Investment Account</h3>

                        <div className="py-4">
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Account Type</span>
                                </label>
                                <select
                                    value={newAccountType}
                                    onChange={(e) => setNewAccountType(e.target.value as TaxAccountType)}
                                    className="select select-bordered"
                                >
                                    {ACCOUNT_TYPES.map(a => (
                                        <option key={a.type} value={a.type}>
                                            {a.name} - {a.description}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="modal-action">
                            <button onClick={() => setShowAddModal(false)} className="btn btn-ghost">
                                Cancel
                            </button>
                            <button onClick={handleAddAccount} className="btn btn-primary">
                                Add Account
                            </button>
                        </div>
                    </div>
                    <form method="dialog" className="modal-backdrop">
                        <button onClick={() => setShowAddModal(false)}>close</button>
                    </form>
                </dialog>
            )}

            {/* Edit Account Modal */}
            {editingAccount && (
                <dialog className="modal modal-open">
                    <div className="modal-box max-w-2xl">
                        <h3 className="font-bold text-lg">
                            {accounts.find(a => a.name === editingAccount.name) ? 'Edit' : 'Add'} Account
                        </h3>

                        <div className="py-4 space-y-4">
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Account Name</span>
                                </label>
                                <input
                                    type="text"
                                    value={editingAccount.name}
                                    onChange={(e) => setEditingAccount({ ...editingAccount, name: e.target.value })}
                                    className="input input-bordered"
                                />
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Annual Limit (0 for unlimited)</span>
                                </label>
                                <input
                                    type="number"
                                    value={editingAccount.annual_limit || ''}
                                    onChange={(e) => setEditingAccount({ ...editingAccount, annual_limit: parseFloat(e.target.value) || null })}
                                    className="input input-bordered"
                                    placeholder="e.g., 1200000"
                                />
                                <label className="label">
                                    <span className="label-text-alt">Leave empty for unlimited (taxable accounts)</span>
                                </label>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-control">
                                    <label className="label">
                                        <span className="label-text">Current Balance</span>
                                    </label>
                                    <input
                                        type="number"
                                        value={editingAccount.current_balance}
                                        onChange={(e) => setEditingAccount({ ...editingAccount, current_balance: parseFloat(e.target.value) || 0 })}
                                        className="input input-bordered"
                                    />
                                </div>

                                <div className="form-control">
                                    <label className="label">
                                        <span className="label-text">Available Space</span>
                                    </label>
                                    <input
                                        type="number"
                                        value={editingAccount.available_space}
                                        onChange={(e) => setEditingAccount({ ...editingAccount, available_space: parseFloat(e.target.value) || 0 })}
                                        className="input input-bordered"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-control">
                                    <label className="label">
                                        <span className="label-text">Dividend Tax Rate (%)</span>
                                    </label>
                                    <input
                                        type="number"
                                        step="0.001"
                                        value={editingAccount.dividend_tax_rate * 100}
                                        onChange={(e) => setEditingAccount({ ...editingAccount, dividend_tax_rate: (parseFloat(e.target.value) || 0) / 100 })}
                                        className="input input-bordered"
                                    />
                                </div>

                                <div className="form-control">
                                    <label className="label">
                                        <span className="label-text">Capital Gains Tax Rate (%)</span>
                                    </label>
                                    <input
                                        type="number"
                                        step="0.001"
                                        value={editingAccount.capital_gains_tax_rate * 100}
                                        onChange={(e) => setEditingAccount({ ...editingAccount, capital_gains_tax_rate: (parseFloat(e.target.value) || 0) / 100 })}
                                        className="input input-bordered"
                                    />
                                </div>
                            </div>

                            <div className="form-control">
                                <label className="label cursor-pointer justify-start gap-3">
                                    <input
                                        type="checkbox"
                                        checked={editingAccount.contribution_deductible}
                                        onChange={(e) => setEditingAccount({ ...editingAccount, contribution_deductible: e.target.checked })}
                                        className="checkbox checkbox-primary"
                                    />
                                    <span className="label-text">Contributions are tax-deductible (iDeCo)</span>
                                </label>
                            </div>

                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text">Withdrawal Rules (optional)</span>
                                </label>
                                <textarea
                                    value={editingAccount.withdrawal_rules || ''}
                                    onChange={(e) => setEditingAccount({ ...editingAccount, withdrawal_rules: e.target.value || undefined })}
                                    className="textarea textarea-bordered"
                                    placeholder="e.g., Withdrawals only after age 60"
                                    rows={2}
                                />
                            </div>
                        </div>

                        <div className="modal-action">
                            <button
                                onClick={() => setEditingAccount(null)}
                                className="btn btn-ghost"
                            >
                                Cancel
                            </button>
                            <button onClick={handleSaveAccount} className="btn btn-primary">
                                Save Account
                            </button>
                        </div>
                    </div>
                    <form method="dialog" className="modal-backdrop">
                        <button onClick={() => setEditingAccount(null)}>close</button>
                    </form>
                </dialog>
            )}
        </div>
    );
}
