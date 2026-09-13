'use client';

import React from 'react';

export default function PrivacyPage() {
  return (
    <div className="animate-fade-in">
      <div className="page-header" style={{ marginBottom: '2.5rem' }}>
        <h1 className="page-title">Privacy Policy</h1>
        <p className="page-subtitle">
          How HustleYetu collects, uses, and safeguards your data under the Kenya Data Protection Act (KDPA) 2019.
        </p>
      </div>

      <div style={{ maxWidth: '840px', marginBottom: '4rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              1. Commitment to Data Protection
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              HustleYetu is an independent civic platform dedicated to public legal literacy. We strictly adhere to the principles set out in the <strong>Kenya Data Protection Act, 2019 (KDPA)</strong> and the guidelines of the Office of the Data Protection Commissioner (ODPC).
            </p>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              2. Data We Collect
            </h2>
            <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <li>
                <strong>Mobile Phone Numbers:</strong> Collected exclusively when you opt in to receive SMS legislative notifications or when verifying feedback submission via OTP.
              </li>
              <li>
                <strong>Language Preference:</strong> Your chosen language (English or Swahili) for legislative SMS alerts.
              </li>
              <li>
                <strong>Citizen Stance & Feedback:</strong> Stance votes (Support, Oppose, Neutral), impact ratings (1–5), and voluntary written concerns submitted on specific bills.
              </li>
            </ul>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              3. How We Use Your Data
            </h2>
            <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <li>To dispatch SMS alerts regarding bills that affect the transport and informal workforce.</li>
              <li>To aggregate public opinion metrics anonymously for the citizen insights dashboard and submit aggregated reports to legislative clerks.</li>
              <li>We <strong>never</strong> sell, rent, monetize, or disclose individual user records or phone numbers to third parties or commercial advertisers.</li>
            </ul>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              4. Anonymous Aggregation & Gated Feedback
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              Phone verification for citizen feedback is used solely as a one-time anti-spam mechanism to ensure authentic public participation. Once verified, your stance and rating are aggregated into anonymous statistical totals. No feedback comment is publicly associated with your mobile number.
            </p>
          </div>

          <div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
              5. Your Rights & Unsubscribing
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
              Under the KDPA 2019, you retain the right to access, rectify, or request deletion of your phone number from our SMS registry at any time. You can deactivate your subscription immediately via our <a href="/subscribe" style={{ color: 'var(--primary)', fontWeight: 600 }}>Manage Subscription</a> page.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
