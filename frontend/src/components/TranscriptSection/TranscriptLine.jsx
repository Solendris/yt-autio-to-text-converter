/**
 * TranscriptLine Component
 * Renders a single line of transcript with clickable timestamps
 */

import React from 'react';
import { parseTimestamp } from '../../utils/time';
import { SPEAKER_CONFIG, REGEX } from '../../utils/constants';

const TranscriptLine = ({ line, onTimestampClick }) => {
    if (line.type === 'speaker') {
        // Speaker line: [timestamp] Speaker: content
        const cssClass = `${SPEAKER_CONFIG.COLOR_PREFIX}${line.colorId}`;
        const timeInSeconds = parseTimestamp(line.timestamp);

        return (
            <div className={`transcript-line ${cssClass}`}>
                <span
                    className="timestamp-link"
                    onClick={(e) => {
                        e.stopPropagation();
                        // console.log(`[TranscriptLine] Clicked timestamp: ${line.timestamp}`);
                        onTimestampClick(timeInSeconds);
                    }}
                >
                    {line.timestamp}
                </span>
                <span className="speaker-label">{line.speakerName}</span>
                {line.content}
            </div>
        );
    }

    // Regular line: may contain inline timestamps
    const parts = line.content.split(REGEX.TIMESTAMP);
    const timestamps = line.content.match(REGEX.TIMESTAMP) || [];

    const processedContent = [];
    let timestampIndex = 0;

    parts.forEach((part, index) => {
        if (part) {
            processedContent.push(
                <span key={`text-${index}`}>{part}</span>
            );
        }

        if (timestampIndex < timestamps.length) {
            const timestamp = timestamps[timestampIndex];
            const timeInSeconds = parseTimestamp(timestamp);

            processedContent.push(
                <span
                    key={`timestamp-${index}`}
                    className="timestamp-link"
                    onClick={(e) => {
                        e.stopPropagation();
                        // console.log(`[TranscriptLine] Clicked inline timestamp: ${timestamp}`);
                        onTimestampClick(timeInSeconds);
                    }}
                >
                    {timestamp}
                </span>
            );
            timestampIndex++;
        }
    });

    // Only render if there's actual content
    if (processedContent.length === 0) return null;

    return <div className="transcript-line">{processedContent}</div>;
};

export default React.memo(TranscriptLine);
