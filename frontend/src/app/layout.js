"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import "./globals.css";

const navItems = [
  { label: "Dashboard", href: "/", icon: "📊" },
  { label: "Transactions", href: "/transactions", icon: "💳" },
  { label: "Analytics", href: "/analytics", icon: "🧠" },
  { label: "Budget", href: "/budget", icon: "🎯" },
];

function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Link href="/" className="sidebar-logo">
          <div className="sidebar-logo-icon">💰</div>
          <span className="sidebar-logo-text">FinanceAI</span>
        </Link>
      </div>
      <nav className="sidebar-nav">
        <span className="nav-section-label">Menu</span>
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-link ${pathname === item.href ? "active" : ""}`}
          >
            <span className="nav-link-icon">{item.icon}</span>
            {item.label}
          </Link>
        ))}
        <span className="nav-section-label" style={{ marginTop: "auto" }}>
          System
        </span>
        <div className="nav-link" style={{ cursor: "default" }}>
          <span className="nav-link-icon">🤖</span>
          <span style={{ fontSize: "12px", color: "var(--text-tertiary)" }}>
            ML Models Active
          </span>
          <span
            style={{
              marginLeft: "auto",
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "var(--accent-emerald)",
              boxShadow: "0 0 8px rgba(16, 185, 129, 0.5)",
            }}
          />
        </div>
      </nav>
    </aside>
  );
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <title>FinanceAI — ML-Powered Finance Tracker</title>
        <meta
          name="description"
          content="Track your finances with AI-powered categorization, spending predictions, and anomaly detection."
        />
      </head>
      <body>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
