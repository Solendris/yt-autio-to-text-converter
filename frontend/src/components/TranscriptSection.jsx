import React, { useState } from 'react';
import StatusMessage from './StatusMessage';
import { api } from '../services/api';

const TranscriptSection = ({ videoUrl }) => {
    const [useDiarization, setUseDiarization] = useState(false);
    const [status, setStatus] = useState({ message: '', type: '' });
    const [transcriptData, setTranscriptData] = useState(null);

    const generateTranscript = async () => {
        if (!videoUrl) {
            setStatus({ message: 'Enter URL', type: 'error' });
            return;
        }

        setStatus({ message: 'Processing...', type: 'loading' });

        try {
            const data = await api.generateTranscript(videoUrl, useDiarization);
            setTranscriptData(data);
            setStatus({ message: `[OK] Ready! Source: ${data.source}`, type: 'success' });
        } catch (e) {
            setStatus({ message: 'Error: ' + e.message, type: 'error' });
        }
    };

    const downloadTranscript = () => {
        if (!transcriptData) return;
        const blob = new Blob([transcriptData.transcript], { type: 'text/plain' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = transcriptData.filename || 'transcript.txt';
        link.click();
    };

    const seekToTimestamp = (timeStr) => {
        if (!window.ytPlayer || typeof window.ytPlayer.seekTo !== 'function') return;

        const parts = timeStr.split(':');
        let seconds = 0;
        if (parts.length === 2) {
            seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);
        } else if (parts.length === 3) {
            seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
        }

        window.ytPlayer.seekTo(seconds, true);
        window.ytPlayer.playVideo();
    };

    const renderTranscriptContent = () => {
        if (!transcriptData) return null;

        const text = transcriptData.transcript;
        const lines = text.split('\n');
        const speakerRegex = /^(\[\d{1,2}:\d{2}(?::\d{2})?\])\s*(Speaker \d+|[\w\s]+):(.*)/i;
        const speakerMap = {};
        let nextColorId = 1;
        const maxColors = 12;

        return lines.map((line, index) => {
            const match = line.match(speakerRegex);
            if (match) {
                const timeStr = match[1];
                const speakerName = match[2].trim();
                const content = match[3].trim();

                if (!speakerMap[speakerName]) {
                    speakerMap[speakerName] = nextColorId;
                    nextColorId = (nextColorId % maxColors) + 1;
                }
                const colorId = speakerMap[speakerName];
                const cssClass = `speaker-${colorId}`;

                return (
                    <div key={index} className={`transcript-line ${cssClass}`}>
                        <span
                            className="timestamp-link"
                            onClick={() => seekToTimestamp(timeStr.replace(/[\[\]]/g, ''))}
                        >
                            {timeStr}
                        </span>
                        <span className="speaker-label">{speakerName}</span>
                        {content}
                    </div>
                );
            } else {
                const parts = line.split(/(\[\d{1,2}:\d{2}(?::\d{2})?\])/g);
                const processedLine = parts.map((part, i) => {
                    if (part.match(/\[\d{1,2}:\d{2}(?::\d{2})?\]/)) {
                        return (
                            <span
                                key={i}
                                className="timestamp-link"
                                onClick={() => seekToTimestamp(part.replace(/[\[\]]/g, ''))}
                            >
                                {part}
                            </span>
                        );
                    }
                    return part;
                });

                return processedLine.some(p => typeof p !== 'string' || p.trim()) ? (
                    <div key={index}>{processedLine}</div>
                ) : null;
            }
        });
    };

    return (
        <div className="section transcript">
            <h2>📝 Section 1: Transcript</h2>

            <div className="info-box">
                ✓ Auto source detection<br />
                ✓ 3-5 minutes processing<br />
                ✓ Cost: FREE
            </div>

            <div className="option-group" style={{ marginTop: '15px' }}>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                        type="checkbox"
                        checked={useDiarization}
                        onChange={(e) => setUseDiarization(e.target.checked)}
                        style={{ width: 'auto', marginRight: '8px' }}
                    />
                    Identify Speakers (Gemini AI) ⭐
                </label>
            </div>

            <div className="action-buttons">
                <button className="btn-action" onClick={generateTranscript}>Generate Transcript</button>
            </div>

            <StatusMessage status={status} />

            {transcriptData && (
                <>
                    <div className="timestamp-hint">
                        💡 Tip: Click timestamps <b>[MM:SS]</b> to jump to that moment in the video.
                    </div>
                    <div className="transcript-box">
                        {renderTranscriptContent()}
                    </div>
                    <button className="btn-download" onClick={downloadTranscript}>
                        ↓ Download Transcript
                    </button>
                </>
            )}
        </div>
    );
};

export default TranscriptSection;
