/**
 * API Service for YouTube Summarizer
 * Handles all communication with the Flask backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

console.log(`[API] Initialized with base URL: ${API_BASE}`);

export const api = {
    /**
     * Check backend health
     */
    async checkHealth() {
        try {
            console.log(`[API] Checking health at ${API_BASE}/health...`);
            const response = await fetch(`${API_BASE}/health`);
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
            headers: { 'Content-Type': 'application/json' },
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
     * Generate summary for a video or file
     * @param {Object} options - { url, type, format, file }
     */
    async generateSummary({ url, type = 'normal', format = 'pdf', file = null }) {
        let response;

        if (file) {
            // Multipart upload
            const formData = new FormData();
            formData.append('transcript_file', file);
            formData.append('type', type);
            formData.append('format', format);
            if (url) formData.append('url', url);

            response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                body: formData
            });
        } else {
            // JSON request
            response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, type, format })
            });
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || 'Failed to generate summary';
            console.error(`[API] Summary generation failed: ${errorMessage}`, errorData);
            throw new Error(errorMessage);
        }

        // Summary returns a BLOB (PDF/TXT)
        return response.blob();
    },

    /**
     * Generate hybrid PDF (Summary + Transcript)
     * @param {string} url - YouTube video URL
     * @param {string} type - Summary type (concise, normal, detailed)
     */
    async generateHybrid(url, type = 'normal') {
        const response = await fetch(`${API_BASE}/hybrid`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, type })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || 'Failed to generate hybrid PDF';
            console.error(`[API] Hybrid generation failed: ${errorMessage}`, errorData);
            throw new Error(errorMessage);
        }

        return response.blob();
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
