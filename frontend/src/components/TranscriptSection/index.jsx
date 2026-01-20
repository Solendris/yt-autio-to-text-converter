/**
 * TranscriptSection Component
 * Main container for transcript section
 */

import React from 'react';
import TranscriptActions from './TranscriptActions';
import TranscriptDisplay from './TranscriptDisplay';
import { MESSAGES } from '../../utils/constants';

const TranscriptSection = () => {
    return (
        <div className="section transcript">
            <h2>Transcript</h2>

            <TranscriptActions />

            <div className="timestamp-hint">
                {MESSAGES.TIMESTAMP_HINT}
            </div>

            <div className="transcript-box">
                <TranscriptDisplay />
            </div>
        </div>
    );
};

export default TranscriptSection;
