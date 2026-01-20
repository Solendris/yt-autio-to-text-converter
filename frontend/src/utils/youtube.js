/**
 * YouTube Utility Functions
 * Handles YouTube URL parsing, validation, and related operations
 */

import {
    REGEX,
    VALIDATION,
    PROCESSING_ESTIMATES,
    TIME_THRESHOLDS
} from './constants';

/**
 * Extract video ID from YouTube URL
 * @param {string} url - YouTube URL
 * @returns {string|null} Video ID or null if invalid
 */
export const extractVideoId = (url) => {
    if (!url || typeof url !== 'string') return null;

    const match = url.match(REGEX.YOUTUBE_URL);
    return (match && match[2].length === VALIDATION.YOUTUBE_VIDEO_ID_LENGTH)
        ? match[2]
        : null;
};

/**
 * Validate if URL is a valid YouTube URL
 * @param {string} url - URL to validate
 * @returns {boolean} True if valid YouTube URL
 */
export const isValidYouTubeUrl = (url) => {
    return extractVideoId(url) !== null;
};

/**
 * Get estimated processing time message based on video duration
 * @param {number|null} duration - Video duration in seconds
 * @returns {string} Processing time estimate message
 */
export const getEstimatedTimeMessage = (duration) => {
    if (!duration) return PROCESSING_ESTIMATES.DEFAULT;

    const minutes = duration / 60;

    if (minutes < TIME_THRESHOLDS.SHORT) return PROCESSING_ESTIMATES.SHORT;
    if (minutes < TIME_THRESHOLDS.MEDIUM) return PROCESSING_ESTIMATES.MEDIUM;
    if (minutes < TIME_THRESHOLDS.LONG) return PROCESSING_ESTIMATES.LONG;
    if (minutes < TIME_THRESHOLDS.VERY_LONG) return PROCESSING_ESTIMATES.VERY_LONG;
    if (minutes < TIME_THRESHOLDS.EXTRA_LONG) return PROCESSING_ESTIMATES.EXTRA_LONG;

    return PROCESSING_ESTIMATES.DEFAULT;
};

/**
 * Generate YouTube embed URL
 * @param {string} videoId - YouTube video ID
 * @returns {string} Embed URL
 */
export const getEmbedUrl = (videoId) => {
    return `https://www.youtube.com/embed/${videoId}`;
};

/**
 * Generate YouTube watch URL
 * @param {string} videoId - YouTube video ID
 * @returns {string} Watch URL
 */
export const getWatchUrl = (videoId) => {
    return `https://www.youtube.com/watch?v=${videoId}`;
};
