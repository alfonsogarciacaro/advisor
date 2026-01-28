'use client';

import React, { useEffect, useState } from 'react';
import { AgentLog, AgentRunStatus, getRunLogs, getRunStatus } from '../lib/api-client';

interface AgentMonitorProps {
    runId: string | null;
}

export default function AgentMonitor({ runId }: AgentMonitorProps) {
    const [status, setStatus] = useState<AgentRunStatus | null>(null);
    const [logs, setLogs] = useState<AgentLog[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!runId) return;

        let polling = true;
        const fetchData = async () => {
            try {
                const [runStatus, runLogs] = await Promise.all([
                    getRunStatus(runId),
                    getRunLogs(runId)
                ]);

                setStatus(runStatus);
                setLogs(runLogs);

                if (runStatus.status === 'completed' || runStatus.status === 'failed') {
                    polling = false;
                }
            } catch (err) {
                console.error("Monitor error:", err);
                setError("Failed to fetch agent progress");
                polling = false;
            }
        };

        fetchData(); // Initial fetch

        const interval = setInterval(() => {
            if (polling) {
                fetchData();
            } else {
                clearInterval(interval);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [runId]);

    if (!runId) {
        return <div className="text-gray-500 italic">No agent running.</div>;
    }

    if (error) {
        return <div className="text-error">{error}</div>;
    }

    return (
        <div className="card bg-base-100 shadow-xl border border-base-200">
            <div className="card-body">
                <h2 className="card-title flex justify-between">
                    Agent Monitor
                    {status && (
                        <span className={`badge ${status.status === 'completed' ? 'badge-success' :
                            status.status === 'failed' ? 'badge-error' : 'badge-info animate-pulse'
                            }`}>
                            {status.status}
                        </span>
                    )}
                </h2>

                <div className="overflow-x-auto mt-4 max-h-[400px] overflow-y-auto">
                    <table className="table table-xs w-full">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Step</th>
                                <th>Status</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log, index) => (
                                <tr key={index}>
                                    <td className="whitespace-nowrap font-mono text-xs opacity-70">
                                        {new Date(log.timestamp).toLocaleTimeString()}
                                    </td>
                                    <td className="font-bold">{log.step}</td>
                                    <td>
                                        <span className={`badge badge-sm ${log.status === 'completed' ? 'badge-success badge-outline' :
                                            log.status === 'failed' ? 'badge-error badge-outline' : 'badge-ghost'
                                            }`}>
                                            {log.status}
                                        </span>
                                    </td>
                                    <td className="font-mono text-xs truncate max-w-[200px]" title={JSON.stringify(log.details, null, 2)}>
                                        {log.details ? JSON.stringify(log.details) : '-'}
                                    </td>
                                </tr>
                            ))}
                            {logs.length === 0 && (
                                <tr>
                                    <td colSpan={4} className="text-center italic opacity-50">Waiting for logs...</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
