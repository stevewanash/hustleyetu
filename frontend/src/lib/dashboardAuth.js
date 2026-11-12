/**
 * Dashboard Authentication Service (Simulated / Demo-Ready & Secret-Configurable)
 *
 * Implements authentication specifically for the Insights Dashboard page.
 * Supports configurable deployment secrets (via NEXT_PUBLIC_DASHBOARD_AUTH_PASSWORD)
 * with robust demo fallbacks so it works seamlessly during class presentations.
 */

const STORAGE_KEY = 'hustleyetu_insights_session';

export function getExpectedPassword() {
  return process.env.NEXT_PUBLIC_DASHBOARD_AUTH_PASSWORD || 'hustleyetu2026';
}

export function getExpectedEmail() {
  return process.env.NEXT_PUBLIC_DASHBOARD_AUTH_EMAIL || 'analyst@hustleyetu.ke';
}

export function getExpectedOtp() {
  return process.env.NEXT_PUBLIC_DASHBOARD_DEMO_OTP || '123456';
}

export function getDemoCredentials() {
  return {
    email: getExpectedEmail(),
    password: getExpectedPassword(),
    otp: getExpectedOtp(),
  };
}

/**
 * Retrieve the active dashboard session from localStorage
 */
export function getDashboardSession() {
  if (typeof window === 'undefined') return null;

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;

    const session = JSON.parse(raw);
    if (!session || !session.expiresAt) return null;

    // Check expiry
    if (Date.now() > session.expiresAt) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }

    return session;
  } catch (err) {
    console.error('Error reading dashboard auth session:', err);
    return null;
  }
}

/**
 * Authenticate using Policy Analyst Email and Passcode/Secret
 */
export async function authenticateWithPasscode(email, password) {
  // Simulate network latency (500ms) for realistic UX
  await new Promise((resolve) => setTimeout(resolve, 500));

  const cleanEmail = (email || '').trim().toLowerCase();
  const cleanPass = (password || '').trim();
  const expectedPass = getExpectedPassword();

  // Allow the configured secret password, or fallback demo passwords
  const validPasswords = [expectedPass, 'hustleyetu2026', 'admin123', 'demo123'].filter(Boolean);

  if (!cleanPass) {
    throw new Error('Please enter your passcode or secret key.');
  }

  if (!validPasswords.includes(cleanPass)) {
    throw new Error(`Invalid passcode. Hint: Use '${expectedPass}' or check your deployment secret.`);
  }

  const session = {
    token: `demo-jwt-insights-${Date.now()}`,
    user: {
      identifier: cleanEmail || getExpectedEmail(),
      name: cleanEmail ? cleanEmail.split('@')[0] : 'Policy Analyst',
      role: 'Verified Policy Analyst',
      department: 'Legislative Impact & Sentiment Research',
      authMethod: 'passcode',
    },
    loginTime: new Date().toISOString(),
    expiresAt: Date.now() + 24 * 60 * 60 * 1000, // 24 hours session
  };

  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }

  return session;
}

/**
 * Authenticate using Mobile Phone SMS OTP (Simulated Flow)
 */
export async function authenticateWithOtp(phone, otpToken) {
  // Simulate network latency (600ms) for realistic UX
  await new Promise((resolve) => setTimeout(resolve, 600));

  const cleanPhone = (phone || '').trim();
  const cleanOtp = (otpToken || '').trim();
  const expectedOtp = getExpectedOtp();

  if (!cleanPhone) {
    throw new Error('Please enter your mobile phone number.');
  }

  if (!cleanOtp || cleanOtp.length < 6) {
    throw new Error('Please enter the complete 6-digit verification code.');
  }

  // Accepts configured OTP, default 123456, or any 6-digit number in demo simulation
  const isValidOtp = cleanOtp === expectedOtp || cleanOtp === '123456' || /^\d{6}$/.test(cleanOtp);

  if (!isValidOtp) {
    throw new Error(`Invalid verification code. Enter '${expectedOtp}' for demo access.`);
  }

  const session = {
    token: `demo-jwt-phone-${Date.now()}`,
    user: {
      identifier: cleanPhone,
      name: 'Verified Stakeholder',
      role: 'Civic Stakeholder',
      department: 'Transport Sector Representative',
      authMethod: 'sms_otp',
    },
    loginTime: new Date().toISOString(),
    expiresAt: Date.now() + 24 * 60 * 60 * 1000,
  };

  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }

  return session;
}

/**
 * Sign out and clear active dashboard session
 */
export function logoutDashboard() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY);
  }
}
