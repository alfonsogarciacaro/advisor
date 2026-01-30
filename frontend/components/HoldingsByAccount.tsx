'use client';

import React from 'react';
import { AssetHolding, TaxAccountType } from '../lib/api-client';

interface HoldingsByAccountProps {
    holdings: AssetHolding[];
    baseCurrency?: string;  // For display (e.g., "¥" for JPY)
    accountLimits?: Record<string, { annual_limit: number; used_space: number; available_space: number }>;
}

const ACCOUNT_NAMES: Record<TaxAccountType, string> = {
    taxable: 'Taxable Account',
    nisa_general: 'NISA General',
    nisa_growth: 'NISA Growth',
    ideco: 'iDeCo',
    dc_pension: 'DC Pension',
    other: 'Other',
};

export default function HoldingsByAccount({ holdings, baseCurrency = 'JPY', accountLimits }: HoldingsByAccountProps) {
    const currencySymbol = baseCurrency === 'JPY' ? '¥' : baseCurrency === 'USD' ? '$' : baseCurrency;

    // Group holdings by account type
    const groupedByAccount = holdings.reduce((acc, holding) => {
        if (!acc[holding.account_type]) {
            acc[holding.account_type] = [];
        }
        acc[holding.account_type].push(holding);
        return acc;
    }, {} as Record<TaxAccountType, AssetHolding[]>);

    // Calculate totals per account
    const accountTotals: Record<string, number> = {};
    let grandTotal = 0;

    Object.entries(groupedByAccount).forEach(([accountType, accountHoldings]) => {
        const total = accountHoldings.reduce((sum, h) => sum + h.monetary_value, 0);
        accountTotals[accountType] = total;
        grandTotal += total;
    });

    const formatCurrency = (value: number) => {
        return `${currencySymbol}${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
    };

    if (holdings.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-base-content/60">No holdings registered</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {Object.entries(groupedByAccount).map(([accountType, accountHoldings]) => {
                const total = accountTotals[accountType];
                const limit = accountLimits?.[accountType];
                const usagePercentage = limit ? (total / limit.annual_limit) * 100 : 0;

                return (
                    <div key={accountType} className="card bg-base-200">
                        <div className="card-body p-4">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="font-semibold text-lg">{ACCOUNT_NAMES[accountType as TaxAccountType]}</h4>
                                <span className="text-lg font-bold">{formatCurrency(total)}</span>
                            </div>

                            {/* Progress bar for account limit */}
                            {limit && (
                                <div className="mb-3">
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-base-content/60">Annual Usage</span>
                                        <span className="text-base-content/60">
                                            {formatCurrency(total)} / {formatCurrency(limit.annual_limit)}
                                        </span>
                                    </div>
                                    <progress
                                        className="progress w-full"
                                        value={total}
                                        max={limit.annual_limit}
                                    ></progress>
                                </div>
                            )}

                            {/* Holdings list */}
                            <div className="space-y-2">
                                {accountHoldings.map((holding, idx) => (
                                    <div key={idx} className="flex justify-between items-center py-2 border-b border-base-300 last:border-0">
                                        <div>
                                            <span className="font-medium">{holding.ticker}</span>
                                        </div>
                                        <span className="font-mono">{formatCurrency(holding.monetary_value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                );
            })}

            {/* Grand total */}
            <div className="flex justify-between items-center p-4 bg-base-300 rounded-lg">
                <span className="font-semibold text-lg">Total Portfolio Value</span>
                <span className="text-xl font-bold">{formatCurrency(grandTotal)}</span>
            </div>
        </div>
    );
}
