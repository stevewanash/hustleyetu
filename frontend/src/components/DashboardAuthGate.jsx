'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  authenticateWithPasscode,
  authenticateWithOtp,
  getDemoCredentials,
} from '../lib/dashboardAuth';
import { formatE164, isValidKenyanPhone } from '../lib/phone';

export default function DashboardAuthGate({ onAuthenticated }) {
  const [tab, setTab] = useState('passcode'); // 'passcode' | 'otp'

  // Passcode form state
  const demoCreds = getDemoCredentials();
  const [email, setEmail] = useState(demoCreds.email);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // OTP form state
  const [otpStep, setOtpStep] = useState('phone'); // 'phone' | 'verify'
  const [phone, setPhone] = useState('0712345678');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [resendCountdown, setResendCountdown] = useState(0);

  // Feedback state
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [infoMsg, setInfoMsg] = useState('');

  const digitRefs = useRef([]);

  // Countdown timer for OTP resend
  useEffect(() => {
    let timer;
    if (resendCountdown > 0) {
      timer = setInterval(() => {
        setResendCountdown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [resendCountdown]);

  // Focus first OTP digit when step switches to 'verify'
  useEffect(() => {
    if (tab === 'otp' && otpStep === 'verify') {
      setTimeout(() => {
        digitRefs.current[0]?.focus();
      }, 100);
    }
  }, [tab, otpStep]);

  // Handle Passcode Login
  const handlePasscodeSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setInfoMsg('');
    setLoading(true);

    try {
      const session = await authenticateWithPasscode(email, password);
      setInfoMsg('Authentication verified. Loading citizen analytics...');
      setTimeout(() => {
        onAuthenticated(session);
      }, 400);
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please verify your passcode.');
    } finally {
      setLoading(false);
    }
  };

  // Quick autofill demo credentials
  const handleAutofillDemo = () => {
    setEmail(demoCreds.email);
    setPassword(demoCreds.password);
    setErrorMsg('');
    setInfoMsg('Demo credentials applied.');
  };

  // Handle Request OTP
  const handleSendOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setInfoMsg('');

    const formatted = formatE164(phone.trim());
    if (!isValidKenyanPhone(formatted)) {
      setErrorMsg('Please enter a valid Kenyan phone number (e.g. 0712345678 or +254712345678)');
      return;
    }

    setLoading(true);
    // Simulate SMS dispatch
    setTimeout(() => {
      setPhone(formatted);
      setOtpStep('verify');
      setOtpDigits(['', '', '', '', '', '']);
      setResendCountdown(30);
      setInfoMsg(`Demo verification code sent to ${formatted}. Use code: ${demoCreds.otp}`);
      setLoading(false);
    }, 600);
  };

  // Handle OTP digit changes
  const handleDigitChange = (index, value) => {
    const cleanVal = value.replace(/\D/g, '');
    if (cleanVal.length > 1) {
      handlePasteOtp(cleanVal);
      return;
    }

    const newDigits = [...otpDigits];
    newDigits[index] = cleanVal.slice(-1);
    setOtpDigits(newDigits);
    setErrorMsg('');

    if (cleanVal && index < 5) {
      digitRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      digitRefs.current[index - 1]?.focus();
    }
  };

  const handlePasteOtp = (value) => {
    const numbers = value.replace(/\D/g, '').slice(0, 6);
    if (!numbers) return;

    const newDigits = ['', '', '', '', '', ''];
    for (let i = 0; i < numbers.length; i++) {
      newDigits[i] = numbers[i];
    }
    setOtpDigits(newDigits);
    setErrorMsg('');

    const nextIdx = Math.min(numbers.length, 5);
    digitRefs.current[nextIdx]?.focus();
  };

  const handleFillDemoOtp = () => {
    handlePasteOtp(demoCreds.otp);
    setInfoMsg(`Demo OTP code '${demoCreds.otp}' entered.`);
  };

  // Handle OTP Submit
  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setInfoMsg('');

    const fullOtp = otpDigits.join('');
    if (fullOtp.length < 6) {
      setErrorMsg('Please enter all 6 digits of the verification code.');
      return;
    }

    setLoading(true);
    try {
      const session = await authenticateWithOtp(phone, fullOtp);
      setInfoMsg('Mobile verification confirmed. Unlocking dashboard...');
      setTimeout(() => {
        onAuthenticated(session);
      }, 400);
    } catch (err) {
      setErrorMsg(err.message || 'Invalid verification code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-auth-wrapper">
      <div className="dashboard-auth-card">
        {/* Header Badge */}
        <div className="auth-gate-header">
          <div className="auth-gate-shield-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </div>
          <span className="auth-gate-badge">Class Project • Protected Route</span>
          <h2 className="auth-gate-title">Citizen Insights Dashboard</h2>
          <p className="auth-gate-subtitle">
            Restricted access for accredited policy analysts, civil society researchers, and verified civic participants.
          </p>
        </div>

        {/* Tab Selection */}
        <div className="dashboard-auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'passcode'}
            className={`dashboard-auth-tab ${tab === 'passcode' ? 'active' : ''}`}
            onClick={() => { setTab('passcode'); setErrorMsg(''); setInfoMsg(''); }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            Analyst Passcode
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'otp'}
            className={`dashboard-auth-tab ${tab === 'otp' ? 'active' : ''}`}
            onClick={() => { setTab('otp'); setErrorMsg(''); setInfoMsg(''); }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
              <line x1="12" y1="18" x2="12.01" y2="18" />
            </svg>
            Mobile SMS OTP
          </button>
        </div>

        {/* Alerts */}
        {errorMsg && (
          <div className="auth-alert error-alert" role="alert">
            <span>⚠️ {errorMsg}</span>
          </div>
        )}

        {infoMsg && (
          <div className="auth-alert info-alert" role="status">
            <span>ℹ️ {infoMsg}</span>
          </div>
        )}

        {/* TAB 1: PASSCODE LOGIN */}
        {tab === 'passcode' && (
          <form onSubmit={handlePasscodeSubmit} className="auth-gate-form">
            <div className="form-group">
              <label htmlFor="auth-email-input" className="form-label">
                Official / Analyst Email
              </label>
              <input
                id="auth-email-input"
                type="email"
                className="form-input"
                placeholder="analyst@hustleyetu.ke"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label htmlFor="auth-password-input" className="form-label" style={{ marginBottom: '0.25rem' }}>
                  Deployment Secret / Passcode
                </label>
                <button
                  type="button"
                  className="btn-text"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ fontSize: '0.78rem' }}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <input
                id="auth-password-input"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="Enter passcode (e.g. hustleyetu2026)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="demo-credentials-helper">
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Demo Passcode: <code>{demoCreds.password}</code>
              </div>
              <button
                type="button"
                className="demo-pill-btn"
                onClick={handleAutofillDemo}
                disabled={loading}
              >
                Auto-Fill Demo Credentials
              </button>
            </div>

            <button
              type="submit"
              className="btn-primary-accent"
              disabled={loading || !password}
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              {loading ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="animate-spin">
                    <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" />
                  </svg>
                  Verifying Session...
                </span>
              ) : (
                'Unlock Insights Dashboard'
              )}
            </button>
          </form>
        )}

        {/* TAB 2: SMS OTP LOGIN */}
        {tab === 'otp' && (
          <div className="auth-gate-form">
            {otpStep === 'phone' ? (
              <form onSubmit={handleSendOtp}>
                <div className="form-group">
                  <label htmlFor="otp-phone-input" className="form-label">
                    Kenyan Mobile Number
                  </label>
                  <input
                    id="otp-phone-input"
                    type="tel"
                    className="form-input"
                    placeholder="e.g. 0712345678 or +254712345678"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                    disabled={loading}
                  />
                  <span className="form-hint">
                    Enter any Kenyan mobile number to simulate OTP delivery.
                  </span>
                </div>

                <button
                  type="submit"
                  className="btn-primary-accent"
                  disabled={loading || !phone}
                  style={{ width: '100%', marginTop: '0.75rem' }}
                >
                  {loading ? 'Sending SMS Code...' : 'Request Verification Code'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleOtpSubmit}>
                <div className="form-group">
                  <label className="form-label" style={{ textAlign: 'center', display: 'block' }}>
                    Enter 6-Digit Code sent to {phone}
                  </label>

                  <div
                    className="otp-segmented-container"
                    onPaste={(e) => {
                      e.preventDefault();
                      handlePasteOtp(e.clipboardData.getData('text'));
                    }}
                  >
                    {otpDigits.map((digit, idx) => (
                      <input
                        key={idx}
                        ref={(el) => (digitRefs.current[idx] = el)}
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleKeyDown(idx, e)}
                        disabled={loading}
                        className="otp-digit-input"
                        aria-label={`Digit ${idx + 1}`}
                      />
                    ))}
                  </div>

                  <div className="demo-credentials-helper" style={{ justifyContent: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Demo Code: <strong>{demoCreds.otp}</strong>
                    </span>
                    <button
                      type="button"
                      className="demo-pill-btn"
                      onClick={handleFillDemoOtp}
                    >
                      Fill Code
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn-primary-accent"
                  disabled={loading || otpDigits.join('').length < 6}
                  style={{ width: '100%', marginTop: '0.5rem' }}
                >
                  {loading ? 'Verifying Code...' : 'Verify & Unlock'}
                </button>

                <div style={{ textAlign: 'center', marginTop: '0.75rem' }}>
                  <button
                    type="button"
                    className="btn-text"
                    onClick={() => { setOtpStep('phone'); setOtpDigits(['', '', '', '', '', '']); }}
                    style={{ fontSize: '0.82rem' }}
                  >
                    ← Change Phone Number
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Footer Notes for the Class Evaluator */}
        <div className="auth-gate-evaluator-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, color: 'var(--primary)', marginBottom: '0.2rem' }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            Deployment & Evaluation Notes
          </div>
          <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.45 }}>
            This temporary authentication gate guards only the <strong>/dashboard</strong> route. You can set the deployment secret <code>NEXT_PUBLIC_DASHBOARD_AUTH_PASSWORD</code> in your hosting provider (e.g. Vercel, Netlify) to require a custom password, or use the default passcode <code>{demoCreds.password}</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
