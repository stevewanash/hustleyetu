'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import FeedbackSection from '../../../components/FeedbackSection';
import LoadingSpinner from '../../../components/LoadingSpinner';
import { api } from '../../../lib/api';

export default function ImpactDetailPage() {
  const params = useParams();
  const billId = params?.id;

  const [impactData, setImpactData] = useState(null);
  const [billDetail, setBillDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Client-side calculator state
  const [customValue, setCustomValue] = useState(150000);
  const [calcResult, setCalcResult] = useState(null);

  useEffect(() => {
    if (!billId) return;

    async function loadData() {
      try {
        setLoading(true);
        const [impactRes, billRes] = await Promise.all([
          api.getImpact(billId).catch(() => null),
          api.getBill(billId).catch(() => null)
        ]);

        setImpactData(impactRes);
        setBillDetail(billRes);

        if (impactRes?.scenario_persona?.metrics?.vehicle_value) {
          setCustomValue(impactRes.scenario_persona.metrics.vehicle_value);
        }
      } catch (err) {
        console.error('Error loading impact detail:', err);
        setError(err.message || 'Failed to load impact details');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [billId]);

  // Deterministic calculator formula evaluation
  useEffect(() => {
    if (!impactData || impactData.bill_type === 'regulatory') return;

    const val = Number(customValue) || 0;
    const formula = impactData.calculator_formula || 'min(max(vehicle_value * 0.025, 5000), 100000)';

    let annualCost = 0;
    try {
      if (formula.includes('min') || formula.includes('max')) {
        const evalFn = new Function('vehicle_value', 'min', 'max', `return ${formula};`);
        annualCost = evalFn(val, Math.min, Math.max);
      } else {
        const evalFn = new Function('vehicle_value', `return ${formula};`);
        annualCost = evalFn(val);
      }
    } catch (e) {
      annualCost = val * 0.025;
      if (annualCost < 5000) annualCost = 5000;
      if (annualCost > 100000) annualCost = 100000;
    }

    setCalcResult({
      annual: Math.round(annualCost),
      monthly: Math.round(annualCost / 12)
    });
  }, [customValue, impactData]);

  const isFinancial = impactData?.bill_type !== 'regulatory';

  const getRiskChip = (riskLevel) => {
    const level = (riskLevel || 'MEDIUM').toUpperCase();
    if (level === 'HIGH') {
      return <span className="chip-risk-high">High Risk</span>;
    }
    if (level === 'LOW') {
      return <span className="chip-risk-low">Low Risk</span>;
    }
    return <span className="chip-risk-medium">Medium Risk</span>;
  };

  return (
    <div className="animate-fade-in">
      {/* Back Link */}
      <div style={{ marginTop: '0.5rem', marginBottom: '1.25rem' }}>
        <a href="/impact" className="back-link">
          ← Back to Legislative Impact Center
        </a>
      </div>

      {/* Loading Spinner */}
      {loading && (
        <LoadingSpinner message="Loading worked impact scenario..." />
      )}

      {error && (
        <div style={{ background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', color: 'var(--danger)', padding: '1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {!loading && impactData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginBottom: '3rem' }}>
          {/* Main Continuous Narrative Surface */}
          <article className="article-surface">
            {/* Header: Title, Risk Chip, Type Badge */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <h1 style={{ fontFamily: 'var(--font-title)', fontSize: '1.85rem', fontWeight: 700, flex: '1', minWidth: '240px', color: 'var(--text-primary)', lineHeight: 1.25 }}>
                {impactData.bill_title || billDetail?.title || 'Legislative Document'}
              </h1>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                {getRiskChip(impactData.risk_level)}
                <span className={isFinancial ? 'badge-financial' : 'badge-regulatory'}>
                  {isFinancial ? 'Financial' : 'Regulatory'}
                </span>
              </div>
            </div>

            {/* Concise Summary */}
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.025rem', lineHeight: '1.7', marginBottom: '1.75rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', width: '100%' }}>
              {impactData.concise_summary || billDetail?.ai_summary_en}
            </p>

            {/* FINANCIAL SECTION FLOW: Scenario -> Policy Figures -> Math -> Calculator */}
            {isFinancial && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2.25rem' }}>
                {/* 1. Worked Example Narrative */}
                <div>
                  <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                    1. Representative Operator Scenario
                  </h3>
                  <div className="callout-box">
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--primary)', display: 'block', marginBottom: '0.35rem' }}>
                      Persona
                    </span>
                    <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                      {impactData.scenario_persona?.description || 'A boda boda rider operating a 150cc motorcycle valued at KES 150,000 for daily commercial transport services.'}
                    </p>
                  </div>
                </div>

                {/* 2. Key Policy Figures */}
                {impactData.key_figures && impactData.key_figures.length > 0 && (
                  <div>
                    <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                      2. Statutory Policy Parameters
                    </h3>
                    <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
                      {impactData.key_figures.map((fig, idx) => (
                        <span key={idx} className="badge-neutral" style={{ fontSize: '0.825rem', padding: '0.35rem 0.75rem', fontWeight: 600 }}>
                          {fig}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Step-by-Step Math Breakdown */}
                {impactData.math_breakdown && impactData.math_breakdown.length > 0 && (
                  <div>
                    <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                      3. Step-by-Step Financial Math Breakdown
                    </h3>
                    <div style={{ background: 'var(--bg-card-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontFamily: 'monospace', fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                      {impactData.math_breakdown.map((line, idx) => (
                        <div key={idx} style={{ display: 'flex', gap: '0.5rem' }}>
                          <span style={{ color: 'var(--primary)', fontWeight: 700 }}>&bull;</span>
                          <span className="tabular-nums">{line}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 4. Interactive Client-Side Calculator: Header & Text OUTSIDE colored container */}
                <div>
                  <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                    4. Live Interactive Cost Calculator
                  </h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
                    Test custom asset values in your browser to evaluate exact levy formulas before paying.
                  </p>

                  <div style={{ background: 'var(--bg-card-alt)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', width: '100%', boxSizing: 'border-box' }}>
                    {/* Responsive Grid: Stacks on mobile without horizontal clipping */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', alignItems: 'center', width: '100%' }}>
                      <div className="form-group" style={{ marginBottom: 0, width: '100%' }}>
                        <label className="form-label" style={{ fontWeight: 700 }}>
                          Declared Motorcycle / Vehicle Value (KES):
                        </label>
                        <input
                          type="number"
                          value={customValue}
                          onChange={(e) => setCustomValue(e.target.value)}
                          step="10000"
                          min="10000"
                          className="form-input tabular-nums"
                          style={{ fontSize: '1.15rem', fontWeight: 700, width: '100%', boxSizing: 'border-box' }}
                        />
                        <span className="form-hint">Standard market valuation range: KES 80,000 – 350,000</span>
                      </div>

                      <div style={{ background: 'var(--bg-card)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', textAlign: 'center', boxShadow: 'var(--shadow-sm)', width: '100%', boxSizing: 'border-box' }}>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                          Estimated Annual Cost Impact
                        </span>
                        <div className="tabular-nums" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--primary)', margin: '0.35rem 0' }}>
                          KES {calcResult?.annual ? calcResult.annual.toLocaleString() : 0} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 500 }}>/ year</span>
                        </div>
                        <div className="tabular-nums" style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 600 }}>
                          ~ KES {calcResult?.monthly ? calcResult.monthly.toLocaleString() : 0} / month
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* REGULATORY SECTION FLOW: Changes -> Compliance Checklist & Actions */}
            {!isFinancial && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                {/* 1. Regulatory Provisions */}
                {impactData.regulatory_changes && impactData.regulatory_changes.length > 0 && (
                  <div>
                    <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                      1. Key Regulatory Provisions & County Mandates
                    </h3>
                    <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.975rem', lineHeight: '1.7' }}>
                      {impactData.regulatory_changes.map((change, idx) => (
                        <li key={idx} style={{ marginBottom: '0.4rem' }}>{change}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 2. Action Items Checklist */}
                {impactData.compliance_checklist && impactData.compliance_checklist.length > 0 && (
                  <div>
                    <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                      2. Operator Compliance Checklist & Deadlines
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      {impactData.compliance_checklist.map((item, idx) => (
                        <div key={idx} style={{ padding: '1rem 1.25rem', background: 'var(--bg-card-subtle)', borderLeft: '3.5px solid var(--primary)', borderRadius: '0 var(--radius-md) var(--radius-md) 0', border: '1px solid var(--border-color)', borderLeftWidth: '3.5px' }}>
                          <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.975rem', marginBottom: '0.35rem' }}>
                            {item.action}
                          </div>
                          <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.825rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                            <span>Deadline: <strong>{item.deadline || 'Statutory Enforcement'}</strong></span>
                            <span>Legal Reference: <strong>{item.source || 'County Gazette'}</strong></span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Official PDF Document Link */}
            {(impactData.pdf_url || billDetail?.source_url) && (
              <div style={{ borderTop: '1px solid var(--border-color)', marginTop: '2.25rem', paddingTop: '1.25rem' }}>
                <a
                  href={impactData.pdf_url || billDetail?.source_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: 'var(--primary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                >
                  View Official Bill Document (PDF) &rarr;
                </a>
              </div>
            )}
          </article>

          {/* Shared Collapsible Citizen Feedback Section */}
          <FeedbackSection billId={billId} />
        </div>
      )}
    </div>
  );
}
