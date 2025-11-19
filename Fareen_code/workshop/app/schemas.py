# app/schemas.py
import uuid
from typing import Optional, List, Any
from pydantic import BaseModel, AnyHttpUrl


class CandidateVideoCreate(BaseModel):
    candidate_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None

    original_filename: str
    original_mime_type: str
    original_size_bytes: Optional[int] = None
    original_url: AnyHttpUrl


class CandidateVideoOut(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: Optional[uuid.UUID]

    original_filename: str
    original_mime_type: str
    original_size_bytes: Optional[int]
    original_url: str

    normalized_url: Optional[str]
    thumbnail_url: Optional[str]
    hls_playlist_url: Optional[str]

    duration_seconds: Optional[float]
    upload_status: str
    error_message: Optional[str]

    class Config:
        from_attributes = True


class TranscriptOut(BaseModel):
    full_text: str
    words_json: Optional[Any]
    segments_json: Optional[Any]
    language: Optional[str]
    stt_model: Optional[str]
    avg_confidence: Optional[float]

    class Config:
        from_attributes = True


class AnalyticsOut(BaseModel):
    words_count: Optional[int]
    words_per_minute: Optional[float]
    filler_words_count: Optional[int]
    filler_words_per_minute: Optional[float]
    avg_pause_seconds: Optional[float]
    max_pause_seconds: Optional[float]
    total_speaking_time_s: Optional[float]
    speech_ratio: Optional[float]

    avg_loudness_db: Optional[float]
    peak_loudness_db: Optional[float]
    volume_variation_score: Optional[float]

    tech_issue_flag: Optional[bool]
    reupload_recommended: Optional[bool]
    comments: Optional[str]
    overall_score_0_100: Optional[float]

    class Config:
        from_attributes = True


class CandidateVideoDetailOut(BaseModel):
    video: CandidateVideoOut
    transcript: Optional[TranscriptOut]
    analytics: Optional[AnalyticsOut]
