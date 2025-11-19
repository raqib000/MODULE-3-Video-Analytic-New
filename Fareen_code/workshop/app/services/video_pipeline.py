# app/services/video_pipeline.py
import uuid
import os
from datetime import datetime
from sqlalchemy.orm import Session
import google.generativeai as genai
import ffmpeg
from pydub import AudioSegment

from ..models import (
    CandidateVideo,
    CandidateVideoTranscript,
    CandidateVideoAnalytics,
    ProcessingJob,
)

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)


def _normalize_video_and_extract_audio(video_url: str, video_id: uuid.UUID) -> tuple[str, str, str, str, float]:
    """
    Normalizes video, generates thumbnail, creates HLS stream, extracts audio,
    and returns paths to normalized video, thumbnail, HLS playlist, extracted audio,
    and video duration.
    """
    media_dir = "media"
    hls_dir = os.path.join(media_dir, "hls")
    os.makedirs(media_dir, exist_ok=True)
    os.makedirs(hls_dir, exist_ok=True)

    normalized_video_path = os.path.join(media_dir, f"{video_id}_normalized.mp4")
    thumbnail_path = os.path.join(media_dir, f"{video_id}_thumbnail.jpg")
    hls_playlist_path = os.path.join(hls_dir, f"{video_id}.m3u8")
    audio_path = os.path.join(media_dir, f"{video_id}_audio.flac")

    # Get video duration using ffprobe
    try:
        probe = ffmpeg.probe(video_url)
        duration_seconds = float(probe["streams"][0]["duration"])
    except Exception as e:
        print(f"Error probing video duration: {e}")
        duration_seconds = 0.0

    # Normalize video (to MP4, 720p, 24fps)
    ffmpeg.input(video_url).output(
        normalized_video_path,
        vf="scale='min(1280,iw)':min'(720,ih)',fps=24",
        preset="slow",
        crf=23,
        video_bitrate="2M",
        audio_bitrate="128k",
        vcodec="libx64",
        acodec="aac",
        loglevel="quiet"
    ).run(overwrite_output=True)

    # Generate thumbnail (from middle of the video)
    (
        ffmpeg.input(normalized_video_path)
        .filter("thumbnail")
        .output(thumbnail_path, vframes=1, loglevel="quiet")
        .run(overwrite_output=True)
    )

    # Create HLS stream
    (
        ffmpeg.input(normalized_video_path)
        .output(
            hls_playlist_path,
            format="hls",
            hls_time=10,
            hls_playlist_type="vod",
            hls_segment_filename=os.path.join(hls_dir, f"{video_id}_%03d.ts"),
            loglevel="quiet"
        )
        .run(overwrite_output=True)
    )

    # Extract audio (to FLAC for quality)
    ffmpeg.input(normalized_video_path).output(
        audio_path,
        acodec="flac",
        ar=44100,  # Audio sample rate
        loglevel="quiet"
    ).run(overwrite_output=True)

    return (
        normalized_video_path,
        thumbnail_path,
        hls_playlist_path,
        audio_path,
        duration_seconds,
    )


def _create_job(db: Session, video_id: uuid.UUID, stage: str, status: str, message: str = None):
    job = ProcessingJob(
        video_id=video_id,
        stage=stage,
        status=status,
        message=message,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _calculate_video_analytics(
    transcript_text: str, audio_file_path: str, duration_seconds: float
) -> dict:
    """
    Calculates various video analytics including WPM, filler words, and loudness.
    """
    words = transcript_text.split()
    words_count = len(words)
    duration_minutes = duration_seconds / 60.0 if duration_seconds else 1.0
    words_per_minute = words_count / duration_minutes

    # Filler words (example list, can be expanded)
    filler_words_list = ["um", "uh", "like", "you know", "so", "basically"]
    filler_words_count = sum(
        1 for word in words if word.lower() in filler_words_list
    )
    filler_words_per_minute = filler_words_count / duration_minutes

    # Audio loudness analysis using pydub
    avg_loudness_db = None
    peak_loudness_db = None
    try:
        audio = AudioSegment.from_file(audio_file_path)
        avg_loudness_db = audio.dBFS
        peak_loudness_db = audio.max_dBFS
    except Exception as e:
        print(f"Error calculating loudness: {e}")

    # Placeholder for other metrics due to lack of word-level timestamps
    total_speaking_time_s = duration_seconds  # Cannot accurately determine without word timestamps
    speech_ratio = 1.0  # Cannot accurately determine without word timestamps
    avg_pause_seconds = 0.0  # Cannot accurately determine without word timestamps
    max_pause_seconds = 0.0  # Cannot accurately determine without word timestamps
    volume_variation_score = 0.0 # Cannot accurately determine without word timestamps

    overall_score_0_100 = 70.0 + (words_per_minute / 150) * 10 - (filler_words_count / 10) * 5
    overall_score_0_100 = max(0, min(100, overall_score_0_100)) # Clamp between 0 and 100


    return {
        "words_count": words_count,
        "words_per_minute": words_per_minute,
        "filler_words_count": filler_words_count,
        "filler_words_per_minute": filler_words_per_minute,
        "avg_pause_seconds": avg_pause_seconds,
        "max_pause_seconds": max_pause_seconds,
        "total_speaking_time_s": total_speaking_time_s,
        "speech_ratio": speech_ratio,
        "avg_loudness_db": avg_loudness_db,
        "peak_loudness_db": peak_loudness_db,
        "volume_variation_score": volume_variation_score,
        "tech_issue_flag": False,
        "reupload_recommended": False,
        "comments": "Metrics are estimated. Word-level timestamps from STT are needed for more accurate analytics.",
        "overall_score_0_100": overall_score_0_100,
    }


def run_gemini_stt(audio_file_path: str) -> str:
    """
    Transcribes the given audio file using the Gemini API.
    """
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    audio_file = genai.upload_file(path=audio_file_path)
    try:
        response = model.generate_content(
            ["Please transcribe this audio.", audio_file],
            request_options={"timeout": 600} # 10 minutes
        )
        # Check if the response contains text and handle cases where it might be empty
        if hasattr(response, 'text') and response.text:
            return response.text
        else:
            # Handle cases where transcription might be empty or problematic
            print(f"Warning: Gemini STT returned no text for {audio_file_path}")
            return ""
    except Exception as e:
        print(f"Error during Gemini STT for {audio_file_path}: {e}")
        raise RuntimeError(f"Gemini STT failed: {e}")


def run_full_pipeline(video_id: uuid.UUID, db_session_factory):
    """
    Orchestrates:
    1. Normalize + thumbnail + HLS
    2. STT (Gemini)
    3. Analytics (WPM, pauses, fillers, loudness)
    """

    db: Session = db_session_factory()
    try:
        video = db.query(CandidateVideo).filter(CandidateVideo.id == video_id).first()
        if not video:
            return

        # 1. Normalize & HLS and Extract Audio
        _create_job(db, video_id, "normalize_and_extract_audio", "running")
        try:
            (
                normalized_video_path,
                thumbnail_path,
                hls_playlist_path,
                audio_path_for_stt,
                duration_seconds,
            ) = _normalize_video_and_extract_audio(video.original_url, video.id)

            video.normalized_url = normalized_video_path
            video.thumbnail_url = thumbnail_path
            video.hls_playlist_url = hls_playlist_path
            video.duration_seconds = duration_seconds
            video.upload_status = "hls_ready"
            db.commit()
            _create_job(db, video_id, "normalize_and_extract_audio", "success")
        except Exception as e:
            _create_job(db, video_id, "normalize_and_extract_audio", "failed", message=str(e))
            raise e

        # 2. STT (Gemini)
        _create_job(db, video_id, "stt", "running")
        try:
            transcript_text = run_gemini_stt(audio_path_for_stt)
            
            # Gemini API for STT does not provide word-level timestamps yet
            words_json = [] 
            segments_json = [] 
            
            tv = CandidateVideoTranscript(
                video_id=video_id,
                full_text=transcript_text,
                words_json=words_json,
                segments_json=segments_json,
                language="en",  # Language detection could be added
                stt_model="gemini-2.5-flash",
                avg_confidence=None,  # Confidence score is not available in the same way
            )
            db.add(tv)
            video.upload_status = "stt_done"
            db.commit()
            _create_job(db, video_id, "stt", "success")
        except Exception as stt_error:
            _create_job(db, video_id, "stt", "failed", message=str(stt_error))
            raise stt_error


        # 3. Analytics
        _create_job(db, video_id, "analytics", "running")
        try:
            analytics_data = _calculate_video_analytics(
                transcript_text, audio_path_for_stt, duration_seconds
            )
            analytics = CandidateVideoAnalytics(
                video_id=video_id,
                words_count=analytics_data["words_count"],
                words_per_minute=analytics_data["words_per_minute"],
                filler_words_count=analytics_data["filler_words_count"],
                filler_words_per_minute=analytics_data["filler_words_per_minute"],
                avg_pause_seconds=analytics_data["avg_pause_seconds"],
                max_pause_seconds=analytics_data["max_pause_seconds"],
                total_speaking_time_s=analytics_data["total_speaking_time_s"],
                speech_ratio=analytics_data["speech_ratio"],
                avg_loudness_db=analytics_data["avg_loudness_db"],
                peak_loudness_db=analytics_data["peak_loudness_db"],
                volume_variation_score=analytics_data["volume_variation_score"],
                tech_issue_flag=analytics_data["tech_issue_flag"],
                reupload_recommended=analytics_data["reupload_recommended"],
                comments=analytics_data["comments"],
                overall_score_0_100=analytics_data["overall_score_0_100"],
            )
            db.add(analytics)
            video.upload_status = "analyzed"
            db.commit()
            _create_job(db, video_id, "analytics", "success")
        except Exception as e:
            _create_job(db, video_id, "analytics", "failed", message=str(e))
            raise e

    except Exception as e:
        # Mark failure
        job = _create_job(db, video_id, "pipeline", "failed", message=str(e))
        video = db.query(CandidateVideo).filter(CandidateVideo.id == video_id).first()
        if video:
            video.upload_status = "error"
            video.error_message = str(e)
            db.commit()
    finally:
        db.close()
