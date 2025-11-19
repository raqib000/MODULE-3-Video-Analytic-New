# app/models.py
import uuid
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    ForeignKey, DateTime, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .db import Base


class CandidateVideo(Base):
    __tablename__ = "candidate_video"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    candidate_id = Column(UUID(as_uuid=True), nullable=False)  # FK to candidate.id
    application_id = Column(UUID(as_uuid=True), nullable=True)  # FK to job_application.id

    original_filename = Column(Text, nullable=False)
    original_mime_type = Column(Text, nullable=False)
    original_size_bytes = Column(Integer)
    original_url = Column(Text, nullable=False)

    normalized_url = Column(Text)
    thumbnail_url = Column(Text)

    hls_playlist_url = Column(Text)
    hls_segment_prefix = Column(Text)

    duration_seconds = Column(Float)
    resolution_width = Column(Integer)
    resolution_height = Column(Integer)
    audio_sample_rate = Column(Integer)
    audio_channels = Column(Integer)

    upload_status = Column(
        String(32),
        nullable=False,
        default="uploaded"
        # expected: uploaded, normalized, hls_ready, stt_done, analyzed, error
    )
    error_message = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )


class CandidateVideoTranscript(Base):
    __tablename__ = "candidate_video_transcript"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate_video.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    full_text = Column(Text, nullable=False)
    words_json = Column(JSON)       # [{word,start,end,confidence}, ...]
    segments_json = Column(JSON)    # [{text,start,end}, ...]
    language = Column(String(16))
    stt_model = Column(Text)
    avg_confidence = Column(Float)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


class CandidateVideoAnalytics(Base):
    __tablename__ = "candidate_video_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate_video.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    words_count = Column(Integer)
    words_per_minute = Column(Float)
    filler_words_count = Column(Integer)
    filler_words_per_minute = Column(Float)
    avg_pause_seconds = Column(Float)
    max_pause_seconds = Column(Float)
    total_speaking_time_s = Column(Float)
    speech_ratio = Column(Float)

    avg_loudness_db = Column(Float)
    peak_loudness_db = Column(Float)
    volume_variation_score = Column(Float)

    tech_issue_flag = Column(Boolean, default=False)
    reupload_recommended = Column(Boolean, default=False)
    comments = Column(Text)
    overall_score_0_100 = Column(Float)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


class ProcessingJob(Base):
    __tablename__ = "processing_job"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate_video.id", ondelete="CASCADE"),
        nullable=True
    )
    stage = Column(String(32), nullable=False)   # upload, normalize, hls, stt, analytics
    status = Column(String(32), nullable=False)  # pending, running, success, failed
    message = Column(Text)

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    finished_at = Column(DateTime(timezone=True))
