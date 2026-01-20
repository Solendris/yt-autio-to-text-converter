/**
 * VideoInput Component
 * Main container for video input section
 */

import React, { useEffect } from 'react';
import UrlInput from './UrlInput';
import VideoPreview from './VideoPreview';
import { api } from '../../services/api';

const VideoInput = () => {
    // Perform initial health check on mount
    useEffect(() => {
        api.checkHealth().catch(err => {
            console.warn('[VideoInput] Initial health check failed:', err);
        });
    }, []);

    return (
        <div className="input-section">
            <UrlInput />
            <VideoPreview />
        </div>
    );
};

export default VideoInput;
