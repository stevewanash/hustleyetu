/**
 * Truncate text cleanly at word boundaries to produce concise card teasers.
 *
 * @param {string} text - Source text to truncate
 * @param {number} wordCount - Maximum number of words (default: 15)
 * @param {string} suffix - Suffix to append if truncated (default: '…')
 * @returns {string} Clean teaser text
 */
export function truncateWords(text, wordCount = 15, suffix = '…') {
  if (!text || typeof text !== 'string') return '';
  
  // Clean whitespace and trim
  const clean = text.trim().replace(/\s+/g, ' ');
  const words = clean.split(' ');
  
  if (words.length <= wordCount) {
    return clean;
  }
  
  return words.slice(0, wordCount).join(' ') + suffix;
}
