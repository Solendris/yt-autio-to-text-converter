import React, { useState, useEffect } from 'react';
import './ProcessingOverlay.css';

const ProcessingOverlay = ({ isVisible }) => {
    const [elapsedTime, setElapsedTime] = useState(0);

    useEffect(() => {
        if (!isVisible) {
            setElapsedTime(0);
            return;
        }

        // Timer interval
        const timer = setInterval(() => {
            setElapsedTime(prev => prev + 1);
        }, 1000);

        return () => {
            clearInterval(timer);
        };
    }, [isVisible]);

    if (!isVisible) return null;

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="processing-overlay">
            <div className="processing-visual">
                {/* CSS handles the pulsing animation locally */}
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="white" fillOpacity="0.5" />
                    <path d="M12 6L12 18" stroke="white" strokeWidth="2" strokeLinecap="round" />
                    <path d="M6 12L18 12" stroke="white" strokeWidth="2" strokeLinecap="round" />
                </svg>
            </div>



            <div className="processing-timer">
                Time Elapsed: {formatTime(elapsedTime)}
            </div>
        </div>
    );
};

export default ProcessingOverlay;
