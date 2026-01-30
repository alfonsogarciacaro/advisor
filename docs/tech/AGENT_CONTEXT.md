# ETF Portfolio Advisor - Agent Context

## Project Overview
**ETF Portfolio Advisor** is an application that combines quantitative finance methods (efficient frontier, Monte Carlo simulations) with AI agent orchestration to provide personalized investment guidance.

## Architecture

### Frontend (`/frontend`)
- **Architecture**: Static SPA (Next.js static export, client-side only - no Next.js server).
- **Framework**: Next.js 14+ (App Router for routing), React.
- **Styling**: Tailwind CSS + DaisyUI.
- **Data**: Communicates directly with Backend API (no direct database access).

### Backend (`/backend`)
- **Framework**: Python with FastAPI.
- **Dependency Management**: `uv`.
- **Core Logic**:
    - **Optimization**: Portfolio optimization (scipy/cvxpy).
    - **Simulation**: Monte Carlo simulations.
    - **Planning**: Investment plan management (Tax accounts: NISA, iDeCo).
    - **Agents**: LLM-based research and qualitative analysis.
- **Persistence**: Firestore (abstracted via service layer).

### Infrastructure
- **Deployment**: Google Cloud Run (separate services: static frontend served from CDN, FastAPI backend).
- **Communication**: REST API. Long-running tasks return a job ID; frontend polls for results (future: direct Firestore subscriptions).

## Critical Development Rules
- **Python**: ALWAYS use `uv` for dependency management (`uv add`, `uv run`, `uv sync`) in the `backend/` directory.
- **Testing**:
    - Frontend: Playwright (`frontend/tests/`).
    - Backend: Pytest (`backend/tests/`).
- **Design**: Premium, responsive UI with "wow" factor.
- **Abstraction**: Do NOT use GCP APIs (Firestore, Pub/Sub) directly in business logic. Use the repository/service abstractions.

## Key Workflows
1.  **Portfolio Input**: User provides current holdings and preferences.
2.  **Optimization**: Backend calculates efficient frontier and optimal allocation.
3.  **Simulation**: Monte Carlo methods project future performance (Best/Worst/Avg).
4.  **Research**: AI agents analyze market sentiment/macro factors (using `ForecastingEngine` / `LLMService`).
5.  **Planning**: Users can save "Plans" with specific tax/recurring investment settings.

## Architecture Notes
- **Frontend is static** - No server-side Next.js features (no SSR, no API routes, no server components).
- **Service abstractions** - Business logic never calls GCP APIs directly; always use repository/service layer.
- **Japanese tax context** - Plan Management handles NISA (growth/general) and iDeCo accounts.
