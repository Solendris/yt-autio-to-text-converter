/**
 * Transcript Formatting Hook
 * Handles parsing and formatting of transcript data with speaker identification
 */

import { useMemo } from 'react';
import { REGEX, SPEAKER_CONFIG } from '../utils/constants';

export const useTranscriptFormatting = (transcriptText) => {
    const formattedLines = useMemo(() => {
        if (!transcriptText) return [];

        const lines = transcriptText.split('\n');
        const speakerMap = {};
        let nextColorId = 1;

        return lines.map((line, index) => {
            const match = line.match(REGEX.SPEAKER_LINE);

            if (match) {
                // Speaker line format: [timestamp] Speaker: content
                const timestamp = match[1];
                const speakerName = match[3].trim();
                const content = match[4].trim();

                // Assign color to speaker
                if (!speakerMap[speakerName]) {
                    speakerMap[speakerName] = nextColorId;
                    nextColorId = (nextColorId % SPEAKER_CONFIG.MAX_COLORS) + 1;
                }

                const colorId = speakerMap[speakerName];

                return {
                    id: index,
                    type: 'speaker',
                    timestamp,
                    speakerName,
                    content,
                    colorId,
                    originalLine: line,
                };
            } else {
                // Regular line (may contain inline timestamps)
                return {
                    id: index,
                    type: 'regular',
                    content: line,
                    originalLine: line,
                };
            }
        }).filter(item => {
            // Filter out empty lines
            return item.content && item.content.trim().length > 0;
        });
    }, [transcriptText]);

    /**
     * Extract all timestamps from a line of text
     * @param {string} text - Text to search for timestamps
     * @returns {Array} Array of timestamp strings
     */
    const extractTimestamps = useMemo(() => {
        return (text) => {
            if (!text) return [];
            const matches = text.match(REGEX.TIMESTAMP);
            return matches || [];
        };
    }, []);

    /**
     * Split text by timestamps for rendering
     * @param {string} text - Text to split
     * @returns {Array} Array of text parts and timestamp objects
     */
    const splitByTimestamps = useMemo(() => {
        return (text) => {
            if (!text) return [];

            const parts = text.split(REGEX.TIMESTAMP);
            const timestamps = extractTimestamps(text);

            const result = [];
            let timestampIndex = 0;

            parts.forEach((part, index) => {
                if (part) {
                    result.push({ type: 'text', content: part });
                }

                if (timestampIndex < timestamps.length) {
                    result.push({
                        type: 'timestamp',
                        content: timestamps[timestampIndex]
                    });
                    timestampIndex++;
                }
            });

            return result;
        };
    }, [extractTimestamps]);

    return {
        formattedLines,
        extractTimestamps,
        splitByTimestamps,
    };
};
