import ffmpeg
import os

def normalize_video(input_path: str, output_path: str):
    """
    Normalizes video to a standard format (e.g., mp4, 30fps).
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vcodec='libx264', acodec='aac', r=30)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf8')}")
        return False

def extract_audio(video_path: str, audio_path: str):
    """
    Extracts audio from video for transcription.
    """
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf8')}")
        return False

def analyze_loudness(audio_path: str):
    """
    Analyzes integrated loudness using FFmpeg ebur128 filter.
    Returns loudness in LUFS (dB).
    """
    try:
        out, err = (
            ffmpeg
            .input(audio_path)
            .filter('ebur128', peak='none')
            .output('null', f='null')
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Decode stderr to string
        stderr_text = err.decode('utf8')
        
        # Parse for "I:" value (Integrated Loudness)
        # Example line: "    I:         -23.5 LUFS"
        import re
        match = re.search(r'I:\s+([-\d.]+)\s+LUFS', stderr_text)
        
        if match:
            loudness = float(match.group(1))
            print(f"Integrated loudness: {loudness} LUFS")
            return loudness
        else:
            print("Could not find integrated loudness in FFmpeg output")
            return -20.0  # Fallback
            
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf8')}")
        return None

def get_audio_duration(audio_path: str) -> float:
    """
    Get audio duration in seconds using librosa.
    """
    try:
        import librosa
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        print(f"Audio duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0.0

def detect_pauses(audio_path: str, silence_threshold_db: float = -40, 
                  min_pause_duration: float = 2.0) -> int:
    """
    Detect pauses using audio signal analysis.
    
    Args:
        audio_path: Path to audio file
        silence_threshold_db: dB level below which is considered silence
        min_pause_duration: Minimum duration (seconds) to count as pause
    
    Returns:
        Number of pauses detected
    """
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Convert to dB
        db = librosa.amplitude_to_db(np.abs(y), ref=np.max(y))
        
        # Find silent frames
        silent_frames = db < silence_threshold_db
        
        # Group consecutive silent frames
        pause_count = 0
        current_pause_length = 0
        frame_duration = 1.0 / sr
        
        for is_silent in silent_frames:
            if is_silent:
                current_pause_length += frame_duration
            else:
                if current_pause_length >= min_pause_duration:
                    pause_count += 1
                current_pause_length = 0
        
        # Check if there's a pause at the end
        if current_pause_length >= min_pause_duration:
            pause_count += 1
        
        print(f"Detected {pause_count} pauses (>{min_pause_duration}s)")
        return pause_count
        
    except Exception as e:
        print(f"Error detecting pauses: {e}")
        return 0

def count_filler_words(transcript: str) -> int:
    """
    Count filler words from transcript text.
    
    Args:
        transcript: Full text transcript
    
    Returns:
        Number of filler words detected
    """
    import re
    
    # Common filler words and phrases
    filler_words = [
        'um', 'uh', 'uhm', 'umm',
        'like', 'you know', 'i mean',
        'sort of', 'kind of',
        'actually', 'basically',
        'literally', 'seriously',
        'right', 'okay', 'so',
        'well', 'yeah', 'ah', 'er'
    ]
    
    transcript_lower = transcript.lower()
    count = 0
    
    for filler in filler_words:
        # Use word boundaries to avoid false matches
        pattern = r'\b' + re.escape(filler) + r'\b'
        matches = re.findall(pattern, transcript_lower)
        count += len(matches)
    
    print(f"Detected {count} filler words")
    return count

def calculate_speaking_rate(transcript: str, audio_duration: float) -> float:
    """
    Calculate speaking rate in words per minute.
    
    Args:
        transcript: Full text transcript
        audio_duration: Duration in seconds
    
    Returns:
        Speaking rate in words per minute
    """
    # Count words (simple split)
    word_count = len(transcript.split())
    
    # Convert to words per minute
    duration_minutes = audio_duration / 60.0
    
    if duration_minutes > 0:
        wpm = word_count / duration_minutes
        print(f"Speaking rate: {wpm:.2f} WPM ({word_count} words in {duration_minutes:.2f} minutes)")
        return round(wpm, 2)
    
    return 0.0
