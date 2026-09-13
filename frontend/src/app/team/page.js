'use client';

import React from 'react';

const TEAM_MEMBERS = [
  {
    name: 'Steve',
    role: 'Backend developer',
    imageSrc: '/team-1.jpg',
    bio: 'Passionate about civic tech. Leads backend development and deployment, making sure our platform is reliable and scalable.'
  },
  {
    name: 'Farida',
    role: 'Frontend developer & Research lead',
    imageSrc: '/team-2.jpg',
    bio: "Passionate about human centered design. Leads user research, frontend development and documentation to ensure we're solving a real problem for real users."
  }
];

export default function TeamPage() {
  return (
    <div className="animate-fade-in">
      <div className="page-header" style={{ marginBottom: '2.5rem' }}>
        <h1 className="page-title">Our Team</h1>
        <p className="page-subtitle">
          The independent developers and civic researchers behind HustleYetu.
        </p>
      </div>

      <div style={{ maxWidth: '880px', marginBottom: '4rem' }}>
        <div style={{ marginBottom: '3rem' }}>
          <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.35rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            Civic Literacy Driven by Technology
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.75' }}>
            HustleYetu was created out of a simple observation: legislation and county regulations directly alter the livelihoods of over 1.5 million motorcycle taxi operators in Kenya, yet bills are rarely published in accessible, plain-language formats. We bridge this gap through automated analysis and direct SMS alerts.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '3rem' }}>
          {TEAM_MEMBERS.map((member, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column' }}>
              {/* Header: Photo on Left, Name & Role on Right */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '1rem' }}>
                <div
                  style={{
                    width: '88px',
                    height: '88px',
                    minWidth: '88px',
                    borderRadius: '50%',
                    background: 'var(--bg-card-subtle)',
                    border: '1.5px solid var(--border-color)',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative'
                  }}
                >
                  <img
                    src={member.imageSrc}
                    alt={member.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      if (e.currentTarget.nextSibling) {
                        e.currentTarget.nextSibling.style.display = 'flex';
                      }
                    }}
                  />
                  <div
                    style={{
                      display: 'none',
                      width: '100%',
                      height: '100%',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      color: 'var(--text-muted)',
                      textAlign: 'center'
                    }}
                  >
                    Photo
                  </div>
                </div>

                <div>
                  <h3 style={{ fontFamily: 'var(--font-title)', fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                    {member.name}
                  </h3>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--primary)' }}>
                    {member.role}
                  </div>
                </div>
              </div>

              {/* Bio Paragraph */}
              <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                {member.bio}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
