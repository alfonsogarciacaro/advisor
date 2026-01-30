'use client';

import React, { useState, useEffect } from 'react';
import { AssetHolding, TaxAccountType, EtfInfo, AccountLimitInfo, getAvailableEtfs, validatePortfolioHoldings } from '../lib/api-client';

interface PortfolioEditorProps {
    planId: string;
    initialPortfolio?: AssetHolding[];
    onSave: (holdings: AssetHolding[]) => Promise<void>;
    onCancel: () => void;
    baseCurrency?: string;
}

const ACCOUNT_TYPES: { value: TaxAccountType; label: string }[] = [
    { value: 'taxable', label: 'Taxable Account' },
    { value: 'nisa_growth', label: 'NISA Growth' },
    { value: 'nisa_general', label: 'NISA General' },
    { value: 'ideco', label: 'iDeCo' },
    { value: 'dc_pension', label: 'DC Pension' },
    { value: 'other', label: 'Other' },
];

interface FormHolding {
    ticker: string;
    account_type: TaxAccountType;
    monetary_value: string;
}

export default function PortfolioEditor({ planId, initialPortfolio = [], onSave, onCancel, baseCurrency = 'JPY' }: PortfolioEditorProps) {
    const [holdings, setHoldings] = useState<FormHolding[]>([]);
    const [availableEtfs, setAvailableEtfs] = useState<EtfInfo[]>([]);
    const [accountLimits, setAccountLimits] = useState<Record<string, AccountLimitInfo>>({});
    const [validationErrors, setValidationErrors] = useState<string[]>([]);
    const [isSaving, setIsSaving] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const currencySymbol = baseCurrency === 'JPY' ? '¥' : baseCurrency === 'USD' ? '$' : baseCurrency;

    useEffect(() => {
        const loadData = async () => {
            try {
                const response = await getAvailableEtfs(planId);
                setAvailableEtfs(response.etfs);
                setAccountLimits(response.account_limits);

                // Initialize with existing portfolio
                if (initialPortfolio.length > 0) {
                    setHoldings(initialPortfolio.map(h => ({
                        ticker: h.ticker,
                        account_type: h.account_type,
                        monetary_value: h.monetary_value.toString()
                    })));
                }
            } catch (error) {
                console.error('Error loading data:', error);
            } finally {
                setIsLoading(false);
            }
        };

        loadData();
    }, [planId, initialPortfolio]);

    const addHolding = () => {
        setHoldings([...holdings, {
            ticker: '',
            account_type: 'taxable',
            monetary_value: ''
        }]);
    };

    const updateHolding = (index: number, field: keyof FormHolding, value: string) => {
        const newHoldings = [...holdings];
        if (field === 'account_type') {
            newHoldings[index][field] = value as TaxAccountType;
        } else {
            newHoldings[index][field] = value;
        }
        setHoldings(newHoldings);
        setValidationErrors([]); // Clear validation errors on edit
    };

    const removeHolding = (index: number) => {
        setHoldings(holdings.filter((_, i) => i !== index));
        setValidationErrors([]);
    };

    const handleSave = async () => {
        setIsSaving(true);
        setValidationErrors([]);

        try {
            // Convert to AssetHolding format
            const assetHoldings: AssetHolding[] = holdings
                .filter(h => h.ticker && h.monetary_value)
                .map(h => ({
                    ticker: h.ticker,
                    account_type: h.account_type,
                    monetary_value: parseFloat(h.monetary_value)
                }));

            // Validate holdings
            const validation = await validatePortfolioHoldings(planId, assetHoldings);

            if (!validation.valid && validation.errors.length > 0) {
                setValidationErrors(validation.errors.map(e => e.message));
                setIsSaving(false);
                return;
            }

            // Save
            await onSave(assetHoldings);
        } catch (error: any) {
            setValidationErrors([error.message || 'Failed to save portfolio']);
        } finally {
            setIsSaving(false);
        }
    };

    const getAccountUsage = (accountType: TaxAccountType) => {
        const currentUsage = holdings
            .filter(h => h.account_type === accountType)
            .reduce((sum, h) => sum + (parseFloat(h.monetary_value) || 0), 0);

        const limit = accountLimits[accountType];
        if (!limit) return null;

        const existingUsage = limit.used_space;
        const totalUsage = existingUsage + currentUsage;
        const percentage = (totalUsage / limit.annual_limit) * 100;

        return {
            current: currentUsage,
            existing: existingUsage,
            total: totalUsage,
            limit: limit.annual_limit,
            percentage,
            isOverLimit: totalUsage > limit.annual_limit
        };
    };

    const formatCurrency = (value: number) => {
        return `${currencySymbol}${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
    };

    if (isLoading) {
        return (
            <div className="modal modal-open">
                <div className="modal-box">
                    <div className="flex justify-center py-8">
                        <span className="loading loading-spinner loading-lg"></span>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="modal modal-open">
            <div className="modal-box max-w-4xl">
                <h3 className="font-bold text-lg mb-4">Edit Portfolio Holdings</h3>

                {validationErrors.length > 0 && (
                    <div className="alert alert-error mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                            <h4 className="font-bold">Validation Error</h4>
                            <ul className="text-xs">
                                {validationErrors.map((error, idx) => (
                                    <li key={idx}>{error}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}

                <div className="space-y-4">
                    {holdings.map((holding, index) => {
                        const usage = getAccountUsage(holding.account_type);

                        return (
                            <div key={index} className="card bg-base-200">
                                <div className="card-body p-4">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {/* ETF Selector */}
                                        <div className="form-control">
                                            <label className="label"><span className="label-text">ETF</span></label>
                                            <select
                                                className="select select-bordered"
                                                aria-label="ETF"
                                                value={holding.ticker}
                                                onChange={(e) => updateHolding(index, 'ticker', e.target.value)}
                                            >
                                                <option value="">Select ETF</option>
                                                {availableEtfs.map(etf => (
                                                    <option key={etf.symbol} value={etf.symbol}>
                                                        {etf.symbol} - {etf.name} ({formatCurrency(etf.current_price_base)})
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        {/* Account Type */}
                                        <div className="form-control">
                                            <label className="label"><span className="label-text">Account</span></label>
                                            <select
                                                className="select select-bordered"
                                                aria-label="Account"
                                                value={holding.account_type}
                                                onChange={(e) => updateHolding(index, 'account_type', e.target.value)}
                                            >
                                                {ACCOUNT_TYPES.map(type => (
                                                    <option key={type.value} value={type.value}>{type.label}</option>
                                                ))}
                                            </select>
                                        </div>


                                        {/* Monetary Value */}
                                        <div className="form-control">
                                            <label className="label"><span className="label-text">Value ({baseCurrency})</span></label>
                                            <input
                                                type="number"
                                                className="input input-bordered"
                                                aria-label={`Value (${baseCurrency})`}
                                                placeholder={`e.g., ${currencySymbol}1,000,000`}
                                                value={holding.monetary_value}
                                                onChange={(e) => updateHolding(index, 'monetary_value', e.target.value)}
                                                min="0"
                                                step="0.01"
                                            />
                                        </div>

                                    </div>

                                    {/* Account Limit Warning */}
                                    {usage && (
                                        <div className={`mt-2 ${usage.isOverLimit ? 'text-error' : 'text-success'}`}>
                                            <div className="text-xs">
                                                Account Usage: {formatCurrency(usage.total)} / {formatCurrency(usage.limit)}
                                                ({usage.percentage.toFixed(1)}%)
                                                {usage.isOverLimit && (
                                                    <span className="font-bold ml-2">⚠️ Over limit!</span>
                                                )}
                                            </div>
                                            <progress
                                                className={`progress w-full mt-1 ${usage.isOverLimit ? 'progress-error' : 'progress-success'}`}
                                                value={usage.total}
                                                max={usage.limit}
                                            ></progress>
                                        </div>
                                    )}

                                    {/* Remove Button */}
                                    <div className="flex justify-end mt-2">
                                        <button
                                            className="btn btn-sm btn-ghost text-error"
                                            onClick={() => removeHolding(index)}
                                        >
                                            Remove
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}

                    {/* Add Asset Button */}
                    <button
                        className="btn btn-outline btn-dashed w-full"
                        onClick={addHolding}
                    >
                        + Add Asset
                    </button>

                    {/* Total */}
                    {holdings.length > 0 && (
                        <div className="text-right">
                            <span className="text-lg font-semibold">
                                Total: {formatCurrency(
                                    holdings.reduce((sum, h) => sum + (parseFloat(h.monetary_value) || 0), 0)
                                )}
                            </span>
                        </div>
                    )}
                </div>

                {/* Modal Actions */}
                <div className="modal-action">
                    <button className="btn btn-ghost" onClick={onCancel} disabled={isSaving}>
                        Cancel
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSave}
                        disabled={isSaving || holdings.length === 0 || validationErrors.length > 0}
                    >
                        {isSaving ? <span className="loading loading-spinner"></span> : 'Save Portfolio'}
                    </button>
                </div>
            </div>
        </div>
    );
}
