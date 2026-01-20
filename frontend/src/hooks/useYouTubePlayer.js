/**
 * YouTube Player Hook
 * Manages YouTube IFrame Player API initialization and interactions
 */

import { useEffect, useRef, useCallback } from 'react';
import { YOUTUBE_API, YOUTUBE_PLAYER } from '../utils/constants';

export const useYouTubePlayer = (videoId, onDurationChange) => {
    const playerRef = useRef(null);
    const isAPILoadedRef = useRef(false);

    // Load YouTube IFrame API script
    useEffect(() => {
        if (isAPILoadedRef.current || window.YT) {
            isAPILoadedRef.current = true;
            return;
        }

        const tag = document.createElement('script');
        tag.src = YOUTUBE_API.IFRAME_API_URL;
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

        window.onYouTubeIframeAPIReady = () => {
            isAPILoadedRef.current = true;
        };

        return () => {
            // Cleanup: remove global callback
            delete window.onYouTubeIframeAPIReady;
        };
    }, []);

    // Initialize player when video ID changes
    useEffect(() => {
        if (!videoId) return;

        const initPlayer = () => {
            if (!window.YT || !window.YT.Player) {
                // API not ready yet, wait for it
                setTimeout(initPlayer, 100);
                return;
            }

            if (!playerRef.current) {
                // Create new player
                playerRef.current = new window.YT.Player(YOUTUBE_PLAYER.PLAYER_ID, {
                    height: YOUTUBE_PLAYER.HEIGHT,
                    width: YOUTUBE_PLAYER.WIDTH,
                    videoId: videoId,
                    events: {
                        onReady: handlePlayerReady,
                        onStateChange: handlePlayerStateChange,
                    },
                });

                // Make player globally accessible for timestamp seeking
                window.ytPlayer = playerRef.current;
            } else {
                // Load different video in existing player
                playerRef.current.loadVideoById(videoId);
            }
        };

        const handlePlayerReady = (event) => {
            if (videoId) {
                event.target.loadVideoById(videoId);

                // Get duration after brief delay to ensure metadata is loaded
                setTimeout(() => {
                    const duration = event.target.getDuration();
                    if (duration && onDurationChange) {
                        onDurationChange(duration);
                    }
                }, YOUTUBE_PLAYER.DURATION_CHECK_DELAY);
            }
        };

        const handlePlayerStateChange = (event) => {
            // Update duration when video is playing or cued
            const { PLAYING, CUED } = YOUTUBE_API.PLAYER_STATES;
            if (event.data === PLAYING || event.data === CUED) {
                const duration = event.target.getDuration();
                if (duration && onDurationChange) {
                    onDurationChange(duration);
                }
            }
        };

        initPlayer();

        // Cleanup on unmount
        return () => {
            if (playerRef.current && playerRef.current.destroy) {
                playerRef.current.destroy();
                playerRef.current = null;
                delete window.ytPlayer;
            }
        };
    }, [videoId, onDurationChange]);

    // Seek to specific timestamp
    const seekTo = useCallback((seconds) => {
        if (window.ytPlayer && typeof window.ytPlayer.seekTo === 'function') {
            window.ytPlayer.seekTo(seconds, true);
            window.ytPlayer.playVideo();
        }
    }, []);

    return {
        player: playerRef.current,
        seekTo,
    };
};
