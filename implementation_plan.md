# ML-Powered Finance Tracker — Implementation Plan

Build a full-stack, local-only, single-user ML finance tracker with **Next.js** frontend, **FastAPI** backend, and **local MongoDB**.

## Assumptions (since you said "let's do it")

Since you didn't specify, I'm going with these sensible defaults:
- **Scope**: Single user (personal), no auth needed
- **Data source**: Manual entry + CSV upload
- **Stack**: Next.js (frontend) + FastAPI (backend/ML)
- **Database**: Local MongoDB
- **ML features** (in order): Auto-categorization → Spending prediction → Anomaly detection

> [!IMPORTANT]
> **Prerequisite**: You need **MongoDB Community Server** installed and running locally on the default port (`27017`). You also need **Python 3.10+** and **Node.js 18+**. Let me know if any of these are missing.

---

## Project Structure

```
Finance_tracker/
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app entry + CORS + lifespan
│   │   ├── database.py         # MongoDB connection (Motor async)
│   │   ├── config.py           # Settings via pydantic-settings
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── transaction.py  # Transaction Pydantic models
│   │   │   └── analytics.py    # Analytics response models
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── transactions.py # CRUD + CSV upload endpoints
│   │   │   ├── categories.py   # Category management
│   │   │   └── analytics.py    # ML-powered analytics endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── transaction_service.py
│   │   │   └── analytics_service.py
│   │   └── ml/
│   │       ├── __init__.py
│   │       ├── categorizer.py  # TF-IDF + Random Forest model
│   │       ├── predictor.py    # Prophet spending forecaster
│   │       ├── anomaly.py      # Isolation Forest detector
│   │       └── training_data/
│   │           └── seed_transactions.csv  # Seed data for initial model
│   ├── requirements.txt
│   └── .env
│
├── frontend/                   # Next.js App
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.js       # Root layout with sidebar nav
│   │   │   ├── page.js         # Dashboard (home)
│   │   │   ├── globals.css     # Global styles + design system
│   │   │   ├── transactions/
│   │   │   │   └── page.js     # Transaction list + add/edit
│   │   │   ├── analytics/
│   │   │   │   └── page.js     # ML insights + charts
│   │   │   └── budget/
│   │   │       └── page.js     # Budget management
│   │   ├── components/
│   │   │   ├── Sidebar.js      # Navigation sidebar
│   │   │   ├── StatCard.js     # Metric cards
│   │   │   ├── TransactionTable.js
│   │   │   ├── AddTransactionModal.js
│   │   │   ├── CSVUploadModal.js
│   │   │   ├── SpendingChart.js      # Recharts line/area chart
│   │   │   ├── CategoryPieChart.js   # Recharts pie chart
│   │   │   ├── AnomalyAlert.js       # Anomaly notification cards
│   │   │   └── PredictionChart.js    # Future spending forecast
│   │   └── lib/
│   │       └── api.js          # API client (fetch wrapper)
│   ├── package.json
│   └── next.config.js
│
└── README.md
```

---

## Proposed Changes

### Backend — FastAPI + ML

#### [NEW] `backend/requirements.txt`
Dependencies: `fastapi`, `uvicorn`, `motor`, `pydantic`, `pydantic-settings`, `python-multipart`, `scikit-learn`, `pandas`, `numpy`, `prophet`, `joblib`

#### [NEW] `backend/.env`
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=finance_tracker
```

#### [NEW] `backend/app/config.py`
Pydantic `BaseSettings` loading from `.env` — MongoDB URL, DB name.

#### [NEW] `backend/app/database.py`
Motor async client with lifespan management. Provides `get_db()` dependency.

#### [NEW] `backend/app/main.py`
FastAPI app with:
- CORS middleware (allow `localhost:3000`)
- Lifespan events for MongoDB connect/disconnect
- Router includes for all route modules

#### [NEW] `backend/app/schemas/transaction.py`
Pydantic models:
- `TransactionCreate` — amount, description, date, category (optional), type (income/expense)
- `TransactionResponse` — includes `_id`, `predicted_category`, `is_anomaly`
- `TransactionUpdate` — partial update model

#### [NEW] `backend/app/routes/transactions.py`
Endpoints:
- `GET /api/transactions` — list with filters (date range, category, type)
- `POST /api/transactions` — create (auto-categorize if no category given)
- `PUT /api/transactions/{id}` — update
- `DELETE /api/transactions/{id}` — delete
- `POST /api/transactions/upload-csv` — bulk import from CSV

#### [NEW] `backend/app/routes/categories.py`
- `GET /api/categories` — list all categories
- `GET /api/categories/summary` — spending per category (current month)

#### [NEW] `backend/app/routes/analytics.py`
- `GET /api/analytics/overview` — total income, expenses, savings, trends
- `GET /api/analytics/predictions` — next 30 days spending forecast
- `GET /api/analytics/anomalies` — flagged unusual transactions

#### [NEW] `backend/app/ml/categorizer.py`
- **Model**: TF-IDF vectorizer + Random Forest classifier
- **Training**: Seed data with ~500 labeled transactions across 10 categories (Food, Transport, Shopping, Bills, Entertainment, Health, Education, Travel, Subscriptions, Other)
- Trained on startup, model cached via `joblib`
- `predict_category(description: str) -> str` function

#### [NEW] `backend/app/ml/predictor.py`
- **Model**: Simple linear regression on historical spending (Prophet if enough data)
- `predict_spending(days: int) -> list[dict]` — returns predicted daily spending
- Falls back to rolling average if < 30 transactions

#### [NEW] `backend/app/ml/anomaly.py`
- **Model**: Isolation Forest on (amount, hour_of_day, day_of_week, category_encoded)
- `detect_anomalies(transactions: list) -> list[str]` — returns IDs of anomalous transactions
- Trained on user's historical data

#### [NEW] `backend/app/ml/training_data/seed_transactions.csv`
~500 synthetic labeled transactions for initial model training.

---

### Frontend — Next.js

#### [NEW] `frontend/` — Next.js project
Initialized via `npx create-next-app@latest` with App Router, no TypeScript (plain JS), vanilla CSS.

#### [NEW] `frontend/src/app/globals.css`
Design system:
- Dark theme with glassmorphism cards
- CSS custom properties for colors, spacing, typography
- Google Font: Inter
- Smooth transitions & micro-animations
- Responsive grid system

#### [NEW] `frontend/src/app/layout.js`
Root layout with persistent sidebar navigation (Dashboard, Transactions, Analytics, Budget).

#### [NEW] `frontend/src/app/page.js` (Dashboard)
- 4 stat cards: Total Income, Total Expenses, Net Savings, Anomalies Detected
- Spending trend chart (area chart, last 6 months)
- Category breakdown (pie chart)
- Recent transactions list (last 5)

#### [NEW] `frontend/src/app/transactions/page.js`
- Full transaction table with sorting & filtering
- "Add Transaction" button → modal form
- "Upload CSV" button → file upload modal
- Inline category badge with ML-predicted indicator
- Anomaly warning badges on flagged transactions

#### [NEW] `frontend/src/app/analytics/page.js`
- Spending prediction chart (next 30 days forecast)
- Anomaly alerts with transaction details
- Category spending trends over time
- Monthly comparison bar chart

#### [NEW] `frontend/src/app/budget/page.js`
- Set monthly budgets per category
- Progress bars showing budget utilization
- Over-budget alerts
- Suggested budgets based on spending history

#### [NEW] `frontend/src/components/` — All reusable components
Recharts-based charts, stat cards, modals, tables — all with `"use client"` directive and premium dark theme styling.

#### [NEW] `frontend/src/lib/api.js`
Centralized API client with functions for all backend endpoints. Base URL: `http://localhost:8000`.

---

## UI Design Direction

- **Theme**: Dark mode with deep navy/charcoal background (`#0a0e1a`)
- **Accent colors**: Vibrant gradient (cyan `#00d4ff` → purple `#7c3aed`)
- **Cards**: Glassmorphism with `backdrop-filter: blur()` and subtle borders
- **Typography**: Inter font, clean hierarchy
- **Charts**: Gradient fills, smooth curves, glowing tooltips
- **Animations**: Fade-in on mount, hover scale on cards, smooth page transitions
- **Layout**: Fixed sidebar + scrollable main content area

---

## Verification Plan

### Automated
1. Start MongoDB locally
2. `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
3. `cd frontend && npm install && npm run dev`
4. Test all API endpoints via browser at `http://localhost:8000/docs` (Swagger UI)
5. Verify frontend renders at `http://localhost:3000`

### Manual / Browser Testing
- Add transactions manually and verify auto-categorization works
- Upload a CSV and confirm bulk import
- Check dashboard charts render with real data
- Verify anomaly detection flags unusual transactions
- Test prediction chart shows forecast
- Confirm responsive design on different viewport sizes
