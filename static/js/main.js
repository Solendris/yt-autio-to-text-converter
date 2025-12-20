const API_BASE = '/api';

let currentTranscript = null;
let currentTranscriptFilename = 'transcript.txt';
let currentSummary = null;
let currentHybrid = null;
let selectedSummaryType = 'normal';
let selectedSummaryFormat = 'pdf';
let selectedHybridType = 'normal';
let summarySource = 'video';

function showStatus(elementId, message, type) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.className = `status ${type}`;
}

function setSummarySource(btn, source) {
    Array.from(btn.parentElement.children).forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    summarySource = source;

    const fileGroup = document.getElementById('fileUploadGroup');

    if (source === 'video') {
        fileGroup.style.display = 'none';
    } else {
        fileGroup.style.display = 'block';
    }
}

function setSummaryType(btn, type) {
    document.querySelectorAll('.option-btn').forEach(b => {
        if (b.parentElement.parentElement.querySelector('label')?.textContent.includes('Summary Type')) {
            b.classList.remove('active');
        }
    });
    btn.classList.add('active');
    selectedSummaryType = type;
}

function setSummaryFormat(btn, format) {
    document.querySelectorAll('.option-btn').forEach(b => {
        if (b.parentElement.parentElement.querySelector('label')?.textContent === 'Format:') {
            b.classList.remove('active');
        }
    });
    btn.classList.add('active');
    selectedSummaryFormat = format;
}

function setHybridType(btn, type) {
    Array.from(btn.parentElement.children).forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedHybridType = type;
}

// File input handling
document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('transcriptFile');
    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (!file) return;

            if (!file.name.endsWith('.txt')) {
                showStatus('summarizeStatus', 'Error: Only .txt files allowed', 'error');
                e.target.value = '';
                document.getElementById('fileInfo').innerHTML = '';
                return;
            }

            const fileSize = (file.size / 1024).toFixed(2);
            const reader = new FileReader();
            reader.onload = function (evt) {
                const wordCount = evt.target.result.split(/\s+/).filter(w => w.length > 0).length;
                document.getElementById('fileInfo').innerHTML =
                    `✓ ${file.name} | ${fileSize} KB | ${wordCount} words`;
            };
            reader.readAsText(file);
        });
    }
});

async function generateTranscript() {
    const url = document.getElementById('videoUrl').value.trim();
    if (!url) {
        showStatus('transcriptStatus', 'Enter URL', 'error');
        return;
    }

    showStatus('transcriptStatus', 'Processing...', 'loading');

    try {
        const response = await fetch(`${API_BASE}/transcript`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) throw new Error('Failed');

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // Store transcript for download
        const blob = new Blob([data.transcript], { type: 'text/plain' });
        currentTranscript = blob;
        currentTranscriptFilename = data.filename;

        // Display transcript
        const displayEl = document.getElementById('transcriptDisplay');
        if (displayEl) {
            // Convert plain text to HTML with clickable links
            displayEl.innerHTML = makeTimestampsClickable(data.transcript);
            displayEl.style.display = 'block';

            // Show hint
            const hintEl = document.getElementById('timestampHint');
            if (hintEl) hintEl.style.display = 'block';
        }

        showStatus('transcriptStatus', `[OK] Ready! Source: ${data.source}`, 'success');
        document.getElementById('transcriptDownloadBtn').style.display = 'block';
    } catch (e) {
        showStatus('transcriptStatus', 'Error: ' + e.message, 'error');
    }
}

async function generateSummary() {
    const fileInput = document.getElementById('transcriptFile');

    if (summarySource === 'video') {
        const url = document.getElementById('videoUrl').value.trim();
        if (!url) {
            showStatus('summarizeStatus', 'Enter YouTube URL above', 'error');
            return;
        }

        showStatus('summarizeStatus', 'Processing...', 'loading');

        try {
            const response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    type: selectedSummaryType,
                    format: selectedSummaryFormat
                })
            });

            if (!response.ok) throw new Error('Failed');

            currentSummary = await response.blob();
            showStatus('summarizeStatus', '[OK] Ready!', 'success');
            document.getElementById('summarizeDownloadBtn').style.display = 'block';
        } catch (e) {
            showStatus('summarizeStatus', 'Error: ' + e.message, 'error');
        }
    } else {
        // File upload mode
        if (!fileInput.files.length) {
            showStatus('summarizeStatus', 'Select a .txt file', 'error');
            return;
        }

        const file = fileInput.files[0];
        if (!file.name.endsWith('.txt')) {
            showStatus('summarizeStatus', 'Only .txt files allowed', 'error');
            return;
        }

        showStatus('summarizeStatus', 'Processing...', 'loading');

        try {
            const formData = new FormData();
            formData.append('transcript_file', file);
            formData.append('type', selectedSummaryType);
            formData.append('format', selectedSummaryFormat);

            const response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Failed');

            currentSummary = await response.blob();
            showStatus('summarizeStatus', '[OK] Ready!', 'success');
            document.getElementById('summarizeDownloadBtn').style.display = 'block';
        } catch (e) {
            showStatus('summarizeStatus', 'Error: ' + e.message, 'error');
        }
    }
}

async function generateHybrid() {
    const url = document.getElementById('videoUrl').value.trim();
    if (!url) {
        showStatus('hybridStatus', 'Enter URL', 'error');
        return;
    }

    showStatus('hybridStatus', 'Processing...', 'loading');

    try {
        const response = await fetch(`${API_BASE}/hybrid`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, type: selectedHybridType })
        });

        if (!response.ok) throw new Error('Failed');

        currentHybrid = await response.blob();
        showStatus('hybridStatus', '[OK] Ready!', 'success');
        document.getElementById('hybridDownloadBtn').style.display = 'block';
    } catch (e) {
        showStatus('hybridStatus', 'Error: ' + e.message, 'error');
    }
}

function downloadTranscript() {
    if (!currentTranscript) return;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(currentTranscript);
    link.download = currentTranscriptFilename || 'transcript.txt';
    link.click();
}

function downloadSummary() {
    if (!currentSummary) return;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(currentSummary);
    link.download = `summary.${selectedSummaryFormat}`;
    link.click();
}

function downloadHybrid() {
    if (!currentHybrid) return;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(currentHybrid);
    link.download = 'hybrid.pdf';
    link.click();
}

function extractVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

function updateVideoPreview() {
    const url = document.getElementById('videoUrl').value.trim();
    const container = document.getElementById('videoPreviewContainer');

    // Check if player is initialized
    if (!player || typeof player.loadVideoById !== 'function') return;

    const videoId = extractVideoId(url);

    if (videoId) {
        container.style.display = 'block';
        // Only update if it's a new video to avoid reloading
        // We can check current video data if available, or just load
        // Simply loading is fine, YT player handles buffering
        player.loadVideoById(videoId);
    } else {
        container.style.display = 'none';
        player.stopVideo();
    }
}

// YouTube Player API
let player;
function onYouTubeIframeAPIReady() {
    player = new YT.Player('videoPlayer', {
        height: '315',
        width: '100%',
        videoId: '',
        events: {
            'onReady': onPlayerReady
        }
    });
}

function onPlayerReady(event) {
    // Player ready
}

function seekToTimestamp(timeStr) {
    if (!player || typeof player.seekTo !== 'function') return;

    const parts = timeStr.split(':');
    let seconds = 0;
    if (parts.length === 2) {
        seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);
    } else if (parts.length === 3) {
        seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
    }

    player.seekTo(seconds, true);
    player.playVideo();
}

function makeTimestampsClickable(text) {
    // Regex for [MM:SS] or [HH:MM:SS]
    return text.replace(/\[(\d{1,2}:\d{2}(?::\d{2})?)\]/g, (match, time) => {
        return `<span class="timestamp-link" onclick="seekToTimestamp('${time}')">${match}</span>`;
    });
}
