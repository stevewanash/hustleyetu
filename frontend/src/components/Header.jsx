'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';

export default function Header() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();

  // Close mobile drawer on route navigation
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  // Lock body scroll when drawer is open on mobile
  useEffect(() => {
    if (drawerOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [drawerOpen]);

  const navLinks = [
    { href: '/', label: 'Home', exact: true },
    { href: '/bills', label: 'Browse Bills', exact: false },
    { href: '/impact', label: 'Impact', exact: false },
    { href: '/subscribe', label: 'SMS Alerts', exact: true },
    { href: '/dashboard', label: 'Insights Dashboard', exact: true },
  ];

  const isLinkActive = (link) => {
    if (link.exact) {
      return pathname === link.href;
    }
    return pathname === link.href || pathname?.startsWith(`${link.href}/`);
  };

  return (
    <>
      <header className="app-header">
        <div className="container app-header-inner">
          <a href="/" className="brand-logo" aria-label="HustleYetu Home">
            <div className="brand-mark">
              H
            </div>
            <span>HustleYetu</span>
          </a>

          {/* Desktop Horizontal Navigation */}
          <nav className="nav-menu" aria-label="Main Navigation">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className={`nav-link ${isLinkActive(link) ? 'active' : ''}`}
                aria-current={isLinkActive(link) ? 'page' : undefined}
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Mobile Hamburger Toggle Button */}
          <button
            type="button"
            className="nav-toggle"
            onClick={() => setDrawerOpen(!drawerOpen)}
            aria-label="Toggle navigation menu"
            aria-expanded={drawerOpen}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {drawerOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12"></line>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <line x1="3" y1="18" x2="21" y2="18"></line>
                </>
              )}
            </svg>
          </button>
        </div>
      </header>

      {/* Mobile Slide-Over Sidebar Drawer */}
      {drawerOpen && (
        <div
          className="nav-drawer-backdrop"
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        >
          <div
            className="nav-drawer"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Mobile Navigation Menu"
          >
            <div className="nav-drawer-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div className="brand-mark" style={{ width: '28px', height: '28px', fontSize: '0.95rem' }}>
                  H
                </div>
                <span style={{ fontFamily: 'var(--font-title)', fontWeight: 700, fontSize: '1.25rem', color: 'var(--text-primary)' }}>
                  HustleYetu
                </span>
              </div>
              <button
                type="button"
                className="nav-drawer-close"
                onClick={() => setDrawerOpen(false)}
                aria-label="Close navigation menu"
              >
                ✕
              </button>
            </div>

            <nav className="nav-drawer-links" aria-label="Mobile Drawer Links">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className={`nav-drawer-link ${isLinkActive(link) ? 'active' : ''}`}
                  onClick={() => setDrawerOpen(false)}
                  aria-current={isLinkActive(link) ? 'page' : undefined}
                >
                  {link.label}
                </a>
              ))}
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
