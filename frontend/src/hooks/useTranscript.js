/**
 * Transcript Hook
 * Handles transcript generation, downloading, and status management
 */

import { useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import { api } from '../services/api';
import { getEstimatedTimeMessage } from '../utils/youtube';
import { STATUS_TYPES, MESSAGES } from '../utils/constants';

export const useTranscript = () => {
    const {
        videoUrl,
        videoDuration,
        useDiarization,
        updateTranscriptData,
        updateStatus,
        updateLoading,
    } = useAppContext();

    const generateTranscript = useCallback(async () => {
        if (!videoUrl) {
            updateStatus({ message: MESSAGES.ENTER_URL, type: STATUS_TYPES.ERROR });
            return;
        }

        const loadingMsg = getEstimatedTimeMessage(videoDuration);
        updateStatus({
            message: `${loadingMsg} Please wait.`,
            type: STATUS_TYPES.LOADING
        });
        updateLoading(true);

        try {
            const data = await api.generateTranscript(videoUrl, useDiarization);
            updateTranscriptData(data);
            updateStatus({
                message: `[OK] Ready! Source: ${data.source}`,
                type: STATUS_TYPES.SUCCESS
            });
        } catch (error) {
            updateStatus({
                message: `Error: ${error.message}`,
                type: STATUS_TYPES.ERROR
            });
        } finally {
            updateLoading(false);
        }
    }, [videoUrl, videoDuration, useDiarization, updateTranscriptData, updateStatus, updateLoading]);

    const downloadTranscript = useCallback((transcriptData) => {
        if (!transcriptData) return;

        const blob = new Blob([transcriptData.transcript], { type: 'text/plain' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = transcriptData.filename || 'transcript.txt';
        link.click();

        // Clean up the object URL
        URL.revokeObjectURL(link.href);
    }, []);

    return {
        generateTranscript,
        downloadTranscript,
    };
};
