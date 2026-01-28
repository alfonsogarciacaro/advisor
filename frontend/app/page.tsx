import Image from "next/image";
import { FinancialNews } from "../components/financial-news";
import PortfolioOptimizer from "../components/PortfolioOptimizer";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-5xl flex-col gap-12 py-20 px-6 sm:px-12 bg-white dark:bg-black min-h-screen">
        <header className="flex items-center justify-between">
          <Image
            className="dark:invert"
            src="/next.svg"
            alt="Next.js logo"
            width={100}
            height={20}
            priority
          />
          <nav className="flex gap-6 text-sm font-medium text-zinc-600 dark:text-zinc-400">
            <a href="#" className="hover:text-zinc-950 dark:hover:text-zinc-50">Portfolio</a>
            <a href="#" className="hover:text-zinc-950 dark:hover:text-zinc-50">Analysis</a>
            <a href="#" className="hover:text-zinc-950 dark:hover:text-zinc-50">Settings</a>
          </nav>
        </header>

        <section className="grid grid-cols-1 gap-12 lg:grid-cols-12">
          <div className="lg:col-span-12">
            <div className="flex flex-col gap-6">
              <h1 className="text-4xl font-bold tracking-tight text-black dark:text-zinc-50 sm:text-5xl">
                ETF Portfolio <span className="text-blue-600">Advisor</span>
              </h1>
              <p className="max-w-xl text-lg leading-relaxed text-zinc-600 dark:text-zinc-400">
                Get real-time insights and automated portfolio optimizations.
                Our advisor uses advanced algorithms to keep your investments on track.
              </p>
              <div className="flex flex-wrap gap-4">
                <button className="rounded-full bg-black px-8 py-3 text-sm font-semibold text-white transition-all hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200">
                  Connect Wallet
                </button>
                <button className="rounded-full border border-zinc-200 px-8 py-3 text-sm font-semibold transition-all hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900">
                  View Demo
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-12">
            <div className="h-px w-full bg-zinc-100 dark:bg-zinc-900" />
          </div>

          <div className="lg:col-span-8">
            <PortfolioOptimizer initialAmount={10000} initialCurrency="USD" />
          </div>

          <div className="lg:col-span-4">
            <FinancialNews />
          </div>
        </section>
      </main>
    </div>
  );
}
