/**
 * Application Constants
 * Central location for all magic numbers, strings, and configuration values
 */

// YouTube Player Configuration
export const YOUTUBE_PLAYER = {
    HEIGHT: '315',
    WIDTH: '100%',
    PLAYER_ID: 'videoPlayer',
    CONTAINER_ID: 'videoPreviewContainer',
    DURATION_CHECK_DELAY: 1000, // ms to wait before checking duration
};

// Speaker Identification
export const SPEAKER_CONFIG = {
    MAX_COLORS: 12, // Number of different speaker colors available
    COLOR_PREFIX: 'speaker-', // CSS class prefix for speaker colors
};

// Regular Expressions
export const REGEX = {
    YOUTUBE_URL: /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/,
    SPEAKER_LINE: /^(\[\d{1,2}:\d{2}(:\d{2})?\])\s*(Speaker \d+|[\w\s]+):(.*)/i,
    TIMESTAMP: /\[\d{1,2}:\d{2}(:\d{2})?\]/g,
    TIMESTAMP_FORMAT: /\[\d{1,2}:\d{2}(:\d{2})?\]/,
};

// Processing Time Estimates (in minutes)
export const PROCESSING_ESTIMATES = {
    DEFAULT: 'Processing... usually takes 3-5 minutes.',
    SHORT: 'Processing... Estimated time: ~1-2 minutes.', // < 10 min video
    MEDIUM: 'Processing... Estimated time: ~2-5 minutes.', // 10-30 min video
    LONG: 'Processing... Estimated time: ~5-10 minutes.', // 30-60 min video
    VERY_LONG: 'Processing... Estimated time: ~10-15 minutes.', // 60-90 min video
    EXTRA_LONG: 'Processing... Estimated time: ~15-20 minutes.', // 90-120 min video
};

// Time thresholds for processing estimates (in minutes)
export const TIME_THRESHOLDS = {
    SHORT: 10,
    MEDIUM: 30,
    LONG: 60,
    VERY_LONG: 90,
    EXTRA_LONG: 120,
};

// Status Message Types
export const STATUS_TYPES = {
    SUCCESS: 'success',
    ERROR: 'error',
    LOADING: 'loading',
    INFO: 'info',
};

// YouTube API
export const YOUTUBE_API = {
    IFRAME_API_URL: 'https://www.youtube.com/iframe_api',
    PLAYER_STATES: {
        UNSTARTED: -1,
        ENDED: 0,
        PLAYING: 1,
        PAUSED: 2,
        BUFFERING: 3,
        CUED: 5,
    },
};

// Validation
export const VALIDATION = {
    YOUTUBE_VIDEO_ID_LENGTH: 11,
};

// UI Messages
export const MESSAGES = {
    ENTER_URL: 'Enter URL',
    TIMESTAMP_HINT: 'Tip: Click timestamps to jump to that moment in the video.',
    PLACEHOLDER: 'Transcript will appear here...',
};
