$temp_dir = "C:\Users\fnath\.gemini\tmp\9d3defdc3964952d7f72c35e957f868a3bf83277b2510c3543eed6f57eb1c78c"
$uvicorn_log_out = Join-Path $temp_dir "uvicorn_out.log"
$uvicorn_log_err = Join-Path $temp_dir "uvicorn_err.log"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > $uvicorn_log_out 2> $uvicorn_log_err