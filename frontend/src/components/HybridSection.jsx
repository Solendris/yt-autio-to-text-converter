import React, { useState } from 'react';
import StatusMessage from './StatusMessage';

const HybridSection = ({ videoUrl }) => {
    const [hybridType, setHybridType] = useState('normal');
    const [status, setStatus] = useState({ message: '', type: '' });
    const [currentHybridBlob, setCurrentHybridBlob] = useState(null);

    const generateHybrid = async () => {
        if (!videoUrl) {
            setStatus({ message: 'Enter URL', type: 'error' });
            return;
        }

        setStatus({ message: 'Processing...', type: 'loading' });
        try {
            const response = await fetch('/api/hybrid', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: videoUrl, type: hybridType })
            });

            if (!response.ok) throw new Error('Failed');

            const blob = await response.blob();
            setCurrentHybridBlob(blob);
            setStatus({ message: '[OK] Ready!', type: 'success' });
        } catch (e) {
            setStatus({ message: 'Error: ' + e.message, type: 'error' });
        }
    };

    const downloadHybrid = () => {
        if (!currentHybridBlob) return;
        const link = document.createElement('a');
        link.href = URL.createObjectURL(currentHybridBlob);
        link.download = 'hybrid.pdf';
        link.click();
    };

    return (
        <div className="hybrid-section">
            <h2>🎯 Bonus: Hybrid (Transcript + Summary)</h2>

            <div className="options">
                <div className="option-group">
                    <label>Summary Type:</label>
                    <div className="option-buttons">
                        {['concise', 'normal', 'detailed'].map(type => (
                            <button
                                key={type}
                                className={`option-btn ${hybridType === type ? 'active' : ''}`}
                                onClick={() => setHybridType(type)}
                            >
                                {type.charAt(0).toUpperCase() + type.slice(1)} {type === 'normal' && '⭐'}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="info-box">
                ✓ Single PDF with both<br />
                ✓ Perfect for archiving<br />
                ✓ Cost: $0.05-0.15
            </div>

            <div className="action-buttons">
                <button className="btn-action" onClick={generateHybrid}>Generate Hybrid PDF</button>
            </div>

            <StatusMessage status={status} />

            {currentHybridBlob && (
                <button className="btn-download" onClick={downloadHybrid}>
                    ↓ Download Hybrid
                </button>
            )}
        </div>
    );
};

export default HybridSection;
