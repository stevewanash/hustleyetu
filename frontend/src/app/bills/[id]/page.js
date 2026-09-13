'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import FeedbackSection from '../../../components/FeedbackSection';
import LoadingSpinner from '../../../components/LoadingSpinner';
import { api } from '../../../lib/api';

const DEMO_BILLS_FALLBACK = {
  "finance-bill-2024": {
    id: "finance-bill-2024",
    title: "The Finance Bill, 2024",
    bill_type: "financial",
    tabled_date: "2024-05-09",
    source_url: "https://parliament.go.ke/bills/finance-bill-2024.pdf",
    ai_summary_en: "The Finance Bill, 2024 proposes significant taxation and fiscal adjustments aimed at revenue mobilization. For transport and mobility operators, key proposals include introducing an annual motor vehicle circulation tax calculated at 2.5% of the vehicle's declared value (with a minimum statutory cap of KES 5,000), revisions to fuel levy tariffs, and adjusted withholding tax thresholds for micro-enterprises.\n\nThe legislation also updates excise duties and introduces standardized electronic invoicing requirements. These provisions collectively alter operating overheads, fleet licensing costs, and daily cash-flow requirements for commercial transport service providers across Kenya.",
    ai_summary_sw: "Mswada wa Fedha, 2024 unapendekeza mabadiliko makubwa ya kodi na fedha yenye lengo la kuongeza mapato ya serikali. Kwa waendeshaji wa sekta ya usafirishaji, mapendekezo makuu ni pamoja na kuanzishwa kwa ushuru wa kila mwaka wa mzunguko wa magari uliopangwa kwa asilimia 2.5 ya thamani ya chombo (huku kima cha chini kikiwa KES 5,000), marekebisho ya tozo za mafuta, na viwango vya kodi ya zuio kwa biashara ndogo ndogo.\n\nSheria hii pia inasasisha ushuru wa bidhaa na kuanzisha mfumo wa ankara za kielektroniki. Vifungu hivi kwa pamoja vinabadilisha gharama za uendeshaji, ada za leseni, na mzunguko wa pesa wa kila siku kwa wahudumu wa usafiri nchini Kenya.",
    tags: ["Transport & Logistics", "Finance & Mobile Money"]
  },
  "nairobi-bodaboda-regulations-2025": {
    id: "nairobi-bodaboda-regulations-2025",
    title: "Nairobi Motorcycle Taxi (Boda Boda) Permit Regulations 2025",
    bill_type: "regulatory",
    tabled_date: "2025-02-18",
    source_url: "https://nairobi.go.ke/gazette/bodaboda-regulations-2025.pdf",
    ai_summary_en: "These county regulations mandate annual county operating permits for all commercial motorcycle taxi operators in Nairobi County. They enforce designated SACCO registration, biometric rider badge identification, two standard reflective helmets, and designated CBD pick-and-drop zones.\n\nFailure to comply with operating permits or safety specifications attracts county fines of up to KES 10,000 or vehicle impoundment.",
    ai_summary_sw: "Kanuni hizi za kaunti zinalazimisha vibali vya uendeshaji vya kila mwaka vya kaunti kwa waendeshaji wote wa bodaboda za kibiashara katika Kaunti ya Nairobi. Zinasisitiza usajili wa SACCO maalum, vitambulisho vya kibiometria vya waendeshaji, kofia mbili za usalama zenye viakisi, na maeneo maalum ya kushusha na kupakia mjini CBD.\n\nKukosa kufuata kanuni za vibali au viwango vya usalama kunaweza kupelekea faini ya hadi KES 10,000 au kuzuiliwa kwa chombo.",
    tags: ["Transport & Logistics"]
  }
};

export default function BillDetailPage() {
  const params = useParams();
  const billId = params?.id;

  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lang, setLang] = useState('en');

  useEffect(() => {
    if (!billId) return;

    async function loadBill() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getBill(billId);
        setBill(data);
      } catch (err) {
        console.warn(`Failed to fetch bill ${billId} from backend, checking demo fallback:`, err);
        if (DEMO_BILLS_FALLBACK[billId]) {
          setBill(DEMO_BILLS_FALLBACK[billId]);
        } else {
          setError(err.message || 'Bill not found');
        }
      } finally {
        setLoading(false);
      }
    }

    loadBill();
  }, [billId]);

  const currentSummary = () => {
    if (!bill) return '';
    if (lang === 'sw') {
      return bill.ai_summary_sw || 'Muhtasari wa Kiswahili bado haujakamilika (Swahili translation is currently pending pipeline processing).';
    }
    return bill.ai_summary_en || 'Summary is currently being processed by the AI pipeline.';
  };

  const hasSwahili = Boolean(bill?.ai_summary_sw);

  // F5: Only display date if a reliable tabled_date is available; otherwise omit completely
  const tabledDateRaw = bill?.tabled_date || bill?.date_tabled;
  const formattedTabledDate = tabledDateRaw
    ? new Date(tabledDateRaw).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : null;

  const isFinancial = (bill?.bill_type || 'financial').toLowerCase() === 'financial';

  return (
    <div className="animate-fade-in">
      {/* Navigation Breadcrumb */}
      <div style={{ marginTop: '0.5rem', marginBottom: '1.25rem' }}>
        <a href="/bills" className="back-link">
          ← Back to Browse Bills
        </a>
      </div>

      {/* F10: Spinner on Loading */}
      {loading && (
        <LoadingSpinner message="Loading legislative document details..." />
      )}

      {error && !bill && (
        <div style={{ background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', color: 'var(--danger)', padding: '1.5rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', textAlign: 'center' }}>
          <p style={{ fontWeight: 700, marginBottom: '0.25rem' }}>Unable to load bill</p>
          <p style={{ fontSize: '0.875rem' }}>{error}</p>
        </div>
      )}

      {!loading && bill && (
        <>
          {/* Consolidated Single-Surface Article Layout */}
          <article className="article-surface">
            {/* Headline Title */}
            <h1 className="article-headline">
              {bill.title}
            </h1>

            {/* Metadata Bar */}
            <div className="article-meta-row">
              <span className={isFinancial ? 'badge-financial' : 'badge-regulatory'}>
                {isFinancial ? 'Financial' : 'Regulatory'}
              </span>

              {/* F5: Tabled date if reliably present */}
              {formattedTabledDate && (
                <span>
                  Tabled: <strong>{formattedTabledDate}</strong>
                </span>
              )}

              {bill.tags && bill.tags.length > 0 && (
                <span>
                  Sector: <strong>{bill.tags.join(', ')}</strong>
                </span>
              )}
            </div>

            {/* Language Switcher Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
              <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Plain-Language Legislative Summary
              </h2>

              <div style={{ display: 'flex', background: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-full)', padding: '3px', border: '1px solid var(--border-color)' }}>
                <button
                  type="button"
                  onClick={() => setLang('en')}
                  style={{
                    background: lang === 'en' ? 'var(--primary)' : 'transparent',
                    border: 'none',
                    color: lang === 'en' ? '#ffffff' : 'var(--text-muted)',
                    padding: '0.25rem 0.85rem',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  English
                </button>
                <button
                  type="button"
                  onClick={() => setLang('sw')}
                  title={!hasSwahili ? "Swahili translation pending pipeline processing" : "Swahili summary"}
                  style={{
                    background: lang === 'sw' ? 'var(--primary)' : 'transparent',
                    border: 'none',
                    color: lang === 'sw' ? '#ffffff' : (!hasSwahili ? '#94a3b8' : 'var(--text-muted)'),
                    padding: '0.25rem 0.85rem',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  Swahili {!hasSwahili && <span style={{ fontSize: '0.65rem', opacity: 0.85, fontWeight: 500 }}>(Pending)</span>}
                </button>
              </div>
            </div>

            {/* Translation Pending Banner */}
            {lang === 'sw' && !hasSwahili && (
              <div style={{ background: 'var(--warning-bg)', borderLeft: '3.5px solid var(--warning)', padding: '0.75rem 1rem', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0', marginBottom: '1.25rem', fontSize: '0.875rem', color: 'var(--warning)' }}>
                Swahili translation for this bill has not completed pipeline processing yet. Displaying status notice.
              </div>
            )}

            {/* F5: Flowing Full-Width Article Body */}
            <div className="article-body-text">
              {currentSummary()}
            </div>

            {/* Action Footer */}
            <div className="article-action-footer">
              <div>
                {bill.source_url ? (
                  <a
                    href={bill.source_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: 'var(--primary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                  >
                    View Official Bill Document (PDF) &rarr;
                  </a>
                ) : (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Official PDF link pending gazettement</span>
                )}
              </div>

              <a
                href={`/impact/${bill.id || billId}`}
                className="btn-primary-accent"
                style={{ padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
              >
                View Impact &rarr;
              </a>
            </div>
          </article>

          {/* Shared Collapsible Citizen Feedback Section */}
          <FeedbackSection billId={billId} />
        </>
      )}
    </div>
  );
}
