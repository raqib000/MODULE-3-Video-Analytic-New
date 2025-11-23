import google.generativeai as genai
import os
import time

def configure_genai():
    # Manually read API key from .env to ensure it's loaded correctly
    api_key = None
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]
                    break
    except Exception as e:
        print(f"Warning: Could not read .env file: {e}")
    
    if api_key:
        genai.configure(api_key=api_key)
        print(f"Gemini configured with key: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("Warning: GEMINI_API_KEY not set.")

def transcribe_audio(audio_path: str):
    """
    Uploads audio to Gemini and requests transcription only.
    Metrics will be calculated algorithmically for transparency.
    """
    print(f"Uploading audio to Gemini: {audio_path}")
    
    # 1. Upload the file to Gemini
    audio_file = genai.upload_file(path=audio_path)
    print(f"Uploaded file: {audio_file.name}")
    
    # 2. Wait for processing (usually fast for audio)
    while audio_file.state.name == "PROCESSING":
        print("Waiting for Gemini processing...")
        time.sleep(1)
        audio_file = genai.get_file(audio_file.name)
        
    if audio_file.state.name == "FAILED":
        raise Exception("Gemini file processing failed")

    # 3. Generate Content - Request only transcription
    print("Generating transcription...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """
    Please transcribe this audio exactly as spoken.
    Provide only the transcript text, nothing else.
    Include all words, filler words (um, uh, like, etc.), and natural speech patterns.
    """
    
    response = model.generate_content([prompt, audio_file])
    
    # 4. Return transcript text
    transcript = response.text.strip()
    print(f"Transcription complete: {len(transcript)} characters")
    
    return transcript
