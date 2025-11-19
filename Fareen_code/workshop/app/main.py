# app/main.py
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

load_dotenv()

from . import models, schemas
from .db import SessionLocal, engine, get_db
from .services import video_pipeline

# Create all tables in the database.
# In a real-world app, you'd use Alembic for migrations.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DeepScreen Candidate Video API",
    description="API for uploading and analyzing candidate video submissions.",
    version="1.0.0"
)


@app.post("/videos/", response_model=schemas.CandidateVideoOut, status_code=202)
def create_video_submission(
    video_in: schemas.CandidateVideoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Accepts a new video submission, saves its metadata to the database,
    and triggers the background processing pipeline.
    """
    db_video = models.CandidateVideo(**video_in.model_dump())
    db.add(db_video)
    db.commit()
    db.refresh(db_video)

    # Run the whole pipeline in the background
    background_tasks.add_task(
        video_pipeline.run_full_pipeline,
        video_id=db_video.id,
        db_session_factory=SessionLocal
    )

    return db_video


@app.get("/videos/{video_id}", response_model=schemas.CandidateVideoDetailOut)
def get_video_details(video_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves all available details for a specific video, including its
    transcript and analytics if they have been generated.
    """
    video = db.query(models.CandidateVideo).filter(models.CandidateVideo.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    transcript = db.query(models.CandidateVideoTranscript).filter(
        models.CandidateVideoTranscript.video_id == video_id
    ).first()

    analytics = db.query(models.CandidateVideoAnalytics).filter(
        models.CandidateVideoAnalytics.video_id == video_id
    ).first()

    return schemas.CandidateVideoDetailOut(
        video=video,
        transcript=transcript,
        analytics=analytics
    )


@app.get("/")
def read_root():
    return {"message": "Welcome to the DeepScreen API"}
