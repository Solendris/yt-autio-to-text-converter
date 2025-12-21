import React, { useState } from 'react';
import StatusMessage from './StatusMessage';

const SummarizeSection = ({ videoUrl }) => {
    const [source, setSource] = useState('video');
    const [summaryType, setSummaryType] = useState('normal');
    const [format, setFormat] = useState('pdf');
    const [file, setFile] = useState(null);
    const [fileInfo, setFileInfo] = useState('');
    const [status, setStatus] = useState({ message: '', type: '' });
    const [currentSummaryBlob, setCurrentSummaryBlob] = useState(null);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (!selectedFile) return;

        if (!selectedFile.name.endsWith('.txt')) {
            setStatus({ message: 'Error: Only .txt files allowed', type: 'error' });
            e.target.value = '';
            setFileInfo('');
            return;
        }

        const fileSize = (selectedFile.size / 1024).toFixed(2);
        const reader = new FileReader();
        reader.onload = (evt) => {
            const wordCount = evt.target.result.split(/\s+/).filter(w => w.length > 0).length;
            setFileInfo(`✓ ${selectedFile.name} | ${fileSize} KB | ${wordCount} words`);
            setFile(selectedFile);
        };
        reader.readAsText(selectedFile);
    };

    const generateSummary = async () => {
        if (source === 'video') {
            if (!videoUrl) {
                setStatus({ message: 'Enter YouTube URL above', type: 'error' });
                return;
            }

            setStatus({ message: 'Processing...', type: 'loading' });
            try {
                const response = await fetch('/api/summarize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: videoUrl,
                        type: summaryType,
                        format: format
                    })
                });

                if (!response.ok) throw new Error('Failed');

                const blob = await response.blob();
                setCurrentSummaryBlob(blob);
                setStatus({ message: '[OK] Ready!', type: 'success' });
            } catch (e) {
                setStatus({ message: 'Error: ' + e.message, type: 'error' });
            }
        } else {
            if (!file) {
                setStatus({ message: 'Select a .txt file', type: 'error' });
                return;
            }

            setStatus({ message: 'Processing...', type: 'loading' });
            try {
                const formData = new FormData();
                formData.append('transcript_file', file);
                formData.append('type', summaryType);
                formData.append('format', format);

                const response = await fetch('/api/summarize', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Failed');

                const blob = await response.blob();
                setCurrentSummaryBlob(blob);
                setStatus({ message: '[OK] Ready!', type: 'success' });
            } catch (e) {
                setStatus({ message: 'Error: ' + e.message, type: 'error' });
            }
        }
    };

    const downloadSummary = () => {
        if (!currentSummaryBlob) return;
        const link = document.createElement('a');
        link.href = URL.createObjectURL(currentSummaryBlob);
        link.download = `summary.${format}`;
        link.click();
    };

    return (
        <div className="section summarize">
            <h2>✨ Section 2: Summarize</h2>

            <div className="options">
                <div className="option-group">
                    <label>📁 Transcript Source:</label>
                    <div className="option-buttons">
                        <button
                            className={`option-btn ${source === 'video' ? 'active' : ''}`}
                            onClick={() => setSource('video')}
                        >
                            From Video
                        </button>
                        <button
                            className={`option-btn ${source === 'file' ? 'active' : ''}`}
                            onClick={() => setSource('file')}
                        >
                            From File ⭐
                        </button>
                    </div>
                </div>

                {source === 'file' && (
                    <div className="option-group">
                        <label>📄 Upload Transcript File:</label>
                        <input type="file" accept=".txt" onChange={handleFileChange} />
                        {fileInfo && <div id="fileInfo">{fileInfo}</div>}
                    </div>
                )}

                <div className="option-group">
                    <label>Summary Type:</label>
                    <div className="option-buttons">
                        {['concise', 'normal', 'detailed'].map(type => (
                            <button
                                key={type}
                                className={`option-btn ${summaryType === type ? 'active' : ''}`}
                                onClick={() => setSummaryType(type)}
                            >
                                {type.charAt(0).toUpperCase() + type.slice(1)} {type === 'normal' && '⭐'}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="option-group">
                    <label>Format:</label>
                    <div className="option-buttons">
                        <button
                            className={`option-btn ${format === 'pdf' ? 'active' : ''}`}
                            onClick={() => setFormat('pdf')}
                        >
                            PDF
                        </button>
                        <button
                            className={`option-btn ${format === 'txt' ? 'active' : ''}`}
                            onClick={() => setFormat('txt')}
                        >
                            TXT
                        </button>
                    </div>
                </div>
            </div>

            <div className="action-buttons">
                <button className="btn-action" onClick={generateSummary}>Generate Summary</button>
            </div>

            <StatusMessage status={status} />

            {currentSummaryBlob && (
                <button className="btn-download" onClick={downloadSummary}>
                    ↓ Download Summary
                </button>
            )}
        </div>
    );
};

export default SummarizeSection;
