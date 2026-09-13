/**
 * Kenyan E.164 phone number formatting and validation helpers.
 */

export function formatE164(raw) {
  if (!raw) return '';
  const cleaned = String(raw).replace(/[\s\-().]/g, '');
  if (cleaned.startsWith('+254') && cleaned.length === 13) return cleaned;
  if (cleaned.startsWith('254') && cleaned.length === 12) return `+${cleaned}`;
  if (cleaned.startsWith('0') && cleaned.length === 10) return `+254${cleaned.slice(1)}`;
  if (cleaned.length === 9) return `+254${cleaned}`;
  return cleaned.startsWith('+') ? cleaned : `+${cleaned}`;
}

export function isValidKenyanPhone(phone) {
  if (!phone) return false;
  const formatted = formatE164(phone);
  return /^\+254\d{9}$/.test(formatted);
}

export function formatDisplayPhone(phone) {
  if (!phone) return '';
  let cleaned = String(phone).replace(/[\s\-().]/g, '');
  if (cleaned.startsWith('+254')) {
    cleaned = `0${cleaned.slice(4)}`;
  } else if (cleaned.startsWith('254')) {
    cleaned = `0${cleaned.slice(3)}`;
  }
  if (cleaned.length >= 10) {
    return `${cleaned.slice(0, 4)}***${cleaned.slice(-3)}`;
  }
  return cleaned;
}
