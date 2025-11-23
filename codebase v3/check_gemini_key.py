import google.generativeai as genai
import os
from dotenv import load_dotenv

# Manually read .env to ensure we get the latest content
api_key = None
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.strip().split("=", 1)[1]
                break
except Exception as e:
    print(f"❌ Error reading .env file: {e}")
    exit(1)

print(f"Checking API Key: {api_key[:5]}...{api_key[-5:] if api_key else ''}")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

try:
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            
    # Try a fallback model if flash fails
    model_name = 'gemini-pro'
    print(f"\nTesting with {model_name}...")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello")
    print(f"✅ Success! Gemini responded: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
