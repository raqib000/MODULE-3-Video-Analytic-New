# 🔄 Hybrid Analysis Approach

## Overview

The codebase now uses a **hybrid approach** for video analysis:
- **AI (Gemini)**: Handles transcription only
- **Algorithms**: Calculate all metrics (filler words, pauses, speaking rate, loudness)

This provides the best of both worlds: accurate AI transcription with transparent, reproducible metrics.

---

## 📊 What Changed

### Before (AI-Only)
```
Gemini API
├── Transcription ✓
├── Filler word counting ✗ (black box)
├── Pause detection ✗ (black box)
└── Speaking rate ✗ (black box)
```

### After (Hybrid)
```
Gemini API
└── Transcription ✓ (AI is best at this)

Python Algorithms
├── Filler word counting ✓ (regex on transcript)
├── Pause detection ✓ (audio signal analysis)
├── Speaking rate ✓ (word count / duration)
└── Loudness ✓ (FFmpeg ebur128)
```

---

## 🔧 Implementation Details

### 1. **Transcription** (`ai_service.py`)
- **Method**: `transcribe_audio(audio_path)`
- **Technology**: Google Gemini 2.5 Flash
- **Output**: Plain text transcript
- **Why AI**: Speech recognition is complex; Gemini excels at this

### 2. **Filler Word Counting** (`processor.py`)
- **Method**: `count_filler_words(transcript)`
- **Technology**: Regex pattern matching
- **Filler words detected**:
  - Basic: um, uh, uhm, umm
  - Common: like, you know, i mean
  - Qualifiers: sort of, kind of
  - Intensifiers: actually, basically, literally, seriously
  - Discourse markers: right, okay, so, well, yeah, ah, er
- **Why algorithmic**: Transparent, reproducible, auditable

### 3. **Pause Detection** (`processor.py`)
- **Method**: `detect_pauses(audio_path)`
- **Technology**: Librosa audio analysis
- **Parameters**:
  - `silence_threshold_db`: -40 dB (configurable)
  - `min_pause_duration`: 2.0 seconds (configurable)
- **Process**:
  1. Load audio at 16kHz
  2. Convert amplitude to dB
  3. Identify frames below threshold
  4. Count consecutive silent periods > 2 seconds
- **Why algorithmic**: Precise, consistent, explainable

### 4. **Speaking Rate** (`processor.py`)
- **Method**: `calculate_speaking_rate(transcript, duration)`
- **Technology**: Simple word counting
- **Formula**: `(word_count / duration_minutes) = WPM`
- **Why algorithmic**: Simple, accurate, standard metric

### 5. **Loudness** (`processor.py`)
- **Method**: `analyze_loudness(audio_path)`
- **Technology**: FFmpeg ebur128 filter
- **Output**: Integrated Loudness in LUFS
- **Process**:
  1. Run FFmpeg with ebur128 filter
  2. Parse stderr output
  3. Extract "I:" value (Integrated Loudness)
- **Why algorithmic**: Industry standard (EBU R128)

---

## 📦 New Dependencies

Added to `requirements.txt`:
```
librosa      # Audio analysis for pause detection
soundfile    # Audio I/O support for librosa
```

### Installation
```bash
pip install -r requirements.txt
```

---

## 🎯 Benefits of Hybrid Approach

### ✅ Transparency
- You know exactly how each metric is calculated
- Can explain to candidates how they're scored
- No "black box" AI decisions

### ✅ Reproducibility
- Same input = same output (deterministic)
- Can write unit tests
- Easy to debug

### ✅ Cost Efficiency
- Reduced Gemini API usage (transcription only, not analysis)
- No repeated API calls for metrics recalculation

### ✅ Auditability
- Can validate metrics manually
- Can adjust thresholds (e.g., pause duration)
- Can add/remove filler words from list

### ✅ Performance
- Algorithmic calculations are fast
- No network latency for metrics
- Can run offline after transcription

### ✅ Flexibility
- Easy to customize filler word list
- Adjustable pause detection sensitivity
- Can add new metrics without API changes

---

## 🧪 Testing

### Run the test script:
```bash
python test_api.py
```

### Expected output:
```
Creating test candidate...
Candidate ID: <uuid>
Uploading video...
Upload response: {'message': 'Upload successful, processing started', ...}
Polling for analysis...

Background processing will show:
- Downloading video...
- Normalizing video...
- Extracting audio...
- Running AI transcription...
- Calculating metrics algorithmically...
  - Audio duration: X.XX seconds
  - Detected X filler words
  - Detected X pauses (>2.0s)
  - Speaking rate: XXX.XX WPM
  - Integrated loudness: -XX.X LUFS
- Saving results...
```

---

## 🎛️ Customization

### Adjust Pause Detection Sensitivity

In `main.py`, modify the `detect_pauses()` call:

```python
# More sensitive (detect shorter pauses)
pause_count = processor.detect_pauses(str(audio_path), 
                                      silence_threshold_db=-35,  # Less strict
                                      min_pause_duration=1.5)    # Shorter

# Less sensitive (only long pauses)
pause_count = processor.detect_pauses(str(audio_path), 
                                      silence_threshold_db=-45,  # More strict
                                      min_pause_duration=3.0)    # Longer
```

### Customize Filler Words List

In `processor.py`, edit the `filler_words` list in `count_filler_words()`:

```python
filler_words = [
    'um', 'uh',  # Keep basics
    # Add industry-specific jargon to penalize
    'synergy', 'leverage', 'circle back',
    # Add language-specific fillers
    'euh', 'alors',  # French
]
```

### Adjust Scoring Algorithm

In `main.py`, modify the scoring logic:

```python
# Current: Simple deduction
score = 100 - (filler_count * 2) - (pause_count * 1)

# Enhanced: Factor in loudness and speaking rate
score = 100
score -= filler_count * 2
score -= pause_count * 1

# Penalize too quiet (< -35 LUFS)
if loudness_db < -35:
    score -= 10

# Penalize too fast (> 180 WPM) or too slow (< 100 WPM)
if speaking_rate > 180 or speaking_rate < 100:
    score -= 5

score = max(0, min(100, score))
```

---

## 📊 Typical Metric Ranges

### Speaking Rate
- **100-130 WPM**: Slow, deliberate (good for clarity)
- **130-160 WPM**: Normal conversational pace
- **160-180 WPM**: Fast but understandable
- **>180 WPM**: Very fast (may seem nervous)

### Loudness (LUFS)
- **-20 to -25**: Good recording level
- **-25 to -30**: Acceptable, slightly quiet
- **-30 to -35**: Quiet (distant mic or soft speaker)
- **< -35**: Very quiet (poor audio setup)
- **> -15**: Too loud (may have clipping)

### Pauses (per minute)
- **0-2**: Fluent speaker
- **3-5**: Normal conversational pauses
- **6-10**: Frequent pauses (thinking or nervous)
- **>10**: Excessive pauses (unprepared or struggling)

### Filler Words (per minute)
- **0-2**: Excellent (very polished)
- **3-5**: Good (natural speech)
- **6-10**: Moderate (noticeable but acceptable)
- **>10**: Excessive (needs improvement)

---

## 🔮 Future Enhancements

Potential algorithmic additions:

1. **Pitch Analysis**: Detect monotone vs. dynamic speech
2. **Energy/Enthusiasm**: Measure vocal energy over time
3. **Articulation**: Detect mumbling or unclear speech
4. **Confidence Markers**: Detect hedging language ("maybe", "I think")
5. **Sentiment Analysis**: Positive vs. negative language
6. **Eye Contact** (if video analysis added): Face detection and gaze tracking
7. **Gesture Analysis**: Hand movement and body language

---

## 📝 Summary

The hybrid approach gives you:
- ✅ **Accurate transcription** from state-of-the-art AI
- ✅ **Transparent metrics** from proven algorithms
- ✅ **Full control** over scoring logic
- ✅ **Lower costs** (less API usage)
- ✅ **Better debugging** (can validate each step)
- ✅ **Easy customization** (adjust thresholds, add metrics)

This is the best architecture for a production recruitment system! 🎯
