'use client';

import React from 'react';

const STEPS = [
  {
    step: '1',
    title: 'Bill Tracking & Official Gazette Ingestion',
    desc: 'We monitor official legislative repositories including the Parliament of Kenya and County Assembly gazettes for newly tabled financial bills and transport sector regulations.'
  },
  {
    step: '2',
    title: 'Plain-Language & Bilingual Synthesis',
    desc: 'Our specialized policy models distill hundreds of pages of legal text into concise 2–4 paragraph overviews in plain English and Swahili, eliminating dense jargon.'
  },
  {
    step: '3',
    title: 'Worked Impact Modeling & Calculators',
    desc: 'We model representative worked scenarios (such as an operator with a 150cc motorcycle) to demonstrate exact tax changes, circulation levies, or compliance steps with live browser calculators.'
  },
  {
    step: '4',
    title: 'Proactive SMS Alert Broadcasts',
    desc: 'Subscribers receive timely SMS notifications as bills are tabled in parliament, ensuring operators are never surprised by new laws.'
  },
  {
    step: '5',
    title: 'Anonymous Citizen Feedback Aggregation',
    desc: 'Operators submit verified public stances, ratings, and concerns. We aggregate this data into live civic insights and deliver public memos to parliamentary committees.'
  }
];

export default function HowItWorksPage() {
  return (
    <div className="animate-fade-in">
      <div className="page-header" style={{ marginBottom: '2.5rem' }}>
        <h1 className="page-title">How HustleYetu Works</h1>
        <p className="page-subtitle">
          From parliamentary bills to actionable insights on your phone in 5 clear steps.
        </p>
      </div>

      <div style={{ maxWidth: '820px', marginBottom: '4rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.25rem' }}>
          {STEPS.map((item, idx) => (
            <div key={idx} style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
              <div
                style={{
                  minWidth: '38px',
                  height: '38px',
                  borderRadius: '50%',
                  background: 'var(--primary)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: 'var(--font-title)',
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  boxShadow: '0 2px 6px rgba(30, 78, 66, 0.25)',
                  marginTop: '0.15rem'
                }}
              >
                {item.step}
              </div>
              <div>
                <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                  {item.title}
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.975rem', lineHeight: '1.7' }}>
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '3rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <a href="/bills" className="btn-primary-accent">
            Browse Analyzed Bills &rarr;
          </a>
          <a href="/subscribe" className="btn-secondary-outline">
            Sign Up for SMS Alerts
          </a>
        </div>
      </div>
    </div>
  );
}
