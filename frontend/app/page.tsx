'use client';

import React, { useState } from 'react';
import { FinancialNews } from "../components/FinancialNews";
import PlanManager from "../components/PlanManager";
import PlanDetail from "../components/PlanDetail";
import { Plan } from "../lib/api-client";

export default function Home() {
    const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    return (
        <div className="flex min-h-screen flex-col items-center bg-zinc-50 font-sans dark:bg-black">
            <main className="flex w-full max-w-6xl flex-col gap-6 md:gap-12 py-6 md:py-20 px-4 sm:px-6 md:px-12 bg-white dark:bg-black min-h-screen">
                <header className="flex items-center justify-between relative">
                    <div className="flex items-center gap-3">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 md:w-10 md:h-10">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v-.75M8.25 2.25h.008v.008H8.25V2.25zm2.25 0h.008v.008h-.008V2.25zm2.25 0h.008v.008h-.008V2.25z" />
                        </svg>
                        <div>
                            <h1 className="text-lg md:text-xl font-bold tracking-tight text-black dark:text-zinc-50">
                                ETF Portfolio <span className="text-blue-600">Advisor</span>
                            </h1>
                            <p className="text-[10px] md:text-xs text-base-content/60">Plan • Optimize • Research</p>
                        </div>
                    </div>

                    {/* Desktop Nav */}
                    <nav className="hidden md:flex gap-6 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                        <a href="#" className="hover:text-zinc-950 dark:hover:text-zinc-50">Plans</a>
                        <a href="#" className="hover:text-zinc-950 dark:hover:text-zinc-50">Docs</a>
                        <a href="#" className="hover:text-zinc-950 dark:hover:text-zinc-50">Settings</a>
                    </nav>

                    {/* Mobile Hamburger */}
                    <button
                        className="md:hidden p-2 text-zinc-600 dark:text-zinc-400"
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                        </svg>
                    </button>

                    {/* Mobile Menu Dropdown */}
                    {isMobileMenuOpen && (
                        <div className="absolute top-16 right-0 w-48 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-xl z-50 p-2 flex flex-col gap-2 md:hidden">
                            <a href="#" className="block px-4 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md">Plans</a>
                            <a href="#" className="block px-4 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md">Docs</a>
                            <a href="#" className="block px-4 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md">Settings</a>
                        </div>
                    )}
                </header>

                <section className="grid grid-cols-1 gap-6 md:gap-12 lg:grid-cols-12">
                    {selectedPlan ? (
                        // Plan Detail View
                        <div className="lg:col-span-12">
                            <PlanDetail
                                plan={selectedPlan}
                                onBack={() => setSelectedPlan(null)}
                                onPlanUpdate={setSelectedPlan}
                            />
                        </div>
                    ) : (
                        // Plan Selection View
                        <>
                            {/* Welcome Section */}
                            <div className="lg:col-span-12">
                                <div className="flex flex-col gap-4">
                                    <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-black dark:text-zinc-50">
                                        Your Investment Plans
                                    </h2>
                                    <p className="max-w-2xl text-base md:text-lg leading-relaxed text-zinc-600 dark:text-zinc-400">
                                        Create and manage your investment plans. Each plan can contain portfolio optimizations,
                                        research analysis, and track your long-term investment goals.
                                    </p>
                                </div>
                            </div>

                            {/* Plan Manager */}
                            <div className="lg:col-span-8">
                                <PlanManager
                                    onPlanSelect={setSelectedPlan}
                                    currentPlanId={null}
                                />
                            </div>

                            {/* News Sidebar */}
                            <div className="lg:col-span-4">
                                <FinancialNews />
                            </div>
                        </>
                    )}
                </section>
            </main>
        </div>
    );
}
