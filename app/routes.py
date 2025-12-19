import time
from flask import Blueprint, request, jsonify, send_file
from app.config import Config
from app.utils.logger import logger
from app.services.youtube_service import get_transcript, extract_video_id, get_video_title
from app.services.summarization_service import summarize_with_perplexity, summarize_with_gemini
from app.services.pdf_service import create_transcript_file, create_pdf_summary, create_hybrid_pdf
from io import BytesIO
from datetime import datetime

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/health', methods=['GET'])
def health():
    logger.debug("Health check")
    return jsonify({
        'status': 'ok',
        'version': '4.0',
        'sections': ['transcript', 'summarize'],
        'perplexity_configured': Config.USE_PERPLEXITY,
        'gemini_configured': bool(Config.GOOGLE_API_KEY),
        'ai_provider': 'perplexity' if Config.USE_PERPLEXITY else 'gemini'
    })

@bp.route('/transcript', methods=['POST'])
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

@bp.route('/summarize', methods=['POST'])
def summarize_transcript():
    """SEKCJA 2: Podsumuj transkrypt (z URL VIDEO lub z UPLOADED PLIKU)"""
    try:
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
        
        if Config.USE_PERPLEXITY:
            logger.info("Using Perplexity API...")
            summary = summarize_with_perplexity(transcript, summary_type)
            if not summary:
                logger.warning("Perplexity failed, trying Gemini...")
                if Config.GOOGLE_API_KEY:
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
            # Try to fetch real title
            real_title = get_video_title(video_url)
            title = real_title if real_title else f'Video {video_id}'
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

@bp.route('/hybrid', methods=['POST'])
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
        
        if Config.USE_PERPLEXITY:
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

@bp.route('/upload-transcript', methods=['POST'])
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
