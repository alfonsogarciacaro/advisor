"use client";

import { useAuth } from "@/contexts/AuthContext";
import { X, Loader2, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";

export function LoginModal() {
    const { showLoginModal, setShowLoginModal, login, register, isLoading } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState(""); // For registration
    const [error, setError] = useState<string | null>(null);

    // Clear state when modal closes
    useEffect(() => {
        if (!showLoginModal) {
            setUsername("");
            setPassword("");
            setConfirmPassword("");
            setError(null);
            setIsLogin(true);
        }
    }, [showLoginModal]);

    if (!showLoginModal) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!username || !password) {
            setError("Please fill in all fields.");
            return;
        }

        if (!isLogin && password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        try {
            if (isLogin) {
                await login(username, password);
            } else {
                await register(username, password);
                // After successful registration, usually we want to log them in automatically
                // The context register function might handle this or we call login after
                // Let's assume register just registers, and we can switch to login or auto-login
                // For better UX, let's assume register logs them in or we call login.
                // NOTE: The previous context design plan implies register calls backend register.
                // We'll see how robust we make the context.
            }
            setShowLoginModal(false);
        } catch (err: any) {
            setError(err.message || "An error occurred. Please try again.");
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop with blur */}
            <div
                className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200"
                onClick={() => setShowLoginModal(false)}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-md bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 border border-neutral-200 dark:border-neutral-800">

                {/* Header */}
                <div className="px-8 pt-8 pb-6 text-center">
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
                        {isLogin ? "Welcome Back" : "Create Account"}
                    </h2>
                    <p className="text-neutral-500 dark:text-neutral-400 mt-2">
                        {isLogin ? "Enter your credentials to access your account" : "Sign up to start managing your portfolio"}
                    </p>
                </div>

                {/* Close Button */}
                <button
                    onClick={() => setShowLoginModal(false)}
                    className="absolute top-4 right-4 p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                >
                    <X size={20} />
                </button>

                {/* Form */}
                <div className="px-8 pb-8">
                    {error && (
                        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm flex items-start gap-2">
                            <AlertCircle size={16} className="mt-0.5 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Username</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-3 rounded-xl bg-neutral-50 dark:bg-neutral-800 border-transparent focus:bg-white dark:focus:bg-neutral-900 border-2 focus:border-blue-500 outline-none transition-all placeholder:text-neutral-400"
                                placeholder="Enter your username"
                                disabled={isLoading}
                                autoFocus
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 rounded-xl bg-neutral-50 dark:bg-neutral-800 border-transparent focus:bg-white dark:focus:bg-neutral-900 border-2 focus:border-blue-500 outline-none transition-all placeholder:text-neutral-400"
                                placeholder="Enter your password"
                                disabled={isLoading}
                            />
                        </div>

                        {!isLogin && (
                            <div className="space-y-2 animate-in slide-in-from-top-2 fade-in duration-200">
                                <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Confirm Password</label>
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full px-4 py-3 rounded-xl bg-neutral-50 dark:bg-neutral-800 border-transparent focus:bg-white dark:focus:bg-neutral-900 border-2 focus:border-blue-500 outline-none transition-all placeholder:text-neutral-400"
                                    placeholder="Confirm your password"
                                    disabled={isLoading}
                                />
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full mt-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-lg shadow-blue-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="animate-spin" size={20} />
                                    <span>Processing...</span>
                                </>
                            ) : (
                                <span>{isLogin ? "Sign In" : "Create Account"}</span>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-neutral-500 dark:text-neutral-400">
                            {isLogin ? "Don't have an account?" : "Already have an account?"}
                            <button
                                onClick={() => {
                                    setIsLogin(!isLogin);
                                    setError(null);
                                }}
                                className="ml-1.5 text-blue-600 dark:text-blue-400 font-medium hover:underline focus:outline-none"
                            >
                                {isLogin ? "Sign up" : "Log in"}
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
