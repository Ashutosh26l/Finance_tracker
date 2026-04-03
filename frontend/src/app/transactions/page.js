"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

const CATEGORIES = [
  "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
  "Entertainment", "Health & Fitness", "Education", "Travel",
  "Subscriptions", "Groceries", "Rent & Housing", "Income", "Other"
];

function AddTransactionModal({ onClose, onAdded, categories }) {
  const [form, setForm] = useState({
    description: "", amount: "", type: "expense",
    category: "", date: new Date().toISOString().split("T")[0], notes: "",
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createTransaction({
        ...form,
        amount: parseFloat(form.amount),
        category: form.category || null,
        date: form.date ? new Date(form.date).toISOString() : null,
      });
      onAdded();
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
          <h2 className="modal-title">Add Transaction</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Description</label>
            <input
              className="form-input"
              placeholder="e.g. Starbucks Coffee"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              required
              autoFocus
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Amount ($)</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0.00"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Type</label>
              <select
                className="form-select"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                Category <span style={{ color: "var(--text-muted)", fontWeight: 400, textTransform: "none" }}>(auto-detected if empty)</span>
              </label>
              <select
                className="form-select"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              >
                <option value="">🤖 Auto-detect with AI</option>
                {(categories || CATEGORIES).map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Date</label>
              <input
                className="form-input"
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Notes (optional)</label>
            <input
              className="form-input"
              placeholder="Add a note..."
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : "Add Transaction"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CSVUploadModal({ onClose, onUploaded }) {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const res = await api.uploadCSV(file);
      setResult(res);
      if (res.imported > 0) onUploaded();
    } catch (err) {
      alert("Upload error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Upload CSV</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {result ? (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>
              {result.imported > 0 ? "✅" : "⚠️"}
            </div>
            <p style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>
              {result.imported} transactions imported
            </p>
            {result.failed > 0 && (
              <div style={{ marginTop: 12 }}>
                <p style={{ color: "var(--accent-rose)", fontSize: 14, fontWeight: 'bold' }}>
                  {result.failed} failed
                </p>
                {result.errors?.length > 0 && (
                  <div style={{
                    maxHeight: 120, overflowY: "auto", textAlign: "left", 
                    background: "rgba(225,29,72,0.1)", padding: 8, borderRadius: 6,
                    fontSize: 12, marginTop: 8, color: "var(--text-secondary)",
                    fontFamily: "monospace"
                  }}>
                    {result.errors.map((err, i) => (
                      <div key={i} style={{ marginBottom: 4 }}>• {err}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div className="modal-actions" style={{ justifyContent: "center" }}>
              <button className="btn btn-primary" onClick={onClose}>Done</button>
            </div>
          </div>
        ) : (
          <>
            <div
              className={`upload-zone ${dragging ? "dragging" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                setFile(e.dataTransfer.files[0]);
              }}
              onClick={() => document.getElementById("csv-input").click()}
            >
              <div className="upload-zone-icon">📄</div>
              <p className="upload-zone-text">
                {file ? file.name : "Drop your CSV file here or click to browse"}
              </p>
              <p className="upload-zone-hint">
                Expected columns: description, amount, type, category, date
              </p>
              <input
                id="csv-input"
                type="file"
                accept=".csv"
                style={{ display: "none" }}
                onChange={(e) => setFile(e.target.files[0])}
              />
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={!file || loading}
              >
                {loading ? <span className="spinner" /> : "Upload & Import"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showCSV, setShowCSV] = useState(false);
  const [categories, setCategories] = useState(CATEGORIES);
  const [filters, setFilters] = useState({ search: "", category: "", type: "" });
  const perPage = 20;

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        skip: (page - 1) * perPage,
        limit: perPage,
      };
      if (filters.category) params.category = filters.category;
      if (filters.type) params.type = filters.type;
      if (filters.search) params.search = filters.search;

      const data = await api.getTransactions(params);
      setTransactions(data.transactions || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchTransactions();
    api.getCategories().then((d) => setCategories(d.categories || CATEGORIES)).catch(() => {});
  }, [fetchTransactions]);

  const handleDelete = async (id) => {
    if (!confirm("Delete this transaction?")) return;
    try {
      await api.deleteTransaction(id);
      fetchTransactions();
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <div>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">Transactions</h1>
          <p className="page-subtitle">{total} transaction{total !== 1 ? "s" : ""} total</p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <button className="btn btn-secondary" onClick={() => setShowCSV(true)}>
            📄 Upload CSV
          </button>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
            ➕ Add Transaction
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="toolbar">
        <div className="toolbar-search">
          <span className="toolbar-search-icon">🔍</span>
          <input
            className="form-input"
            placeholder="Search transactions..."
            value={filters.search}
            onChange={(e) => { setFilters({ ...filters, search: e.target.value }); setPage(1); }}
          />
        </div>
        <div className="toolbar-filters">
          <select
            className="form-select"
            value={filters.category}
            onChange={(e) => { setFilters({ ...filters, category: e.target.value }); setPage(1); }}
            style={{ width: 180 }}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <select
            className="form-select"
            value={filters.type}
            onChange={(e) => { setFilters({ ...filters, type: e.target.value }); setPage(1); }}
            style={{ width: 140 }}
          >
            <option value="">All Types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <div className="spinner" style={{ margin: "0 auto" }} />
          </div>
        ) : transactions.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">💳</div>
            <p className="empty-state-title">No transactions found</p>
            <p className="empty-state-text">Add your first transaction or upload a CSV to get started.</p>
            <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
              ➕ Add Transaction
            </button>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Description</th>
                <th>Category</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Date</th>
                <th style={{ width: 60 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn, i) => (
                <tr key={txn.id} className="animate-in" style={{ animationDelay: `${i * 30}ms` }}>
                  <td>
                    <span className="table-description">{txn.description}</span>
                    {txn.is_anomaly && (
                      <span className="badge badge-anomaly" style={{ marginLeft: 8, fontSize: 10 }}>
                        ⚠ Anomaly
                      </span>
                    )}
                    {txn.predicted_category && txn.predicted_category === txn.category && !txn.is_anomaly && (
                      <span className="badge badge-ml" style={{ marginLeft: 8 }}>🤖 AI</span>
                    )}
                  </td>
                  <td><span className="badge badge-category">{txn.category}</span></td>
                  <td>
                    <span className={`badge badge-${txn.type}`}>
                      {txn.type === "income" ? "↗ Income" : "↘ Expense"}
                    </span>
                  </td>
                  <td className={`table-amount ${txn.type}`}>
                    {txn.type === "income" ? "+" : "-"}${txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                    {new Date(txn.date).toLocaleDateString()}
                  </td>
                  <td>
                    <button
                      className="btn btn-ghost btn-icon"
                      onClick={() => handleDelete(txn.id)}
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 20 }}>
          <button
            className="btn btn-secondary"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            ← Prev
          </button>
          <span style={{ display: "flex", alignItems: "center", color: "var(--text-secondary)", fontSize: 14 }}>
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next →
          </button>
        </div>
      )}

      {/* Modals */}
      {showAdd && (
        <AddTransactionModal
          onClose={() => setShowAdd(false)}
          onAdded={fetchTransactions}
          categories={categories}
        />
      )}
      {showCSV && (
        <CSVUploadModal
          onClose={() => setShowCSV(false)}
          onUploaded={fetchTransactions}
        />
      )}
    </div>
  );
}
