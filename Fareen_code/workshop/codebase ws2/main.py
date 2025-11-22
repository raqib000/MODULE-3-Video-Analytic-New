from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import processor
import ai_service

# Manually load .env to ensure variables are set correctly
def load_env_manually():
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")

load_env_manually()

app = FastAPI(title="DeepScreen Candidate Video API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase Setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = None

if url and key:
    supabase = create_client(url, key)
else:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not set.")

def process_video_pipeline(candidate_id: str, video_id: str, storage_path: str):
    """
    Background task to process the video:
    1. Download from Supabase Storage
    2. Normalize
    3. Extract Audio
    4. Analyze with AI
    5. Save results
    """
    print(f"Starting processing for video {video_id}...")
    
    temp_dir = tempfile.mkdtemp()
    temp_video_path = Path(temp_dir) / "input_video.mp4"
    normalized_path = Path(temp_dir) / "normalized.mp4"
    audio_path = Path(temp_dir) / "audio.wav"
    
    try:
        # 1. Download video
        print(f"Downloading {storage_path}...")
        file_bytes = supabase.storage.from_("videos").download(storage_path)
        with open(temp_video_path, "wb") as f:
            f.write(file_bytes)
            
        # 2. Normalize Video
        print("Normalizing video...")
        if not processor.normalize_video(str(temp_video_path), str(normalized_path)):
            raise Exception("Video normalization failed")
            
        # 3. Extract Audio
        print("Extracting audio...")
        if not processor.extract_audio(str(normalized_path), str(audio_path)):
            raise Exception("Audio extraction failed")
            
        # 4. AI Analysis
        print("Running AI analysis...")
        # Ensure AI service is configured
        ai_service.configure_genai()
        analysis = ai_service.transcribe_and_analyze(str(audio_path))
        
        # Calculate simple score (placeholder logic)
        # Score starts at 100, deduct for fillers and pauses
        score = 100 - (analysis.get("filler_count", 0) * 2) - (analysis.get("pause_count", 0) * 1)
        score = max(0, min(100, score))
        
        # 5. Save Results
        print("Saving results...")
        
        # Update video status
        supabase.table("videos").update({"status": "completed"}).eq("id", video_id).execute()
        
        # Insert analysis
        result_data = {
            "video_id": video_id,
            "transcript": analysis.get("transcript"),
            "speaking_rate": analysis.get("speaking_rate"),
            "pause_count": analysis.get("pause_count"),
            "filler_count": analysis.get("filler_count"),
            "loudness_db": -20.0, # TODO: Get real loudness from processor
            "score": score
        }
        supabase.table("analysis_results").insert(result_data).execute()
        
        print(f"Processing complete for video {video_id}")
        
    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        supabase.table("videos").update({"status": "failed"}).eq("id", video_id).execute()
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

@app.get("/")
def read_root():
    return {"message": "DeepScreen API is running"}

@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    candidate_id: str = Form(...),
    file: UploadFile = File(...)
):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")

    try:
        # 1. Upload to Supabase Storage
        file_content = await file.read()
        file_ext = Path(file.filename).suffix
        storage_path = f"{candidate_id}/{file.filename}"
        
        # Check if bucket exists, if not create it (optional, usually done manually)
        # For now assuming 'videos' bucket exists
        
        # Upload (upsert=True to overwrite if exists)
        supabase.storage.from_("videos").upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
        
        # 2. Create Video Record
        video_data = {
            "candidate_id": candidate_id,
            "storage_path": storage_path,
            "status": "processing"
        }
        response = supabase.table("videos").insert(video_data).execute()
        video_id = response.data[0]['id']
        
        # 3. Queue Background Processing
        background_tasks.add_task(process_video_pipeline, candidate_id, video_id, storage_path)
        
        return {
            "message": "Upload successful, processing started", 
            "video_id": video_id,
            "storage_path": storage_path
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/candidates/{candidate_id}/analysis")
def get_analysis(candidate_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
        
    # Get latest video for candidate
    videos = supabase.table("videos").select("id, status, created_at").eq("candidate_id", candidate_id).order("created_at", desc=True).limit(1).execute()
    
    if not videos.data:
        raise HTTPException(status_code=404, detail="No videos found for this candidate")
        
    video = videos.data[0]
    
    if video['status'] == 'processing':
        return {"status": "processing", "message": "Video is still being processed"}
    elif video['status'] == 'failed':
        return {"status": "failed", "message": "Video processing failed"}
        
    # Get analysis results
    results = supabase.table("analysis_results").select("*").eq("video_id", video['id']).execute()
    
    if not results.data:
        return {"status": "completed", "message": "Processing complete but no results found (unexpected)"}
        
    return {"status": "completed", "data": results.data[0]}
