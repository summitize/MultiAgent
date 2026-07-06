@echo off
REM Start the Consolidated Portal app from the correct directory
cd /d "c:\Users\Sumeet.Boob\OneDrive - Brillio\GitHubRepo\MultiAgent\Consolidated_Portal"
echo Starting FastAPI server on http://localhost:8080
echo Press Ctrl+C to stop
python -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
pause
