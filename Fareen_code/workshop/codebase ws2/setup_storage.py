import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not set in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Creating 'videos' bucket...")
try:
    # Try to create the bucket
    res = supabase.storage.create_bucket("videos", options={"public": False})
    print(f"✅ Bucket 'videos' created: {res}")
except Exception as e:
    # If it fails, it might already exist or be a permission issue
    print(f"⚠️  Could not create bucket (it might already exist): {e}")

# List buckets to verify
print("\nListing buckets:")
try:
    buckets = supabase.storage.list_buckets()
    for b in buckets:
        print(f"- {b.name}")
except Exception as e:
    print(f"❌ Failed to list buckets: {e}")
