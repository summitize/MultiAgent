# PHASE 1 INTEGRATION CHECKLIST

Quick guide to integrate Digital Twin Foundation into FastAPI application.

## ✅ Files Already Created

- [x] `twin_models.py` - Unified data models
- [x] `twin_adapters.py` - Data source adapters  
- [x] `twin_orchestrator.py` - Sync orchestration
- [x] `twin_integration.py` - FastAPI integration
- [x] `twin_config.json` - Configuration

## 📋 Integration Steps

### Step 1: Update Requirements.txt

Add dependencies for adapters:

```bash
# Jira adapter
jira>=3.13.0

# GitHub adapter
PyGithub>=1.59.0

# Azure DevOps adapter
azure-devops>=7.0.0
msrest>=0.6.21

# Existing dependencies
fastapi>=0.139.0
requests>=2.31.0
uvicorn>=0.28.0
python-multipart>=0.0.6
```

### Step 2: Update app.py (Main FastAPI App)

**Add imports at top:**
```python
from twin_integration import initialize_twin, start_twin, create_twin_routes
import logging
```

**Add startup/shutdown events:**
```python
# Global reference to twin
digital_twin = None

@app.on_event("startup")
async def startup_event():
    """Initialize Digital Twin during app startup"""
    global digital_twin
    logger.info("=" * 60)
    logger.info("INITIALIZING DELIVERY DIGITAL TWIN")
    logger.info("=" * 60)
    
    digital_twin = await initialize_twin()
    
    if digital_twin.is_initialized:
        await start_twin(digital_twin)
        logger.info("✅ Digital Twin started - background sync running")
    else:
        logger.warning("⚠️  Twin initialized but some adapters may be offline")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Digital Twin during app shutdown"""
    global digital_twin
    if digital_twin:
        await digital_twin.stop()
        logger.info("Digital Twin stopped")
```

**Add twin routes:**
```python
# Include twin routes (add after other routes)
if digital_twin:
    twin_routes = create_twin_routes(digital_twin)
    app.include_router(twin_routes)
```

### Step 3: Configure Adapters

Edit `twin_config.json` with your credentials:

```json
{
  "organization_id": "your-org-id",
  "organization_name": "Your Organization",
  "adapters": {
    "jira": {
      "enabled": true,
      "jira_url": "https://your-jira.atlassian.net",
      "jira_token": "YOUR_JIRA_API_TOKEN",
      "board_id": "1"
    },
    "github": {
      "enabled": true,
      "owner": "your-github-org",
      "repos": ["repo1", "repo2"],
      "github_token": "YOUR_GITHUB_TOKEN"
    },
    "azure_devops": {
      "enabled": false,
      "organization": "your-org",
      "project": "your-project",
      "pat_token": "YOUR_PAT_TOKEN"
    }
  },
  "sync_schedule": {
    "jira": 5,
    "github": 10,
    "azure_devops": 15
  }
}
```

**OR use environment variables:**
```bash
# .env file
JIRA_API_TOKEN=your_token_here
GITHUB_TOKEN=your_token_here
AZURE_DEVOPS_TOKEN=your_token_here
```

Then reference in config:
```json
"jira_token": "${JIRA_API_TOKEN}"
```

### Step 4: Test the Integration

**Start the app:**
```bash
python -m uvicorn app:app --reload
```

**Check twin status:**
```bash
curl http://localhost:8000/api/twin/status
```

Expected response:
```json
{
  "status": "running",
  "is_running": true,
  "adapters_connected": 2,
  "total_adapters": 3,
  "memory_updated": "2025-01-15T14:30:45.123456",
  "sync_history_count": 5
}
```

**Get current context:**
```bash
curl http://localhost:8000/api/twin/context
```

**Trigger manual sync:**
```bash
curl -X POST http://localhost:8000/api/twin/sync
```

## 📊 New API Endpoints

All endpoints under `/api/twin/`:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/status` | Twin operational status |
| GET | `/context` | Current sprint/program context |
| GET | `/risks` | Detected risks & proactive alerts |
| POST | `/sync` | Manually trigger sync |
| GET | `/memory` | Full memory snapshot (debug) |
| GET | `/sync-history` | Recent sync operations |
| GET | `/health` | Health check |

## 🚀 What Happens Automatically

Once running, the twin:

1. **Connects to all adapters** on startup
2. **Starts background sync loop** with configured schedule
3. **Fetches data** from Jira, GitHub, Azure DevOps every N minutes
4. **Normalizes** into unified models
5. **Merges** into SharedProjectMemory
6. **Persists** to disk
7. **Tracks** all updates with timestamps

## 🔧 Troubleshooting

### Adapter Connection Failed

```
❌ Failed to connect to Jira: ...
```

**Check:**
- API credentials are correct
- URL is accessible
- API token has required permissions
- Network connectivity

### Memory File Not Found

```
⚠️  Memory file not found, starting fresh
```

**OK** - First run creates it automatically.

### Sync Timeout

Adapters taking too long:
- Check network latency
- Reduce data scope (fewer issues/repos)
- Increase timeout in adapter code

## 📝 Example: Using Twin in an Agent

```python
# In any agent code
from twin_integration import digital_twin

async def my_agent_function():
    # Get current context
    memory = await digital_twin.memory_service.get_memory()
    
    # Read sprint data
    sprint = memory.current_sprint
    if sprint:
        print(f"Sprint: {sprint.sprint_name}")
        print(f"Velocity: {sprint.current_velocity}")
        print(f"Blocked: {sprint.num_blocked}")
    
    # Read resources
    for resource in memory.resources:
        print(f"{resource.name}: {resource.utilization}% utilized")
    
    # Check security
    if memory.security_context:
        print(f"Vulnerabilities: {len(memory.security_context.vulnerabilities)}")
```

## 🎯 Success Criteria

After integration:

- [x] Twin starts without errors
- [x] All adapters connect (or gracefully fail)
- [x] /api/twin/status returns "running": true
- [x] /api/twin/context returns sprint/program data
- [x] Memory file created (project_memory.json)
- [x] Sync history shows recent operations
- [x] Agents can read SharedProjectMemory

## 📚 Next Phase

Once integration complete:

1. **Phase 2**: Risk Detection Engine
   - 6 risk detectors
   - Proactive alerts
   - Risk recommendations

2. **Phase 3**: Agent Collaboration
   - Agents request information from each other
   - Transparent reasoning via audit trail
   - Distributed decision making

3. **Phase 4**: Visualization
   - React Flow for dependency graph
   - Risk dashboard
   - Memory timeline viewer

---

*Estimated integration time: 30-60 minutes*
*Support: See PHASE_1_COMPLETE.md for full architecture*
