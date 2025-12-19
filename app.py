# app.py v4.0 - 2 NIEZALEŻNE SEKCJE: Transkrypcja + Streszczanie
# Zastąp tym plikiem obecny app.py

import os
import re
import tempfile
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from faster_whisper import WhisperModel
import yt_dlp
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO
import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# ═══════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler = RotatingFileHandler(
    log_filename,
    maxBytes=5*1024*1024,
    backupCount=3
)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

logger.info("="*80)
logger.info("YouTube Summarizer v4.0 - 2 SECTIONS")
logger.info(f"Log file: {log_filename}")
logger.info("="*80)

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def encode_text_for_pdf(text):
    """Konwertuj polskie znaki na HTML entities dla reportlab"""
    if not text:
        return text
    
    replacements = {
        'ą': '&aacute;', 'ć': '&#263;', 'ę': '&eacute;', 'ł': '&#322;',
        'ń': '&#324;', 'ó': '&oacute;', 'ś': '&#347;', 'ź': '&#378;',
        'ż': '&#380;', 'Ą': '&#260;', 'Ć': '&#262;', 'Ę': '&#280;',
        'Ł': '&#321;', 'Ń': '&#323;', 'Ó': '&Oacute;', 'Ś': '&#346;',
        'Ź': '&#377;', 'Ż': '&#379;',
    }
    
    result = text
    for char, entity in replacements.items():
        result = result.replace(char, entity)
    
    return result

# ═══════════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app)

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '').strip()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '').strip()
USE_PERPLEXITY = PERPLEXITY_API_KEY != ''

logger.info(f"Perplexity configured: {USE_PERPLEXITY}")
logger.info(f"Gemini configured: {GOOGLE_API_KEY != ''}")

whisper_model = None

def init_whisper():
    global whisper_model
    if whisper_model is None:
        logger.info("Initializing Whisper model...")
        whisper_model = WhisperModel("base", device="cpu", compute_type="float32")
        logger.info("[OK] Whisper model loaded")
    return whisper_model

def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&?\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(video_id):
    try:
        logger.info(f"Attempting YouTube transcript API for: {video_id}")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            transcript = transcript_list.find_manually_created_transcript() or transcript_list.find_generated_transcript()
        
        transcript_data = transcript.fetch()
        full_text = ' '.join([item['text'] for item in transcript_data])
        logger.info(f"[OK] YouTube transcript fetched ({len(full_text)} characters)")
        return full_text, "youtube"
    
    except Exception as e:
        logger.warning(f"YouTube transcript not available: {str(e)}")
        return None, None

def download_audio_from_youtube(video_url):
    try:
        logger.info(f"Downloading audio: {video_url}")
        
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"yt_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m4a")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': audio_path.replace('.m4a', ''),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 60,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Audio download attempt {attempt}/{max_attempts}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                break
            except Exception as e:
                if attempt == max_attempts:
                    raise
                logger.warning(f"Attempt {attempt} failed, retrying...")
                import time
                time.sleep(5)
        
        mp3_path = audio_path.replace('.m4a', '.mp3')
        if os.path.exists(mp3_path):
            logger.info(f"[OK] Audio downloaded: {mp3_path}")
            return mp3_path
        
        logger.error("Downloaded audio file not found")
        return None
    
    except Exception as e:
        logger.error(f"Audio download error: {str(e)}")
        return None

def transcribe_with_whisper(audio_path):
    try:
        logger.info(f"Transcribing with Whisper...")
        
        model = init_whisper()
        segments, info = model.transcribe(audio_path, language="pl", beam_size=5)
        
        transcript = ' '.join([segment.text for segment in segments])
        
        logger.info(f"[OK] Transcription complete ({len(transcript)} characters)")
        
        try:
            os.remove(audio_path)
        except:
            pass
        
        return transcript
    
    except Exception as e:
        logger.error(f"Whisper error: {str(e)}")
        return None

def get_transcript(video_url):
    """SEKCJA 1: Pobierz transkrypt (YouTube API lub Whisper)"""
    video_id = extract_video_id(video_url)
    if not video_id:
        logger.error("Invalid YouTube URL")
        return None, "Invalid YouTube URL"
    
    logger.info(">>> SECTION 1: Getting transcript <<<")
    
    transcript, source = get_youtube_transcript(video_id)
    if transcript:
        logger.info(f"Using YouTube transcript source")
        return transcript, source
    
    logger.info("Falling back to Whisper...")
    audio_path = download_audio_from_youtube(video_url)
    if not audio_path:
        logger.error("Audio download failed")
        return None, "Failed to download audio"
    
    transcript = transcribe_with_whisper(audio_path)
    if transcript:
        logger.info(f"Using Whisper transcript source")
        return transcript, "whisper"
    
    logger.error("Both YouTube and Whisper failed")
    return None, "Failed to transcribe audio"

def summarize_with_perplexity(text, summary_type="normal"):
    """SEKCJA 2: Podsumuj transkrypt za pomocą Perplexity API"""
    try:
        logger.info(f"Perplexity API: summarizing ({summary_type} mode)...")
        
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        text_to_summarize = text[:20000] if len(text) > 20000 else text
        
        prompts = {
            "concise": "Podsumuj poniższy transkrypt w 3-5 zdaniach. Zachowaj GŁÓWNĄ MYŚL i kluczowe punkty. Bądź bardzo krótki i bezpośredni.",
            "normal": "Podsumuj poniższy transkrypt w ~300-500 słów. Zachowaj strukturę: Intro → Główne punkty → Wnioski. Używaj bullet points dla czytelności.",
            "detailed": "Podsumuj poniższy transkrypt w ~800-1000 słów. Zachowaj wszystkie ważne punkty, cytaty i przykłady. Strukturalizuj: Abstrakt → Sekcje → Analiza → Wnioski.",
        }
        
        prompt = prompts.get(summary_type, prompts["normal"])
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates high-quality summaries of video transcripts in Polish. Process the ENTIRE transcript provided and maintain important details."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nTRANSKRYPT:\n\n{text_to_summarize}"
                }
            ],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        summary = result['choices'][0]['message']['content']
        logger.info(f"[OK] Perplexity response ({len(summary)} characters)")
        return summary
    
    except Exception as e:
        logger.error(f"Perplexity API error: {str(e)}")
        return None

def summarize_with_gemini(text, summary_type="normal"):
    """Fallback: Gemini API"""
    try:
        logger.info(f"Gemini API: summarizing ({summary_type} mode)...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        text_to_summarize = text[:20000] if len(text) > 20000 else text
        
        prompts = {
            "concise": "Podsumuj w 3-5 zdaniach",
            "normal": "Podsumuj w ~300-500 słów z bullet points",
            "detailed": "Podsumuj w ~800-1000 słów ze wszystkimi szczegółami",
        }
        
        prompt = prompts.get(summary_type, prompts["normal"])
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt}\n\nTRANSKRYPT:\n\n{text_to_summarize}"
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 3000,
                "temperature": 0.7
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text']
        logger.info(f"[OK] Gemini response ({len(summary)} characters)")
        return summary
    
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return None

def create_pdf_summary(title, summary, video_url, transcript_source, summary_type):
    """Stwórz PDF ze streszczeniem"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1F2937',
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#6B7280',
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=12,
        fontName='Helvetica'
    )
    
    story = []
    
    title_encoded = encode_text_for_pdf(title)
    summary_encoded = encode_text_for_pdf(summary)
    
    story.append(Paragraph("YouTube Video Summary", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {now}", subtitle_style))
    story.append(Paragraph(f"<b>Transcript source:</b> {transcript_source.upper()}", subtitle_style))
    story.append(Paragraph(f"<b>Summary type:</b> {summary_type.upper()}", subtitle_style))
    story.append(Paragraph(f"<b>Video URL:</b> {video_url}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(f"<b>{title_encoded}</b>", styles['Heading2']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Summary:</b>", styles['Heading3']))
    story.append(Spacer(1, 0.1*inch))
    
    summary_html = summary_encoded.replace('\n', '<br/>')
    story.append(Paragraph(summary_html, body_style))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<font size=8 color=#9CA3AF>Generated by YouTube Summarizer v4.0 | Powered by Perplexity AI & Whisper</font>",
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)
    ))
    
    doc.build(story)
    logger.info("[OK] Summary PDF created")
    buffer.seek(0)
    return buffer

def create_transcript_file(transcript, source):
    """Stwórz plik tekstowy z transkryptem"""
    content = f"""YouTube Video Transcript
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Transcript Source: {source.upper()}

{"="*80}

{transcript}

{"="*80}

Generated by YouTube Summarizer v4.0
"""
    
    buffer = BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    logger.info("[OK] Transcript file created")
    return buffer

def create_hybrid_pdf(title, summary, transcript, video_url, transcript_source, summary_type):
    """Stwórz PDF z transkryptem + streszczeniem"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor='#1F2937',
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#6B7280',
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=9,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=11,
        fontName='Helvetica'
    )
    
    story = []
    
    title_encoded = encode_text_for_pdf(title)
    summary_encoded = encode_text_for_pdf(summary)
    transcript_encoded = encode_text_for_pdf(transcript)
    
    story.append(Paragraph("YouTube Video Summary & Transcript", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {now}", subtitle_style))
    story.append(Paragraph(f"<b>Transcript:</b> {transcript_source.upper()} | <b>Summary type:</b> {summary_type.upper()}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>SUMMARY</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    summary_html = summary_encoded.replace('\n', '<br/>')
    story.append(Paragraph(summary_html, body_style))
    
    story.append(PageBreak())
    
    story.append(Paragraph("<b>FULL TRANSCRIPT</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    transcript_html = transcript_encoded.replace('\n', '<br/>')
    story.append(Paragraph(transcript_html, body_style))
    
    doc.build(story)
    logger.info("[OK] Hybrid PDF created")
    buffer.seek(0)
    return buffer

# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    logger.debug("Health check")
    return jsonify({
        'status': 'ok',
        'version': '4.0',
        'sections': ['transcript', 'summarize'],
        'perplexity_configured': USE_PERPLEXITY,
        'gemini_configured': bool(GOOGLE_API_KEY),
        'ai_provider': 'perplexity' if USE_PERPLEXITY else 'gemini'
    })

@app.route('/api/transcript', methods=['POST'])
def get_transcript_only():
    """SEKCJA 1: ONLY Transkrypt (bez streszczenia)"""
    try:
        data = request.json
        video_url = data.get('url', '').strip()
        
        if not video_url:
            logger.warning("Transcript: No URL")
            return jsonify({'error': 'No video URL provided'}), 400
        
        logger.info(f">>> ENDPOINT: /api/transcript <<<")
        logger.info(f"Processing: {video_url}")
        
        transcript, source = get_transcript(video_url)
        
        if not transcript:
            logger.error(f"Transcript failed: {source}")
            return jsonify({'error': source}), 400
        
        logger.info(f"[OK] Transcript ready - source: {source}")
        
        transcript_buffer = create_transcript_file(transcript, source)
        
        return send_file(
            transcript_buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'transcript_{extract_video_id(video_url)}_{source}.txt'
        )
    
    except Exception as e:
        logger.error(f"Transcript endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize_transcript():
    """SEKCJA 2: Podsumuj transkrypt (z URL VIDEO lub z UPLOADED PLIKU)"""
    try:
        import time
        start_time = time.time()
        
        # Obsługuj zarówno JSON jak i multipart/form-data
        if request.is_json:
            data = request.json
            video_url = data.get('url', '').strip()
            summary_type = data.get('type', 'normal').lower()
            output_format = data.get('format', 'pdf').lower()
            transcript_file = None
            transcript = None
        else:
            # File upload via form
            video_url = request.form.get('url', '').strip()
            summary_type = request.form.get('type', 'normal').lower()
            output_format = request.form.get('format', 'pdf').lower()
            transcript_file = request.files.get('transcript_file')
            transcript = None
        
        if summary_type not in ['concise', 'normal', 'detailed']:
            summary_type = 'normal'
        
        # OPCJA 1: Transkrypt z pliku (jeśli wczytany)
        if transcript_file:
            logger.info(f">>> ENDPOINT: /api/summarize (FILE UPLOAD MODE) <<<")
            logger.info(f"File: {transcript_file.filename}")
            
            try:
                transcript_content = transcript_file.read().decode('utf-8')
                logger.info(f"[OK] Transcript file loaded ({len(transcript_content)} characters)")
                
                # Wyciągnij transkrypt z pliku (usuń header jeśli istnieje)
                lines = transcript_content.split('\n')
                transcript_start = 0
                for i, line in enumerate(lines):
                    if '=' * 20 in line:
                        transcript_start = i + 1
                        break
                
                transcript_end = len(lines)
                for i in range(len(lines) - 1, -1, -1):
                    if '=' * 20 in lines[i]:
                        transcript_end = i
                        break
                
                transcript = '\n'.join(lines[transcript_start:transcript_end]).strip()
                
                if not transcript:
                    transcript = transcript_content
                
                source = "file_upload"
                logger.info(f"[PROCESS] Extracted transcript: {len(transcript)} characters")
                
            except Exception as e:
                logger.error(f"[ERROR] Could not read transcript file: {str(e)}")
                return jsonify({'error': f'Could not read transcript file: {str(e)}'}), 400
        
        # OPCJA 2: Transkrypt z URL video (jeśli nie wczytano pliku)
        elif video_url:
            logger.info(f">>> ENDPOINT: /api/summarize (VIDEO URL MODE) <<<")
            logger.info(f"Video: {video_url} | Type: {summary_type} | Format: {output_format}")
            
            transcript, source = get_transcript(video_url)
            
            if not transcript:
                logger.error(f"Summarize: Transcript failed - {source}")
                return jsonify({'error': source}), 400
            
            logger.info(f"Transcript ready ({len(transcript)} chars)")
        
        # Brak transkryptu i URL
        else:
            logger.warning("Summarize: No URL or file provided")
            return jsonify({'error': 'Provide either video URL or transcript file'}), 400
        
        # ═══════════════════════════════════════════════════════════════════
        # GENERUJ STRESZCZENIE
        # ═══════════════════════════════════════════════════════════════════
        
        logger.info(f"[START] Summarization process ({summary_type} mode)")
        
        if USE_PERPLEXITY:
            logger.info("Using Perplexity API...")
            summary = summarize_with_perplexity(transcript, summary_type)
            if not summary:
                logger.warning("Perplexity failed, trying Gemini...")
                if GOOGLE_API_KEY:
                    summary = summarize_with_gemini(transcript, summary_type)
        else:
            logger.info("Using Gemini API...")
            summary = summarize_with_gemini(transcript, summary_type)
        
        if not summary:
            logger.error("All summarization APIs failed")
            return jsonify({'error': 'Failed to generate summary'}), 500
        
        logger.info(f"[OK] Summary generated ({len(summary)} characters)")
        
        # Wyciągnij video_id jeśli dostępny
        if video_url:
            video_id = extract_video_id(video_url)
            title = f'Video {video_id}'
        else:
            video_id = 'manual_upload'
            title = transcript_file.filename.replace('.txt', '') if transcript_file else 'Transcript Summary'
        
        # ═══════════════════════════════════════════════════════════════════
        # EKSPORTUJ WYNIK
        # ═══════════════════════════════════════════════════════════════════
        
        if output_format == 'pdf':
            logger.info(f"[EXPORT] Creating PDF...")
            pdf_buffer = create_pdf_summary(title, summary, video_url or 'Manual Upload', source, summary_type)
            
            elapsed_time = time.time() - start_time
            logger.info(f"[COMPLETE] Summary PDF ready for download ({elapsed_time:.1f}s total)")
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'summary_{video_id}_{summary_type}.pdf'
            )
        else:
            logger.info(f"[EXPORT] Creating TXT...")
            content = f"""SUMMARY - {summary_type.upper()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: {source.upper()}
{'Video: ' + video_url if video_url else 'File: ' + transcript_file.filename}

{"="*80}

{summary}

{"="*80}

Generated by YouTube Summarizer v4.0
"""
            buffer = BytesIO()
            buffer.write(content.encode('utf-8'))
            buffer.seek(0)
            
            elapsed_time = time.time() - start_time
            logger.info(f"[COMPLETE] Summary TXT ready for download ({elapsed_time:.1f}s total)")
            
            return send_file(
                buffer,
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'summary_{video_id}_{summary_type}.txt'
            )
    
    except Exception as e:
        logger.error(f"Summarize endpoint error: {str(e)}")
        import traceback
        logger.error(f"[TRACEBACK]\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hybrid', methods=['POST'])
def hybrid_output():
    """HYBRID: Transkrypt + Streszczenie w jednym PDF"""
    try:
        data = request.json
        video_url = data.get('url', '').strip()
        summary_type = data.get('type', 'normal').lower()
        
        if not video_url:
            logger.warning("Hybrid: No URL")
            return jsonify({'error': 'No video URL provided'}), 400
        
        logger.info(f">>> ENDPOINT: /api/hybrid <<<")
        logger.info(f"Video: {video_url} | Type: {summary_type}")
        
        transcript, source = get_transcript(video_url)
        
        if not transcript:
            logger.error(f"Hybrid: Transcript failed - {source}")
            return jsonify({'error': source}), 400
        
        logger.info(f"Transcript ready ({len(transcript)} chars)")
        
        if USE_PERPLEXITY:
            summary = summarize_with_perplexity(transcript, summary_type)
        else:
            summary = summarize_with_gemini(transcript, summary_type)
        
        if not summary:
            logger.error("Hybrid: Summarization failed")
            return jsonify({'error': 'Failed to generate summary'}), 500
        
        logger.info(f"[OK] Summary generated ({len(summary)} characters)")
        
        title = data.get('title', f'Video {extract_video_id(video_url)}')
        pdf_buffer = create_hybrid_pdf(title, summary, transcript, video_url, source, summary_type)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'hybrid_{extract_video_id(video_url)}.pdf'
        )
    
    except Exception as e:
        logger.error(f"Hybrid endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-transcript', methods=['POST'])
def validate_transcript():
    """Waliduj wczytany plik transkryptu"""
    try:
        logger.info(f">>> ENDPOINT: /api/upload-transcript <<<")
        
        if 'file' not in request.files:
            logger.warning("No file provided")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.warning("Empty filename")
            return jsonify({'error': 'Empty filename'}), 400
        
        if not file.filename.endswith('.txt'):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Only .txt files allowed'}), 400
        
        logger.info(f"[PROCESS] Validating file: {file.filename}")
        
        # Odczytaj plik
        content = file.read().decode('utf-8')
        file_size = len(content)
        word_count = len(content.split())
        
        logger.info(f"[OK] File validated")
        logger.info(f"[STATS] Size: {file_size} characters | Words: {word_count}")
        
        return jsonify({
            'filename': file.filename,
            'size': file_size,
            'words': word_count,
            'preview': content[:200] + '...' if len(content) > 200 else content
        })
    
    except Exception as e:
        logger.error(f"Upload validation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask server v4.0...")
    logger.info("Frontend: http://localhost:8000/index.html")
    logger.info("Endpoints:")
    logger.info("  - POST /api/transcript")
    logger.info("  - POST /api/summarize")
    logger.info("  - POST /api/hybrid")
    logger.info("Backend: http://localhost:5000")
    app.run(debug=True, port=5000)
