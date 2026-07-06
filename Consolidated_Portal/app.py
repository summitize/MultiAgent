from fastapi import FastAPI, HTTPException, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Callable
import logging
import logging.handlers
import sys

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

# File handler for detailed logs
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Console handler for console output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Application logger
logger = logging.getLogger(__name__)
logger.info(f"Application started. Logs will be written to: {log_file}")

# Create FastAPI app instance
app = FastAPI(title="MultiAgent AI Delivery Operating System", docs_url=None, redoc_url=None)

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mapping
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configuration from environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
# Ensure HTTP protocol (not HTTPS for local Ollama)
if OLLAMA_BASE_URL.startswith("https://"):
    OLLAMA_BASE_URL = OLLAMA_BASE_URL.replace("https://", "http://", 1)
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "NEWS_API_KEY")  # Replace with actual API key if available

# Track Ollama status
ollama_status = {"available": True, "last_check": None, "error": None}

# ============================================================================
# AGENT INTERFACE & REGISTRY
# ============================================================================

@dataclass
class Agent:
    """
    Unified Agent Interface
    Every agent must expose these properties to be managed by the system.
    """
    name: str  # Display name (e.g., "Code Assistant", "Program Director")
    id: str  # Unique identifier (e.g., "code-assistant", "program-director")
    description: str  # What the agent does
    systemPrompt: str  # System instruction/prompt template
    supportedModels: List[str]  # List of models this agent can use
    category: str  # Category (e.g., "development", "content", "delivery")
    icon: str  # FontAwesome icon class (e.g., "fa-code", "fa-crown")
    tools: List[Dict[str, Any]] = field(default_factory=list)  # Available tools for the agent
    memory: Dict[str, Any] = field(default_factory=dict)  # Memory/context storage
    actions: List[str] = field(default_factory=list)  # Available actions
    suggestedPrompts: List[str] = field(default_factory=list)  # Example prompts to guide users
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary, excluding memory for API responses"""
        data = asdict(self)
        # Don't expose internal memory in API
        data.pop('memory', None)
        return data


class AgentRegistry:
    """Manages all registered agents"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    def register(self, agent: Agent) -> None:
        """Register a new agent"""
        self.agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.id})")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    def list_agents_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all agents"""
        return [agent.to_dict() for agent in self.get_all_agents()]


# Create global registry
agent_registry = AgentRegistry()

# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

# Initialize all agents
def initialize_agents():
    """Register all agents with the system"""
    
    agents = [
        Agent(
            name="Code Assistant",
            id="code-assistant",
            description="Generate or debug code with support for multiple languages",
            systemPrompt="Write clean, well-documented {prompt} code snippet.",
            supportedModels=["qwen2.5-coder:7b"],
            category="development",
            icon="fa-code",
            suggestedPrompts=[
                "Write a Python function to sort a list",
                "Debug this TypeScript async function",
                "Create a REST API endpoint in FastAPI"
            ],
            actions=["generate", "debug", "explain", "refactor"]
        ),
        Agent(
            name="Content Writer",
            id="content-writer",
            description="Write blog posts, articles, and content in various styles",
            systemPrompt="Write a detailed blog post about '{topic}' in a {style} tone.",
            supportedModels=["gemma4:latest"],
            category="content",
            icon="fa-pen-nib",
            suggestedPrompts=[
                "Write about AI in healthcare",
                "Create marketing copy for a SaaS product",
                "Draft a technical whitepaper on cloud computing"
            ],
            actions=["write", "edit", "rewrite", "expand"]
        ),
        Agent(
            name="Legal Analyzer",
            id="legal-analyzer",
            description="Extract insights from legal documents and contracts",
            systemPrompt="Extract key insights from the legal document: {text}. Summarize important clauses, risks, and obligations.",
            supportedModels=["phi3:14b"],
            category="legal",
            icon="fa-scale-balanced",
            suggestedPrompts=[
                "Analyze this employment contract",
                "Review NDA terms",
                "Identify risks in this service agreement"
            ],
            actions=["analyze", "summarize", "identify-risks", "explain-terms"]
        ),
        Agent(
            name="News Summarizer",
            id="news-summarizer",
            description="Fetch and summarize news articles by category",
            systemPrompt="Summarize these news headlines: {news_text}",
            supportedModels=["qwen3.6:27b"],
            category="content",
            icon="fa-newspaper",
            suggestedPrompts=[
                "Get tech news summary",
                "Summarize business headlines",
                "Review health news stories"
            ],
            actions=["summarize", "filter", "categorize"]
        ),
        Agent(
            name="Proofreader",
            id="proofreader",
            description="Proofread and correct text for grammar and clarity",
            systemPrompt="Correct the grammar, spelling, and sentence structure of the following text: {text}",
            supportedModels=["DeepSeek-R1:latest"],
            category="content",
            icon="fa-spell-check",
            suggestedPrompts=[
                "Proofread my essay",
                "Fix grammar in this paragraph",
                "Improve clarity of this document"
            ],
            actions=["proofread", "correct", "improve-clarity", "check-tone"]
        ),
        Agent(
            name="Text Summarizer",
            id="text-summarizer",
            description="Summarize long texts into concise summaries",
            systemPrompt="Summarize this text concisely: {text}",
            supportedModels=["mistral:7b"],
            category="content",
            icon="fa-compress",
            suggestedPrompts=[
                "Summarize this article",
                "Create executive summary",
                "Condense this report"
            ],
            actions=["summarize", "extract-key-points", "create-outline"]
        ),
        Agent(
            name="Virtual Assistant",
            id="virtual-assistant",
            description="AI-powered assistant for task scheduling and queries",
            systemPrompt="You are an AI-powered virtual assistant that helps with task scheduling and answering queries. User: {user_query}",
            supportedModels=["gemma4:latest"],
            category="assistant",
            icon="fa-robot",
            suggestedPrompts=[
                "Schedule a meeting for tomorrow",
                "What's the weather in New York?",
                "Remind me to call the bank"
            ],
            actions=["schedule", "answer", "remind", "organize"]
        ),
        Agent(
            name="Customer Support",
            id="customer-support",
            description="Professional customer support chatbot",
            systemPrompt="You are a customer support chatbot. Answer the user's question professionally and concisely. User: {user_query}",
            supportedModels=["qwen3.6:27b"],
            category="support",
            icon="fa-headset",
            suggestedPrompts=[
                "How do I reset my password?",
                "What's your refund policy?",
                "I'm having trouble with my account"
            ],
            actions=["support", "troubleshoot", "escalate", "document"]
        ),
        Agent(
            name="Shop Recommender",
            id="shop-recommender",
            description="AI product recommendation engine",
            systemPrompt="You are an AI product recommender. Based on user preferences, suggest the best matching products. User Preferences: {preferences}",
            supportedModels=["granite4.1:8b"],
            category="ecommerce",
            icon="fa-cart-shopping",
            suggestedPrompts=[
                "Recommend laptops under $1000",
                "Suggest summer clothes",
                "Find budget-friendly cameras"
            ],
            actions=["recommend", "compare", "filter", "review"]
        ),
        Agent(
            name="Symptom Checker",
            id="symptom-checker",
            description="Medical AI assistant for symptom analysis",
            systemPrompt="You are a medical AI assistant. Analyze symptoms and provide possible explanations and general advice. Do not provide diagnosis. User Symptoms: {symptoms}",
            supportedModels=["phi3:14b"],
            category="medical",
            icon="fa-stethoscope",
            suggestedPrompts=[
                "I have a headache and fever",
                "Analyze these allergy symptoms",
                "What could cause persistent cough?"
            ],
            actions=["analyze", "advise", "educate", "refer"]
        ),
    ]
    
    for agent in agents:
        agent_registry.register(agent)
    
    logger.info(f"Initialized {len(agents)} agents")


# Initialize agents when app starts
initialize_agents()


@app.get("/")
def serve_homepage():
    """ Serve the index.html file when accessing the root URL """
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/agents")
def get_all_agents():
    """ Get all available agents with metadata """
    agents = agent_registry.list_agents_metadata()
    return {"total_agents": len(agents), "agents": agents}

@app.get("/api/endpoints")
def get_all_endpoints():
    """ 
    BACKWARD COMPATIBILITY: Get all available API endpoints with descriptions 
    This endpoint maintains backward compatibility with old frontend code
    """
    agents = agent_registry.get_all_agents()
    endpoints = []
    
    for idx, agent in enumerate(agents, 1):
        endpoint_data = {
            "id": idx,
            "name": agent.name,
            "agent_id": agent.id,
            "description": agent.description,
            "model": agent.supportedModels[0] if agent.supportedModels else "unknown",
            "category": agent.category,
            "icon": agent.icon
        }
        endpoints.append(endpoint_data)
    
    return {"total_agents": len(endpoints), "agents": endpoints}

@app.get("/api/health")
def health_check():
    """ Health check endpoint """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/default")
def default_check():
    """ Default health check that responds with model greeting """
    return {"message": "Hi, I am Ollama Multi-Agent Portal", "version": "1.0", "status": "operational"}

@app.get("/api/ollama-status")
def check_ollama_status():
    """ Check if Ollama is available """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_status["available"] = True
            ollama_status["error"] = None
            ollama_status["last_check"] = datetime.now().isoformat()
            models = response.json().get("models", [])
            return {"available": True, "models_count": len(models), "models": [m.get("name") for m in models]}
        else:
            ollama_status["available"] = False
            ollama_status["error"] = f"HTTP {response.status_code}"
            return {"available": False, "error": f"Ollama returned HTTP {response.status_code}"}
    except requests.exceptions.Timeout:
        ollama_status["available"] = False
        ollama_status["error"] = "Connection timeout"
        return {"available": False, "error": "Ollama connection timeout. Service may be down."}
    except requests.exceptions.ConnectionError:
        ollama_status["available"] = False
        ollama_status["error"] = "Connection refused"
        return {"available": False, "error": "Cannot connect to Ollama. Is it running locally?"}
    except Exception as e:
        ollama_status["available"] = False
        ollama_status["error"] = str(e)
        return {"available": False, "error": f"Ollama check failed: {str(e)}"}

# ============================================================================
# UNIFIED AGENT ROUTING
# ============================================================================

def build_prompt(agent: Agent, **kwargs) -> str:
    """
    Build the actual prompt by substituting template variables
    """
    prompt = agent.systemPrompt
    for key, value in kwargs.items():
        prompt = prompt.replace(f"{{{key}}}", str(value))
    return prompt


@app.post("/api/agent/{agent_id}/invoke")
def invoke_agent(agent_id: str, **form_data):
    """
    Universal agent invocation endpoint
    Works with any registered agent
    """
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    logger.info(f"Invoking agent: {agent.name} ({agent_id})")
    
    # Build prompt from system prompt template
    prompt = build_prompt(agent, **form_data)
    
    # Use first supported model
    model = agent.supportedModels[0] if agent.supportedModels else "mistral:7b"
    
    return call_ollama(model, prompt)


# ============================================================================
# BACKWARD COMPATIBILITY ENDPOINTS (Maps old routes to new agent system)
# ============================================================================

@app.post("/api/generate_code")
def generate_code(prompt: str = Form(...), mode: str = Form(...)):
    """DEPRECATED: Use /api/agent/code-assistant/invoke instead"""
    agent = agent_registry.get_agent("code-assistant")
    if mode == "generate":
        prompt_text = f"Write a clean, well-documented {prompt} code snippet."
    elif mode == "debug":
        prompt_text = f"Debug and fix the following code:\n{prompt}"
    else:
        raise HTTPException(status_code=400, detail="Invalid mode selected.")
    
    model = agent.supportedModels[0]
    return call_ollama(model, prompt_text)

@app.post("/api/generate_content")
def generate_content(topic: str = Form(...), style: str = Form(...)):
    """DEPRECATED: Use /api/agent/content-writer/invoke instead"""
    agent = agent_registry.get_agent("content-writer")
    prompt = f"Write a detailed blog post about '{topic}' in a {style} tone."
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)

@app.post("/api/analyze_legal_text")
def analyze_legal_text(text: str = Form(...)):
    """DEPRECATED: Use /api/agent/legal-analyzer/invoke instead"""
    agent = agent_registry.get_agent("legal-analyzer")
    prompt = f"Extract key insights from the following legal document:\n{text}\nSummarize important clauses, risks, and obligations."
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)

@app.get("/api/fetch_and_summarize_news")
def fetch_and_summarize_news(category: str = Query("technology")):
    """DEPRECATED: Use /api/agent/news-summarizer/invoke instead"""
    headers = {"Authorization": f"Bearer {NEWS_API_KEY}"}
    params = {"category": category, "language": "en", "apiKey": NEWS_API_KEY}
    try:
        news_response = requests.get(NEWS_API_URL, params=params, headers=headers)
        if news_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch news articles")
        news_data = news_response.json()
        if "articles" not in news_data or not news_data["articles"]:
            return {"summary": "No news articles found for this category."}
        
        articles = news_data["articles"][:3]
        news_text = "\n".join([f"- {article['title']} ({article['source']['name']})" for article in articles])
        
        agent = agent_registry.get_agent("news-summarizer")
        model = agent.supportedModels[0]
        ollama_res = call_ollama(model, f"Summarize these news headlines:\n{news_text}")
        return {"summary": ollama_res.get("response", "No summary available."), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch or summarize news: {str(e)}")

@app.post("/api/proofread")
def proofread_text(text: str = Form(...)):
    """DEPRECATED: Use /api/agent/proofreader/invoke instead"""
    agent = agent_registry.get_agent("proofreader")
    prompt = f"Correct the grammar, spelling, and sentence structure of the following text:\n{text}"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)

@app.post("/api/summarize")
def summarize_text(text: str = Form(...)):
    """DEPRECATED: Use /api/agent/text-summarizer/invoke instead"""
    agent = agent_registry.get_agent("text-summarizer")
    prompt = f"Summarize this: {text}"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)

@app.post("/api/virtual_assistant")
def virtual_assistant(user_query: str = Form(...)):
    """DEPRECATED: Use /api/agent/virtual-assistant/invoke instead"""
    agent = agent_registry.get_agent("virtual-assistant")
    prompt = f"You are an AI-powered virtual assistant that helps with task scheduling and answering queries.\nUser: {user_query}\nAI:"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)

@app.post("/api/customer_support")
def customer_support(user_query: str = Form(...)):
    """DEPRECATED: Use /api/agent/customer-support/invoke instead"""
    agent = agent_registry.get_agent("customer-support")
    prompt = f"You are a customer support chatbot. Answer the user's question professionally and concisely.\nUser: {user_query}\nChatbot:"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)

@app.post("/api/ecommerce_recommender")
def ecommerce_recommender(preferences: str = Form(...)):
    """DEPRECATED: Use /api/agent/shop-recommender/invoke instead"""
    agent = agent_registry.get_agent("shop-recommender")
    prompt = f"You are an AI product recommender. Based on the user's preferences, suggest the best matching products.\nUser Preferences: {preferences}\nRecommendations:"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)

@app.post("/api/medical_symptom_checker")
def medical_symptom_checker(symptoms: str = Form(...)):
    """DEPRECATED: Use /api/agent/symptom-checker/invoke instead"""
    agent = agent_registry.get_agent("symptom-checker")
    prompt = f"You are a medical AI assistant trained to analyze symptoms. Based on the provided symptoms, give possible explanations and general advice. Do not provide a diagnosis or replace a doctor's consultation.\nUser Symptoms: {symptoms}\nMedical AI:"
    model = agent.supportedModels[0]
    return call_ollama(model, prompt)


# ============================================================================
# LLM SERVICE
# ============================================================================

def call_ollama(model_name: str, prompt: str):
    """
    Central LLM abstraction layer
    All agent requests go through this function
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model_name, "prompt": prompt, "stream": False},
            headers=headers,
            timeout=300  # 5 min timeout for inference
        )
        response_data = response.text.strip()
        try:
            json_response = json.loads(response_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from Ollama: {response_data}")
        return {"response": json_response.get("response", "No valid response received.")}
    except requests.exceptions.Timeout:
        ollama_status["available"] = False
        logger.error(f"Ollama timeout for model {model_name}")
        raise HTTPException(status_code=503, detail="⚠️ Ollama is not responding. The service may be offline or overloaded. Please try again later.")
    except requests.exceptions.ConnectionError:
        ollama_status["available"] = False
        logger.error(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        raise HTTPException(status_code=503, detail="⚠️ Cannot connect to Ollama. Please ensure the local Ollama service is running on " + OLLAMA_BASE_URL)
    except requests.exceptions.RequestException as e:
        ollama_status["available"] = False
        logger.error(f"Ollama request failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"⚠️ Ollama request failed: {str(e)}")

# Ensure the app is properly exported as ASGI application
asgi_app = app

if __name__ == "__main__":
    import uvicorn
    # Using 8080 to avoid conflicts with 8000
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
