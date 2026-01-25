# YouTube Transcript Generator

A web app I built for automatically transcribing YouTube videos. Originally started as a simple script, but I expanded it to practice full-stack development and working with AI APIs.

[**Try it live here**](https://solendris.github.io/yt-autio-to-text-converter/)

## What it does

The app takes a YouTube URL and generates a text transcript. It's smarter than it sounds - it tries multiple approaches:

1. First checks if YouTube has captions available (fastest)
2. If not, downloads the audio and uses Whisper to transcribe
3. For speaker diarization (identifying who's talking), it uses Google's Gemini API

I also added a 90-minute limit because longer videos take forever to process.

## Why I built this

I wanted to learn:
- How to structure a proper REST API (not just throw everything in one file)
- Frontend-backend communication and state management
- Working with third-party APIs (YouTube, Google Gemini)
- Handling file uploads and audio processing
- Security basics (CORS, input validation, etc.)

The codebase evolved a lot - I refactored it several times as I learned better patterns. Initially had Perplexity integration for summarization, but I removed it to keep things focused.

## Tech stack

**Backend:**
- Flask for the API
- yt-dlp for downloading videos
- Faster-Whisper for local transcription
- Google Gemini API for speaker detection

**Frontend:**
- React (chose it because most jobs seem to want it)
- Vite (way faster than create-react-app)
- Context API for state (kept it simple, didn't need Redux)

## Project structure

I tried to keep things organized:

```
app/
├── routes.py           # API endpoints
├── config.py           # Environment variables and settings
├── controllers/        # Business logic (separate from routes)
├── services/           # External integrations (YouTube, Gemini, etc.)
├── utils/              # Helper functions
└── middleware/         # Error handling, CORS
```

Nothing crazy, just trying to follow separation of concerns. Controllers handle the business logic, services deal with external APIs, routes just route.

## API Endpoints

Pretty straightforward:

```
GET  /api/health              # Checks if everything's configured
POST /api/transcript          # Main endpoint - transcribes a video
POST /api/upload-transcript   # Validates uploaded .txt files
```

Example request:
```json
POST /api/transcript
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "diarization": true  // set to true if you want speaker labels
}
```

## Running it locally

**You'll need:**
- Python 3.8+ 
- Node.js (for the frontend)
- FFmpeg (Whisper needs it for audio)
- A Google API key ([get one here](https://makersuite.google.com/app/apikey))

**Setup:**

1. Clone the repo and install Python dependencies:
   ```bash
   cd local
   python -m venv venv
   venv\Scripts\activate  # on Windows
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API key:
   ```
   GOOGLE_API_KEY=your_actual_key_here
   API_KEY=any_string_for_basic_auth
   ```

3. Run the backend:
   ```bash
   python run.py
   ```

4. In another terminal, run the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Open `http://localhost:5173` and you should be good to go.

## Things I learned

**Architecture stuff:**
- How to properly structure a Flask app (not just one massive file)
- Dependency injection makes testing easier
- Config validation should happen at startup, not when things break

**Security:**
- CORS is annoying but important
- Never trust user input - validate everything
- Environment variables for secrets (learned this the hard way)

**Challenges:**
- Speaker diarization was harder than expected - Gemini's API has quirks
- Audio processing can eat up memory fast
- Error handling needs to be comprehensive or users get confused

## Known limitations

- Maximum 90 minutes per video (processing longer ones takes too long)
- Speaker diarization isn't perfect - works best with 2-4 clear speakers
- Only supports YouTube (could expand to other platforms later)

## What I'd improve

If I had more time:
- **Persistent transcripts with shareable links** - Generate a unique GUID for each transcript so you can bookmark/share it without re-processing the video every time. Would need a simple database (maybe SQLite) to store them.
- **Transcript viewer page** - A dedicated page where you can paste a GUID or upload a previously generated .txt file and view it with the same nice formatting (timestamps, speaker labels, etc.) without hitting the API again.
- Add proper testing (I have some basic tests but could use more)
- Better progress indicators (right now it just says "loading")
- Support for other video platforms
- Caching for frequently accessed videos
- More sophisticated error messages

## License

MIT License - feel free to use this however you want.

---

Built this to learn and practice. If you're looking at this for a job application, the code's on GitHub if you want to see how it's actually implemented.
