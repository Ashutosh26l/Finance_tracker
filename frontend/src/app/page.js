"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from "recharts";

const COLORS = [
  "#6366f1", "#8b5cf6", "#22d3ee", "#10b981", "#f43f5e",
  "#f59e0b", "#3b82f6", "#ec4899", "#14b8a6", "#a855f7",
  "#f97316", "#84cc16", "#06b6d4",
];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload) return null;
  return (
    <div className="custom-tooltip">
      <p className="label">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="value" style={{ color: entry.color }}>
          {entry.name}: ${entry.value?.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

function StatCard({ label, value, icon, type, trend, trendValue }) {
  return (
    <div className={`stat-card ${type} animate-in`}>
      <div className="stat-card-header">
        <div className="stat-card-icon">{icon}</div>
        {trendValue !== undefined && trendValue !== 0 && (
          <span className={`stat-card-trend ${trend}`}>
            {trend === "up" ? "↑" : "↓"} {Math.abs(trendValue)}%
          </span>
        )}
      </div>
      <p className="stat-card-label">{label}</p>
      <p className="stat-card-value">{value}</p>
    </div>
  );
}

function RecentTransactions({ transactions }) {
  if (!transactions?.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <p className="empty-state-title">No transactions yet</p>
        <p className="empty-state-text">
          Add your first transaction to see it here
        </p>
      </div>
    );
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Description</th>
          <th>Category</th>
          <th>Amount</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {transactions.slice(0, 6).map((txn, i) => (
          <tr key={txn.id} className="animate-in" style={{ animationDelay: `${i * 50}ms` }}>
            <td className="table-description">
              {txn.description}
              {txn.is_anomaly && <span className="badge badge-anomaly" style={{ marginLeft: 8 }}>⚠</span>}
            </td>
            <td><span className="badge badge-category">{txn.category}</span></td>
            <td className={`table-amount ${txn.type}`}>
              {txn.type === "income" ? "+" : "-"}${txn.amount.toLocaleString()}
            </td>
            <td style={{ color: "var(--text-secondary)", fontSize: 13 }}>
              {new Date(txn.date).toLocaleDateString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [overviewData, trendsData, txnData] = await Promise.all([
          api.getOverview(30).catch(() => null),
          api.getTrends(6).catch(() => []),
          api.getTransactions({ limit: 6 }).catch(() => ({ transactions: [] })),
        ]);
        setOverview(overviewData);
        setTrends(trendsData || []);
        setTransactions(txnData?.transactions || []);
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Your financial overview at a glance</p>
        </div>
        <div className="stats-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="stat-card" style={{ height: 140 }}>
              <div className="skeleton" style={{ height: 20, width: "60%", marginBottom: 12 }} />
              <div className="skeleton" style={{ height: 32, width: "40%" }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const fmt = (n) => `$${(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Your financial overview at a glance —{" "}
          {new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" })}
        </p>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        <StatCard
          label="Total Income"
          value={fmt(overview?.total_income)}
          icon="💰"
          type="income"
          trend={overview?.income_trend >= 0 ? "up" : "down"}
          trendValue={overview?.income_trend}
        />
        <StatCard
          label="Total Expenses"
          value={fmt(overview?.total_expenses)}
          icon="💸"
          type="expense"
          trend={overview?.expense_trend >= 0 ? "up" : "down"}
          trendValue={overview?.expense_trend}
        />
        <StatCard
          label="Net Savings"
          value={fmt(overview?.net_savings)}
          icon="🏦"
          type="savings"
        />
        <StatCard
          label="Avg Daily Spend"
          value={fmt(overview?.avg_daily_spending)}
          icon="📈"
          type="anomaly"
        />
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Spending Trend */}
        <div className="chart-card">
          <div className="chart-title">
            <span className="chart-title-icon">📈</span>
            Monthly Trends
          </div>
          {trends?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={trends}>
                <defs>
                  <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="income" stroke="#10b981" fill="url(#incomeGrad)" strokeWidth={2} name="Income" />
                <Area type="monotone" dataKey="expenses" stroke="#f43f5e" fill="url(#expenseGrad)" strokeWidth={2} name="Expenses" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <p className="empty-state-text">Add transactions to see trends</p>
            </div>
          )}
        </div>

        {/* Category Breakdown */}
        <div className="chart-card">
          <div className="chart-title">
            <span className="chart-title-icon">🍩</span>
            By Category
          </div>
          {overview?.categories?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={overview.categories}
                  dataKey="total"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  stroke="none"
                >
                  {overview.categories.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) =>
                    active && payload?.[0] ? (
                      <div className="custom-tooltip">
                        <p className="label">{payload[0].name}</p>
                        <p className="value">${payload[0].value?.toLocaleString()}</p>
                      </div>
                    ) : null
                  }
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => (
                    <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <p className="empty-state-text">No expense data yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="chart-card">
        <div className="chart-title">
          <span className="chart-title-icon">🕐</span>
          Recent Transactions
        </div>
        <RecentTransactions transactions={transactions} />
      </div>
    </div>
  );
}
