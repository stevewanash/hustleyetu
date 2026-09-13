'use client';

import React, { useState } from 'react';
import TrustStrip from '../../components/TrustStrip';
import { api } from '../../lib/api';
import { formatE164, isValidKenyanPhone } from '../../lib/phone';

export default function SubscribePage() {
  // Subscribe form state
  const [phone, setPhone] = useState('');
  const [language, setLanguage] = useState('en');
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [subscribeSuccess, setSubscribeSuccess] = useState(false);
  const [subscribeError, setSubscribeError] = useState(null);

  // Manage subscription state
  const [managePhone, setManagePhone] = useState('');
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [statusResult, setStatusResult] = useState(null);
  const [manageError, setManageError] = useState(null);
  const [unsubscribing, setUnsubscribing] = useState(false);
  const [unsubscribeSuccess, setUnsubscribeSuccess] = useState(false);

  const handleSubscribe = async (e) => {
    e.preventDefault();
    setSubscribeError(null);

    const formatted = formatE164(phone.trim());
    if (!isValidKenyanPhone(formatted)) {
      setSubscribeError('Please enter a valid Kenyan phone number (e.g., 0712345678 or +254712345678)');
      return;
    }

    if (!consent) {
      setSubscribeError('Consent is required under the Kenya Data Protection Act.');
      return;
    }

    try {
      setSubmitting(true);
      await api.subscribe(formatted, language, ['sms']);
      setSubscribeSuccess(true);
    } catch (err) {
      console.error('Subscription error:', err);
      setSubscribeError(err.message || 'Failed to register subscription. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCheckStatus = async (e) => {
    e.preventDefault();
    setManageError(null);
    setStatusResult(null);
    setUnsubscribeSuccess(false);

    const formatted = formatE164(managePhone.trim());
    if (!isValidKenyanPhone(formatted)) {
      setManageError('Please enter a valid Kenyan phone number (e.g., 0712345678 or +254712345678)');
      return;
    }

    try {
      setCheckingStatus(true);
      const res = await api.getSubscriptionStatus(formatted);
      setStatusResult(res);
    } catch (err) {
      console.error('Status lookup error:', err);
      setManageError(err.message || 'Failed to check subscription status.');
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleUnsubscribe = async () => {
    setManageError(null);
    const formatted = formatE164(managePhone.trim());
    if (!isValidKenyanPhone(formatted)) {
      setManageError('Please enter a valid Kenyan phone number.');
      return;
    }

    try {
      setUnsubscribing(true);
      await api.unsubscribe(formatted);
      setUnsubscribeSuccess(true);
      setStatusResult((prev) => (prev ? { ...prev, is_active: false } : null));
    } catch (err) {
      console.error('Unsubscribe error:', err);
      setManageError(err.message || 'Failed to cancel subscription.');
    } finally {
      setUnsubscribing(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header" style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
        <h1 className="page-title">Subscribe to Legislative Alerts</h1>
        <p className="page-subtitle" style={{ margin: '0 auto' }}>
          Receive timely SMS alerts for transport sector bills and regulations when they are tabled in Parliament.
        </p>
      </div>

      {/* Trust Strip */}
      <TrustStrip />

      {/* Subscription Signup Card */}
      <div className="content-card" style={{ marginBottom: '2.5rem', padding: '2rem 2.25rem' }}>
        <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1.25rem' }}>
          New SMS Alert Subscription
        </h2>

        {subscribeSuccess ? (
          <div style={{ padding: '2rem', background: 'var(--success-bg)', border: '1px solid var(--success-border)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
            <h3 style={{ color: 'var(--success)', fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Successfully Subscribed
            </h3>
            <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: '0.5rem' }}>
              Your phone number (<strong className="tabular-nums">{formatE164(phone)}</strong>) has been registered for legislative alerts.
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              A confirmation SMS will be sent shortly to your mobile number.
            </p>
            <button
              type="button"
              className="btn-text"
              onClick={() => { setSubscribeSuccess(false); setPhone(''); }}
            >
              Subscribe another phone number &rarr;
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubscribe}>
            {subscribeError && (
              <div style={{ padding: '0.85rem 1rem', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                {subscribeError}
              </div>
            )}

            {/* Phone input */}
            <div className="form-group">
              <label htmlFor="subscribe-phone" className="form-label">
                Kenyan Mobile Number
              </label>
              <input
                id="subscribe-phone"
                type="tel"
                className="form-input tabular-nums"
                placeholder="e.g. 0712345678 or +254712345678"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                disabled={submitting}
              />
              <p className="form-hint">Strictly protected under Kenya Data Protection Act.</p>
            </div>

            {/* Language Selection */}
            <div className="form-group">
              <label className="form-label">Preferred Alert Language</label>
              <div style={{ display: 'flex', gap: '2rem', marginTop: '0.4rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.925rem' }}>
                  <input
                    type="radio"
                    name="language"
                    value="en"
                    checked={language === 'en'}
                    onChange={() => setLanguage('en')}
                  />
                  <span>English</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.925rem' }}>
                  <input
                    type="radio"
                    name="language"
                    value="sw"
                    checked={language === 'sw'}
                    onChange={() => setLanguage('sw')}
                  />
                  <span>Swahili</span>
                </label>
              </div>
            </div>

            {/* Delivery Channel Line */}
            <div style={{ background: 'var(--bg-card-subtle)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', marginBottom: '1.25rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              <strong>Delivery Channel:</strong> Direct SMS alerts.
            </div>

            {/* Consent Checkbox */}
            <div className="form-group" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem', marginBottom: '1.5rem' }}>
              <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={() => setConsent(!consent)}
                  required
                  style={{ marginTop: '0.2rem', cursor: 'pointer' }}
                />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  I consent to HustleYetu processing my mobile number to deliver legislative alerts in full compliance with the <strong>Kenya Data Protection Act (KDPA) 2019</strong>.
                </span>
              </label>
            </div>

            <button
              type="submit"
              className="btn-primary-accent"
              disabled={submitting}
              style={{ width: '100%' }}
            >
              {submitting ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
                    <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" />
                  </svg>
                  Registering Number...
                </span>
              ) : (
                "Confirm SMS Subscription"
              )}
            </button>
          </form>
        )}
      </div>

      {/* Manage Existing Subscription Card */}
      <div className="content-card" style={{ marginBottom: '3rem', padding: '2rem 2.25rem' }}>
        <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
          Manage Existing Subscription
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Check your subscription status, change language preference, or unsubscribe from SMS alerts at any time.
        </p>

        {manageError && (
          <div style={{ padding: '0.85rem 1rem', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            {manageError}
          </div>
        )}

        {unsubscribeSuccess && (
          <div style={{ padding: '1rem 1.25rem', background: 'var(--success-bg)', border: '1px solid var(--success-border)', color: 'var(--success)', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem', fontWeight: 600 }}>
            Subscription successfully deactivated. You will no longer receive SMS alerts.
          </div>
        )}

        <form onSubmit={handleCheckStatus} style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <input
              type="tel"
              className="form-input tabular-nums"
              placeholder="e.g. 0712345678"
              value={managePhone}
              onChange={(e) => setManagePhone(e.target.value)}
              required
              style={{ flex: 1, minWidth: '220px' }}
            />
            <button
              type="submit"
              className="btn-secondary-outline"
              disabled={checkingStatus}
            >
              {checkingStatus ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
                    <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" />
                  </svg>
                  Checking...
                </span>
              ) : (
                "Check Status"
              )}
            </button>
          </div>
        </form>

        {statusResult && (
          <div style={{ background: 'var(--bg-card-subtle)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', marginTop: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>Subscription Status:</span>
              <span className={statusResult.is_active ? 'chip-risk-low' : 'chip-risk-high'}>
                {statusResult.is_active ? 'Active' : 'Inactive / Unsubscribed'}
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
              Preferred Language: <strong>{statusResult.preferred_language?.toUpperCase() || 'EN'}</strong>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
              Channels: <strong>{statusResult.channels?.join(', ') || 'SMS'}</strong>
            </div>

            {statusResult.is_active && (
              <button
                type="button"
                onClick={handleUnsubscribe}
                disabled={unsubscribing}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--danger)',
                  color: 'var(--danger)',
                  padding: '0.5rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {unsubscribing ? "Unsubscribing..." : "Unsubscribe from SMS Alerts"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
