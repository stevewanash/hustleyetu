'use client';

import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../../components/LoadingSpinner';
import { api } from '../../lib/api';
import { truncateWords } from '../../lib/excerpt';

const DEFAULT_DEMO_BILLS = [
  {
    id: "8992647a-c924-4e64-bed5-2136b9c2a402",
    title: "The Traffic (Motor Vehicle Inspection) Rules, 2026",
    bill_type: "regulatory",
    created_at: "2026-08-13T00:00:00Z",
    impact_summary: "Key statutory inspection intervals, compliance certificates, and penalty guidelines for commercial and private motor vehicles."
  },
  {
    id: "a7e1b8e6-b31e-42b6-8bc5-37be68ffecde",
    title: "The Nairobi City County Transport Act, 2020 — Motorcycle Taxi (Boda Boda) Permit Regulations, 2025",
    bill_type: "regulatory",
    created_at: "2026-08-05T00:00:00Z",
    impact_summary: "Key regulatory and compliance requirements for commercial motorcycle operators in Nairobi County."
  }
];

export default function ImpactListPage() {
  const [bills, setBills] = useState([]);
  const [filterType, setFilterType] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadBills() {
      try {
        setLoading(true);
        const res = await api.getBills(1, 50);
        if (res && res.bills && res.bills.length > 0) {
          const billsWithImpact = await Promise.all(
            res.bills.map(async (b) => {
              if (b.impact_summary) return b;
              try {
                const impactRes = await api.getImpact(b.id);
                return {
                  ...b,
                  impact_summary: impactRes?.concise_summary || b.ai_summary_en || ''
                };
              } catch (e) {
                return b;
              }
            })
          );
          setBills(billsWithImpact);
        } else {
          setBills(DEFAULT_DEMO_BILLS);
        }
      } catch (err) {
        console.warn('Failed to load bills via API, using fallback:', err);
        setBills(DEFAULT_DEMO_BILLS);
      } finally {
        setLoading(false);
      }
    }
    loadBills();
  }, []);

  const filteredBills = bills.filter((bill) => {
    if (filterType === 'ALL') return true;
    return bill.bill_type?.toLowerCase() === filterType.toLowerCase();
  });

  const getBillTypeBadge = (type) => {
    const isFin = (type || 'financial').toLowerCase() === 'financial';
    return isFin ? (
      <span className="badge-financial">Financial</span>
    ) : (
      <span className="badge-regulatory">Regulatory</span>
    );
  };

  const getImpactTeaser = (bill) => {
    const text = bill.impact_summary || bill.concise_summary || (
      bill.bill_type === 'regulatory'
        ? "Key regulatory compliance requirements, SACCO mandates, and county permit enforcement rules for transport operators."
        : "Key financial and tax policy impacts, motor vehicle levies, and cash-flow estimates for transport operators."
    );
    return truncateWords(text, 18);
  };

  return (
    <div className="animate-fade-in">
      {/* Page Header */}
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <h1 className="page-title">Legislative Impact & Calculators</h1>
        <p className="page-subtitle">
          Worked example scenarios, compliance guides, and client-side calculators for Kenya's bodaboda sector.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="content-card" style={{ marginBottom: '1.75rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <label htmlFor="filter-select" className="form-label" style={{ marginBottom: 0, fontWeight: 700 }}>Filter by Type:</label>
            <select
              id="filter-select"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="form-input"
              style={{
                width: 'auto',
                padding: '0.45rem 1rem',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <option value="ALL">All Legislation</option>
              <option value="financial">Financial</option>
              <option value="regulatory">Regulatory</option>
            </select>
          </div>

          <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Showing <strong>{filteredBills.length}</strong> of {bills.length} bills
          </div>
        </div>
      </div>

      {/* F10: Loading State with Spinner */}
      {loading && (
        <LoadingSpinner message="Loading legislative impact data..." />
      )}

      {/* Error Message */}
      {error && (
        <div style={{ padding: '1.25rem', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {/* Bills Cards List with Interactive Hover */}
      {!loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '3rem' }}>
          {filteredBills.map((bill) => (
            <div key={bill.id} className="content-card content-card-interactive">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                <h2 className="card-title" style={{ flex: '1', minWidth: '240px', fontSize: '1.3rem', lineHeight: '1.35' }}>
                  <a href={`/impact/${bill.id}`} style={{ color: 'var(--text-primary)', textDecoration: 'none' }}>
                    {bill.title}
                  </a>
                </h2>
                <div>
                  {getBillTypeBadge(bill.bill_type)}
                </div>
              </div>

              <p className="card-description" style={{ marginBottom: '1.25rem' }}>
                {getImpactTeaser(bill)}
              </p>

              <div style={{
                display: 'flex',
                justifyContent: 'flex-end',
                alignItems: 'center',
                paddingTop: '0.85rem',
                borderTop: '1px solid var(--border-color)'
              }}>
                <a
                  href={`/impact/${bill.id}`}
                  className="card-link"
                  style={{ fontSize: '0.925rem', fontWeight: 600 }}
                >
                  View Impact &rarr;
                </a>
              </div>
            </div>
          ))}

          {filteredBills.length === 0 && (
            <div className="content-card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: 'var(--text-muted)' }}>
              No legislation found matching the selected filter.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
