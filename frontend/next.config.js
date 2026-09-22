/** @type {import('next').NextConfig} */
const isVercel = process.env.VERCEL === '1';
const buildStandalone = process.env.BUILD_STANDALONE === 'true';

const nextConfig = {
  reactStrictMode: true,
  // Enable standalone output ONLY for VPS / self-hosted production builds, never on Vercel
  ...(buildStandalone || (!isVercel && process.env.NODE_ENV === 'production')
    ? { output: 'standalone' }
    : {}),
};

module.exports = nextConfig;

