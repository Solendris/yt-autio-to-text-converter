/**
 * API Service for YouTube Summarizer
 * Handles all communication with the Flask backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api';
const API_KEY = import.meta.env.VITE_API_KEY || '';

// Common headers for all requests
const COMMON_HEADERS = {
    'ngrok-skip-browser-warning': 'true'
};

// Only add API key header if configured (for non-whitelisted origins)
if (API_KEY) {
    COMMON_HEADERS['X-API-Key'] = API_KEY;
}

console.log(`[API] Initialized with base URL: ${API_BASE}`);

export const api = {
    /**
     * Check backend health
     */
    async checkHealth() {
        try {
            console.log(`[API] Checking health at ${API_BASE}/health...`);
            const response = await fetch(`${API_BASE}/health`, {
                headers: COMMON_HEADERS
            });
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            console.log('[API] Health check passed:', data);
            return data;
        } catch (error) {
            console.error(`[API] CRITICAL: Connection to backend failed at ${API_BASE}/health`, error);
            throw error;
        }
    },

    /**
     * Generate transcript for a video
     * @param {string} url - YouTube video URL
     * @param {boolean} diarization - Whether to use speaker identification
     */
    async generateTranscript(url, diarization = false) {
        const response = await fetch(`${API_BASE}/transcript`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...COMMON_HEADERS
            },
            body: JSON.stringify({ url, diarization })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || 'Failed to generate transcript';
            console.error(`[API] Transcript generation failed: ${errorMessage}`, errorData);
            throw new Error(errorMessage);
        }

        return response.json();
    },

    /**
     * Validate an uploaded transcript file
     * @param {File} file - The .txt file
     */
    async validateTranscript(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload-transcript`, {
            method: 'POST',
            headers: COMMON_HEADERS,
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || 'Failed to validate file';
            console.error(`[API] File validation failed: ${errorMessage}`, errorData);
            throw new Error(errorMessage);
        }

        return response.json();
    }
};

