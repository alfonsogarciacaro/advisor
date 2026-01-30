'use client';

import React, { useEffect, useState } from 'react';
import { getLatestNews, NewsItem } from '../lib/api-client';

export const FinancialNews: React.FC = () => {
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchNews = async () => {
            const data = await getLatestNews();
            setNews(data);
            setLoading(false);
        };
        fetchNews();
    }, []);

    if (loading) {
        return (
            <div className="w-full animate-pulse space-y-4">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-24 rounded-xl bg-zinc-100 dark:bg-zinc-800" />
                ))}
            </div>
        );
    }

    if (news.length === 0) {
        return (
            <div className="rounded-xl border border-dashed border-zinc-200 p-8 text-center dark:border-zinc-800">
                <p className="text-zinc-500">No news available at the moment.</p>
            </div>
        );
    }

    return (
        <div className="w-full space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                    Latest Financial News
                </h2>
                <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                    Updated every 12h
                </span>
            </div>
            <div className="grid max-h-[600px] gap-4 overflow-y-auto pr-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-1">
                {news.map((item, index) => (
                    <a
                        key={index}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group relative block overflow-hidden rounded-2xl border border-zinc-200 bg-white p-5 transition-all hover:border-zinc-300 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:border-zinc-700"
                    >
                        <div className="flex flex-col gap-2">
                            <div className="flex items-center justify-between text-xs text-zinc-500">
                                <span className="font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                                    {item.source}
                                </span>
                                <span>{new Date(parseInt(item.time_published.substring(0, 8) + 'T' + item.time_published.substring(9, 15))).toLocaleDateString()}</span>
                            </div>
                            <h3 className="text-lg font-semibold leading-6 text-zinc-900 group-hover:text-blue-600 dark:text-zinc-100 dark:group-hover:text-blue-400">
                                {item.title}
                            </h3>
                            <p className="line-clamp-2 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                                {item.summary}
                            </p>
                        </div>
                    </a>
                ))}
            </div>
        </div>
    );
};
