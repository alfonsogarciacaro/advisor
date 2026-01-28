# System Flows

This document outlines the core workflows of the Advisor application, clarifying the roles of different services.

## 1. Portfolio Optimizer Flow (Quantitative Allocation)

**Goal:** Provide a mathematically optimal asset allocation based on historical data.
**User Query Example:** "How should I split my $10,000 investment?"

### Workflow Steps:
1.  **User Input:** The user submits an investment amount and currency via the Frontend.
2.  **PortfolioOptimizer Service:** Receives the request.
3.  **Data Fetching:** The service fetches historical price and dividend data for the available ETF universe using `HistoryService`.
4.  **Forecasting (Quantitative):**
    *   The `PortfolioOptimizer` calls the `ForecastingEngine`.
    *   The engine runs quantitative models (e.g., GBM, ARIMA) to estimate **Expected Returns** and **Volatility** for each asset over the next 6-12 months.
    *   *Note:* This process is automated and uses standard statistical assumptions.
5.  **Optimization:** The `PortfolioOptimizer` runs **Mean-Variance Optimization (MVO)** using the forecasted returns and historical covariance.
6.  **Output:** The system returns an optimal portfolio (list of assets and their recommended weights) to the user.

## 2. Research Agent Flow (Qualitative Analysis & "What If")

**Goal:** Provide qualitative insights and analyze specific market scenarios ("What If" analysis).
**User Query Example:** "What happens if there's a recession?" or "Analyze the tech sector."

### Workflow Steps:
1.  **User Input:** The user submits a natural language query.
2.  **ResearchAgent (LangGraph):** The agent orchestrates the analysis process.
3.  **Information Gathering:**
    *   Fetches market data via `HistoryService`.
    *   Fetches news/sentiment via `NewsService`.
    *   Fetches macro indicators via `MacroService`.
4.  **LLM Analysis (Qualitative):**
    *   The `LLMService` analysis the gathered data and the user's specific question.
    *   Calculates **Scenarios** (e.g., "Bear Case: Recession").
    *   Defines specific parameters for these scenarios (e.g., "Drift: -5%, Volatility: +20%").
    *   *Caching:* LLM responses are cached to prevent redundant API calls.
5.  **Simulation (Quantitative Validation):**
    *   The Agent calls the `ForecastingEngine` *using the LLM-generated scenario parameters*.
    *   The engine runs Monte Carlo simulations under these specific conditions.
6.  **Output:** The Agent generates a comprehensive report combining the qualitative reasoning (from the LLM) with the quantitative simulation results (charts, projected values).
