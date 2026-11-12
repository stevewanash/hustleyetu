'use client';

import React, { useState, useEffect } from 'react';
import DonutChart from '../../components/DonutChart';
import LoadingSpinner from '../../components/LoadingSpinner';
import DashboardAuthGate from '../../components/DashboardAuthGate';
import { getDashboardSession, logoutDashboard } from '../../lib/dashboardAuth';
import { api } from '../../lib/api';

const DEFAULT_DEMO_BILLS = [
  { id: "8992647a-c924-4e64-bed5-2136b9c2a402", title: "The Traffic (Motor Vehicle Inspection) Rules, 2026" },
  { id: "a7e1b8e6-b31e-42b6-8bc5-37be68ffecde", title: "The Nairobi City County Transport Act, 2020 — Motorcycle Taxi (Boda Boda) Permit Regulations, 2025" }
];

export default function DashboardPage() {
  const [session, setSession] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  const [bills, setBills] = useState([]);
  const [selectedBill, setSelectedBill] = useState('');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 1. Verify Authentication on Client Mount
  useEffect(() => {
    const active = getDashboardSession();
    if (active) {
      setSession(active);
    }
    setAuthChecked(true);
  }, []);

  // 2. Fetch bills once authenticated
  useEffect(() => {
    if (!session) return;

    async function loadBills() {
      try {
        const response = await api.getBills(1, 100);
        const billList = (response?.bills && response.bills.length > 0)
          ? response.bills
          : DEFAULT_DEMO_BILLS;

        setBills(billList);
        if (billList.length > 0) {
          setSelectedBill(billList[0].id);
        }
      } catch (err) {
        console.warn('Failed to load bills for dashboard dropdown, using fallback:', err);
        setBills(DEFAULT_DEMO_BILLS);
        setSelectedBill(DEFAULT_DEMO_BILLS[0].id);
      }
    }

    loadBills();
  }, [session]);

  // 3. Fetch stats for selected bill once authenticated
  useEffect(() => {
    if (!session || !selectedBill) return;

    async function loadStats() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getDashboardStats(selectedBill);
        setStats(data);
      } catch (err) {
        console.error('Failed to load dashboard stats:', err);
        setError('Failed to load feedback statistics for the selected bill');
        setStats({
          total_feedback: 0,
          support_pct: { support: 0.0, oppose: 0.0, neutral: 0.0 },
          avg_rating: 0.0,
          top_concerns: []
        });
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, [session, selectedBill]);

  const handleSignOut = () => {
    logoutDashboard();
    setSession(null);
    setSelectedBill('');
    setStats(null);
  };

  // Prevent hydration flash while checking session
  if (!authChecked) {
    return (
      <div className="animate-fade-in" style={{ padding: '4rem 0', textAlign: 'center' }}>
        <LoadingSpinner message="Checking dashboard authorization..." />
      </div>
    );
  }

  // If unauthenticated, display the protected Dashboard Auth Gate
  if (!session) {
    return (
      <div className="animate-fade-in">
        <DashboardAuthGate onAuthenticated={(newSession) => setSession(newSession)} />
      </div>
    );
  }

  const supportPct = stats?.support_pct || { support: 0, oppose: 0, neutral: 0 };
  const totalResponses = stats?.total_feedback || 0;
  const avgRating = stats?.avg_rating ? Number(stats.avg_rating).toFixed(1) : '0.0';
  const topConcerns = stats?.top_concerns || [];
  const currentBillObj = bills.find((b) => b.id === selectedBill);

  // Visual 5-dot rating indicator
  const renderRatingDots = (ratingNum) => {
    const score = Math.round(Number(ratingNum) || 0);
    return (
      <div className="rating-visual-stars" aria-label={`Average rating ${ratingNum} out of 5`}>
        {[1, 2, 3, 4, 5].map((idx) => (
          <span
            key={idx}
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: idx <= score ? 'var(--primary)' : 'var(--border-color)',
              display: 'inline-block'
            }}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="animate-fade-in">
      {/* Authenticated Session Status Bar */}
      <div className="dashboard-auth-status-bar">
        <div className="dashboard-auth-status-left">
          <span className="auth-live-dot" aria-hidden="true" />
          <span className="auth-session-text">Authenticated Session:</span>
          <strong className="auth-user-email">{session.user?.identifier}</strong>
          <span className="auth-role-tag">{session.user?.role || 'Verified Analyst'}</span>
        </div>
        <button
          type="button"
          className="btn-dashboard-signout"
          onClick={handleSignOut}
          title="Lock and sign out of dashboard"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          Lock & Sign Out
        </button>
      </div>

      <div className="page-header" style={{ marginBottom: '1.75rem' }}>
        <h1 className="page-title">Citizen Insights Dashboard</h1>
        <p className="page-subtitle">
          Anonymously aggregated public sentiment on transport legislation.
        </p>
      </div>

      {/* Bill Selector Dropdown (F9: No "All Bills" aggregate option) */}
      <div className="content-card" style={{ marginBottom: '2rem', padding: '1.25rem 1.5rem' }}>
        <label htmlFor="bill-selector" className="form-label" style={{ fontWeight: 700, marginBottom: '0.4rem' }}>
          Select Bill to View Insights:
        </label>
        <select
          id="bill-selector"
          className="form-input"
          value={selectedBill}
          onChange={(e) => setSelectedBill(e.target.value)}
          style={{ maxWidth: '640px', cursor: 'pointer', fontWeight: 600 }}
        >
          {bills.map((b) => (
            <option key={b.id} value={b.id}>{b.title}</option>
          ))}
        </select>
        {currentBillObj && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Showing verified responses specifically for: <strong>{currentBillObj.title}</strong>
          </div>
        )}
      </div>

      {/* Loading State with Spinner */}
      {loading && (
        <LoadingSpinner message="Aggregating verified citizen stance metrics..." />
      )}

      {error && !loading && (
        <div style={{ background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', color: 'var(--danger)', padding: '1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {!loading && stats && (
        <div className="dashboard-grid">
          {/* Card 1: Stance Distribution Donut Chart */}
          <div className="content-card">
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1.5rem', textAlign: 'center' }}>
              Public Stance Distribution
            </h2>

            <DonutChart
              supportPct={supportPct}
              totalResponses={totalResponses}
            />
          </div>

          {/* Right Column: Headline Stats + Ranked Concerns */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Card 2: Headline Stats */}
            <div className="content-card">
              <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1.25rem' }}>
                Feedback Overview
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.25rem' }}>
                <div style={{ background: 'var(--bg-card-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, marginBottom: '0.25rem' }}>
                    Total Responses
                  </div>
                  <div className="stat-big-number">
                    {totalResponses}
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Verified citizens</span>
                </div>

                <div style={{ background: 'var(--bg-card-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, marginBottom: '0.25rem' }}>
                    Average Rating
                  </div>
                  <div className="stat-rating-number">
                    {avgRating} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 400 }}>/ 5</span>
                  </div>
                  {renderRatingDots(avgRating)}
                </div>
              </div>

              <div style={{ fontSize: '0.825rem', color: 'var(--primary)', lineHeight: 1.5 }}>
                <strong>Privacy Assured:</strong> All feedback is gathered with explicit KDPA compliance and tallied anonymously to prevent individual identification.
              </div>
            </div>

            {/* Card 3: Tight Ranked Concerns List */}
            <div className="content-card">
              <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                Top Public Concerns & Inquiries
              </h2>

              {topConcerns.length > 0 ? (
                <div className="concerns-ranked-list">
                  {topConcerns.map((concern, idx) => (
                    <div key={idx} className="concern-rank-item">
                      <span className="concern-rank-number">
                        {idx + 1}.
                      </span>
                      <span className="concern-rank-text">
                        {concern}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  No specific citizen concerns submitted yet for this bill.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
