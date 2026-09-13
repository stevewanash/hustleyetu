'use client';

import React, { useState } from 'react';

export default function ReportPage() {
  const [billTitle, setBillTitle] = useState('');
  const [issueType, setIssueType] = useState('summary');
  const [description, setDescription] = useState('');
  const [suggestedCorrection, setSuggestedCorrection] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();

    // Compose mailto link to wanangwesteve@gmail.com
    const subject = encodeURIComponent(`[HustleYetu Inaccuracy Report] ${billTitle || 'General Inaccuracy'}`);
    const body = encodeURIComponent(
      `HUSTLEYETU CORRECTION REPORT\n` +
      `============================\n\n` +
      `Bill Title / Page URL: ${billTitle}\n` +
      `Type of Inaccuracy: ${issueType}\n\n` +
      `Description:\n${description}\n\n` +
      `Suggested Correction:\n${suggestedCorrection || 'N/A'}\n\n` +
      `Reporter Contact:\n${contactEmail || 'Anonymous'}\n\n` +
      `Timestamp: ${new Date().toISOString()}\n`
    );

    const mailtoUrl = `mailto:wanangwesteve@gmail.com?subject=${subject}&body=${body}`;
    window.location.href = mailtoUrl;

    setSubmitted(true);
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header" style={{ marginBottom: '2.5rem' }}>
        <h1 className="page-title">Report Incorrect Information</h1>
        <p className="page-subtitle">
          Help us maintain 100% statutory accuracy. Submit corrections on legislative summaries, math breakdowns, or dates directly to our verification team.
        </p>
      </div>

      <div style={{ maxWidth: '680px', marginBottom: '4rem' }}>
        {submitted ? (
          <div style={{ padding: '2rem 0' }}>
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'var(--success-bg)',
                border: '2px solid var(--success-border)',
                color: 'var(--success)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                fontWeight: 700,
                marginBottom: '1.25rem'
              }}
            >
              ✓
            </div>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Thank You for Your Report
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6', marginBottom: '1.5rem' }}>
              Your correction report has been dispatched to <strong>wanangwesteve@gmail.com</strong>. Our policy verification team will review your correction against the official gazette within 24 hours.
            </p>
            <button
              type="button"
              className="btn-text"
              onClick={() => {
                setSubmitted(false);
                setBillTitle('');
                setDescription('');
                setSuggestedCorrection('');
              }}
            >
              Submit another correction &rarr;
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Bill Title or Page URL</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. The Finance Bill, 2024 or /bills/finance-bill-2024"
                value={billTitle}
                onChange={(e) => setBillTitle(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Type of Inaccuracy</label>
              <select
                className="form-input"
                value={issueType}
                onChange={(e) => setIssueType(e.target.value)}
                style={{ cursor: 'pointer' }}
              >
                <option value="summary">Summary Wording or Legal Translation Error</option>
                <option value="math">Math Breakdown or Calculator Formula Error</option>
                <option value="date">Tabled Date or Gazettement Timeline Error</option>
                <option value="checklist">Regulatory Compliance Checklist Error</option>
                <option value="other">Other Inaccuracy</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Description of the Inaccuracy</label>
              <textarea
                className="form-textarea"
                placeholder="Please describe what is incorrect on the page..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Suggested Correction (Optional)</label>
              <textarea
                className="form-textarea"
                placeholder="What should the correct text or formula be?"
                value={suggestedCorrection}
                onChange={(e) => setSuggestedCorrection(e.target.value)}
                rows={3}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '2rem' }}>
              <label className="form-label">Your Email or Contact (Optional)</label>
              <input
                type="email"
                className="form-input"
                placeholder="e.g. yourname@example.com (in case we need clarification)"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
              />
            </div>

            <button type="submit" className="btn-primary-accent">
              Submit Correction Report &rarr;
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
