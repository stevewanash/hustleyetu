'use client';

import React from 'react';

export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="container">
        <div className="footer-grid">
          {/* Column 1: Brand & Independence Disclaimer */}
          <div className="footer-brand">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div className="brand-mark" style={{ width: '28px', height: '28px', fontSize: '0.95rem' }}>
                H
              </div>
              <span className="footer-brand-title">HustleYetu</span>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Democratizing legislative literacy and regulatory clarity for Kenya's informal and transport workforce.
            </p>
            <p className="footer-disclaimer">
              <strong>Independent Civic Resource:</strong> HustleYetu is an independent civic education and policy analysis platform. It is not affiliated with, endorsed by, or operating on behalf of the Parliament of Kenya, the Nairobi City County Assembly, or any government ministry.
            </p>
          </div>

          {/* Column 2: Platform Navigation */}
          <div>
            <h4 className="footer-column-title">Platform</h4>
            <ul className="footer-links">
              <li>
                <a href="/" className="footer-link">Home</a>
              </li>
              <li>
                <a href="/bills" className="footer-link">Browse Bills</a>
              </li>
              <li>
                <a href="/impact" className="footer-link">Impact & Calculators</a>
              </li>
              <li>
                <a href="/subscribe" className="footer-link">SMS Alerts</a>
              </li>
              <li>
                <a href="/dashboard" className="footer-link">Insights Dashboard</a>
              </li>
            </ul>
          </div>

          {/* Column 3: About & How It Works (F4) */}
          <div>
            <h4 className="footer-column-title">About</h4>
            <ul className="footer-links">
              <li>
                <a href="/how-it-works" className="footer-link">How It Works</a>
              </li>
              <li>
                <a href="/team" className="footer-link">Our Team</a>
              </li>
              <li>
                <a href="/report" className="footer-link">Report Incorrect Info</a>
              </li>
            </ul>
          </div>

          {/* Column 4: Privacy & Legal (F4) */}
          <div>
            <h4 className="footer-column-title">Privacy & Legal</h4>
            <ul className="footer-links">
              <li>
                <a href="/privacy" className="footer-link">Privacy Policy</a>
              </li>
              <li>
                <a href="/terms" className="footer-link">Terms of Service</a>
              </li>
            </ul>
          </div>
        </div>

        {/* Footer Bottom Bar */}
        <div className="footer-bottom-bar">
          <div>
            © {new Date().getFullYear()} HustleYetu. All rights reserved.
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <span>Kenya Civic Literacy Project</span>
            <span>·</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
