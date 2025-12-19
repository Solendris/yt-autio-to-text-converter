import os
import requests
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
from app.utils.logger import logger

# Constants
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts')

# Using Lato for reliable Polish support
REGULAR_FONT_NAME = 'Lato-Regular'
REGULAR_FONT_PATH = os.path.join(FONT_DIR, 'Lato-Regular.ttf')
REGULAR_URLS = [
    'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf',
    'https://cdnjs.cloudflare.com/ajax/libs/lato-font/3.0.0/fonts/lato-normal/lato-normal.ttf'
]

BOLD_FONT_NAME = 'Lato-Bold'
BOLD_FONT_PATH = os.path.join(FONT_DIR, 'Lato-Bold.ttf')
BOLD_URLS = [
    'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf',
    'https://cdnjs.cloudflare.com/ajax/libs/lato-font/3.0.0/fonts/lato-bold/lato-bold.ttf'
]

def download_font(urls, path):
    """Download font from a list of mirrors."""
    if os.path.exists(path):
        return True

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    for url in urls:
        logger.info(f"Attempting download from {url}...")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Font downloaded successfully to {path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {e}")
            continue
    
    logger.error(f"All download attempts failed for {path}")
    return False

def ensure_fonts_exist():
    """Ensure font files exist."""
    download_font(REGULAR_URLS, REGULAR_FONT_PATH)
    download_font(BOLD_URLS, BOLD_FONT_PATH)

def register_fonts():
    """Register the TrueType fonts."""
    try:
        registered = False
        if os.path.exists(REGULAR_FONT_PATH):
            pdfmetrics.registerFont(TTFont(REGULAR_FONT_NAME, REGULAR_FONT_PATH))
            registered = True
            
        if os.path.exists(BOLD_FONT_PATH):
            pdfmetrics.registerFont(TTFont(BOLD_FONT_NAME, BOLD_FONT_PATH))
            
        if registered:
            try:
                pdfmetrics.registerFontFamily(
                    REGULAR_FONT_NAME,
                    normal=REGULAR_FONT_NAME,
                    bold=BOLD_FONT_NAME if os.path.exists(BOLD_FONT_PATH) else REGULAR_FONT_NAME,
                    italic=REGULAR_FONT_NAME,
                    boldItalic=BOLD_FONT_NAME if os.path.exists(BOLD_FONT_PATH) else REGULAR_FONT_NAME
                )
            except:
                pass
            
            logger.info(f"Registered fonts: {REGULAR_FONT_NAME}")
            return True
        else:
            logger.warning("Font files not found, using default fonts.")
            return False
    except Exception as e:
        logger.error(f"Error registering font: {e}")
        return False

# Initialize fonts on module load
ensure_fonts_exist()
FONTS_REGISTERED = register_fonts()
MAIN_FONT = REGULAR_FONT_NAME if FONTS_REGISTERED else 'Helvetica'
BOLD_FONT = BOLD_FONT_NAME if (FONTS_REGISTERED and os.path.exists(BOLD_FONT_PATH)) else 'Helvetica-Bold'

def parse_markdown(text):
    """Convert Markdown text to ReportLab XML/HTML format."""
    if not text:
        return ""

    # 1. Escape XML characters (except those we are about to add)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    # 2. Handle Bold (**text** or __text__)
    # Note: ReportLab uses <b> tag
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)

    # 3. Handle Italics (*text* or _text_)
    # Note: ReportLab uses <i> tag
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    # 4. Handle Headers (# Header) - make them bold and maybe bigger? 
    # For now just bold, as we are creating Flowables usually
    text = re.sub(r'^#+\s*(.*?)$', r'<b>\1</b><br/>', text, flags=re.MULTILINE)

    return text

def create_pdf_summary(title, summary, video_url, transcript_source, summary_type):
    """Create PDF summary with Polish character support and Markdown parsing."""
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
    
    title_safe = parse_markdown(title)
    
    story.append(Paragraph("YouTube Video Summary", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {now}", subtitle_style))
    story.append(Paragraph(f"<b>Transcript source:</b> {transcript_source.upper()}", subtitle_style))
    story.append(Paragraph(f"<b>Summary type:</b> {summary_type.upper()}", subtitle_style))
    story.append(Paragraph(f"<b>Video URL:</b> {parse_markdown(video_url)}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(f"<b>{title_safe}</b>", styles['Heading2']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Summary:</b>", styles['Heading3']))
    story.append(Spacer(1, 0.1*inch))
    
    # Process summary lines for lists vs paragraphs
    summary_lines = summary.split('\n')
    for line in summary_lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect list items
        if line.startswith('- ') or line.startswith('* '):
            # Remove the identifier and leading space
            content = line[2:]
            parsed_content = parse_markdown(content)
            # Use a bullet point char that works with DejaVuSans or ReportLab's bullet mechanism
            story.append(Paragraph(f"• {parsed_content}", body_style))
        else:
            parsed_content = parse_markdown(line)
            story.append(Paragraph(parsed_content, body_style))
            
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
    
    title_safe = parse_markdown(title)
    
    story.append(Paragraph("YouTube Video Summary & Transcript", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {now}", subtitle_style))
    story.append(Paragraph(f"<b>Transcript:</b> {transcript_source.upper()} | <b>Summary type:</b> {summary_type.upper()}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>SUMMARY</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    # Parse summary
    summary_lines = summary.split('\n')
    for line in summary_lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('- ') or line.startswith('* '):
            content = line[2:]
            parsed_content = parse_markdown(content)
            story.append(Paragraph(f"• {parsed_content}", body_style))
        else:
            parsed_content = parse_markdown(line)
            story.append(Paragraph(parsed_content, body_style))
    
    story.append(PageBreak())
    
    story.append(Paragraph("<b>FULL TRANSCRIPT</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    # Transcript is usually just text, but we can do basic parsing if needed. 
    # Usually huge block of text, better minimal parsing.
    transcript_safe = parse_markdown(transcript).replace('\n', '<br/>')
    story.append(Paragraph(transcript_safe, body_style))
    
    doc.build(story)
    logger.info("[OK] Hybrid PDF created")
    buffer.seek(0)
    return buffer
