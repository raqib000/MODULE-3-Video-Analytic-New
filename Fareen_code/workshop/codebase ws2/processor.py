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
        # Parse stderr for loudness (simplified parsing)
        # In a real implementation, we'd parse the JSON output or specific log lines.
        # For now, returning a dummy value or implementing basic parsing logic would be needed.
        return -20.0 # Placeholder
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf8')}")
        return None
