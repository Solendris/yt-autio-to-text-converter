/**
 * TranscriptActions Component
 * Handles transcript generation, download, and settings
 */

import React from 'react';
import { useAppContext } from '../../context/AppContext';
import { useTranscript } from '../../hooks/useTranscript';
import StatusMessage from '../StatusMessage';

const TranscriptActions = () => {
    const {
        transcriptData,
        status,
        useDiarization,
        updateDiarization
    } = useAppContext();

    const { generateTranscript, downloadTranscript } = useTranscript();

    const handleGenerate = () => {
        generateTranscript();
    };

    const handleDownload = () => {
        downloadTranscript(transcriptData);
    };

    return (
        <>
            <div className="option-group" style={{ marginTop: '15px' }}>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                        type="checkbox"
                        checked={useDiarization}
                        onChange={(e) => updateDiarization(e.target.checked)}
                        style={{ width: 'auto', marginRight: '8px' }}
                    />
                    Identify Speakers (Gemini AI)
                </label>
            </div>

            <div className="action-buttons">
                <button className="btn-action" onClick={handleGenerate}>
                    Generate Transcript
                </button>
            </div>

            <StatusMessage status={status} />

            {transcriptData && (
                <button className="btn-download" onClick={handleDownload}>
                    ↓ Download Transcript
                </button>
            )}
        </>
    );
};

export default React.memo(TranscriptActions);
