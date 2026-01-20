/**
 * Time Utility Functions
 * Handles timestamp parsing and formatting operations
 */

/**
 * Parse timestamp string to seconds
 * Supports formats: [MM:SS] and [HH:MM:SS]
 * @param {string} timeStr - Timestamp string (e.g., "1:30" or "1:30:45")
 * @returns {number} Time in seconds
 */
export const parseTimestamp = (timeStr) => {
    if (!timeStr || typeof timeStr !== 'string') return 0;

    // Remove brackets if present
    const cleanStr = timeStr.replace(/[\[\]]/g, '').trim();
    const parts = cleanStr.split(':');

    let seconds = 0;

    if (parts.length === 2) {
        // MM:SS format
        const minutes = parseInt(parts[0], 10) || 0;
        const secs = parseInt(parts[1], 10) || 0;
        seconds = minutes * 60 + secs;
    } else if (parts.length === 3) {
        // HH:MM:SS format
        const hours = parseInt(parts[0], 10) || 0;
        const minutes = parseInt(parts[1], 10) || 0;
        const secs = parseInt(parts[2], 10) || 0;
        seconds = hours * 3600 + minutes * 60 + secs;
    }

    return seconds;
};

/**
 * Format seconds to timestamp string
 * @param {number} totalSeconds - Time in seconds
 * @param {boolean} includeHours - Force HH:MM:SS format
 * @returns {string} Formatted timestamp (e.g., "1:30" or "1:30:45")
 */
export const formatSeconds = (totalSeconds, includeHours = false) => {
    if (typeof totalSeconds !== 'number' || totalSeconds < 0) return '0:00';

    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    const pad = (num) => String(num).padStart(2, '0');

    if (hours > 0 || includeHours) {
        return `${hours}:${pad(minutes)}:${pad(seconds)}`;
    }

    return `${minutes}:${pad(seconds)}`;
};

/**
 * Validate if string is a valid timestamp format
 * @param {string} timeStr - String to validate
 * @returns {boolean} True if valid timestamp format
 */
export const isValidTimestamp = (timeStr) => {
    if (!timeStr || typeof timeStr !== 'string') return false;

    const cleanStr = timeStr.replace(/[\[\]]/g, '').trim();
    const parts = cleanStr.split(':');

    if (parts.length < 2 || parts.length > 3) return false;

    return parts.every(part => {
        const num = parseInt(part, 10);
        return !isNaN(num) && num >= 0;
    });
};
