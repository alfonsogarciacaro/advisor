"use client";

import { useAuth } from "@/contexts/AuthContext";
import { LogOut, User } from "lucide-react";
import { useState } from "react";

export function UserMenu() {
    const { user, logout, isAuthenticated } = useAuth();
    const [isOpen, setIsOpen] = useState(false);

    if (!isAuthenticated || !user) {
        return null; // Or a Login button if you prefer it inline
    }

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            >
                <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-300">
                    <User size={18} />
                </div>
                <span className="text-sm font-medium text-neutral-700 dark:text-neutral-200 hidden md:block">
                    {user.username}
                </span>
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-neutral-900 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-800 py-1 z-20 animate-in fade-in zoom-in-95 duration-100">
                        <div className="px-4 py-2 border-b border-neutral-100 dark:border-neutral-800">
                            <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
                                {user.username}
                            </p>
                            <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
                                {user.role}
                            </p>
                        </div>
                        <button
                            onClick={() => {
                                logout();
                                setIsOpen(false);
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 flex items-center gap-2 transition-colors"
                        >
                            <LogOut size={16} />
                            Sign Out
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
