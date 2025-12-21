def parse_transcript_file(content):
    """
    Extracts the core transcript from a file, 
    removing any headers or footers marked with '==='.
    """
    lines = content.split('\n')
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
    return transcript if transcript else content.strip()
