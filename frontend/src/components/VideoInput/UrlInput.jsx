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
        const videoId = extractVideoId(localUrl);
        updateVideoData(localUrl, videoId);

        // Clear previous transcript when URL changes
        if (localUrl !== '') {
            clearTranscript();
        }
    }, [localUrl, updateVideoData, clearTranscript]);

    return (
        <div className="input-group">
            <input
                type="text"
                placeholder="Paste YouTube URL..."
                value={localUrl}
                onChange={(e) => setLocalUrl(e.target.value)}
            />
        </div>
    );
};

export default React.memo(UrlInput);
