/**
 * API Service for YouTube Summarizer
 * Handles all communication with the Flask backend.
 */

const API_BASE = '/api';

export const api = {
    /**
     * Check backend health
     */
    async checkHealth() {
        const response = await fetch(`${API_BASE}/health`);
        return response.json();
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
            throw new Error(errorData.error || 'Failed to generate transcript');
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
            throw new Error(errorData.error || 'Failed to generate summary');
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
            throw new Error(errorData.error || 'Failed to generate hybrid PDF');
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
            throw new Error(errorData.error || 'Failed to validate file');
        }

        return response.json();
    }
};
