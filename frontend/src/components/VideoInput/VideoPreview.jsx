/**
 * VideoPreview Component
 * Displays YouTube video player using IFrame API
 */

import React from 'react';
import { useAppContext } from '../../context/AppContext';
import { useYouTubePlayer } from '../../hooks/useYouTubePlayer';
import { YOUTUBE_PLAYER } from '../../utils/constants';

const VideoPreview = () => {
    const { videoId, updateVideoDuration, playerRef } = useAppContext();

    // Initialize YouTube player with custom hook
    useYouTubePlayer(videoId, updateVideoDuration, playerRef);

    if (!videoId) return null;

    return (
        <div
            id={YOUTUBE_PLAYER.CONTAINER_ID}
            className="video-preview"
            style={{ display: 'block' }}
        >
            <div id={YOUTUBE_PLAYER.PLAYER_ID}></div>
        </div>
    );
};

export default React.memo(VideoPreview);
