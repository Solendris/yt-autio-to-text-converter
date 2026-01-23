/**
 * Application Context
 * Provides centralized state management for the entire app
 */

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

const AppContext = createContext(null);

export const useAppContext = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useAppContext must be used within AppProvider');
    }
    return context;
};

export const AppProvider = ({ children }) => {
    // Video State
    const [videoUrl, setVideoUrl] = useState('');
    const [videoId, setVideoId] = useState(null);
    const [videoDuration, setVideoDuration] = useState(null);
    const playerRef = useRef(null);

    // Transcript State
    const [transcriptData, setTranscriptData] = useState(null);
    const [status, setStatus] = useState({ message: '', type: '' });
    const [isLoading, setIsLoading] = useState(false);

    // Settings
    const [useDiarization, setUseDiarization] = useState(false);

    // Video Actions
    const updateVideoUrl = useCallback((url) => {
        setVideoUrl(url);
    }, []);

    const updateVideoId = useCallback((id) => {
        setVideoId(id);
    }, []);

    const updateVideoDuration = useCallback((duration) => {
        setVideoDuration(duration);
    }, []);

    const updateVideoData = useCallback((url, id) => {
        setVideoUrl(url);
        setVideoId(id);
        setVideoDuration(null); // Reset duration when URL changes
    }, []);

    // Transcript Actions
    const updateTranscriptData = useCallback((data) => {
        setTranscriptData(data);
    }, []);

    const updateStatus = useCallback((newStatus) => {
        setStatus(newStatus);
    }, []);

    const updateLoading = useCallback((loading) => {
        setIsLoading(loading);
    }, []);

    const clearTranscript = useCallback(() => {
        setTranscriptData(null);
        setStatus({ message: '', type: '' });
    }, []);

    // Settings Actions
    const toggleDiarization = useCallback(() => {
        setUseDiarization(prev => !prev);
    }, []);

    const updateDiarization = useCallback((value) => {
        setUseDiarization(value);
    }, []);

    // Player Actions
    const seekTo = useCallback((seconds) => {
        if (playerRef.current && typeof playerRef.current.seekTo === 'function') {
            playerRef.current.seekTo(seconds, true);
            playerRef.current.playVideo();
        }
    }, []);

    const value = {
        // Video State
        videoUrl,
        videoId,
        videoDuration,
        playerRef,

        // Transcript State
        transcriptData,
        status,
        isLoading,

        // Settings
        useDiarization,

        // Video Actions
        updateVideoUrl,
        updateVideoId,
        updateVideoDuration,
        updateVideoData,

        // Transcript Actions
        updateTranscriptData,
        updateStatus,
        updateLoading,
        clearTranscript,

        // Settings Actions
        toggleDiarization,
        updateDiarization,

        // Player Actions
        seekTo,
    };

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
