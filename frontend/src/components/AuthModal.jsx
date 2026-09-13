'use client';

import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { sendPhoneOtp, verifyPhoneOtp } from '../lib/supabase';
import { formatE164, isValidKenyanPhone } from '../lib/phone';

export default function AuthModal({ isOpen, onClose, onSuccess }) {
  const [mounted, setMounted] = useState(false);
  const [step, setStep] = useState('phone'); // 'phone' | 'otp'
  const [phone, setPhone] = useState('');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [infoMsg, setInfoMsg] = useState('');
  const [resendCountdown, setResendCountdown] = useState(0);

  const digitRefs = useRef([]);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Lock body scroll when modal is active
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        resetForm();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Resend countdown timer
  useEffect(() => {
    let timer;
    if (resendCountdown > 0) {
      timer = setInterval(() => {
        setResendCountdown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [resendCountdown]);

  // Auto-focus first digit on OTP step
  useEffect(() => {
    if (isOpen && step === 'otp') {
      setTimeout(() => {
        digitRefs.current[0]?.focus();
      }, 50);
    }
  }, [isOpen, step]);

  if (!mounted || !isOpen) return null;

  const handleSendOtp = async (e) => {
    if (e) e.preventDefault();
    setErrorMsg('');
    setInfoMsg('');

    const formatted = formatE164(phone.trim());
    if (!isValidKenyanPhone(formatted)) {
      setErrorMsg('Please enter a valid Kenyan phone number (e.g., 0712345678 or +254712345678)');
      return;
    }

    setLoading(true);
    try {
      await sendPhoneOtp(formatted);
      setPhone(formatted);
      setStep('otp');
      setOtpDigits(['', '', '', '', '', '']);
      setResendCountdown(30);
      setInfoMsg(`Verification code sent via SMS to ${formatted}`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to send OTP code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDigitChange = (index, value) => {
    // Only accept numeric inputs
    const cleanVal = value.replace(/\D/g, '');

    if (cleanVal.length > 1) {
      // User pasted into a single digit box
      handlePasteValue(cleanVal);
      return;
    }

    const newDigits = [...otpDigits];
    newDigits[index] = cleanVal.slice(-1);
    setOtpDigits(newDigits);
    setErrorMsg('');

    // Auto-advance to next box
    if (cleanVal && index < 5) {
      digitRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      if (!otpDigits[index] && index > 0) {
        digitRefs.current[index - 1]?.focus();
      }
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim();
    handlePasteValue(pastedData);
  };

  const handlePasteValue = (value) => {
    const numbers = value.replace(/\D/g, '').slice(0, 6);
    if (!numbers) return;

    const newDigits = ['', '', '', '', '', ''];
    for (let i = 0; i < numbers.length; i++) {
      newDigits[i] = numbers[i];
    }
    setOtpDigits(newDigits);
    setErrorMsg('');

    const nextIndex = Math.min(numbers.length, 5);
    digitRefs.current[nextIndex]?.focus();
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    const fullOtp = otpDigits.join('');
    if (fullOtp.length < 6) {
      setErrorMsg('Please enter all 6 digits of the verification code.');
      return;
    }

    setLoading(true);
    try {
      const data = await verifyPhoneOtp(phone, fullOtp);
      if (onSuccess) {
        onSuccess(data?.session);
      }
      resetForm();
      onClose();
    } catch (err) {
      setErrorMsg(err.message || 'Invalid or expired verification code. Please check and try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep('phone');
    setPhone('');
    setOtpDigits(['', '', '', '', '', '']);
    setErrorMsg('');
    setInfoMsg('');
    setResendCountdown(0);
  };

  const modalContent = (
    <div
      className="modal-backdrop"
      onClick={() => { resetForm(); onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button
          className="modal-close-btn"
          onClick={() => { resetForm(); onClose(); }}
          aria-label="Close modal"
        >
          ✕
        </button>

        <div className="auth-modal-header">
          <div className="auth-modal-icon-badge">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <h3 id="auth-modal-title" style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {step === 'phone' ? 'Verify Your Phone Number' : 'Enter Verification Code'}
          </h3>
          <p className="auth-modal-subtitle">
            {step === 'phone'
              ? 'Enter your Kenyan mobile number to receive a secure SMS verification code.'
              : `Enter the 6-digit code sent via SMS to ${phone}`}
          </p>
        </div>

        {errorMsg && (
          <div className="auth-alert error-alert">
            <span>⚠️ {errorMsg}</span>
          </div>
        )}

        {infoMsg && (
          <div className="auth-alert info-alert">
            <span>ℹ️ {infoMsg}</span>
          </div>
        )}

        {step === 'phone' ? (
          <form onSubmit={handleSendOtp} className="auth-form">
            <div className="form-group">
              <label htmlFor="phone-input" className="form-label">
                Mobile Phone Number
              </label>
              <input
                id="phone-input"
                type="tel"
                className="form-input"
                placeholder="e.g. 0712345678 or +254712345678"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                disabled={loading}
                autoFocus
              />
            </div>

            <button type="submit" className="btn-primary-accent" disabled={loading} style={{ width: '100%' }}>
              {loading ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
                    <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" />
                  </svg>
                  Sending Code...
                </span>
              ) : (
                'Send SMS Verification Code'
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="auth-form">
            <div className="form-group">
              <label className="form-label" style={{ textAlign: 'center', display: 'block' }}>
                6-Digit Verification Code
              </label>

              {/* Segmented OTP 6-box input */}
              <div className="otp-segmented-container" onPaste={handlePaste}>
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
            </div>

            <button type="submit" className="btn-primary-accent" disabled={loading || otpDigits.join('').length < 6} style={{ width: '100%' }}>
              {loading ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
                    <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" />
                  </svg>
                  Verifying...
                </span>
              ) : (
                'Verify & Submit Feedback'
              )}
            </button>

            <div className="auth-modal-footer">
              {resendCountdown > 0 ? (
                <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  Resend code in <strong className="tabular-nums">{resendCountdown}s</strong>
                </span>
              ) : (
                <button
                  type="button"
                  className="btn-resend-otp"
                  onClick={handleSendOtp}
                  disabled={loading}
                >
                  Resend SMS Code
                </button>
              )}

              <button
                type="button"
                className="btn-text"
                onClick={() => setStep('phone')}
                disabled={loading}
                style={{ marginTop: '0.25rem' }}
              >
                ← Change Phone Number
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
