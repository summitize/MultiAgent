#!/usr/bin/env python3
"""
Log Monitoring Script
Monitor FastAPI and Ollama logs in real-time
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time

def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def monitor_logs():
    """Monitor application logs"""
    print_header("CONSOLIDATED AI PORTAL - LOG MONITORING")
    
    base_dir = Path(__file__).resolve().parent
    logs_dir = base_dir / "logs"
    
    # 1. Show log directory info
    print("1. LOG DIRECTORY INFORMATION")
    print(f"   Location: {logs_dir}")
    
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("app_*.log"), reverse=True)
        print(f"   Total log files: {len(log_files)}")
        if log_files:
            print(f"\n   Latest log files:")
            for log_file in log_files[:5]:
                file_size = log_file.stat().st_size
                size_kb = file_size / 1024
                print(f"     - {log_file.name} ({size_kb:.2f} KB)")
    else:
        print(f"   Status: Log directory not created yet (will be created on startup)")
    
    # 2. Show Ollama information
    print("\n\n2. OLLAMA BACKEND INFORMATION")
    print(f"   Expected location: http://localhost:11434")
    print(f"   Logs: Check Ollama's own logging (typically in %USERPROFILE%\\.ollama\\logs)")
    
    # 3. Show how to access logs via API
    print("\n\n3. ACCESS LOGS VIA API")
    print(f"   Endpoint: http://localhost:9999/api/logs")
    print(f"   Parameters:")
    print(f"     - lines: Number of recent log lines to retrieve (default: 50)")
    print(f"   Example: http://localhost:9999/api/logs?lines=100")
    
    # 4. Show real-time monitoring
    print("\n\n4. REAL-TIME LOG MONITORING")
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("app_*.log"), reverse=True)
        if log_files:
            latest_log = log_files[0]
            print(f"   Monitoring: {latest_log.name}")
            print(f"\n   Press Ctrl+C to stop monitoring\n")
            
            # Read initial position
            try:
                with open(latest_log, "r") as f:
                    # Get last 10 lines
                    lines = f.readlines()
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                    print("   Recent log entries:")
                    for line in recent_lines:
                        print(f"   {line.rstrip()}")
                
                # Monitor for new entries
                print(f"\n   Waiting for new log entries...")
                file_pos = latest_log.stat().st_size
                
                while True:
                    time.sleep(1)
                    current_size = latest_log.stat().st_size
                    
                    if current_size > file_pos:
                        with open(latest_log, "r") as f:
                            f.seek(file_pos)
                            new_entries = f.read()
                            if new_entries.strip():
                                print(f"\n   [NEW ENTRIES]")
                                for line in new_entries.split("\n"):
                                    if line.strip():
                                        print(f"   {line}")
                            file_pos = current_size
            
            except KeyboardInterrupt:
                print("\n\n   Monitoring stopped.")
        else:
            print("   No log files found. Start the application first.")
    else:
        print("   Log directory not yet created. Start the application to begin logging.")
    
    # 5. Show environment setup
    print("\n\n5. ENVIRONMENT SETUP FOR DEBUG LOGGING")
    print(f"   For Ollama debug logging:")
    print(f"   > $env:OLLAMA_DEBUG = \"1\"")
    print(f"   > ollama serve")
    
    print(f"\n   For FastAPI debug mode (modify startup):")
    print(f"   > python -m uvicorn app:app --host 127.0.0.1 --port 9999 --log-level debug")
    
    # 6. Show log locations summary
    print("\n\n6. LOG LOCATIONS SUMMARY")
    print(f"   FastAPI/Uvicorn Logs:")
    print(f"     → {logs_dir}/app_YYYYMMDD_HHMMSS.log")
    print(f"     → Also printed to console (INFO level and above)")
    
    print(f"\n   Ollama Logs:")
    print(f"     → Windows: %USERPROFILE%\\.ollama\\logs\\")
    print(f"     → Or check console output where Ollama is running")
    
    print(f"\n   API Response Logs:")
    print(f"     → http://localhost:9999/api/logs")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    monitor_logs()
