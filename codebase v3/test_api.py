import requests
import os
import time
import subprocess
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Config
API_URL = "http://127.0.0.1:8000"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def create_dummy_video():
    print("Creating dummy video...")
    # Create a 1-second black video with silent audio
    # Requires ffmpeg to be in PATH
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x480:d=1", 
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
        "-c:v", "libx264", "-t", "1", "dummy.mp4"
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "dummy.mp4"

def test_flow():
    print(f"Connecting to Supabase: {SUPABASE_URL}")
    # 1. Setup Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 2. Create Candidate
    print("Creating test candidate...")
    # Email must be unique usually, so let's make it random
    import random
    email = f"test_{random.randint(1000, 9999)}@example.com"
    candidate_data = {"name": "Test User", "email": email}
    res = supabase.table("candidates").insert(candidate_data).execute()
    candidate_id = res.data[0]['id']
    print(f"Candidate ID: {candidate_id}")
    
    # 3. Create Video
    video_path = create_dummy_video()
    
    # 4. Upload Video
    print("Uploading video...")
    with open(video_path, "rb") as f:
        files = {"file": ("dummy.mp4", f, "video/mp4")}
        data = {"candidate_id": candidate_id}
        try:
            response = requests.post(f"{API_URL}/upload", files=files, data=data)
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to API. Is the server running?")
            return

    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return
        
    print(f"Upload response: {response.json()}")
    
    # 5. Poll for Analysis
    print("Polling for analysis...")
    for i in range(30):
        response = requests.get(f"{API_URL}/candidates/{candidate_id}/analysis")
        data = response.json()
        print(f"Attempt {i+1}: {data.get('status')} - {data.get('message', '')}")
        
        if data.get('status') == 'completed':
            print("\n✅ Analysis complete!")
            print(data.get('data'))
            break
        elif data.get('status') == 'failed':
            print("\n❌ Analysis failed!")
            break
            
        time.sleep(2)
    else:
        print("\n❌ Timed out waiting for analysis.")

if __name__ == "__main__":
    test_flow()
