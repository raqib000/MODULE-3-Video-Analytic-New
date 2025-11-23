import os
from dotenv import load_dotenv
from supabase import create_client, Client
import subprocess

load_dotenv()

def check_ffmpeg():
    print("Checking FFmpeg...")
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ FFmpeg is installed and available.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg is NOT found in PATH. Please install FFmpeg.")
        return False

def check_supabase():
    print("\nChecking Supabase Connection...")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env file.")
        return False

    try:
        supabase: Client = create_client(url, key)
        # Try a simple query (even if table doesn't exist, it checks auth)
        # We'll just check if the client initializes without error for now, 
        # or try to list tables if possible (but that requires specific permissions).
        # A simple way is to try to select from a non-existent table and see if we get a connection error vs a 404/400.
        # Or better, just check if we can access the auth endpoint.
        
        # Let's try to get the user session (should be null but no error)
        auth = supabase.auth.get_session()
        print("✅ Supabase client initialized successfully.")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

def check_gemini():
    print("\nChecking Gemini API Key...")
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("❌ Missing GEMINI_API_KEY in .env file.")
        return False
    print("✅ GEMINI_API_KEY is present.")
    return True

if __name__ == "__main__":
    print("--- System Verification ---")
    ffmpeg_ok = check_ffmpeg()
    supabase_ok = check_supabase()
    gemini_ok = check_gemini()

    if ffmpeg_ok and supabase_ok and gemini_ok:
        print("\n✅ All systems go! Ready to proceed.")
    else:
        print("\n⚠️ Some checks failed. Please fix them before proceeding.")
