import os
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
from app.utils.logger import logger

# Constants
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts')
FONT_NAME = 'Roboto-Regular'
FONT_PATH = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
FONT_URL = 'https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf'

def ensure_font_exists():
    """Ensure the font file exists, download if not."""
    if not os.path.exists(FONT_DIR):
        os.makedirs(FONT_DIR)
    
    if not os.path.exists(FONT_PATH):
        logger.info(f"Downloading font from {FONT_URL}...")
        try:
            response = requests.get(FONT_URL, timeout=30)
            response.raise_for_status()
            with open(FONT_PATH, 'wb') as f:
                f.write(response.content)
            logger.info("Font downloaded successfully.")
        except Exception as e:
            logger.error(f"Failed to download font: {e}")
            # Fallback to standard if download fails (though encoding might still break)

def register_fonts():
    """Register the TrueType font."""
    try:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
            logger.info(f"Registered font: {FONT_NAME}")
            return True
        else:
            logger.warning("Font file not found, using default fonts (Polish chars might fail).")
            return False
    except Exception as e:
        logger.error(f"Error registering font: {e}")
        return False

# Initialize fonts on module load
ensure_font_exists()
FONTS_REGISTERED = register_fonts()
MAIN_FONT = FONT_NAME if FONTS_REGISTERED else 'Helvetica'
BOLD_FONT = FONT_NAME if FONTS_REGISTERED else 'Helvetica-Bold' # Ideally should download Bold variant too, but Regular works for now or let's just use Regular for all if specific bold not present to avoid error

def clean_text(text):
    """Clean text simply, ReportLab with TTF handles unicode."""
    if not text:
        return ""
    # ReportLab Paragraph accepts HTML-like tags (<b>, <i>). 
    # If the text comes from an external source and contains special chars, 
    # usually we just need to replace newlines with <br/> for HTML flow
    # or keep it as is if we want it flowing.
    # However, we must escape XML characters like < > & if they are NOT intended as markup.
    # But since we insert <br/> later, let's just replace newlines.
    
    # Minimal escape for XML validity in Paragraph
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def create_pdf_summary(title, summary, video_url, transcript_source, summary_type):
    """Create PDF summary with Polish character support."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Update styles to use our font
    styles['Normal'].fontName = MAIN_FONT
    styles['Heading1'].fontName = MAIN_FONT
    styles['Heading2'].fontName = MAIN_FONT
    styles['Heading3'].fontName = MAIN_FONT
    styles['BodyText'].fontName = MAIN_FONT
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1F2937',
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=MAIN_FONT
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#6B7280',
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=MAIN_FONT
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=14,
        fontName=MAIN_FONT
    )
    
    story = []
    
    # We don't need the elaborate encode_text_for_pdf anymore, but we should escape special XML chars
    title_safe = clean_text(title)
    
    story.append(Paragraph("YouTube Video Summary", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {now}", subtitle_style))
    story.append(Paragraph(f"<b>Transcript source:</b> {transcript_source.upper()}", subtitle_style))
    story.append(Paragraph(f"<b>Summary type:</b> {summary_type.upper()}", subtitle_style))
    story.append(Paragraph(f"<b>Video URL:</b> {clean_text(video_url)}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(f"<b>{title_safe}</b>", styles['Heading2']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Summary:</b>", styles['Heading3']))
    story.append(Spacer(1, 0.1*inch))
    
    # Handle newlines for paragraph flow
    summary_safe = clean_text(summary).replace('\n', '<br/>')
    story.append(Paragraph(summary_safe, body_style))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<font size=8 color=#9CA3AF>Generated by YouTube Summarizer v4.0 | Powered by Perplexity AI & Whisper</font>",
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, fontName=MAIN_FONT)
    ))
    
    doc.build(story)
    logger.info("[OK] Summary PDF created")
    buffer.seek(0)
    return buffer

def create_transcript_file(transcript, source):
    """Create text file (UTF-8)"""
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
    """Create Hybrid PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
     # Update styles
    styles['Normal'].fontName = MAIN_FONT
    styles['Heading1'].fontName = MAIN_FONT
    styles['Heading2'].fontName = MAIN_FONT
    styles['BodyText'].fontName = MAIN_FONT

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor='#1F2937',
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName=MAIN_FONT
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#6B7280',
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName=MAIN_FONT
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=9,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=12,
        fontName=MAIN_FONT
    )
    
    story = []
    
    title_safe = clean_text(title)
    
    story.append(Paragraph("YouTube Video Summary & Transcript", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {now}", subtitle_style))
    story.append(Paragraph(f"<b>Transcript:</b> {transcript_source.upper()} | <b>Summary type:</b> {summary_type.upper()}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>SUMMARY</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    summary_safe = clean_text(summary).replace('\n', '<br/>')
    story.append(Paragraph(summary_safe, body_style))
    
    story.append(PageBreak())
    
    story.append(Paragraph("<b>FULL TRANSCRIPT</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    transcript_safe = clean_text(transcript).replace('\n', '<br/>')
    story.append(Paragraph(transcript_safe, body_style))
    
    doc.build(story)
    logger.info("[OK] Hybrid PDF created")
    buffer.seek(0)
    return buffer
