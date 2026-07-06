"""
MultiAgent AI Delivery Operating System - Complete Application
Integrates: Agent Registry, Digital Twin Foundation, Risk Detection, 
Agent Collaboration, and Visualization
"""

from fastapi import FastAPI, HTTPException, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
import logging
import logging.handlers
import sys

# Twin components
from twin_integration import initialize_twin, start_twin, create_twin_routes
from twin_risks import RiskDetectionEngine
from twin_collaboration import initialize_agent_collaboration, CollaborationPatterns
from twin_visualization import VisualizationExporter, RiskDashboard

# Get the directory of the current file
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
log_file = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info(f"Application started. Logs will be written to: {log_file}")

# Create FastAPI app
app = FastAPI(
    title="MultiAgent AI Delivery Operating System",
    description="Unified agent platform with Digital Twin, Risk Detection, and Collaboration",
    version="2.0",
    docs_url=None,
    redoc_url=None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
if OLLAMA_BASE_URL.startswith("https://"):
    OLLAMA_BASE_URL = OLLAMA_BASE_URL.replace("https://", "http://", 1)
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "NEWS_API_KEY")

# Global state
ollama_status = {"available": True, "last_check": None, "error": None}
digital_twin = None
risk_engine = None
agent_registry_collab = None
orchestrator_collab = None

# ============================================================================
# AGENT INTERFACE
# ============================================================================

@dataclass
class Agent:
    """Unified Agent Interface"""
    name: str
    id: str
    description: str
    systemPrompt: str
    supportedModels: List[str]
    category: str
    icon: str
    tools: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    suggestedPrompts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return asdict(self)


class AgentRegistry:
    """Manages registered agents"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    def register(self, agent: Agent):
        """Register an agent"""
        self.agents[agent.id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        """Get all agents"""
        return list(self.agents.values())
    
    def list_agents_metadata(self) -> List[Dict]:
        """List agent metadata"""
        return [
            {
                "name": agent.name,
                "id": agent.id,
                "category": agent.category,
                "icon": agent.icon,
                "model": agent.supportedModels[0] if agent.supportedModels else "unknown"
            }
            for agent in self.agents.values()
        ]


agent_registry = AgentRegistry()


def initialize_agents():
    """Initialize all agents"""
    
    agents = [
        Agent(
            name="Code Assistant",
            id="code-assistant",
            description="Generates and debugs code in multiple languages",
            systemPrompt="You are an expert code assistant. {prompt}",
            supportedModels=["qwen2.5-coder:7b"],
            category="development",
            icon="fa-code",
            suggestedPrompts=["Write Python code to...", "Debug this code...", "Optimize this function..."]
        ),
        Agent(
            name="Content Writer",
            id="content-writer",
            description="Writes articles, blogs, and marketing content",
            systemPrompt="You are a professional content writer. Write about: {prompt}",
            supportedModels=["gemma4:latest"],
            category="content",
            icon="fa-pen-nib",
            suggestedPrompts=["Write a blog post about...", "Create marketing copy for..."]
        ),
        Agent(
            name="Legal Analyzer",
            id="legal-analyzer",
            description="Analyzes legal documents and contracts",
            systemPrompt="You are a legal expert. Analyze this document: {text}",
            supportedModels=["phi3:14b"],
            category="legal",
            icon="fa-scale-balanced",
            suggestedPrompts=["Analyze this contract...", "What are the key terms in..."]
        ),
        Agent(
            name="News Summarizer",
            id="news-summarizer",
            description="Fetches and summarizes news articles",
            systemPrompt="Summarize these news articles: {articles}",
            supportedModels=["qwen3.6:27b"],
            category="news",
            icon="fa-newspaper",
            suggestedPrompts=["Summarize tech news", "Get news on AI developments"]
        ),
        Agent(
            name="Proofreader",
            id="proofreader",
            description="Proofreads and improves text quality",
            systemPrompt="Proofread and improve this text: {text}",
            supportedModels=["DeepSeek-R1:latest"],
            category="content",
            icon="fa-spell-check",
            suggestedPrompts=["Proofread my document", "Check this for grammar"]
        ),
        Agent(
            name="Text Summarizer",
            id="text-summarizer",
            description="Summarizes long-form content",
            systemPrompt="Summarize this text concisely: {text}",
            supportedModels=["mistral:7b"],
            category="analysis",
            icon="fa-compress",
            suggestedPrompts=["Summarize this article", "Create a summary of..."]
        ),
        Agent(
            name="Virtual Assistant",
            id="virtual-assistant",
            description="Personal productivity and scheduling assistant",
            systemPrompt="You are a virtual assistant. Help with: {task}",
            supportedModels=["gemma4:latest"],
            category="productivity",
            icon="fa-robot",
            suggestedPrompts=["Schedule a meeting", "Create a task list"]
        ),
        Agent(
            name="Customer Support",
            id="customer-support",
            description="Handles customer inquiries and support tickets",
            systemPrompt="You are a customer support agent. Address: {query}",
            supportedModels=["qwen3.6:27b"],
            category="support",
            icon="fa-headset",
            suggestedPrompts=["I have a problem with...", "How do I..."]
        ),
        Agent(
            name="Shop Recommender",
            id="ecommerce-recommender",
            description="Recommends products based on preferences",
            systemPrompt="You are an ecommerce expert. Recommend products for: {preference}",
            supportedModels=["granite4.1:8b"],
            category="ecommerce",
            icon="fa-shopping-cart",
            suggestedPrompts=["Recommend products for...", "What should I buy..."]
        ),
        Agent(
            name="Symptom Checker",
            id="medical-symptom-checker",
            description="Provides medical information (NOT a substitute for professional medical advice)",
            systemPrompt="You are a medical information assistant. About these symptoms: {symptoms}",
            supportedModels=["phi3:14b"],
            category="medical",
            icon="fa-stethoscope",
            suggestedPrompts=["I have these symptoms...", "What could cause..."]
        ),
    ]
    
    for agent in agents:
        agent_registry.register(agent)
    
    logger.info(f"✅ Registered {len(agents)} agents")


def call_ollama(model_name: str, prompt: str) -> Dict[str, Any]:
    """Call Ollama LLM"""
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            return {
                "response": response.json().get("response", ""),
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "error": f"Ollama returned HTTP {response.status_code}",
                "model": model_name
            }
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return {"error": str(e), "model": model_name}


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global digital_twin, risk_engine, agent_registry_collab, orchestrator_collab
    
    logger.info("=" * 60)
    logger.info("STARTING MULTIAGENT AI DELIVERY OPERATING SYSTEM")
    logger.info("=" * 60)
    
    # Initialize agents
    initialize_agents()
    
    # Initialize Digital Twin (Phase 1)
    logger.info("\n📊 Initializing Delivery Digital Twin...")
    digital_twin = await initialize_twin()
    
    if digital_twin.is_initialized:
        await start_twin(digital_twin)
        logger.info("✅ Digital Twin running - background sync active")
    
    # Initialize Risk Engine (Phase 2)
    logger.info("\n🚨 Initializing Risk Detection Engine...")
    if digital_twin and digital_twin.memory_service:
        memory = await digital_twin.memory_service.get_memory()
        risk_engine = RiskDetectionEngine(memory)
        logger.info("✅ Risk Detection Engine ready (6 detectors)")
    
    # Initialize Agent Collaboration (Phase 3)
    logger.info("\n🤝 Initializing Agent Collaboration Engine...")
    agent_registry_collab, orchestrator_collab = initialize_agent_collaboration()
    logger.info("✅ Agent Collaboration Engine ready")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL SYSTEMS INITIALIZED")
    logger.info("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global digital_twin
    if digital_twin:
        await digital_twin.stop()
        logger.info("Digital Twin stopped")


# ============================================================================
# CORE API ROUTES
# ============================================================================

@app.get("/")
def read_root():
    """Root endpoint"""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health_check():
    """Health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "twin_running": digital_twin.is_initialized if digital_twin else False,
    }


@app.get("/api/default")
def default_check():
    """Default response"""
    return {
        "message": "MultiAgent AI Delivery Operating System",
        "version": "2.0",
        "status": "operational",
        "phases": ["Phase 1: Digital Twin ✅", "Phase 2: Risk Detection ✅", "Phase 3: Collaboration ✅", "Phase 4: Visualization ✅"]
    }


@app.get("/api/agents")
def get_agents():
    """Get all registered agents"""
    agents = agent_registry.get_all_agents()
    return {
        "total_agents": len(agents),
        "agents": agent_registry.list_agents_metadata()
    }


@app.post("/api/agent/{agent_id}/invoke")
async def invoke_agent(agent_id: str, **kwargs):
    """Invoke any agent"""
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    logger.info(f"Invoking: {agent.name}")
    
    # Extract form data
    form_data = await request.form() if hasattr(request, 'form') else kwargs
    
    prompt = agent.systemPrompt
    for key, value in form_data.items():
        prompt = prompt.replace(f"{{{key}}}", str(value))
    
    model = agent.supportedModels[0] if agent.supportedModels else "mistral:7b"
    return call_ollama(model, prompt)


# ============================================================================
# BACKWARD COMPATIBILITY ENDPOINTS (FIXED)
# ============================================================================

@app.post("/api/generate_code")
async def generate_code(prompt: str = Form(...)):
    """Generate code"""
    agent = agent_registry.get_agent("code-assistant")
    prompt_text = f"Write clean, well-documented code: {prompt}"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt_text)


@app.post("/api/generate_content")
async def generate_content(topic: str = Form(...)):
    """Generate content"""
    agent = agent_registry.get_agent("content-writer")
    prompt_text = f"Write detailed content about: {topic}"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt_text)


@app.post("/api/analyze_legal_text")
async def analyze_legal_text(text: str = Form(...)):
    """Analyze legal text"""
    agent = agent_registry.get_agent("legal-analyzer")
    prompt_text = f"Analyze this legal document: {text}"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt_text)


@app.post("/api/proofread")
async def proofread(text: str = Form(...)):
    """Proofread text"""
    agent = agent_registry.get_agent("proofreader")
    prompt_text = f"Proofread and improve: {text}"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt_text)


@app.post("/api/summarize")
async def summarize(text: str = Form(...)):
    """Summarize text"""
    agent = agent_registry.get_agent("text-summarizer")
    prompt_text = f"Summarize: {text}"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt_text)


@app.get("/api/fetch_and_summarize_news")
def fetch_news(category: str = Query("technology")):
    """Fetch news"""
    try:
        params = {"category": category, "language": "en", "apiKey": NEWS_API_KEY}
        response = requests.get("https://newsapi.org/v2/top-headlines", params=params, timeout=10)
        
        if response.status_code == 200:
            articles = response.json().get("articles", [])[:5]
            return {"articles": articles, "category": category}
        else:
            return {"error": "Failed to fetch news"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/ollama-status")
def check_ollama_status():
    """Check Ollama status"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {"available": True, "models_count": len(models), "models": [m.get("name") for m in models]}
        else:
            return {"available": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"available": False, "error": str(e)}


# ============================================================================
# DIGITAL TWIN API ROUTES (PHASE 1)
# ============================================================================

if digital_twin:
    twin_routes = create_twin_routes(digital_twin)
    app.include_router(twin_routes)


# ============================================================================
# RISK DETECTION API ROUTES (PHASE 2)
# ============================================================================

@app.get("/api/risks/detect")
async def detect_risks():
    """Run risk detection"""
    if not risk_engine or not digital_twin:
        raise HTTPException(status_code=503, detail="Risk engine not initialized")
    
    memory = await digital_twin.memory_service.get_memory()
    report = await risk_engine.detect_all()
    
    return {
        "timestamp": report.timestamp.isoformat(),
        "summary": report.summary,
        "risks": [r.to_dict() for r in report.risks],
    }


@app.get("/api/risks/summary")
async def get_risk_summary():
    """Get risk summary"""
    if not risk_engine or not risk_engine.last_report:
        return {"errors": [], "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0}}
    
    dashboard = RiskDashboard.generate_risk_summary(risk_engine.last_report.risks)
    return dashboard


# ============================================================================
# AGENT COLLABORATION API ROUTES (PHASE 3)
# ============================================================================

@app.post("/api/collaboration/request")
async def create_collaboration_request(
    from_agent: str,
    request_type: str,
    context: Dict = None,
):
    """Create collaboration request"""
    if not orchestrator_collab:
        raise HTTPException(status_code=503, detail="Collaboration engine not initialized")
    
    request = await orchestrator_collab.create_request(
        from_agent_id=from_agent,
        request_type=request_type,
        context=context or {},
    )
    
    return request.to_dict()


@app.get("/api/collaboration/history")
async def get_collaboration_history(agent_id: str = Query(...)):
    """Get agent collaboration history"""
    if not orchestrator_collab:
        raise HTTPException(status_code=503, detail="Collaboration engine not initialized")
    
    history = orchestrator_collab.get_collaboration_history(agent_id)
    return {"agent_id": agent_id, "history": history}


@app.get("/api/collaboration/audit/{request_id}")
async def get_request_audit(request_id: str):
    """Get audit trail for request"""
    if not orchestrator_collab:
        raise HTTPException(status_code=503, detail="Collaboration engine not initialized")
    
    trail = orchestrator_collab.get_audit_trail(request_id)
    return {"request_id": request_id, "audit_trail": trail}


# ============================================================================
# VISUALIZATION API ROUTES (PHASE 4)
# ============================================================================

@app.get("/api/visualization/dashboard")
async def get_visualization_dashboard():
    """Get complete dashboard"""
    if not digital_twin or not risk_engine:
        raise HTTPException(status_code=503, detail="Dashboard not ready")
    
    memory = await digital_twin.memory_service.get_memory()
    risks = risk_engine.last_report.risks if risk_engine.last_report else []
    
    dashboard = VisualizationExporter.export_full_dashboard(memory, risks)
    return dashboard


@app.get("/api/visualization/dependencies")
async def get_dependency_graph():
    """Get dependency graph"""
    if not digital_twin:
        raise HTTPException(status_code=503, detail="Twin not ready")
    
    from twin_visualization import ReactFlowGenerator
    
    memory = await digital_twin.memory_service.get_memory()
    graph = ReactFlowGenerator.generate_dependency_graph(memory)
    return graph


@app.get("/api/visualization/burndown")
async def get_burndown_chart():
    """Get burndown chart"""
    if not digital_twin:
        raise HTTPException(status_code=503, detail="Twin not ready")
    
    from twin_visualization import BurndownChart
    
    memory = await digital_twin.memory_service.get_memory()
    burndown = BurndownChart.generate_burndown_data(memory)
    return burndown


# ============================================================================
# DEBUG ENDPOINTS
# ============================================================================

@app.get("/api/debug/memory")
async def debug_memory():
    """Debug endpoint: Get full memory"""
    if not digital_twin:
        return {"error": "Twin not initialized"}
    
    memory = await digital_twin.memory_service.get_memory()
    return memory.to_dict()


@app.get("/api/debug/agents")
def debug_agents():
    """Debug endpoint: List all agents"""
    return {
        "total": len(agent_registry.agents),
        "agents": [
            {"id": agent.id, "name": agent.name, "category": agent.category}
            for agent in agent_registry.get_all_agents()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
