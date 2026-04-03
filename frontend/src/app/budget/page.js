"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

const CATEGORIES = [
  "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
  "Entertainment", "Health & Fitness", "Education", "Travel",
  "Subscriptions", "Groceries", "Rent & Housing", "Other"
];

function SetBudgetModal({ onClose, onSaved, categories, existingBudgets }) {
  const [category, setCategory] = useState("");
  const [limit, setLimit] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!category || !limit) return;
    setLoading(true);
    try {
      await api.setBudget(category, parseFloat(limit));
      onSaved();
      onClose();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Set Budget</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Category</label>
            <select
              className="form-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              required
            >
              <option value="">Select a category</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Monthly Budget Limit ($)</label>
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="1"
              placeholder="e.g. 500.00"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : "Save Budget"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function BudgetPage() {
  const [budgetData, setBudgetData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const fetchBudget = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getBudget();
      setBudgetData(data);
    } catch (err) {
      console.error("Budget fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBudget();
  }, [fetchBudget]);

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Budget</h1>
          <p className="page-subtitle">Track your spending against budget limits</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="budget-item">
              <div className="skeleton" style={{ height: 20, width: "40%", marginBottom: 12 }} />
              <div className="skeleton" style={{ height: 8, width: "100%" }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const budgets = budgetData?.budgets || [];
  const withLimit = budgets.filter((b) => b.budget_limit > 0);
  const withoutLimit = budgets.filter((b) => b.budget_limit === 0 && b.spent > 0);

  const statusEmoji = (status) => {
    switch (status) {
      case "on_track": return "✅";
      case "warning": return "⚠️";
      case "over_budget": return "🔴";
      default: return "—";
    }
  };

  const statusLabel = (status) => {
    switch (status) {
      case "on_track": return "On Track";
      case "warning": return "Warning";
      case "over_budget": return "Over Budget";
      default: return "—";
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">Budget</h1>
          <p className="page-subtitle">
            Track your spending against monthly budget limits
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          ➕ Set Budget
        </button>
      </div>

      {/* Overall Summary */}
      {budgetData && budgetData.total_budget > 0 && (
        <div className="stats-grid" style={{ marginBottom: 28 }}>
          <div className="stat-card expense animate-in stagger-1">
            <p className="stat-card-label">Total Budget</p>
            <p className="stat-card-value">
              ${budgetData.total_budget.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="stat-card savings animate-in stagger-2">
            <p className="stat-card-label">Total Spent</p>
            <p className="stat-card-value">
              ${budgetData.total_spent.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="stat-card income animate-in stagger-3">
            <p className="stat-card-label">Overall Utilization</p>
            <p className="stat-card-value">
              {budgetData.overall_utilization.toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Budget Items with limits */}
      {withLimit.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {withLimit.map((b, i) => (
            <div
              key={b.category}
              className="budget-item animate-in"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="budget-header">
                <div>
                  <span className="budget-category">{b.category}</span>
                  <span style={{ marginLeft: 10 }}>{statusEmoji(b.status)}</span>
                </div>
                <div className="budget-amounts">
                  <span>${b.spent.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  {" / "}
                  ${b.budget_limit.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div className="budget-progress">
                <div
                  className={`budget-progress-bar ${b.status}`}
                  style={{ width: `${Math.min(b.utilization, 100)}%` }}
                />
              </div>
              <div className="budget-status">
                <span style={{ color: b.status === "over_budget" ? "var(--accent-rose)" : b.status === "warning" ? "var(--accent-amber)" : "var(--accent-emerald)" }}>
                  {statusLabel(b.status)}
                </span>
                <span style={{ color: "var(--text-tertiary)" }}>
                  {b.remaining >= 0
                    ? `$${b.remaining.toFixed(2)} remaining`
                    : `$${Math.abs(b.remaining).toFixed(2)} over`}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-card">
          <div className="empty-state">
            <div className="empty-state-icon">🎯</div>
            <p className="empty-state-title">No budgets set yet</p>
            <p className="empty-state-text">
              Set monthly budget limits for your spending categories to track your progress
            </p>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              ➕ Set Your First Budget
            </button>
          </div>
        </div>
      )}

      {/* Unbudgeted spending */}
      {withoutLimit.length > 0 && (
        <div style={{ marginTop: 28 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--text-secondary)" }}>
            📋 Unbudgeted Categories (spending detected)
          </h3>
          <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Spent This Month</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {withoutLimit.map((b) => (
                  <tr key={b.category}>
                    <td>
                      <span className="badge badge-category">{b.category}</span>
                    </td>
                    <td className="table-amount expense">
                      ${b.spent.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost"
                        onClick={() => setShowModal(true)}
                        style={{ fontSize: 12 }}
                      >
                        Set Budget →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <SetBudgetModal
          onClose={() => setShowModal(false)}
          onSaved={fetchBudget}
          categories={CATEGORIES}
          existingBudgets={budgets}
        />
      )}
    </div>
  );
}
