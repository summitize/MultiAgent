# AI Portal - Comprehensive Logging Guide

## 📊 Logging Setup Completed

Your Consolidated AI Portal now has **three-tier comprehensive logging** enabled:

---

## 1. 📁 FastAPI Application Logs

### Location
```
Consolidated_Portal/logs/app_YYYYMMDD_HHMMSS.log
```

### What's Logged
- ✓ Application startup information
- ✓ All API request/response details
- ✓ Ollama connection status
- ✓ Error messages with line numbers
- ✓ Timestamps for every event

### Log Levels
- **DEBUG** (File only): Detailed information for troubleshooting
- **INFO** (Console + File): General informational messages
- **WARNING** (Console + File): Warning messages
- **ERROR** (Console + File): Error occurrences

### Format
```
2026-07-06 17:50:42 - __main__ - INFO - [app.py:156] - Application started. Logs will be written to: C:\...\logs\app_20260706_175042.log
```

---

## 2. 🌐 Ollama Backend Logs

### Running Ollama for Debugging

#### Enable Debug Mode (Windows PowerShell):
```powershell
$env:OLLAMA_DEBUG = "1"
ollama serve
```

#### Ollama Log Locations
- **Default Windows**: `%USERPROFILE%\.ollama\logs\`
  - Full path: `C:\Users\Sumeet.Boob\.ollama\logs\`
- **Alternative**: Look at console output where `ollama serve` runs

#### What Ollama Logs
- Model loading information
- Request/response times
- GPU/VRAM usage
- Connection issues

---

## 3. 🔌 API Endpoints for Log Access

### View Application Logs via API

**Endpoint**: `GET /api/logs`

**Parameters**:
- `lines` (optional): Number of recent log lines (default: 50)

**Examples**:
```bash
# Get last 50 lines
curl http://localhost:9999/api/logs

# Get last 200 lines
curl http://localhost:9999/api/logs?lines=200

# Get last 10 lines
curl http://localhost:9999/api/logs?lines=10
```

**Response Format**:
```json
{
  "log_file": "app_20260706_175042.log",
  "total_lines": 1250,
  "returned_lines": 50,
  "logs": "2026-07-06 17:50:42 - __main__ - INFO - Application started...\n..."
}
```

---

## 4. 🚀 Enabling Debug Logging

### For FastAPI (Enhanced Console Output)

Restart the application with debug logging:
```powershell
cd "Consolidated_Portal"
.\venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 9999 --log-level debug
```

### For Ollama (Detailed Model Logs)

```powershell
$env:OLLAMA_DEBUG = "1"
ollama serve
```

---

## 5. 📊 Log Monitoring Script

Use the provided monitoring tool:
```powershell
cd "Consolidated_Portal"
.\venv\Scripts\python.exe monitor_logs.py
```

**Features**:
- Shows all log files in directory
- Displays file sizes
- Provides real-time log monitoring
- Shows last 10 log entries

---

## 6. 🔍 Troubleshooting with Logs

### Common Log Patterns

**Ollama Not Available**:
```
ERROR - Cannot connect to Ollama at http://localhost:11434
```
→ Check if `ollama serve` is running

**Model Loading Issues**:
```
ERROR - Invalid JSON response from Ollama
```
→ Model may not be fully loaded. Wait and retry.

**Request Timeout**:
```
ERROR - Timeout while calling Ollama
```
→ Model is processing. Try again or increase timeout.

**Successful Request**:
```
INFO - Successfully processed with qwen2.5-coder:7b
INFO - Code generation completed
```
→ Request succeeded!

---

## 7. 📈 Log File Management

### Automatic Log Rotation
- **Created**: One log file per application startup
- **Format**: `app_YYYYMMDD_HHMMSS.log`
- **Storage**: `Consolidated_Portal/logs/`

### Manual Cleanup
```powershell
# Remove logs older than 7 days
$logDir = "Consolidated_Portal\logs"
Get-ChildItem -Path $logDir -Filter "*.log" | 
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | 
  Remove-Item
```

---

## 8. 🎯 Quick Reference

| Component | Log Location | Access Method | Format |
|-----------|--------------|----------------|--------|
| **FastAPI** | `logs/app_*.log` | File or `/api/logs` endpoint | Text + Console |
| **Ollama** | `%USERPROFILE%\.ollama\logs\` or Console | Console output | Text |
| **Tests** | Same as FastAPI | View in logs directory | Text |

---

## 9. 📋 Files Added

✓ `logging_config.py` - Centralized logging setup
✓ `monitor_logs.py` - Real-time log monitoring script
✓ `logs/` - Directory automatically created on startup

---

## 10. ✨ Key Features

- ✅ **No Code Changes Needed** - Logging is transparent
- ✅ **File + Console Output** - See logs in two places
- ✅ **API Access** - Query logs programmatically
- ✅ **Automatic Timestamps** - Track exact timing of events
- ✅ **Error Tracking** - Full stack traces with line numbers
- ✅ **Request Logging** - See all API calls and responses
- ✅ **Debug Mode** - Enhanced logging for troubleshooting

---

## 11. 🔗 Quick Start

**Step 1**: Ensure Ollama is running
```powershell
ollama serve
```

**Step 2**: Start FastAPI server
```powershell
cd Consolidated_Portal
.\venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 9999
```

**Step 3**: Check logs in real-time
```powershell
# Option A: View via API
curl http://localhost:9999/api/logs

# Option B: View file directly
Get-Content "Consolidated_Portal\logs\app_*.log" -Tail 50 -Wait

# Option C: Run monitor script
.\venv\Scripts\python.exe monitor_logs.py
```

---

## Notes

- Logs are **DEBUG level in files** (very detailed)
- Logs are **INFO level in console** (important messages only)
- Each application startup creates a **new log file**
- All timestamps are in **local timezone**
- Logs include **filename and line number** for easy debugging

---

**Setup completed!** Your system now has comprehensive logging enabled for debugging and monitoring.
