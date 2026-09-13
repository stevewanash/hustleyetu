'use client';

import React from 'react';

export default function DonutChart({
  supportPct = { support: 0, oppose: 0, neutral: 0 },
  totalResponses = 0
}) {
  const supportVal = Math.max(0, Number(supportPct.support) || 0);
  const opposeVal = Math.max(0, Number(supportPct.oppose) || 0);
  const neutralVal = Math.max(0, Number(supportPct.neutral) || 0);

  const supportCount = Math.round((totalResponses * supportVal) / 100);
  const opposeCount = Math.round((totalResponses * opposeVal) / 100);
  const neutralCount = Math.round((totalResponses * neutralVal) / 100);

  const size = 180;
  const strokeWidth = 26;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  // If no responses or all 0
  const isEmpty = totalResponses === 0 || (supportVal === 0 && opposeVal === 0 && neutralVal === 0);

  // Compute stroke dashes
  const supportDash = (supportVal / 100) * circumference;
  const opposeDash = (opposeVal / 100) * circumference;
  const neutralDash = (neutralVal / 100) * circumference;

  const supportOffset = 0;
  const opposeOffset = -supportDash;
  const neutralOffset = -(supportDash + opposeDash);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
      {/* SVG Donut Graphic */}
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{ transform: 'rotate(-90deg)', overflow: 'visible' }}
        >
          {/* Base Track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="transparent"
            stroke="var(--bg-card-subtle)"
            strokeWidth={strokeWidth}
          />

          {isEmpty ? (
            <circle
              cx={center}
              cy={center}
              r={radius}
              fill="transparent"
              stroke="var(--border-color)"
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
            />
          ) : (
            <>
              {/* Oppose (Red) */}
              {opposeVal > 0 && (
                <circle
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="transparent"
                  stroke="var(--danger)"
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${opposeDash} ${circumference}`}
                  strokeDashoffset={opposeOffset}
                  style={{ transition: 'stroke-dasharray 0.5s ease' }}
                />
              )}

              {/* Support (Green) */}
              {supportVal > 0 && (
                <circle
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="transparent"
                  stroke="var(--success)"
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${supportDash} ${circumference}`}
                  strokeDashoffset={supportOffset}
                  style={{ transition: 'stroke-dasharray 0.5s ease' }}
                />
              )}

              {/* Neutral (Gray) */}
              {neutralVal > 0 && (
                <circle
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="transparent"
                  stroke="#8A948E"
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${neutralDash} ${circumference}`}
                  strokeDashoffset={neutralOffset}
                  style={{ transition: 'stroke-dasharray 0.5s ease' }}
                />
              )}
            </>
          )}
        </svg>

        {/* Center Label */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            pointerEvents: 'none'
          }}
        >
          <span className="tabular-nums" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
            {totalResponses}
          </span>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.2rem' }}>
            Responses
          </span>
        </div>
      </div>

      {/* Legend with Counts and Percentages */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
        {/* Support */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--success)' }} />
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Support</span>
          </div>
          <div className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>
            <strong>{supportVal}%</strong> <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({supportCount})</span>
          </div>
        </div>

        {/* Oppose */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--danger)' }} />
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Oppose</span>
          </div>
          <div className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>
            <strong>{opposeVal}%</strong> <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({opposeCount})</span>
          </div>
        </div>

        {/* Neutral */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#8A948E' }} />
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Neutral</span>
          </div>
          <div className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>
            <strong>{neutralVal}%</strong> <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({neutralCount})</span>
          </div>
        </div>
      </div>
    </div>
  );
}
