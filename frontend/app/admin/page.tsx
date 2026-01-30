'use client';

import { useState, useEffect } from 'react';
import {
    getAdminConfig,
    updateETFConfig,
    updateForecastingConfig,
    resetConfig,
    getCacheStats,
    clearCache,
    AdminConfig,
    CacheStats,
} from '@/lib/api-client';

export default function AdminSettings() {
    const [activeTab, setActiveTab] = useState<'config' | 'cache'>('config');
    const [config, setConfig] = useState<AdminConfig | null>(null);
    const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Editor states
    const [etfConfigText, setEtfConfigText] = useState('');
    const [forecastingConfigText, setForecastingConfigText] = useState('');

    // Confirmation dialog state
    const [showConfirm, setShowConfirm] = useState(false);
    const [confirmAction, setConfirmAction] = useState<(() => Promise<void>) | null>(null);
    const [confirmMessage, setConfirmMessage] = useState('');

    useEffect(() => {
        loadConfig();
        loadCacheStats();
    }, []);

    const loadConfig = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getAdminConfig();
            setConfig(data);
            setEtfConfigText(JSON.stringify(data.etfs, null, 2));
            setForecastingConfigText(JSON.stringify(data.forecasting, null, 2));
        } catch (err: any) {
            setError(`Failed to load config: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const loadCacheStats = async () => {
        try {
            const stats = await getCacheStats();
            setCacheStats(stats);
        } catch (err: any) {
            console.error('Failed to load cache stats:', err);
        }
    };

    const handleSaveETFConfig = async () => {
        try {
            setLoading(true);
            setError(null);
            const parsed = JSON.parse(etfConfigText);
            await updateETFConfig(parsed);
            setSuccess('ETF config updated successfully!');
            setTimeout(() => setSuccess(null), 3000);
            await loadConfig();
        } catch (err: any) {
            setError(`Failed to save ETF config: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveForecastingConfig = async () => {
        try {
            setLoading(true);
            setError(null);
            const parsed = JSON.parse(forecastingConfigText);
            await updateForecastingConfig(parsed);
            setSuccess('Forecasting config updated successfully!');
            setTimeout(() => setSuccess(null), 3000);
            await loadConfig();
        } catch (err: any) {
            setError(`Failed to save forecasting config: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleResetConfig = async () => {
        try {
            setLoading(true);
            setError(null);
            await resetConfig();
            setSuccess('Configuration reset to defaults!');
            setTimeout(() => setSuccess(null), 3000);
            await loadConfig();
        } catch (err: any) {
            setError(`Failed to reset config: ${err.message}`);
        } finally {
            setLoading(false);
            setShowConfirm(false);
        }
    };

    const handleClearCache = async (cacheType: string) => {
        try {
            setLoading(true);
            setError(null);
            const result = await clearCache(cacheType);
            setSuccess(`Cleared ${result.items_deleted} items from ${cacheType}`);
            setTimeout(() => setSuccess(null), 3000);
            await loadCacheStats();
        } catch (err: any) {
            setError(`Failed to clear cache: ${err.message}`);
        } finally {
            setLoading(false);
            setShowConfirm(false);
        }
    };

    const confirmClearCache = (cacheType: string) => {
        setConfirmMessage(`Are you sure you want to clear the ${cacheType} cache? This action cannot be undone.`);
        setConfirmAction(() => () => handleClearCache(cacheType));
        setShowConfirm(true);
    };

    const confirmResetConfig = () => {
        setConfirmMessage('Are you sure you want to reset all configuration to YAML defaults? This will overwrite your current settings.');
        setConfirmAction(() => handleResetConfig);
        setShowConfirm(true);
    };

    return (
        <div className="container mx-auto p-6 max-w-7xl">
            <h1 className="text-3xl font-bold mb-6">Admin Settings</h1>

            {/* Alerts */}
            {error && (
                <div className="alert alert-error mb-4">
                    <span>{error}</span>
                </div>
            )}
            {success && (
                <div className="alert alert-success mb-4">
                    <span>{success}</span>
                </div>
            )}

            {/* Tabs */}
            <div className="tabs tabs-boxed mb-6">
                <a
                    className={`tab ${activeTab === 'config' ? 'tab-active' : ''}`}
                    onClick={() => setActiveTab('config')}
                >
                    Configuration
                </a>
                <a
                    className={`tab ${activeTab === 'cache' ? 'tab-active' : ''}`}
                    onClick={() => setActiveTab('cache')}
                >
                    Cache Management
                </a>
            </div>

            {/* Configuration Tab */}
            {activeTab === 'config' && (
                <div className="space-y-6">
                    {/* ETF Config */}
                    <div className="card bg-base-200">
                        <div className="card-body">
                            <h2 className="card-title">ETF Configuration</h2>
                            <textarea
                                className="textarea textarea-bordered font-mono text-sm h-96"
                                value={etfConfigText}
                                onChange={(e) => setEtfConfigText(e.target.value)}
                                disabled={loading}
                            />
                            <div className="card-actions justify-end">
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSaveETFConfig}
                                    disabled={loading}
                                >
                                    Save ETF Config
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Forecasting Config */}
                    <div className="card bg-base-200">
                        <div className="card-body">
                            <h2 className="card-title">Forecasting Configuration</h2>
                            <textarea
                                className="textarea textarea-bordered font-mono text-sm h-96"
                                value={forecastingConfigText}
                                onChange={(e) => setForecastingConfigText(e.target.value)}
                                disabled={loading}
                            />
                            <div className="card-actions justify-end">
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSaveForecastingConfig}
                                    disabled={loading}
                                >
                                    Save Forecasting Config
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Reset Config */}
                    <div className="card bg-base-200">
                        <div className="card-body">
                            <h2 className="card-title">Reset Configuration</h2>
                            <p className="text-sm opacity-70">
                                Reset all configuration to the defaults from YAML files. This will overwrite any changes you've made.
                            </p>
                            <div className="card-actions justify-end">
                                <button
                                    className="btn btn-warning"
                                    onClick={confirmResetConfig}
                                    disabled={loading}
                                >
                                    Reset to Defaults
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Cache Management Tab */}
            {activeTab === 'cache' && (
                <div className="space-y-6">
                    <div className="card bg-base-200">
                        <div className="card-body">
                            <h2 className="card-title">Cache Statistics</h2>
                            {cacheStats && (
                                <div className="overflow-x-auto">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th>Cache Type</th>
                                                <th>Items</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {Object.entries(cacheStats).map(([key, value]) => (
                                                <tr key={key}>
                                                    <td className="font-mono">{key}</td>
                                                    <td>
                                                        {value.error ? (
                                                            <span className="text-error">{value.error}</span>
                                                        ) : (
                                                            value.count
                                                        )}
                                                    </td>
                                                    <td>
                                                        <button
                                                            className="btn btn-error btn-sm"
                                                            onClick={() => confirmClearCache(key)}
                                                            disabled={loading || value.count === 0}
                                                        >
                                                            Clear
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                            <div className="card-actions justify-end">
                                <button
                                    className="btn btn-ghost"
                                    onClick={loadCacheStats}
                                    disabled={loading}
                                >
                                    Refresh Stats
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Confirmation Dialog */}
            {showConfirm && (
                <div className="modal modal-open">
                    <div className="modal-box">
                        <h3 className="font-bold text-lg">Confirm Action</h3>
                        <p className="py-4">{confirmMessage}</p>
                        <div className="modal-action">
                            <button
                                className="btn"
                                onClick={() => {
                                    setShowConfirm(false);
                                    setConfirmAction(null);
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn btn-error"
                                onClick={() => confirmAction && confirmAction()}
                                disabled={loading}
                            >
                                Confirm
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
