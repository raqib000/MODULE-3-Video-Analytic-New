# 🚀 Quick Start Guide - Hybrid Approach

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**New dependencies added:**
- `librosa` - Audio signal processing
- `soundfile` - Audio file I/O

### 2. Verify Setup
```bash
python verify_setup.py
```

This checks:
- ✅ FFmpeg is installed
- ✅ Supabase connection works
- ✅ Gemini API key is valid

---

## Running the System

### Start the API Server
```bash
uvicorn main:app --reload
```

Server will start at: `http://127.0.0.1:8000`

### Test the Complete Flow
```bash
python test_api.py
```

---

## What Happens During Processing

### 1. **Upload Phase** (Immediate)
```
POST /upload
├── Upload video to Supabase Storage
├── Create video record (status: processing)
└── Return video_id immediately
```

### 2. **Background Processing** (Async)
```
Background Task
├── Download video from storage
├── Normalize video (FFmpeg: 30fps, h264/aac)
├── Extract audio (FFmpeg: WAV, 16kHz, mono)
├── 🤖 AI Transcription (Gemini)
│   └── Returns: Plain text transcript
├── 📊 Algorithmic Analysis
│   ├── Get audio duration (librosa)
│   ├── Count filler words (regex on transcript)
│   ├── Detect pauses (librosa signal analysis)
│   ├── Calculate speaking rate (words/duration)
│   └── Analyze loudness (FFmpeg ebur128)
├── Calculate score (based on metrics)
├── Save results to database
└── Update status to 'completed'
```

### 3. **Retrieve Results**
```
GET /candidates/{candidate_id}/analysis
└── Returns: transcript + all metrics + score
```

---

## Example Output

### API Response
```json
{
  "status": "completed",
  "data": {
    "id": "uuid",
    "video_id": "uuid",
    "transcript": "Hello, my name is John. Um, I'm applying for the software engineer position...",
    "speaking_rate": 145.5,
    "pause_count": 3,
    "filler_count": 8,
    "loudness_db": -23.2,
    "score": 81,
    "created_at": "2025-11-22T14:30:00Z"
  }
}
```

### Console Output (Background Task)
```
Starting processing for video abc123...
Downloading candidate_123/video.mp4...
Normalizing video...
Extracting audio...
Running AI transcription...
Uploading audio to Gemini: /tmp/xyz/audio.wav
Uploaded file: files/abc123
Generating transcription...
Transcription complete: 1247 characters

Calculating metrics algorithmically...
Audio duration: 62.45 seconds
Detected 8 filler words
Detected 3 pauses (>2.0s)
Speaking rate: 145.50 WPM (151 words in 1.04 minutes)
Integrated loudness: -23.2 LUFS

Saving results...
Processing complete for video abc123
```

---

## Key Differences from Before

### ❌ Old (AI-Only)
- Gemini analyzed everything
- No transparency in metrics
- Higher API costs
- Couldn't validate results

### ✅ New (Hybrid)
- Gemini only transcribes
- Metrics calculated algorithmically
- Lower API costs
- Full transparency and control

---

## Troubleshooting

### Issue: "librosa not found"
```bash
pip install librosa soundfile
```

### Issue: FFmpeg errors
- Ensure FFmpeg is in PATH
- Test: `ffmpeg -version`
- Windows: Download from ffmpeg.org
- Mac: `brew install ffmpeg`
- Linux: `apt-get install ffmpeg`

### Issue: Gemini API errors
- Check API key in `.env`
- Verify quota: https://aistudio.google.com/app/apikey
- Test: `python check_gemini_key.py`

### Issue: Supabase connection fails
- Check URL and key in `.env`
- Verify tables exist (run `setup_complete.sql`)
- Check storage bucket exists (run `setup_storage.py`)

---

## Customization Examples

### 1. Adjust Pause Sensitivity
**File**: `main.py` (line ~92)

```python
# Default: 2 seconds minimum
pause_count = processor.detect_pauses(str(audio_path))

# Detect shorter pauses (1.5 seconds)
pause_count = processor.detect_pauses(str(audio_path), 
                                      min_pause_duration=1.5)

# Only very long pauses (3 seconds)
pause_count = processor.detect_pauses(str(audio_path), 
                                      min_pause_duration=3.0)
```

### 2. Add Custom Filler Words
**File**: `processor.py` (line ~138)

```python
filler_words = [
    'um', 'uh', 'uhm', 'umm',
    'like', 'you know', 'i mean',
    # Add your custom words:
    'basically', 'literally',
    'synergy', 'leverage',  # Corporate jargon
]
```

### 3. Modify Scoring Algorithm
**File**: `main.py` (line ~97)

```python
# Current
score = 100 - (filler_count * 2) - (pause_count * 1)

# Enhanced
score = 100
score -= filler_count * 2
score -= pause_count * 1

# Penalize poor audio quality
if loudness_db < -35:
    score -= 10

# Penalize abnormal speaking rate
if speaking_rate < 100 or speaking_rate > 180:
    score -= 5

score = max(0, min(100, score))
```

---

## Performance Notes

### Processing Time (1-minute video)
- Download: ~2-5 seconds
- Normalize: ~3-5 seconds
- Extract audio: ~1-2 seconds
- AI transcription: ~5-10 seconds
- Algorithmic metrics: ~2-3 seconds
- **Total**: ~15-25 seconds

### API Costs (per video)
- **Before**: ~2-3 Gemini API calls (transcription + analysis)
- **After**: ~1 Gemini API call (transcription only)
- **Savings**: ~50-66% reduction in API costs

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Run `verify_setup.py`
3. ✅ Start server: `uvicorn main:app --reload`
4. ✅ Test: `python test_api.py`
5. ✅ Review `HYBRID_APPROACH.md` for details
6. 🎯 Customize metrics and scoring as needed
7. 🚀 Build frontend dashboard (optional)

---

## Support

For issues or questions:
1. Check `HYBRID_APPROACH.md` for detailed documentation
2. Review console output for error messages
3. Verify all dependencies are installed
4. Check `.env` file has correct credentials

Happy recruiting! 🎯
