const API_BASE = "http://localhost:8000/api";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  // Transactions
  getTransactions: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/transactions?${query}`);
  },
  createTransaction: (data) =>
    request("/transactions", { method: "POST", body: JSON.stringify(data) }),
  updateTransaction: (id, data) =>
    request(`/transactions/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteTransaction: (id) =>
    request(`/transactions/${id}`, { method: "DELETE" }),
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/transactions/upload-csv`, {
      method: "POST",
      body: formData,
    });
    return await res.json();
  },

  // Categories
  getCategories: () => request("/categories"),
  getCategorySummary: () => request("/categories/summary"),

  // Analytics
  getOverview: (period = 30) => request(`/analytics/overview?period=${period}`),
  getTrends: (months = 6) => request(`/analytics/trends?months=${months}`),
  getPredictions: (days = 30) => request(`/analytics/predictions?days=${days}`),
  getAnomalies: () => request("/analytics/anomalies"),
  getBudget: () => request("/analytics/budget"),
  setBudget: (category, limit) =>
    request("/analytics/budget", {
      method: "POST",
      body: JSON.stringify({ category, limit }),
    }),
};
