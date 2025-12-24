"""
Transcript parsing utilities.
"""
from app.constants import SEPARATOR_PATTERN


def parse_transcript_file(content: str) -> str:
    """
    Extract core transcript from a file,
    removing any headers or footers marked with '==='.
    
    Args:
        content: Raw file content
        
    Returns:
        Parsed transcript content
    """
    lines = content.split('\n')
    transcript_start = 0
    
    for i, line in enumerate(lines):
        if SEPARATOR_PATTERN in line:
            transcript_start = i + 1
            break
    
    transcript_end = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if SEPARATOR_PATTERN in lines[i]:
            transcript_end = i
            break
    
    transcript = '\n'.join(lines[transcript_start:transcript_end]).strip()
    return transcript if transcript else content.strip()
