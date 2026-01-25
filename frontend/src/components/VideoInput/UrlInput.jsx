/**
 * UrlInput Component
 * Handles YouTube URL input field
 */

import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import { extractVideoId } from '../../utils/youtube';

const UrlInput = () => {
    const { updateVideoData, clearTranscript } = useAppContext();
    const [localUrl, setLocalUrl] = useState('');

    useEffect(() => {
        const timer = setTimeout(() => {
            if (localUrl) {
                const videoId = extractVideoId(localUrl);
                updateVideoData(localUrl, videoId);
                clearTranscript();
            }
        }, 500); // 500ms debounce

        return () => clearTimeout(timer);
    }, [localUrl, updateVideoData, clearTranscript]);

    return (
        <div className="input-group">
            <input
                type="text"
                placeholder="Paste YouTube URL..."
                value={localUrl}
                onChange={(e) => setLocalUrl(e.target.value)}
            />
            <p className="input-hint">
                <span className="hint-icon">ℹ️</span> Maximum video duration: 90 minutes
            </p>
        </div>
    );
};

export default React.memo(UrlInput);

