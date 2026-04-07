# Finance Tracker

ML-powered personal finance tracker with a FastAPI backend, Next.js frontend, MongoDB storage, and built-in analytics.

## Features

- Add, list, filter, update, and delete transactions
- CSV bulk import for bank/exported statements
- Auto-categorization for uncategorized transactions
- Dashboard with income, expenses, savings, and category breakdown
- Monthly trends and 30-day spending forecast
- Anomaly detection for unusual expense behavior
- Category-wise monthly budget tracking

## Tech Stack

- **Frontend:** Next.js (App Router), React, Recharts
- **Backend:** FastAPI, Pydantic, Motor (MongoDB async driver)
- **Database:** MongoDB
- **ML:** scikit-learn, pandas, numpy, Prophet, joblib

## Project Structure

```text
Finance_tracker/
├── backend/
│   ├── app/
│   │   ├── routes/       # API routes
│   │   ├── services/     # Business logic
│   │   ├── ml/           # Categorization, prediction, anomaly detection
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── main.py       # FastAPI entrypoint
│   │   └── config.py     # Environment config
│   └── requirements.txt
└── frontend/
    ├── src/app/          # App pages (Dashboard, Transactions, Analytics, Budget)
    ├── src/lib/api.js    # Frontend API client
    └── package.json
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (or newer LTS)
- npm
- MongoDB running locally (default: `mongodb://localhost:27017`)

## Backend Setup (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` (optional if defaults are fine):

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=finance_tracker
```

Run backend:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Frontend Setup (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

> Note: Frontend API base URL is currently set to `http://localhost:8000/api` in `frontend/src/lib/api.js`.

## Running Quality Checks

Frontend (available scripts):

```bash
cd frontend
npm run lint
npm run build
```

## Core API Endpoints

### Health

- `GET /` — service and model status
- `GET /api/health` — health check

### Transactions

- `GET /api/transactions`
- `POST /api/transactions`
- `PUT /api/transactions/{transaction_id}`
- `DELETE /api/transactions/{transaction_id}`
- `POST /api/transactions/upload-csv`

### Categories

- `GET /api/categories`
- `GET /api/categories/summary`

### Analytics

- `GET /api/analytics/overview`
- `GET /api/analytics/trends`
- `GET /api/analytics/predictions`
- `GET /api/analytics/anomalies`
- `GET /api/analytics/budget`
- `POST /api/analytics/budget`

## Notes

- Auto-categorization is applied when category is omitted during transaction creation.
- Prediction quality improves with more expense history (model training needs sufficient data).
- Anomaly detection is focused on expense transactions.
