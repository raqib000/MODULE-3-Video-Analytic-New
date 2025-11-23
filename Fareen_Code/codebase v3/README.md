# 🎯 DeepScreen - AI-Powered Candidate Video Analysis

A video analytics system for recruitment that uses **hybrid AI + algorithmic analysis** to evaluate job candidates based on their introductory videos.

---

## 🌟 Features

### Video Processing
- ✅ **Video Upload** - Direct file upload to Supabase Storage
- ✅ **Normalization** - Standardize to 30fps, H264/AAC
- ✅ **Audio Extraction** - Extract WAV audio for analysis
- ✅ **Background Processing** - Non-blocking async pipeline

### AI Analysis (Gemini)
- ✅ **Speech Transcription** - Accurate AI-powered transcription
- ✅ **Natural Language Processing** - Preserves filler words and speech patterns

### Algorithmic Metrics
- ✅ **Filler Word Counting** - Regex-based detection (um, uh, like, etc.)
- ✅ **Pause Detection** - Audio signal analysis for silence periods
- ✅ **Speaking Rate** - Words per minute calculation
- ✅ **Loudness Analysis** - EBU R128 integrated loudness (LUFS)
- ✅ **Automated Scoring** - Objective candidate scoring

---

## 🏗️ Architecture

### Hybrid Approach
```
┌─────────────────────────────────────────────────────────┐
│                    Video Upload                         │
│              (FastAPI + Supabase Storage)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Background Processing                       │
├─────────────────────────────────────────────────────────┤
│  1. Download video                                      │
│  2. Normalize (FFmpeg)                                  │
│  3. Extract audio (FFmpeg)                              │
│  4. 🤖 AI Transcription (Gemini)                        │
│  5. 📊 Algorithmic Analysis:                            │
│     • Duration (librosa)                                │
│     • Filler words (regex)                              │
│     • Pauses (librosa)                                  │
│     • Speaking rate (word count)                        │
│     • Loudness (FFmpeg ebur128)                         │
│  6. Calculate score                                     │
│  7. Save to database                                    │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Results Retrieval                          │
│         (REST API + Supabase Database)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg (in PATH)
- Supabase account
- Google Gemini API key

### Installation

1. **Clone/Download the codebase**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   
   Create/edit `.env` file:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Setup database**
   
   Run the SQL in Supabase dashboard:
   ```bash
   # Copy content from setup_complete.sql
   # Paste in: https://supabase.com/dashboard/project/_/sql
   ```

5. **Create storage bucket**
   ```bash
   python setup_storage.py
   ```

6. **Verify setup**
   ```bash
   python verify_setup.py
   ```

### Running

**Start the server:**
```bash
uvicorn main:app --reload
```

**Test the system:**
```bash
python test_api.py
```

---

## 📡 API Endpoints

### 1. Health Check
```http
GET /
```

**Response:**
```json
{
  "message": "DeepScreen API is running"
}
```

### 2. Upload Video
```http
POST /upload
Content-Type: multipart/form-data

candidate_id: <uuid>
file: <video_file>
```

**Response:**
```json
{
  "message": "Upload successful, processing started",
  "video_id": "uuid",
  "storage_path": "candidate_id/filename.mp4"
}
```

### 3. Get Analysis
```http
GET /candidates/{candidate_id}/analysis
```

**Response (Processing):**
```json
{
  "status": "processing",
  "message": "Video is still being processed"
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "data": {
    "id": "uuid",
    "video_id": "uuid",
    "transcript": "Full transcript text...",
    "speaking_rate": 145.5,
    "pause_count": 3,
    "filler_count": 8,
    "loudness_db": -23.2,
    "score": 81,
    "created_at": "2025-11-22T14:30:00Z"
  }
}
```

---

## 📊 Metrics Explained

### Speaking Rate (WPM)
- **100-130**: Slow, deliberate
- **130-160**: Normal conversational
- **160-180**: Fast but clear
- **>180**: Very fast (may seem nervous)

### Loudness (LUFS)
- **-20 to -25**: Good recording level
- **-25 to -30**: Acceptable
- **-30 to -35**: Quiet
- **< -35**: Very quiet (poor setup)

### Pauses (count)
- **0-2**: Fluent speaker
- **3-5**: Normal pauses
- **6-10**: Frequent pauses
- **>10**: Excessive pauses

### Filler Words (count)
- **0-2**: Excellent
- **3-5**: Good
- **6-10**: Moderate
- **>10**: Excessive

### Score (0-100)
```
Base: 100
- Filler words × 2
- Pauses × 1
= Final score
```

---

## 🗄️ Database Schema

### Tables

**candidates**
- `id` (UUID)
- `name` (text)
- `email` (text)
- `created_at` (timestamp)

**videos**
- `id` (UUID)
- `candidate_id` (UUID → candidates)
- `storage_path` (text)
- `status` (text: processing/completed/failed)
- `created_at` (timestamp)

**analysis_results**
- `id` (UUID)
- `video_id` (UUID → videos)
- `transcript` (text)
- `speaking_rate` (float)
- `pause_count` (integer)
- `filler_count` (integer)
- `loudness_db` (float)
- `score` (float)
- `created_at` (timestamp)

---

## 🔧 Customization

### Adjust Pause Sensitivity
**File:** `main.py` (line ~92)
```python
pause_count = processor.detect_pauses(
    str(audio_path), 
    silence_threshold_db=-40,  # -30 to -50
    min_pause_duration=2.0     # 1.0 to 3.0 seconds
)
```

### Add Custom Filler Words
**File:** `processor.py` (line ~138)
```python
filler_words = [
    'um', 'uh', 'like',
    # Add your custom words here
]
```

### Modify Scoring
**File:** `main.py` (line ~97)
```python
score = 100 - (filler_count * 2) - (pause_count * 1)
# Customize multipliers or add new factors
```

---

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[HYBRID_APPROACH.md](HYBRID_APPROACH.md)** - Detailed technical documentation
- **[CHANGES.md](CHANGES.md)** - Implementation change log

---

## 🧪 Testing

### Manual Test
```bash
# 1. Start server
uvicorn main:app --reload

# 2. In another terminal, run test
python test_api.py
```

### Expected Output
```
Creating test candidate...
Candidate ID: abc-123-def
Uploading video...
Upload response: {'message': 'Upload successful, processing started', ...}
Polling for analysis...
Attempt 1: processing - Video is still being processed
Attempt 2: processing - Video is still being processed
Attempt 3: completed - 
✅ Analysis complete!
{
  'transcript': '...',
  'speaking_rate': 145.5,
  'pause_count': 3,
  'filler_count': 8,
  'loudness_db': -23.2,
  'score': 81
}
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Supabase** - Database + Storage
- **Google Gemini** - AI transcription

### Processing
- **FFmpeg** - Video/audio processing
- **Librosa** - Audio signal analysis
- **Python regex** - Text pattern matching

### Dependencies
```
fastapi
uvicorn
python-multipart
supabase
google-generativeai
ffmpeg-python
python-dotenv
librosa
soundfile
```

---

## ⚠️ Troubleshooting

### FFmpeg not found
```bash
# Windows: Download from ffmpeg.org
# Mac: brew install ffmpeg
# Linux: apt-get install ffmpeg
```

### Librosa installation issues
```bash
pip install librosa soundfile --upgrade
```

### Gemini API errors
- Check API key in `.env`
- Verify quota at https://aistudio.google.com/app/apikey
- Test: `python check_gemini_key.py`

### Supabase connection fails
- Verify URL and key in `.env`
- Check tables exist (run `setup_complete.sql`)
- Test: `python verify_setup.py`

---

## 🎯 Use Cases

- **Recruitment Screening** - Pre-screen candidates before interviews
- **Communication Assessment** - Evaluate presentation skills
- **Training Feedback** - Provide objective metrics for improvement
- **Interview Practice** - Help candidates prepare with metrics
- **Talent Analytics** - Aggregate data across candidates

---

## 🔮 Future Enhancements

- [ ] Video playback endpoint
- [ ] HR dashboard frontend
- [ ] Batch processing
- [ ] Webhook notifications
- [ ] Advanced scoring algorithms
- [ ] Sentiment analysis
- [ ] Pitch/tone analysis
- [ ] Facial expression analysis
- [ ] Multi-language support

---

## 📄 License

This project is for educational/commercial use.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Enhanced scoring algorithms
- Additional metrics (sentiment, confidence, etc.)
- Frontend dashboard
- Unit tests
- Performance optimizations

---

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review console output
3. Verify setup with `verify_setup.py`
4. Check `.env` configuration

---

## ✨ Key Advantages

### Transparency
- Know exactly how metrics are calculated
- Can explain to candidates
- No black box AI

### Cost Efficiency
- 50-66% reduction in API costs
- Only transcription uses Gemini
- Metrics calculated locally

### Accuracy
- Reproducible results
- Validated algorithms
- Industry-standard measurements

### Flexibility
- Customizable thresholds
- Adjustable scoring
- Easy to extend

---

**Built with ❤️ for better recruitment**

**Version:** 2.0 (Hybrid Approach)  
**Last Updated:** 2025-11-22
