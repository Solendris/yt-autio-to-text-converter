/**
 * TranscriptDisplay Component
 * Displays formatted transcript text
 */

import React, { useCallback } from 'react';
import { useAppContext } from '../../context/AppContext';
import { useTranscriptFormatting } from '../../hooks/useTranscriptFormatting';
import { useYouTubePlayer } from '../../hooks/useYouTubePlayer';
import TranscriptLine from './TranscriptLine';
import { MESSAGES } from '../../utils/constants';

const TranscriptDisplay = () => {
    const { transcriptData, videoId } = useAppContext();
    const { seekTo } = useYouTubePlayer(videoId);
    const { formattedLines } = useTranscriptFormatting(
        transcriptData?.transcript || null
    );

    const handleTimestampClick = useCallback((seconds) => {
        seekTo(seconds);
    }, [seekTo]);

    if (!transcriptData) {
        return (
            <div className="placeholder-text">
                {MESSAGES.PLACEHOLDER}
            </div>
        );
    }

    return (
        <>
            {formattedLines.map(line => (
                <TranscriptLine
                    key={line.id}
                    line={line}
                    onTimestampClick={handleTimestampClick}
                />
            ))}
        </>
    );
};

export default React.memo(TranscriptDisplay);
