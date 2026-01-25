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

