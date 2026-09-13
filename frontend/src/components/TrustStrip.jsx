'use client';

import React from 'react';

export default function TrustStrip() {
  return (
    <div className="trust-strip" role="region" aria-label="Trust and Credibility Signals">
      <span className="trust-item">
        <span className="trust-item-icon">✓</span> English & Swahili
      </span>
      <span className="trust-separator">·</span>
      <span className="trust-item">
        <span className="trust-item-icon">✓</span> KDPA 2019 Compliant
      </span>
      <span className="trust-separator">·</span>
      <span className="trust-item">
        <span className="trust-item-icon">✓</span> Official Parliamentary & Gazette PDFs
      </span>
      <span className="trust-separator">·</span>
      <span className="trust-item">
        <span className="trust-item-icon">✓</span> Anonymous feedback aggregation
      </span>
    </div>
  );
}
