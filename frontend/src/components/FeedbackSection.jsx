'use client';

import React, { useState } from 'react';
import AuthModal from './AuthModal';
import { api } from '../lib/api';
import { supabase } from '../lib/supabase';

export default function FeedbackSection({ billId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [stance, setStance] = useState('support');
  const [rating, setRating] = useState(5);
  const [concerns, setConcerns] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [infoMessage, setInfoMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setInfoMessage('');

    if (!stance) {
      setErrorMessage('Please select your stance (Support, Oppose, or Neutral).');
      return;
    }

    const sessionRes = await supabase.auth.getSession();
    const currentSession = sessionRes?.data?.session;

    if (!currentSession) {
      setAuthModalOpen(true);
      return;
    }

    try {
      setSubmitting(true);
      await api.submitFeedback(billId, stance, rating, concerns, currentSession.access_token);
      setSuccess(true);
      await supabase.auth.signOut().catch(() => { });
    } catch (err) {
      console.error('Feedback submission error:', err);
      if (err.message && (err.message.includes('already submitted') || err.message.includes('409'))) {
        setInfoMessage("You've already submitted feedback for this bill.");
      } else {
        setErrorMessage(err.message || 'Failed to submit feedback. Please try again.');
      }
      await supabase.auth.signOut().catch(() => { });
    } finally {
      setSubmitting(false);
    }
  };

  const onAuthSuccess = async (session) => {
    if (session?.access_token) {
      try {
        setSubmitting(true);
        setErrorMessage(null);
        setInfoMessage('');
        await api.submitFeedback(billId, stance, rating, concerns, session.access_token);
        setSuccess(true);
        await supabase.auth.signOut().catch(() => { });
      } catch (err) {
        if (err.message && (err.message.includes('already submitted') || err.message.includes('409'))) {
          setInfoMessage("You've already submitted feedback for this bill.");
        } else {
          setErrorMessage(err.message || 'Failed to submit feedback. Please try again.');
        }
        await supabase.auth.signOut().catch(() => { });
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <>
      <section className="collapsible-feedback-card" aria-labelledby="feedback-heading">
        {/* Collapsible Trigger Row */}
        <button
          type="button"
          className="feedback-trigger-header"
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
        >
          <div className="feedback-trigger-content">
            <div className="feedback-trigger-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div>
              <h3 id="feedback-heading" className="feedback-trigger-title">
                Have your say — what do you think of this bill?
              </h3>
              <p className="feedback-trigger-subtitle">
                {isOpen ? 'Click to collapse feedback form' : 'Share your stance anonymously. Your feedback is aggregated and submitted to clerk of Parliament or County Assembly.'}
              </p>
            </div>
          </div>

          <span className={`feedback-chevron ${isOpen ? 'open' : ''}`}>
            ▼
          </span>
        </button>

        {/* Collapsible Body */}
        {isOpen && (
          <div className="feedback-expand-body">
            {success ? (
              <div style={{ padding: '1.5rem', background: 'var(--success-bg)', border: '1px solid var(--success-border)', borderRadius: 'var(--radius-md)', textAlign: 'center', marginTop: '1rem' }}>
                <p style={{ color: 'var(--success)', fontWeight: 700, fontSize: '1rem', marginBottom: '0.25rem' }}>
                  Feedback Recorded Successfully
                </p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  Thank you! Your stance has been anonymously included in the public legislative insights.
                </p>
              </div>
            ) : infoMessage ? (
              <div style={{ padding: '1.25rem', background: 'var(--info-bg)', border: '1px solid var(--info-border)', borderRadius: 'var(--radius-md)', textAlign: 'center', marginTop: '1rem' }}>
                <p style={{ color: 'var(--info)', fontWeight: 600, fontSize: '0.925rem' }}>
                  {infoMessage}
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} style={{ marginTop: '1rem' }}>
                {errorMessage && (
                  <div style={{ padding: '0.75rem 1rem', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                    {errorMessage}
                  </div>
                )}

                {/* Stance Choice: 3-way radio buttons */}
                <div className="form-group">
                  <label className="form-label">What is your stance on this legislation?</label>
                  <div className="stance-group-3">
                    <button
                      type="button"
                      className={`stance-btn ${stance === 'support' ? 'active-support' : ''}`}
                      onClick={() => setStance('support')}
                    >
                      Support
                    </button>
                    <button
                      type="button"
                      className={`stance-btn ${stance === 'oppose' ? 'active-oppose' : ''}`}
                      onClick={() => setStance('oppose')}
                    >
                      Oppose
                    </button>
                    <button
                      type="button"
                      className={`stance-btn ${stance === 'neutral' ? 'active-neutral' : ''}`}
                      onClick={() => setStance('neutral')}
                    >
                      Neutral
                    </button>
                  </div>
                </div>

                {/* Impact Severity Rating Slider (1 to 5) */}
                <div className="slider-container">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <label className="form-label" style={{ marginBottom: 0 }}>Impact Severity Rating</label>
                    <span className="tabular-nums" style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '0.95rem' }}>
                      {rating} / 5
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={rating}
                    onChange={(e) => setRating(Number(e.target.value))}
                    className="range-input"
                  />
                </div>

                {/* Comments / Concerns */}
                <div className="form-group">
                  <label className="form-label">Comments or Specific Concerns (Optional)</label>
                  <textarea
                    className="form-textarea"
                    placeholder="Share how this bill affects you"
                    value={concerns}
                    onChange={(e) => setConcerns(e.target.value)}
                    rows={3}
                  />
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
                      Submitting Feedback...
                    </span>
                  ) : (
                    'Submit Citizen Feedback'
                  )}
                </button>
              </form>
            )}
          </div>
        )}
      </section>

      {/* Auth Modal Portal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={onAuthSuccess}
      />
    </>
  );
}
