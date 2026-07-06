# Azure Deployment Plan - ai-playground

**Status**: ⏳ Planning  
**Last Updated**: 2026-07-06  
**Created by**: GitHub Copilot

---

## 1. Workspace Analysis

| Item | Value |
|------|-------|
| **Mode** | MODIFY (existing FastAPI application) |
| **Project Root** | `c:\Users\Sumeet.Boob\OneDrive - Brillio\GitHubRepo\MultiAgent\Consolidated_Portal` |
| **Framework** | FastAPI with Uvicorn |
| **Runtime** | Python 3.14 |
| **Has azure.yaml** | ✅ Yes (already configured) |
| **Has requirements.txt** | ✅ Yes (fastapi, uvicorn, requests, python-multipart, gunicorn) |

---

## 2. Requirements & Constraints

| Requirement | Status | Notes |
|-------------|--------|-------|
| **Deployment Target** | Azure App Service (Linux) | PaaS platform |
| **Custom Domain** | ai-playground.summitize.in | DNS configuration required |
| **Environment Variables** | OLLAMA_BASE_URL, NEWS_API_KEY | Auto-configured in App Service |
| **Production Server** | Gunicorn | Already in requirements.txt |
| **Static Files** | HTML, CSS, JS in `static/` | Served via FastAPI |
| **Health Checks** | `/api/health` endpoint | Pre-configured in app.py |
| **CORS** | Enabled (all origins) | For development; adjust as needed |

---

## 3. Architecture Design

```
┌─────────────────────────────────┐
│   Custom Domain                 │
│   ai-playground.summitize.in    │
└──────────────┬──────────────────┘
               │
               ▼
        ┌──────────────┐
        │  App Service │
        │   (Linux)    │
        │  Python 3.14 │
        │  gunicorn    │
        └──────────────┘
               │
               ▼
        ┌──────────────┐
        │   FastAPI    │
        │  Application │
        │  /static/*   │
        │  /api/*      │
        └──────────────┘
```

### Services:
1. **Azure App Service (Linux)**
   - Pricing Tier: B1 (Basic) - recommended starting point
   - Python 3.14 runtime
   - Startup Command: `gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app:app`

2. **Custom Domain Configuration**
   - Domain: ai-playground.summitize.in
   - Requires DNS CNAME or A record configuration
   - SSL Certificate: Azure-managed (free)

---

## 4. Deployment Recipe

| Item | Selection |
|------|-----------|
| **IaC Template** | Bicep (AZD default for App Service) |
| **Deployment Tool** | Azure Developer CLI (azd) |
| **Bicep Modules** | Microsoft.Web/sites (App Service) |
| **Source Control** | Git (.azure directory for infrastructure) |

---

## 5. Infrastructure Components

### Bicep Modules to Generate:
- [ ] `infra/main.bicep` - Main orchestration template
- [ ] `infra/resources.bicep` - Resource definitions
- [ ] `infra/parameters.bicep` - Parameters and variables
- [ ] `infra/app-service.bicep` - App Service configuration
- [ ] `infra/main.parameters.json` - Parameter values

### Configuration Files:
- [ ] `.azure/config.json` - AZD configuration
- [ ] `.azure/deployment-plan.md` - This file (updated with decisions)
- [ ] `.deployment` - Azure App Service deployment script (already exists)
- [ ] `startup.sh` - App Service startup script (update if needed)

---

## 6. Environment Variables & Configuration

### App Service Configuration (to be set during deployment):
```
OLLAMA_BASE_URL = "http://localhost:11434"  # Default, can be customized
NEWS_API_KEY = "<your-news-api-key>"        # Optional
```

### Other Settings:
- Python Version: 3.14
- Startup Command: gunicorn with uvicorn workers
- SCM Deployment: Git + .deployment script

---

## 7. Implementation Checklist

### Phase 1: Planning (🔄 IN PROGRESS)
- [x] Analyze workspace
- [x] Gather requirements
- [x] Design architecture
- [ ] Finalize plan for user review

### Phase 2: Execution (⏳ Awaiting Approval)
- [ ] Research Azure services
- [ ] Confirm Azure context (subscription, location)
- [ ] Generate Bicep infrastructure
- [ ] Create AZD configuration
- [ ] Harden security settings
- [ ] Functional verification
- [ ] Update plan status to "Ready for Validation"

### Phase 3: Validation (⏳ After Approval)
- [ ] Invoke azure-validate
- [ ] Fix any validation errors
- [ ] Get deployment readiness approval

### Phase 4: Deployment (⏳ After Validation)
- [ ] Invoke azure-deploy
- [ ] Monitor deployment progress
- [ ] Verify live application
- [ ] Configure custom domain in Azure Portal

---

## 8. Key Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| **Python Version** | 3.14 | Latest stable as requested |
| **App Service Tier** | B1 (Basic) | Cost-effective for startup; scalable |
| **Region** | *To be confirmed* | Depends on your location/requirements |
| **Startup Command** | Gunicorn + Uvicorn | Production-grade ASGI server |
| **Custom Domain** | ai-playground.summitize.in | User-specified |
| **SSL/TLS** | Azure-managed certificate | Free, automatic renewal |

---

## 9. Estimated Timeline

| Phase | Duration |
|-------|----------|
| Infrastructure generation | ~5 minutes |
| Bicep template creation | ~10 minutes |
| User review & approval | *Your time* |
| Validation | ~5 minutes |
| Deployment | ~3-5 minutes |
| Domain configuration | ~10-15 minutes (manual in Portal) |
| **Total** | ~40-50 minutes |

---

## 10. Cost Estimate

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| App Service (Linux) | B1 Basic | ~$12 USD |
| Custom Domain | - | Depends on registrar |
| SSL Certificate | Azure-managed | $0 (free) |
| **Estimated Total** | | ~$12 USD/month |

---

## 11. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| OLLAMA_BASE_URL connectivity | Medium | Document local vs remote setup |
| Custom domain DNS propagation | Low | Provide clear DNS configuration steps |
| Python 3.14 runtime availability | Low | Will select best available runtime |
| Static files serving | Low | FastAPI StaticFiles pre-configured |

---

## 12. Next Steps

✅ **Plan Ready for Review**

**Please review the plan above and confirm:**
1. ✅ Azure subscription and region for deployment
2. ✅ App Service tier (B1, B2, B3, or other preference)
3. ✅ Confirmation to proceed with infrastructure generation

Once approved, I will proceed with **Phase 2: Execution** to generate all infrastructure files and prepare for deployment.

---

## Notes
- The existing `azure.yaml` is already properly configured for App Service
- The `app.py` correctly uses environment variables for Ollama configuration
- The `requirements.txt` includes all necessary dependencies including gunicorn
- Custom domain configuration will be completed in Azure Portal after deployment
