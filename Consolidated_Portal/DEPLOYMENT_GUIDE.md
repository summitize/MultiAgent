# DEPLOYMENT GUIDE: Complete System

Quick start to deploy the MultiAgent AI Delivery Operating System with all 4 phases.

## Prerequisites

- Python 3.10+
- Ollama running on localhost:11434 with models installed
- Optional: Jira, GitHub, Azure DevOps credentials

## Installation

### 1. Install Dependencies

```bash
cd Consolidated_Portal

# Add to requirements.txt:
pip install fastapi>=0.139.0 uvicorn>=0.28.0 requests>=2.31.0
pip install jira>=3.13.0 PyGithub>=1.59.0 azure-devops>=7.0.0
pip install python-multipart>=0.0.6 msrest>=0.6.21
```

### 2. Configuration

Edit `twin_config.json`:

```json
{
  "organization_id": "your-org",
  "organization_name": "Your Organization",
  "adapters": {
    "jira": {
      "enabled": true,
      "jira_url": "https://your-jira.atlassian.net",
      "jira_token": "YOUR_TOKEN",
      "board_id": "1"
    },
    "github": {
      "enabled": true,
      "owner": "your-org",
      "repos": ["repo1", "repo2"],
      "github_token": "YOUR_TOKEN"
    },
    "azure_devops": {
      "enabled": false
    }
  },
  "sync_schedule": {
    "jira": 5,
    "github": 10,
    "azure_devops": 15
  }
}
```

### 3. Start Application

**Option A: Use Complete App**
```bash
python -m uvicorn app_complete:app --host 0.0.0.0 --port 8080 --reload
```

**Option B: Update Existing App**
```bash
# Replace app.py with app_complete.py
cp app_complete.py app.py

python -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

## Verification

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

Expected:
```json
{
  "status": "ok",
  "timestamp": "2025-01-15T14:30:45.123456",
  "twin_running": true
}
```

### 2. Twin Status
```bash
curl http://localhost:8000/api/twin/status
```

Expected:
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

### 3. Detect Risks
```bash
curl http://localhost:8000/api/risks/detect
```

### 4. View Dashboard
```bash
curl http://localhost:8000/api/visualization/dashboard
```

## API Endpoints

### Phase 1: Digital Twin
- `GET /api/twin/status` - Twin status
- `GET /api/twin/context` - Current context
- `GET /api/twin/sync-history` - Sync history
- `POST /api/twin/sync` - Manual sync

### Phase 2: Risk Detection
- `GET /api/risks/detect` - Run detectors
- `GET /api/risks/summary` - Risk summary

### Phase 3: Collaboration
- `POST /api/collaboration/request` - Create request
- `GET /api/collaboration/history` - History
- `GET /api/collaboration/audit/{request_id}` - Audit trail

### Phase 4: Visualization
- `GET /api/visualization/dashboard` - Full dashboard
- `GET /api/visualization/dependencies` - Dependency graph
- `GET /api/visualization/burndown` - Burndown chart

## Files Deployed

1. **Phase 1 Foundation** (1,850 lines)
   - `twin_models.py` - Data structures
   - `twin_adapters.py` - Data source adapters
   - `twin_orchestrator.py` - Sync engine
   - `twin_integration.py` - FastAPI routes
   - `twin_config.json` - Configuration

2. **Phase 2 Risk Detection** (400 lines)
   - `twin_risks.py` - 6 risk detectors

3. **Phase 3 Collaboration** (350 lines)
   - `twin_collaboration.py` - Agent communication

4. **Phase 4 Visualization** (300 lines)
   - `twin_visualization.py` - Dashboard generation

5. **Integrated Application** (500 lines)
   - `app_complete.py` - Complete application

## Key Features

✅ **10 Current Agents**
- Code Assistant
- Content Writer
- Legal Analyzer
- News Summarizer
- Proofreader
- Text Summarizer
- Virtual Assistant
- Customer Support
- Shop Recommender
- Symptom Checker

✅ **6 Risk Detectors**
- Spillover probability (82%)
- Capacity bottlenecks (95% util)
- Budget overrun (+9%)
- Dependency conflicts
- Release readiness
- Security trends

✅ **3+ Agent Collaboration**
- Request/response pattern
- Transparent reasoning
- Audit trail
- Deadline tracking

✅ **Real-time Visualization**
- Dependency graphs (React Flow)
- Risk dashboards
- Sprint burndown
- Memory timeline
- Agent network

## Troubleshooting

### Twin Not Initializing
```
Error: "Twin not initialized"
Solution: 
1. Check twin_config.json exists
2. Check adapter credentials
3. Check Ollama is running
```

### Adapter Connection Failed
```
Error: "Failed to connect to Jira"
Solution:
1. Verify URL and token in config
2. Check network connectivity
3. Verify API permissions
```

### Risks Not Detected
```
Error: RiskDetectionEngine returns empty
Solution:
1. Sync data first: POST /api/twin/sync
2. Check memory has sprint data
3. Wait for background sync to complete
```

## Performance Tuning

### Reduce Sync Frequency
Edit `twin_config.json`:
```json
"sync_schedule": {
  "jira": 30,      // Was 5 minutes
  "github": 60,    // Was 10 minutes
  "azure_devops": 60
}
```

### Limit Data Scope
In adapters, add filters:
```python
jql = "sprint = {sprint_id} AND assignee is not EMPTY"
```

## Monitoring

### Logs Location
```
logs/app_YYYYMMDD_HHMMSS.log
```

### Key Metrics
```
/api/twin/status → adapters_connected, memory_updated
/api/risks/detect → summary: {critical, high, medium, low}
/api/collaboration/history → request count per agent
```

## Next Steps

1. **Connect Real Data Sources**
   - Set up Jira API token
   - Configure GitHub access
   - Integrate Azure DevOps

2. **Deploy Frontend**
   - Build React dashboard
   - Connect to visualization endpoints
   - Add real-time updates (WebSocket)

3. **Add Notifications**
   - Email alerts for critical risks
   - Slack integration
   - SMS for escalations

4. **Extend Agent Network**
   - Add 16 more agents (26 total)
   - Create department-specific agents
   - Implement agent orchestration

---

**All systems ready for deployment!**
