from io import BytesIO

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'  # success_response sets status to 'ok'

def test_generate_transcript_invalid_url(client):
    response = client.post('/api/transcript', json={
        'url': 'invalid_url'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_debug_info(client, mocker):
    # Mock subprocess.run for ffmpeg check
    mock_run = mocker.patch('app.routes.subprocess.run')
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "mocked output"

    response = client.get('/api/debug')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'yt_dlp_version' in data
    assert data['ffmpeg_installed'] is True

def test_generate_transcript_success(client, mock_youtube):
    # Setup mocks
    mock_youtube['extract_video_id'].return_value = "video123"
    mock_youtube['get_video_title'].return_value = "Test Video"
    
    # Return (transcript, source) tuple
    mock_youtube['get_transcript'].return_value = ("Line 1\nLine 2", "youtube")
    mock_youtube['get_diarized_transcript'].return_value = ("Speaker 1: Hello", "youtube")

    # Test
    response = client.post('/api/transcript', json={
        'url': 'https://www.youtube.com/watch?v=video123',
        'diarization': False
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'transcript' in data
    assert 'filename' in data
    assert 'video123' in data['filename']

def test_validate_transcript_upload(client):
    data = {
        'file': (BytesIO(b"Test transcript content"), 'test.txt')
    }
    response = client.post('/api/upload-transcript', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['filename'] == 'test.txt'
    assert data['words'] == 3

def test_summarize_missing_data(client):
    response = client.post('/api/summarize', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_summarize_success(client, mock_youtube, mock_summarizer):
    # Setup mocks for getting transcript
    mock_youtube['extract_video_id'].return_value = "video123"
    mock_youtube['get_video_title'].return_value = "Test Video"
    mock_youtube['get_transcript'].return_value = ("Transcript content", "youtube")
    
    # Setup mock for summary
    mock_summarizer['summarize_with_perplexity'].return_value = "This is a summary."
    
    response = client.post('/api/summarize', json={
        'transcript_source': 'video', 
        'url': 'https://www.youtube.com/watch?v=video123',
        'type': 'concise',
        'format': 'txt'
    })
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
    assert b"This is a summary." in response.data

def test_summarize_file_success(client, mock_summarizer):
    # Setup mock for summary
    mock_summarizer['summarize_with_perplexity'].return_value = "File summary content."
    
    data = {
        'transcript_file': (BytesIO(b"Uploaded transcript content"), 'upload.txt'),
        'type': 'normal',
        'format': 'txt'
    }
    response = client.post('/api/summarize', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    assert b"File summary content." in response.data
    assert b"Source: FILE_UPLOAD" in response.data

def test_summarize_pdf_success(client, mock_youtube, mock_summarizer, mock_pdf):
    # Setup mocks
    mock_youtube['extract_video_id'].return_value = "video123"
    mock_youtube['get_video_title'].return_value = "Test Video"
    mock_youtube['get_transcript'].return_value = ("Transcript content", "youtube")
    mock_summarizer['summarize_with_perplexity'].return_value = "Summary content."
    
    # Mock PDF buffer with real BytesIO
    mock_buffer = BytesIO(b"%PDF-1.4...")
    mock_pdf['create_pdf_summary'].return_value = mock_buffer

    response = client.post('/api/summarize', json={
        'transcript_source': 'video',
        'url': 'https://www.youtube.com/watch?v=video123',
        'type': 'concise',
        'format': 'pdf'
    })
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'

def test_hybrid_output_success(client, mock_youtube, mock_summarizer, mock_pdf):
    # Setup mocks
    mock_youtube['get_transcript'].return_value = ("Full transcript", "youtube")
    mock_youtube['extract_video_id'].return_value = "video123"
    mock_summarizer['summarize_with_perplexity'].return_value = "Summary text"
    
    mock_buffer = BytesIO(b"%PDF-hybrid")
    mock_pdf['create_hybrid_pdf'].return_value = mock_buffer

    response = client.post('/api/hybrid', json={
        'url': 'https://www.youtube.com/watch?v=video123',
        'type': 'normal'
    })
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
    assert response.headers['Content-Disposition'] == 'attachment; filename=hybrid_video123.pdf'

def test_summarize_api_error(client, mock_youtube, mock_summarizer):
    # Setup mocks
    mock_youtube['get_transcript'].return_value = ("Transcript content", "youtube")
    mock_youtube['extract_video_id'].return_value = "video123"
    mock_summarizer['summarize_with_perplexity'].return_value = None # Simulate failure
    mock_summarizer['summarize_with_gemini'].return_value = None # Both fail
    
    response = client.post('/api/summarize', json={
        'url': 'https://www.youtube.com/watch?v=video123',
        'type': 'normal',
        'format': 'txt'
    })
    
    assert response.status_code == 500
    assert 'error' in response.get_json()
