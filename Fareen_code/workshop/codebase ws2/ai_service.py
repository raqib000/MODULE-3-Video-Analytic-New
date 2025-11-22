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

def transcribe_and_analyze(audio_path: str):
    """
    Uploads audio to Gemini and requests transcription + metrics.
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

    # 3. Generate Content
    print("Generating analysis...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """
    Analyze this audio for a job interview context.
    Provide the output in strict JSON format with the following keys:
    - "transcript": The full text transcript of the speech.
    - "filler_count": The integer count of filler words (um, uh, like, you know).
    - "pause_count": The integer count of significant pauses (silence > 2 seconds).
    - "speaking_rate": The estimated speaking rate in words per minute (float).
    
    Do not include markdown formatting like ```json. Just the raw JSON string.
    """
    
    response = model.generate_content([prompt, audio_file])
    
    # 4. Parse Response
    import json
    import re
    
    text = response.text
    # Clean up markdown code blocks if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    
    try:
        data = json.loads(text)
        return data
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from Gemini: {text}")
        # Fallback
        return {
            "transcript": text, # Return raw text if JSON fails
            "filler_count": 0,
            "pause_count": 0,
            "speaking_rate": 0.0
        }
