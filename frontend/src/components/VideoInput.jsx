import React, { useState, useEffect, useRef } from 'react';

const VideoInput = ({ onUrlChange }) => {
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
    }, [url, onUrlChange]);

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
                        if (id) event.target.loadVideoById(id);
                        window.ytPlayer = event.target; // Make it globally accessible for seekTo
                    },
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
