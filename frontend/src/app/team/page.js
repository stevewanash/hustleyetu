'use client';

import React from 'react';

function LinkedInIcon({ size = 18 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

function GmailIcon({ size = 18 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" />
    </svg>
  );
}

const TEAM_MEMBERS = [
  {
    name: 'Steve',
    role: 'Backend developer',
    imageSrc: '/team-1.jpg',
    bio: 'Passionate about civic tech. Leads backend development and deployment, making sure our platform is reliable and scalable.',
    linkedin: 'https://www.linkedin.com/in/steve-wanangwe-6a72b1254/',
    email: 'stevewanash1@gmail.com'
  },
  {
    name: 'Farida',
    role: 'Frontend developer & Research lead',
    imageSrc: '/team-2.jpg',
    bio: "Passionate about human centered design. Leads user research, frontend development and documentation to ensure we're solving a real problem for real users.",
    linkedin: 'https://www.linkedin.com/in/maryannefarida/',
    email: 'maryannefarida@gmail.com'
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: '3rem' }}>
          {TEAM_MEMBERS.map((member, idx) => (
            <div key={idx} className="team-member-card">
              {/* Header: Photo on Left, Name, Role & Social Links on Right */}
              <div className="team-member-header">
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
                    position: 'relative',
                    flexShrink: 0
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
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--primary)', marginBottom: '0.5rem' }}>
                    {member.role}
                  </div>

                  {/* Contact Links */}
                  <div className="team-social-links">
                    <a
                      href={member.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="team-social-btn team-social-linkedin"
                      aria-label={`${member.name} on LinkedIn`}
                      title={`${member.name} on LinkedIn`}
                    >
                      <LinkedInIcon size={18} />
                    </a>
                    <a
                      href={`mailto:${member.email}`}
                      className="team-social-btn team-social-gmail"
                      aria-label={`Email ${member.name} (${member.email})`}
                      title={`Email ${member.name}: ${member.email}`}
                    >
                      <GmailIcon size={18} />
                    </a>
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
