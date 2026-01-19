import React, { useState, useEffect, useRef } from 'react';

const VideoInput = ({ onUrlChange, onDurationChange }) => {
    const [url, setUrl] = useState('');
    const [videoId, setVideoId] = useState(null);
    const playerRef = useRef(null);
    const playerContainerRef = useRef(null);

    const extractVideoId = (url) => {
        const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
        const match = url.match(regExp);
        return (match && match[2].length === 11) ? match[2] : null;
    };

    useEffect(() => {
        const id = extractVideoId(url);
        setVideoId(id);
        onUrlChange(url, id);
        if (onDurationChange) onDurationChange(null); // Reset duration on new URL
    }, [url, onUrlChange, onDurationChange]);

    // Load YouTube IFrame API if not already loaded
    useEffect(() => {
        if (!window.YT) {
            const tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            const firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

            window.onYouTubeIframeAPIReady = () => {
                initPlayer(videoId);
            };
        } else if (videoId) {
            if (!playerRef.current) {
                initPlayer(videoId);
            } else {
                playerRef.current.loadVideoById(videoId);
            }
        }
    }, [videoId]);

    const initPlayer = (id) => {
        if (window.YT && window.YT.Player && !playerRef.current) {
            playerRef.current = new window.YT.Player('videoPlayer', {
                height: '315',
                width: '100%',
                videoId: id || '',
                events: {
                    'onReady': (event) => {
                        if (id) {
                            event.target.loadVideoById(id);
                            // Brief delay to ensure metadata is loaded or use onStateChange if reliable
                            // Usually onReady is enough, but getDuration might be 0 initially
                            if (onDurationChange) {
                                // Try immediately, but also could set up an interval or wait for '5' (cued)
                                // For simplicity, we'll try checking duration after a short moment
                                setTimeout(() => {
                                    const dur = event.target.getDuration();
                                    console.log("Video Duration:", dur);
                                    if (dur) onDurationChange(dur);
                                }, 1000);
                            }
                        }
                        window.ytPlayer = event.target; // Make it globally accessible for seekTo
                    },
                    'onStateChange': (event) => {
                        // YT.PlayerState.CUED = 5, PLAYING = 1
                        if (event.data === 1 || event.data === 5) {
                            const dur = event.target.getDuration();
                            if (dur && onDurationChange) onDurationChange(dur);
                        }
                    }
                }
            });
        }
    };

    return (
        <div className="input-section">
            <div className="input-group">
                <input
                    type="text"
                    placeholder="Paste YouTube URL..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                />
            </div>
            <div
                id="videoPreviewContainer"
                className="video-preview"
                style={{ display: videoId ? 'block' : 'none' }}
            >
                <div id="videoPlayer"></div>
            </div>
        </div>
    );
};

export default VideoInput;
