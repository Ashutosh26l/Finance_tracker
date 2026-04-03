"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line, Legend,
} from "recharts";

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

export default function AnalyticsPage() {
  const [predictions, setPredictions] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [trends, setTrends] = useState([]);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAll() {
      try {
        const [predData, anomData, trendData, overviewData] = await Promise.all([
          api.getPredictions(30).catch(() => null),
          api.getAnomalies().catch(() => null),
          api.getTrends(6).catch(() => []),
          api.getOverview(30).catch(() => null),
        ]);
        setPredictions(predData);
        setAnomalies(anomData);
        setTrends(trendData || []);
        setOverview(overviewData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, []);

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">ML-powered financial insights</p>
        </div>
        <div className="stats-grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="stat-card" style={{ height: 120 }}>
              <div className="skeleton" style={{ height: 20, width: "60%", marginBottom: 12 }} />
              <div className="skeleton" style={{ height: 28, width: "45%" }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const predChart = predictions?.predictions?.map((p) => ({
    date: new Date(p.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    predicted: p.predicted_amount,
    lower: p.lower_bound,
    upper: p.upper_bound,
  })) || [];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <p className="page-subtitle">ML-powered financial insights & predictions</p>
      </div>

      {/* ML Stats */}
      <div className="stats-grid">
        <div className="stat-card savings animate-in stagger-1">
          <div className="stat-card-header">
            <div className="stat-card-icon" style={{ background: "rgba(99, 102, 241, 0.12)", color: "#6366f1" }}>🧠</div>
          </div>
          <p className="stat-card-label">Predicted Spending (30d)</p>
          <p className="stat-card-value">
            ${predictions?.total_predicted?.toLocaleString() || "—"}
          </p>
        </div>
        <div className="stat-card anomaly animate-in stagger-2">
          <div className="stat-card-header">
            <div className="stat-card-icon" style={{ background: "rgba(245, 158, 11, 0.12)", color: "#f59e0b" }}>⚠️</div>
          </div>
          <p className="stat-card-label">Anomalies Detected</p>
          <p className="stat-card-value">{anomalies?.total_flagged || 0}</p>
        </div>
        <div className="stat-card income animate-in stagger-3">
          <div className="stat-card-header">
            <div className="stat-card-icon" style={{ background: "rgba(16, 185, 129, 0.12)", color: "#10b981" }}>🎯</div>
          </div>
          <p className="stat-card-label">Categorization Accuracy</p>
          <p className="stat-card-value">
            {predictions?.categorizer_accuracy
              ? `${(predictions.categorizer_accuracy * 100).toFixed(1)}%`
              : "—"}
          </p>
        </div>
      </div>

      {/* Prediction Chart */}
      <div className="chart-card animate-in" style={{ marginBottom: 20 }}>
        <div className="chart-title">
          <span className="chart-title-icon">🔮</span>
          30-Day Spending Forecast
          <span className="badge badge-ml" style={{ marginLeft: 12 }}>
            🤖 ML Prediction
          </span>
        </div>
        {predChart.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={predChart}>
              <defs>
                <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="boundGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.1} />
                  <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" interval={4} />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#boundGrad)" name="Upper Bound" />
              <Area type="monotone" dataKey="predicted" stroke="#6366f1" fill="url(#predGrad)" strokeWidth={2.5} name="Predicted" />
              <Area type="monotone" dataKey="lower" stroke="transparent" fill="none" name="Lower Bound" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">🔮</div>
            <p className="empty-state-title">Not enough data for predictions</p>
            <p className="empty-state-text">Add at least 14 transactions to enable spending forecasts</p>
          </div>
        )}
      </div>

      <div className="charts-grid">
        {/* Monthly Comparison */}
        <div className="chart-card animate-in">
          <div className="chart-title">
            <span className="chart-title-icon">📊</span>
            Monthly Comparison
          </div>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={(value) => (
                    <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{value}</span>
                  )}
                />
                <Bar dataKey="income" fill="#10b981" radius={[4, 4, 0, 0]} name="Income" />
                <Bar dataKey="expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} name="Expenses" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <p className="empty-state-text">Add transactions to see monthly comparisons</p>
            </div>
          )}
        </div>

        {/* Anomaly Alerts */}
        <div className="chart-card animate-in">
          <div className="chart-title">
            <span className="chart-title-icon">🚨</span>
            Anomaly Alerts
            {anomalies?.total_flagged > 0 && (
              <span className="nav-link-badge" style={{ marginLeft: 8 }}>
                {anomalies.total_flagged}
              </span>
            )}
          </div>
          {anomalies?.anomalies?.length > 0 ? (
            <div style={{ maxHeight: 300, overflowY: "auto" }}>
              {anomalies.anomalies.map((a, i) => (
                <div key={i} className="anomaly-card">
                  <div className="anomaly-header">
                    <span className="anomaly-icon">⚠️</span>
                    <span className="anomaly-title">{a.description}</span>
                    <span className="anomaly-amount">
                      ${a.amount?.toLocaleString()}
                    </span>
                  </div>
                  <p className="anomaly-reason">{a.reason}</p>
                  <div style={{ paddingLeft: 36, marginTop: 8 }}>
                    <span className="badge badge-category">{a.category}</span>
                    <span style={{ color: "var(--text-tertiary)", fontSize: 12, marginLeft: 8 }}>
                      {new Date(a.date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: "40px 20px" }}>
              <div className="empty-state-icon" style={{ fontSize: 40 }}>✅</div>
              <p className="empty-state-title" style={{ fontSize: 16 }}>No Anomalies Detected</p>
              <p className="empty-state-text">All your transactions look normal</p>
            </div>
          )}
        </div>
      </div>

      {/* Category Trends */}
      {overview?.categories?.length > 0 && (
        <div className="chart-card animate-in" style={{ marginTop: 20 }}>
          <div className="chart-title">
            <span className="chart-title-icon">📈</span>
            Top Spending Categories (This Month)
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={overview.categories.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="category" type="category" width={120} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="total" fill="#6366f1" radius={[0, 4, 4, 0]} name="Spent">
                {overview.categories.slice(0, 8).map((_, i) => {
                  const colors = ["#6366f1", "#8b5cf6", "#22d3ee", "#10b981", "#f43f5e", "#f59e0b", "#3b82f6", "#ec4899"];
                  return <rect key={i} fill={colors[i % colors.length]} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
