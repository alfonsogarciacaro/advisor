# ETF Portfolio Advisor - Project Specification

## Project Overview

An AI-powered ETF portfolio advisor that combines quantitative finance methods (portfolio optimization, efficient frontier, Monte Carlo simulations) with AI agent orchestration to provide personalized investment guidance. The system analyzes user portfolios and offers scenario-based projections with intelligent rebalancing recommendations.

## Core Value Proposition

- Users input their current ETF portfolio distribution
- System uses quantitative methods + AI agents to analyze market conditions
- Provides best-case, worst-case, and most likely scenarios through Monte Carlo simulations
- Offers rebalancing recommendations accounting for transaction costs and taxes
- Focuses primarily on ETFs for simplicity

## Technology Stack

### Frontend
- **Next.js 14+** (App Router)
- **Tailwind CSS** + **DaisyUI** for styling
- **Mastra** for AI agent orchestration
- **Recharts** or **D3.js** for data visualization

### Backend
- **Python** with **FastAPI**
- Quantitative libraries: NumPy, SciPy, pandas
- Portfolio optimization libraries (e.g., PyPortfolioOpt, cvxpy)

### Infrastructure (Google Cloud Platform)
- **Cloud Run**: Hosting for Next.js frontend and Python backend (separate services)
- **Pub/Sub**: Message queue for asynchronous processing
- **Firestore**: NoSQL database for user data and portfolio states
- **Cloud Logging**: Automatic logging and monitoring

### Local Development
- **Docker Compose**: Orchestrate all services locally
- **Firestore Emulator**: Local database for development
- **Pub/Sub Emulator**: Local message queue

## Architecture Principles

### Dependency Injection & Abstraction
**CRITICAL**: All vendor-specific APIs must be abstracted through dependency injection. Never use GCP APIs directly in business logic.

#### Examples:
```python
# ❌ BAD - Direct vendor dependency
from google.cloud import firestore
db = firestore.Client()
db.collection('portfolios').add(data)

# ✅ GOOD - Abstracted through interface
class DatabaseRepository(ABC):
    @abstractmethod
    def save_portfolio(self, portfolio: Portfolio) -> str:
        pass

class FirestoreRepository(DatabaseRepository):
    def save_portfolio(self, portfolio: Portfolio) -> str:
        # Firestore implementation here
        pass
```

```typescript
// ❌ BAD - Direct vendor dependency
import { PubSub } from '@google-cloud/pubsub';
const pubsub = new PubSub();
await pubsub.topic('calculations').publish(data);

// ✅ GOOD - Abstracted through interface
interface QueueService {
  publish(topic: string, data: unknown): Promise<void>;
}

class PubSubQueueService implements QueueService {
  async publish(topic: string, data: unknown): Promise<void> {
    // Pub/Sub implementation
  }
}
```

### Layers to Abstract:
1. **Database Layer**: All Firestore operations
2. **Queue Layer**: All Pub/Sub operations
3. **Logging Layer**: All Cloud Logging operations
4. **Storage Layer**: Any file/blob storage (if needed later)

## System Architecture

### High-Level Flow

```
User Input (Portfolio) 
    ↓
Next.js Frontend (Mastra Agents)
    ↓
Pub/Sub Queue
    ↓
Python Backend (Quant Calculations)
    ↓
Results stored in Firestore
    ↓
Frontend polls/subscribes for results
    ↓
Display visualizations & recommendations
```

### Components

#### 1. Next.js Frontend + Mastra Agents

**AI Agent Network:**
- **Market Research Agent**: Reads financial news, performs sentiment analysis on sectors/ETFs
- **Historical Data Analyst**: Analyzes ETF performance, correlations, volatility patterns
- **Economic Context Agent**: Interprets macro conditions (Fed policy, inflation, etc.)
- **Risk Assessment Agent**: Evaluates portfolio risk metrics, tail risks
- **Coordination Agent**: Synthesizes insights from all agents to inform simulations

**Responsibilities:**
- User interface for portfolio input
- Orchestrate AI agents for market intelligence gathering
- Publish calculation requests to Pub/Sub
- Poll/subscribe for calculation results
- Visualize efficient frontier, scenario paths, recommendations
- Display rebalancing suggestions

**Key Pages/Routes:**
- `/` - Landing page with project description
- `/portfolio/input` - Form for current portfolio entry
- `/portfolio/analysis` - Display results, visualizations, recommendations
- `/api/calculate` - API route to trigger calculations (publishes to Pub/Sub)
- `/api/results/[id]` - API route to fetch calculation results

#### 2. Python Backend (FastAPI)

**Quantitative Engine Responsibilities:**
- Portfolio optimization (mean-variance, Black-Litterman)
- Efficient frontier calculation
- Monte Carlo simulation engine
- Rebalancing optimization with constraints

**Exposed Endpoints:**

##### `POST /api/v1/optimize`
Calculate optimal portfolio allocation on efficient frontier.

**Request:**
```json
{
  "current_portfolio": [
    {"ticker": "VTI", "allocation": 0.60},
    {"ticker": "VXUS", "allocation": 0.30},
    {"ticker": "BND", "allocation": 0.10}
  ],
  "risk_tolerance": "moderate",
  "time_horizon_years": 10,
  "constraints": {
    "min_allocation": 0.05,
    "max_allocation": 0.70
  }
}
```

**Response:**
```json
{
  "optimal_portfolio": [
    {"ticker": "VTI", "allocation": 0.55},
    {"ticker": "VXUS", "allocation": 0.35},
    {"ticker": "BND", "allocation": 0.10}
  ],
  "expected_return": 0.078,
  "expected_volatility": 0.145,
  "sharpe_ratio": 0.52
}
```

##### `POST /api/v1/simulate`
Run Monte Carlo simulations for portfolio scenarios.

**Request:**
```json
{
  "portfolio": [
    {"ticker": "VTI", "allocation": 0.60},
    {"ticker": "VXUS", "allocation": 0.30},
    {"ticker": "BND", "allocation": 0.10}
  ],
  "initial_investment": 100000,
  "time_horizon_years": 10,
  "num_simulations": 10000,
  "market_conditions": {
    "sentiment": "neutral",
    "volatility_adjustment": 1.0,
    "correlation_adjustment": 1.0
  }
}
```

**Response:**
```json
{
  "scenarios": {
    "best_case": {
      "final_value": 245000,
      "cagr": 0.095,
      "percentile": 95
    },
    "most_likely": {
      "final_value": 178000,
      "cagr": 0.059,
      "percentile": 50
    },
    "worst_case": {
      "final_value": 125000,
      "cagr": 0.023,
      "percentile": 5
    }
  },
  "simulation_paths": [
    [100000, 105000, 98000, ...],
    [100000, 103000, 110000, ...]
  ],
  "statistics": {
    "mean_final_value": 178000,
    "std_dev": 45000,
    "probability_of_loss": 0.12
  }
}
```

##### `POST /api/v1/rebalance/analyze`
Determine if rebalancing is worthwhile.

**Request:**
```json
{
  "current_portfolio": [
    {"ticker": "VTI", "allocation": 0.65, "current_value": 65000},
    {"ticker": "VXUS", "allocation": 0.25, "current_value": 25000},
    {"ticker": "BND", "allocation": 0.10, "current_value": 10000}
  ],
  "target_portfolio": [
    {"ticker": "VTI", "allocation": 0.60},
    {"ticker": "VXUS", "allocation": 0.30},
    {"ticker": "BND", "allocation": 0.10}
  ],
  "constraints": {
    "transaction_cost_percent": 0.001,
    "tax_rate_short_term": 0.24,
    "tax_rate_long_term": 0.15,
    "holding_periods": {
      "VTI": 400,
      "VXUS": 200,
      "BND": 500
    }
  },
  "rebalance_threshold": 0.05
}
```

**Response:**
```json
{
  "should_rebalance": true,
  "drift_analysis": {
    "max_drift": 0.083,
    "drifted_assets": ["VTI", "VXUS"]
  },
  "cost_benefit": {
    "estimated_transaction_costs": 450,
    "estimated_tax_impact": 1200,
    "total_rebalancing_cost": 1650,
    "expected_benefit_1year": 2800,
    "net_benefit": 1150,
    "payback_period_months": 7
  }
}
```

##### `POST /api/v1/rebalance/execute`
Calculate optimal rebalancing trades.

**Request:**
```json
{
  "current_portfolio": [
    {"ticker": "VTI", "allocation": 0.65, "current_value": 65000, "shares": 250},
    {"ticker": "VXUS", "allocation": 0.25, "current_value": 25000, "shares": 450},
    {"ticker": "BND", "allocation": 0.10, "current_value": 10000, "shares": 125}
  ],
  "target_portfolio": [
    {"ticker": "VTI", "allocation": 0.60},
    {"ticker": "VXUS", "allocation": 0.30},
    {"ticker": "BND", "allocation": 0.10}
  ],
  "constraints": {
    "transaction_cost_percent": 0.001,
    "tax_rate_short_term": 0.24,
    "tax_rate_long_term": 0.15,
    "holding_periods": {
      "VTI": 400,
      "VXUS": 200,
      "BND": 500
    },
    "min_trade_size": 100
  },
  "optimization_goal": "minimize_cost"
}
```

**Response:**
```json
{
  "trades": [
    {
      "ticker": "VTI",
      "action": "sell",
      "shares": 19,
      "estimated_value": 4940,
      "tax_impact": 280,
      "transaction_cost": 4.94
    },
    {
      "ticker": "VXUS",
      "action": "buy",
      "shares": 90,
      "estimated_value": 5000,
      "transaction_cost": 5.00
    }
  ],
  "summary": {
    "total_transaction_costs": 9.94,
    "total_tax_impact": 280,
    "total_cost": 289.94,
    "resulting_portfolio": [
      {"ticker": "VTI", "allocation": 0.601, "value": 60060},
      {"ticker": "VXUS", "allocation": 0.299, "value": 30000},
      {"ticker": "BND", "allocation": 0.100, "value": 10000}
    ],
    "max_deviation_from_target": 0.001
  }
}
```

##### `GET /api/v1/market-data/{ticker}`
Fetch historical data and current stats for an ETF.

**Response:**
```json
{
  "ticker": "VTI",
  "name": "Vanguard Total Stock Market ETF",
  "current_price": 260.45,
  "historical_returns": {
    "1year": 0.22,
    "3year": 0.098,
    "5year": 0.135,
    "10year": 0.118
  },
  "volatility": 0.18,
  "expense_ratio": 0.0003,
  "as_of_date": "2026-01-27"
}
```

#### 3. Pub/Sub Queue

**Topics:**
- `portfolio-optimization-requests`
- `monte-carlo-simulation-requests`
- `rebalancing-analysis-requests`

**Message Flow:**
1. Frontend publishes calculation request with unique job ID
2. Python backend subscribes to topics, processes requests
3. Results stored in Firestore with job ID
4. Frontend polls Firestore for results or uses webhooks/SSE

#### 4. Firestore Database

**Collections:**

##### `portfolios`
```json
{
  "id": "uuid",
  "userId": "user-123",
  "name": "My Retirement Portfolio",
  "assets": [
    {"ticker": "VTI", "allocation": 0.60, "shares": 250, "costBasis": 52000}
  ],
  "totalValue": 100000,
  "createdAt": "2026-01-27T10:00:00Z",
  "updatedAt": "2026-01-27T10:00:00Z"
}
```

##### `calculation_jobs`
```json
{
  "id": "job-uuid",
  "type": "monte_carlo_simulation",
  "status": "completed",
  "portfolioId": "portfolio-uuid",
  "requestPayload": {},
  "result": {},
  "createdAt": "2026-01-27T10:00:00Z",
  "completedAt": "2026-01-27T10:02:30Z",
  "error": null
}
```

##### `market_intelligence`
```json
{
  "id": "uuid",
  "date": "2026-01-27",
  "sentiment": {
    "overall": "neutral",
    "sectors": {
      "technology": "bullish",
      "energy": "bearish"
    }
  },
  "keyFindings": [
    "Fed maintaining current rates",
    "Tech sector showing strong momentum"
  ],
  "sources": ["reuters", "bloomberg"],
  "generatedBy": "market-research-agent",
  "createdAt": "2026-01-27T09:00:00Z"
}
```

## Data Sources

### Free/Accessible APIs:
- **yfinance** (Python library) - Historical ETF data
- **Alpha Vantage** - Additional market data (free tier available)
- **FRED API** - Economic indicators (Federal Reserve data)
- **NewsAPI** or web scraping - Financial news for sentiment analysis

## User Flow

### Phase 1: Portfolio Input
1. User navigates to `/portfolio/input`
2. Form to enter:
   - ETF tickers and allocations (must sum to 100%)
   - Total portfolio value
   - Risk tolerance (conservative, moderate, aggressive)
   - Time horizon (years)
   - Tax situation (short-term/long-term rates)
   - Transaction cost assumptions

### Phase 2: Agent Research (Parallel)
1. Market Research Agent queries recent financial news
2. Historical Data Analyst pulls ETF performance data
3. Economic Context Agent analyzes macro indicators
4. Risk Assessment Agent evaluates current market risks
5. Coordination Agent synthesizes findings

### Phase 3: Calculation Request
1. Frontend publishes message to Pub/Sub with:
   - Portfolio details
   - Agent insights (sentiment, volatility adjustments)
   - Simulation parameters
2. User sees loading state with agent activity
3. Backend picks up message and processes

### Phase 4: Results Display
1. Frontend polls for job completion
2. Once completed, displays:
   - Efficient frontier chart
   - Three scenario paths (interactive line chart)
   - Current vs optimal allocation (bar chart)
   - Key statistics (expected return, volatility, Sharpe ratio)
   - Rebalancing recommendation card

### Phase 5: Rebalancing Analysis (Optional)
1. User clicks "Analyze Rebalancing"
2. System calculates if rebalancing is worthwhile
3. If yes, shows specific trades needed
4. Displays cost-benefit breakdown
5. User can export trade instructions

## Key Features for Prototype

### Must Have (MVP):
- Portfolio input form with validation
- Basic agent orchestration with Mastra (2-3 agents)
- Monte Carlo simulation (3 scenarios)
- Efficient frontier visualization
- Simple rebalancing analysis (yes/no recommendation)
- Responsive UI with Tailwind + DaisyUI
- Docker Compose setup for local development
- Cloud Run deployment configuration

### Nice to Have (V2):
- User authentication
- Save multiple portfolios
- Historical portfolio tracking
- Email alerts for rebalancing opportunities
- Tax-loss harvesting suggestions
- Comparison with benchmark indices
- Export reports to PDF

### Explicitly Out of Scope (For Now):
- Background workers / scheduled jobs
- Real-time market data streaming
- Actual trade execution
- Multi-user collaboration
- Mobile app

## Project Structure

```
/etf-portfolio-advisor
├── /frontend                  # Next.js application
│   ├── /app                   # Next.js 14 app router
│   ├── /components            # React components
│   ├── /lib                   # Utilities
│   │   ├── /agents            # Mastra agent definitions
│   │   ├── /services          # Abstracted services
│   │   │   ├── queue.service.ts
│   │   │   ├── database.service.ts
│   │   │   └── logging.service.ts
│   │   └── /repositories      # Data access layer
│   ├── /public                # Static assets
│   ├── Dockerfile
│   └── package.json
│
├── /backend                   # Python FastAPI application
│   ├── /app
│   │   ├── /api               # API routes
│   │   │   └── /v1
│   │   │       ├── optimize.py
│   │   │       ├── simulate.py
│   │   │       └── rebalance.py
│   │   ├── /core              # Business logic
│   │   │   ├── portfolio_optimizer.py
│   │   │   ├── monte_carlo.py
│   │   │   └── rebalancer.py
│   │   ├── /models            # Pydantic models
│   │   ├── /services          # Abstracted services
│   │   │   ├── database_service.py
│   │   │   ├── queue_service.py
│   │   │   └── market_data_service.py
│   │   ├── /repositories      # Data access layer
│   │   └── /utils             # Helper functions
│   ├── /tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docker-compose.yml         # Local development setup
├── .env.example               # Environment variables template
└── README.md
```

## Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
GCP_PROJECT_ID=your-project-id
PUBSUB_TOPIC_OPTIMIZATION=portfolio-optimization-requests
PUBSUB_TOPIC_SIMULATION=monte-carlo-simulation-requests
FIRESTORE_EMULATOR_HOST=localhost:8080  # Only for local dev
```

### Backend (.env)
```bash
GCP_PROJECT_ID=your-project-id
FIRESTORE_EMULATOR_HOST=localhost:8080  # Only for local dev
PUBSUB_EMULATOR_HOST=localhost:8085     # Only for local dev
ALPHA_VANTAGE_API_KEY=your-key
NEWS_API_KEY=your-key
```

## Technical Considerations

### Performance:
- Monte Carlo simulations should complete in < 30 seconds
- Efficient frontier calculation < 10 seconds
- Frontend should feel responsive with loading indicators
- Consider caching market data (daily refresh)

### Security:
- No user authentication in V1 (add later)
- Validate all input data
- Rate limiting on API endpoints
- Sanitize user inputs
- Use service accounts with minimal permissions in GCP

### Scalability:
- Pub/Sub allows horizontal scaling of Python workers
- Cloud Run auto-scales based on traffic
- Firestore handles concurrent reads/writes
- Abstract architecture allows easy migration to other providers

### Testing:
- Unit tests for quant algorithms (pytest)
- Integration tests for API endpoints
- Frontend component tests (Jest/Vitest)
- E2E tests for critical user flows (Playwright)

### Monitoring:
- Cloud Logging for all services
- Track calculation job success/failure rates
- Monitor API endpoint latency
- Set up error alerting
