'use client';

import React, { useState, useEffect, useRef } from 'react';
import TrustStrip from '../components/TrustStrip';

const HERO_SLIDES = [
  {
    headline: "Know the Financial & Regulatory Impact of Bills Before They Hit Your Hustle",
    subhead: "Plain-language breakdowns of national tax laws and transport regulations for Kenya's boda boda sector.",
    imageSrc: "/hero-slide-1.jpg",
    fallbackBg: "linear-gradient(135deg, #132a24 0%, #1e4e42 50%, #2a5b4e 100%)",
    ctaText: "Browse Analyzed Bills",
    ctaLink: "/bills"
  },
  {
    headline: "Demystifying National Tax Acts & Regulatory Laws",
    subhead: "Real-time worked financial scenarios, compliance deadlines, and instant SMS alerts in English and Swahili.",
    imageSrc: "/hero-slide-2.jpg",
    fallbackBg: "linear-gradient(135deg, #1a2320 0%, #263832 50%, #374f46 100%)",
    ctaText: "Explore Impact Summaries",
    ctaLink: "/impact"
  }
];

const FEATURES = [
  {
    title: "Plain-Language Legal Summaries",
    description: "Complex financial and regulatory bills translated into clear English and Swahili summaries so you understand what is proposed before it becomes law."
  },
  {
    title: "Worked Financial & Compliance Scenarios",
    description: "Interactive calculators and step-by-step math breakdowns showing exact cost implications on fuel levies, vehicle circulation taxes, and compliance requirements for regulatory bills."
  },
  {
    title: "SMS Alerts & KDPA Protection",
    description: "Receive timely mobile notifications when bills affecting you are tabled in parliament. Your phone number is strictly safeguarded under KDPA 2019."
  },
  {
    title: "Citizen Feedback & Representation",
    description: "Have your say on active legislation. Submit your stance, severity rating, and concerns — anonymously aggregated and shared with legislative clerks."
  }
];

export default function Home() {
  const [currentHeroSlide, setCurrentHeroSlide] = useState(0);
  const [activeFeatureIndex, setActiveFeatureIndex] = useState(0);
  const heroInteractingRef = useRef(false);
  const featureInteractingRef = useRef(false);
  const featureTrackRef = useRef(null);

  // Auto-advance hero carousel every 6 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      if (!heroInteractingRef.current) {
        setCurrentHeroSlide((prev) => (prev + 1) % HERO_SLIDES.length);
      }
    }, 6000);

    return () => clearInterval(timer);
  }, []);

  // 2. Auto-scroll feature cards every 3 seconds (F1 requirement)
  useEffect(() => {
    const featureTimer = setInterval(() => {
      if (!featureInteractingRef.current) {
        setActiveFeatureIndex((prevIndex) => {
          const nextIndex = (prevIndex + 1) % FEATURES.length;
          scrollToFeatureIndex(nextIndex);
          return nextIndex;
        });
      }
    }, 3000);

    return () => clearInterval(featureTimer);
  }, []);

  const nextHeroSlide = () => {
    setCurrentHeroSlide((prev) => (prev + 1) % HERO_SLIDES.length);
  };

  const prevHeroSlide = () => {
    setCurrentHeroSlide((prev) => (prev - 1 + HERO_SLIDES.length) % HERO_SLIDES.length);
  };

  // Feature carousel scroll helper
  const scrollToFeatureIndex = (index) => {
    if (!featureTrackRef.current) return;
    const track = featureTrackRef.current;
    const card = track.children[index];
    if (card) {
      const targetLeft = card.offsetLeft - (track.clientWidth - card.clientWidth) / 2;
      track.scrollTo({ left: targetLeft, behavior: 'smooth' });
    }
  };

  const handleManualFeatureSelect = (index) => {
    setActiveFeatureIndex(index);
    scrollToFeatureIndex(index);
  };

  const handleFeatureScroll = () => {
    if (!featureTrackRef.current) return;
    const track = featureTrackRef.current;
    const scrollPos = track.scrollLeft + track.clientWidth / 2;

    let closestIdx = 0;
    let minDistance = Infinity;

    Array.from(track.children).forEach((child, idx) => {
      const cardCenter = child.offsetLeft + child.clientWidth / 2;
      const distance = Math.abs(scrollPos - cardCenter);
      if (distance < minDistance) {
        minDistance = distance;
        closestIdx = idx;
      }
    });

    if (closestIdx !== activeFeatureIndex) {
      setActiveFeatureIndex(closestIdx);
    }
  };

  return (
    <div className="animate-fade-in">
      {/* 1. Hero Section — 2-Slide Smooth Carousel */}
      <section
        className="hero-carousel-container"
        onMouseEnter={() => { heroInteractingRef.current = true; }}
        onMouseLeave={() => { heroInteractingRef.current = false; }}
        onTouchStart={() => { heroInteractingRef.current = true; }}
        onTouchEnd={() => { heroInteractingRef.current = false; }}
        aria-roledescription="carousel"
        aria-label="Featured Policy Highlights"
      >
        {HERO_SLIDES.map((slide, idx) => (
          <div
            key={idx}
            className="hero-slide"
            style={{
              display: currentHeroSlide === idx ? 'flex' : 'none',
              backgroundImage: `url('${slide.imageSrc}'), ${slide.fallbackBg}`,
            }}
          >
            <div className="hero-overlay" />

            <div className="hero-content">
              <h1 className="hero-headline">
                {slide.headline}
              </h1>
              <p className="hero-subhead">
                {slide.subhead}
              </p>
              <div style={{ display: 'flex', gap: '0.85rem', flexWrap: 'wrap' }}>
                <a href={slide.ctaLink} className="btn-primary-accent">
                  {slide.ctaText} &rarr;
                </a>
                <a href="/subscribe" className="btn-secondary-outline" style={{ background: 'rgba(255, 255, 255, 0.95)', border: 'none' }}>
                  Get SMS Alerts
                </a>
              </div>
            </div>
          </div>
        ))}

        {/* Carousel Arrow & Dot Controls */}
        <div className="hero-controls">
          <button
            type="button"
            className="hero-nav-arrow"
            onClick={prevHeroSlide}
            aria-label="Previous slide"
          >
            ‹
          </button>

          <div className="hero-dots">
            {HERO_SLIDES.map((_, idx) => (
              <button
                key={idx}
                type="button"
                className={`hero-dot ${currentHeroSlide === idx ? 'active' : ''}`}
                onClick={() => setCurrentHeroSlide(idx)}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>

          <button
            type="button"
            className="hero-nav-arrow"
            onClick={nextHeroSlide}
            aria-label="Next slide"
          >
            ›
          </button>
        </div>
      </section>

      {/* 2. Trust & Credibility Strip */}
      <TrustStrip />

      {/* 3. Section Heading: Built for Transport Operators & Micro-Enterprises */}
      <div style={{ textAlign: 'center', margin: '3.5rem 0 1.5rem 0' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
          Built for Transport Operators & Micro-Enterprises
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.975rem', maxWidth: '600px', margin: '0 auto', lineHeight: '1.55' }}>
          National and county level tax and regulatory bills directly affect your daily fuel costs, SACCO requirements, and licensing overheads.
        </p>
      </div>

      {/* 4. Persona Section: Styled Side-by-Side Banner matching reference */}
      <section className="persona-banner-container" aria-labelledby="testimonial-heading">
        {/* Left Side: Photo Frame */}
        <div className="persona-banner-photo-side">
          <img
            src="/persona-martin.jpg"
            alt="Commercial Motorcycle Operators"
            className="persona-banner-img"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              if (e.currentTarget.nextSibling) {
                e.currentTarget.nextSibling.style.display = 'flex';
              }
            }}
          />
          <div className="persona-banner-placeholder" style={{ display: 'none' }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '0.75rem', opacity: 0.8 }}>
              <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.5 2.8C2 10.9 2 11.2 2 11.5V16c0 .6.4 1 1 1h2" />
              <circle cx="7" cy="17" r="2" />
              <path d="M9 17h6" />
              <circle cx="17" cy="17" r="2" />
            </svg>
            <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>Commercial Transport Operators</div>
            <div style={{ fontSize: '0.8rem', color: '#b8d4c9' }}>Nairobi, Kenya</div>
          </div>
        </div>

        {/* Right Side: Deep Evergreen Solid Quote Box */}
        <div className="persona-banner-quote-side">
          {/* Large Stylized White Quote Mark */}
          <svg className="persona-quote-symbol" viewBox="0 0 32 32" fill="currentColor">
            <path d="M10 8C6.686 8 4 10.686 4 14v10h10V14H8c0-3.314 2.686-6 6-6V8zm14 0c-3.314 0-6 2.686-6 6v10h10V14h-6c0-3.314 2.686-6 6-6V8z" />
          </svg>

          <p className="persona-banner-quote-text">
            This year I was fined KES 5,000 for a SACCO sticker guideline I had never heard about. Most of my colleagues are victims too.
          </p>

          <div>
            <div className="persona-banner-author">Martin</div>
            <div className="persona-banner-role">Commercial Motorcycle Operator · Nairobi</div>
          </div>
        </div>
      </section>

      {/* 5. Feature Carousel (4 Cards, Autoscrolling every 3s, No numbers/tags at top) */}
      <section style={{ margin: '0 0 3.5rem 0' }}>
        <div
          className="feature-carousel-wrapper"
          onMouseEnter={() => { featureInteractingRef.current = true; }}
          onMouseLeave={() => { featureInteractingRef.current = false; }}
          onTouchStart={() => { featureInteractingRef.current = true; }}
          onTouchEnd={() => { featureInteractingRef.current = false; }}
        >
          <div
            ref={featureTrackRef}
            className="feature-carousel-track"
            onScroll={handleFeatureScroll}
          >
            {FEATURES.map((feature, idx) => (
              <div key={idx} className="feature-carousel-card">
                <h3 className="feature-card-title">
                  {feature.title}
                </h3>
                <p className="feature-card-desc">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>

          {/* Carousel Navigation (Dots & Arrows) */}
          <div className="feature-carousel-nav">
            <button
              type="button"
              className="feature-nav-btn"
              onClick={() => handleManualFeatureSelect((activeFeatureIndex - 1 + FEATURES.length) % FEATURES.length)}
              aria-label="Previous feature"
            >
              ‹
            </button>

            <div className="feature-carousel-dots">
              {FEATURES.map((_, idx) => (
                <button
                  key={idx}
                  type="button"
                  className={`feature-dot ${activeFeatureIndex === idx ? 'active' : ''}`}
                  onClick={() => handleManualFeatureSelect(idx)}
                  aria-label={`Go to feature ${idx + 1}`}
                />
              ))}
            </div>

            <button
              type="button"
              className="feature-nav-btn"
              onClick={() => handleManualFeatureSelect((activeFeatureIndex + 1) % FEATURES.length)}
              aria-label="Next feature"
            >
              ›
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
