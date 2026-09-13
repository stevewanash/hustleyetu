'use client';

import React from 'react';

export default function TermsPage() {
  return (
    <div className="animate-fade-in">
      <div className="page-header" style={{ marginBottom: '2.5rem' }}>
        <h1 className="page-title">Terms of Service</h1>
        <p className="page-subtitle">
          Guidelines and informational terms governing the use of the HustleYetu civic literacy platform.
        </p>
      </div>

      <div style={{ maxWidth: '840px', marginBottom: '4rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              1. Informational & Educational Purpose Only
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              HustleYetu provides plain-language summaries, worked scenarios, and cost estimates of Kenyan legislation and county regulations for educational and civic literacy purposes. The content provided on this platform does <strong>not</strong> constitute legal, financial, or formal tax advice. Operators and SACCOs should consult licensed legal professionals or official gazettes for binding legal counsel.
            </p>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              2. Government Independence Disclaimer
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              HustleYetu is an independent civic project. We are not an organ, branch, agency, or contractor of the Parliament of Kenya, the National Treasury, the Nairobi City County Assembly, or any national or county governmental authority. Official bill PDFs linked across our platform originate from public government portals for verification.
            </p>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              3. Acceptable Use & Citizen Participation
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              When submitting citizen feedback, users agree not to post defamatory, abusive, or unlawful content. Phone OTP verification is enforced to protect the integrity of public sentiment metrics against automated manipulation.
            </p>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              4. Accuracy & Limitations of Liability
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              While we strive for 100% accuracy in summarizing statutory provisions and financial formulas, bills undergo frequent legislative amendments during committee stages. HustleYetu assumes no liability for discrepancies between proposed bill versions and final enacted acts of Parliament.
            </p>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              5. Governing Law
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              These terms are governed by and construed in accordance with the Laws of the Republic of Kenya.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
