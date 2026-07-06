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
    DeliveryAI Agent Interface - Advanced Enterprise Agent Model
    Every agent in the organization represents one team member.
    """
    # Identity
    name: str  # Display name (e.g., "Program Manager", "Scrum Master")
    id: str  # Unique identifier (e.g., "program-manager", "scrum-master")
    description: str  # What the agent does
    role: str  # Job title/role in organization
    office: str  # Office tier (executive, delivery, engineering, intelligence, admin)
    
    # AI Configuration
    systemPrompt: str  # System instruction/prompt template
    supportedModels: List[str]  # List of models this agent can use
    recommendedLLM: str = "mistral:7b"  # Preferred model
    temperature: float = 0.7  # LLM temperature
    reasoningMode: bool = False  # Enable advanced reasoning
    
    # Agent Capabilities
    icon: str = "fa-user-tie"  # FontAwesome icon class
    capabilities: List[str] = field(default_factory=list)  # Core capabilities
    tools: List[Dict[str, Any]] = field(default_factory=list)  # Available tools
    templates: List[Dict[str, str]] = field(default_factory=list)  # Response templates
    quickActions: List[str] = field(default_factory=list)  # Quick action buttons
    
    # Memory & Context
    memory: Dict[str, Any] = field(default_factory=dict)  # Long-term memory/context
    conversationHistory: List[Dict[str, str]] = field(default_factory=list)  # Recent conversations
    contextDocuments: List[str] = field(default_factory=list)  # Related documents
    
    # Output & Reporting
    outputFormats: List[str] = field(default_factory=list)  # Supported formats (markdown, json, ppt, docx, pdf)
    reportTemplates: List[Dict[str, Any]] = field(default_factory=list)  # Report types
    exportOptions: List[str] = field(default_factory=list)  # Export capabilities
    
    # Guidance & Learning
    suggestedPrompts: List[str] = field(default_factory=list)  # Example prompts
    actions: List[str] = field(default_factory=list)  # Available actions
    kpis: List[Dict[str, Any]] = field(default_factory=list)  # Key Performance Indicators
    
    # Collaboration
    collaborators: List[str] = field(default_factory=list)  # Other agent IDs this agent works with
    responsibilities: List[str] = field(default_factory=list)  # Primary responsibilities
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary, excluding memory for API responses"""
        data = asdict(self)
        # Don't expose internal memory in API by default
        data.pop('memory', None)
        data.pop('conversationHistory', None)
        return data
    
    def to_dict_with_memory(self) -> Dict[str, Any]:
        """Convert agent to dictionary including memory (for internal use)"""
        return asdict(self)


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
    """Register all DeliveryAI agents with the system"""
    
    agents = [
        # ========== EXECUTIVE OFFICE ==========
        Agent(
            name="Executive Copilot",
            id="executive-copilot",
            role="Executive Leadership",
            office="executive",
            description="Strategic partner for executives. Provides portfolio insights, risk assessment, and board-level recommendations.",
            systemPrompt="You are an Executive Copilot advising C-level executives. Provide strategic insights, portfolio health analysis, and high-level recommendations. Focus on: business impact, ROI, risk mitigation, stakeholder alignment. User query: {prompt}",
            recommendedLLM="claude:latest",
            supportedModels=["claude:latest", "deepseek:latest", "qwen2.5:32b"],
            icon="fa-crown",
            capabilities=["Portfolio Analysis", "Strategic Planning", "Risk Assessment", "Executive Reporting", "Stakeholder Communication"],
            quickActions=["Portfolio Health", "Executive Summary", "Risk Report", "Board Deck"],
            suggestedPrompts=["What is the portfolio health status?", "Analyze cross-project risks", "Create executive summary"],
            outputFormats=["markdown", "json", "ppt", "docx", "pdf"],
            exportOptions=["PDF", "PowerPoint", "Word"],
            kpis=[{"name": "Portfolio Health", "unit": "%"}, {"name": "Budget Variance", "unit": "%"}],
            responsibilities=["Portfolio Strategy", "Board Reporting", "Investor Communication", "Enterprise Risk Management"],
            collaborators=["program-manager", "pmo", "risk-manager"]
        ),
        
        # ========== DELIVERY OFFICE ==========
        Agent(
            name="Program Manager",
            id="program-manager",
            role="Program Management",
            office="delivery",
            description="Manages multiple projects across portfolio. Tracks milestones, dependencies, risks, budgets, and stakeholder coordination.",
            systemPrompt="You are a Program Manager overseeing multiple interdependent projects. Track: milestones, dependencies, budget, risks, stakeholder updates. Provide weekly status reports and executive dashboards. Program context: {prompt}",
            recommendedLLM="claude:latest",
            supportedModels=["claude:latest", "qwen2.5:32b"],
            icon="fa-chart-line",
            capabilities=["Program Planning", "Milestone Tracking", "Risk Management", "Budget Monitoring", "Weekly Reports", "Stakeholder Updates"],
            quickActions=["Weekly Status", "Milestone Report", "Risk Dashboard", "Budget Analysis", "Steering Committee Deck"],
            suggestedPrompts=["Generate weekly status report", "Update on Q3 milestones", "Budget burn analysis"],
            outputFormats=["markdown", "json", "ppt", "docx"],
            exportOptions=["PDF", "PowerPoint"],
            kpis=[{"name": "Schedule Variance", "unit": "%"}, {"name": "Budget Variance", "unit": "%"}, {"name": "Milestone Completion", "unit": "%"}],
            responsibilities=["Program Planning", "Milestone Tracking", "Budget Management", "Risk Identification", "Weekly Reports"],
            collaborators=["scrum-master", "product-owner", "pmo"]
        ),
        
        Agent(
            name="Delivery Manager",
            id="delivery-manager",
            role="Delivery Management",
            office="delivery",
            description="Ensures timely, quality delivery. Manages release planning, environment readiness, and deployment coordination.",
            systemPrompt="You are a Delivery Manager ensuring on-time, quality delivery. Focus on: release planning, deployment readiness, environment health, quality gates, rollback plans. Release details: {prompt}",
            recommendedLLM="qwen2.5:32b",
            supportedModels=["qwen2.5:32b", "mistral:7b"],
            icon="fa-rocket",
            capabilities=["Release Planning", "Deployment Coordination", "Environment Management", "Quality Gates", "Rollback Management"],
            quickActions=["Release Readiness", "Deployment Plan", "Environment Status", "Quality Report"],
            suggestedPrompts=["Is the release ready to go?", "Deployment rollback plan", "Environment readiness check"],
            outputFormats=["markdown", "json", "docx"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Release Planning", "Deployment Coordination", "Environment Health", "Quality Assurance"],
            collaborators=["devops-engineer", "qa-engineer", "architect"]
        ),
        
        Agent(
            name="Scrum Master",
            id="scrum-master",
            role="Scrum Master",
            office="delivery",
            description="Facilitates sprints, removes blockers, tracks velocity, manages retrospectives, and ensures team health.",
            systemPrompt="You are a Scrum Master facilitating agile delivery. Track: sprint health, velocity trends, team capacity, blockers, burndown. Generate: sprint planning summaries, standup updates, retrospective insights. Sprint context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b", "phi3:14b"],
            icon="fa-users",
            capabilities=["Sprint Planning", "Velocity Tracking", "Burndown Management", "Blocker Resolution", "Retrospectives", "Capacity Planning"],
            quickActions=["Sprint Planning", "Standup Summary", "Burndown Chart", "Velocity Report", "Retro Insights"],
            suggestedPrompts=["Plan next sprint", "Generate burndown chart", "Team capacity analysis"],
            outputFormats=["markdown", "json"],
            kpis=[{"name": "Velocity", "unit": "story points"}, {"name": "Burndown", "unit": "%"}, {"name": "Capacity Used", "unit": "%"}],
            responsibilities=["Sprint Facilitation", "Blocker Removal", "Velocity Tracking", "Team Health", "Process Improvement"],
            collaborators=["product-owner", "team-members"]
        ),
        
        Agent(
            name="Product Owner",
            id="product-owner",
            role="Product Ownership",
            office="delivery",
            description="Drives product vision, manages backlog, creates user stories, prioritizes features, and ensures market fit.",
            systemPrompt="You are a Product Owner managing product strategy and backlog. Create user stories with acceptance criteria, manage prioritization, roadmap planning, and competitive analysis. Product details: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-lightbulb",
            capabilities=["Story Creation", "Backlog Refinement", "Prioritization", "Roadmap Planning", "Release Planning", "Acceptance Criteria"],
            quickActions=["Create User Story", "Backlog Refinement", "Priority Matrix", "Release Plan"],
            suggestedPrompts=["Create user story for feature X", "Prioritize backlog", "Build product roadmap"],
            outputFormats=["markdown", "json"],
            kpis=[{"name": "Feature Velocity", "unit": "stories/sprint"}, {"name": "Backlog Size", "unit": "stories"}],
            responsibilities=["Product Vision", "Backlog Management", "Story Creation", "Prioritization", "Feature Acceptance"],
            collaborators=["scrum-master", "business-analyst", "architect"]
        ),
        
        Agent(
            name="Business Analyst",
            id="business-analyst",
            role="Business Analysis",
            office="delivery",
            description="Analyzes business requirements, gaps, processes, and creates documentation for stakeholder alignment.",
            systemPrompt="You are a Business Analyst bridging business and technology. Analyze: requirements, gaps, business rules, process flows, user journeys. Generate: BA documents, gap analysis, process flows. Business context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-magnifying-glass",
            capabilities=["Requirements Analysis", "Gap Analysis", "Process Mapping", "User Journeys", "Business Rules", "Documentation"],
            quickActions=["Requirements Analysis", "Gap Report", "Process Flow", "User Journey"],
            suggestedPrompts=["Analyze business requirements", "Create gap analysis", "Map user journey"],
            outputFormats=["markdown", "json", "docx"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Requirements Gathering", "Gap Analysis", "Process Documentation", "Stakeholder Communication"],
            collaborators=["product-owner", "architect"]
        ),
        
        # ========== ENGINEERING OFFICE ==========
        Agent(
            name="Architect",
            id="architect",
            role="Enterprise Architecture",
            office="engineering",
            description="Designs scalable, secure, maintainable solutions. Reviews architecture, identifies technical debt, and ensures best practices.",
            systemPrompt="You are an Enterprise Architect designing solutions. Create: architecture diagrams, API designs, cloud architecture, technical specifications. Review: design patterns, scalability, security, maintainability. Technical context: {prompt}",
            recommendedLLM="deepseek:latest",
            supportedModels=["deepseek:latest", "qwen2.5:32b"],
            icon="fa-blueprint",
            capabilities=["Architecture Design", "API Design", "Cloud Architecture", "Technical Debt Assessment", "Design Reviews", "Sequence Diagrams"],
            quickActions=["Architecture Review", "Cloud Design", "API Specification", "Technical Debt Report"],
            suggestedPrompts=["Design microservices architecture", "Review API design", "Cloud migration plan"],
            outputFormats=["markdown", "json", "docx"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Solution Design", "Architecture Reviews", "Technical Decisions", "Best Practices", "Technical Debt Management"],
            collaborators=["engineering-manager", "developer", "devops-engineer"]
        ),
        
        Agent(
            name="Engineering Manager",
            id="engineering-manager",
            role="Engineering Leadership",
            office="engineering",
            description="Manages engineering teams, tracks code quality, reviews code velocity, and ensures technical excellence.",
            systemPrompt="You are an Engineering Manager leading technical teams. Track: team productivity, code quality, repository insights, technical health. Generate: team reports, performance reviews, technical recommendations. Team context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-person-hiking",
            capabilities=["Team Management", "Code Review Analysis", "Repository Insights", "Developer Productivity", "Technical Health Tracking"],
            quickActions=["Team Report", "Code Quality Summary", "Productivity Analysis", "Technical Health"],
            suggestedPrompts=["Team productivity analysis", "Code quality trends", "Developer performance"],
            outputFormats=["markdown", "json"],
            kpis=[{"name": "Code Quality", "unit": "score"}, {"name": "Team Velocity", "unit": "commits/week"}],
            responsibilities=["Team Leadership", "Productivity Tracking", "Code Quality", "Technical Development", "Career Growth"],
            collaborators=["developer", "qa-engineer", "devops-engineer"]
        ),
        
        Agent(
            name="Developer",
            id="developer",
            role="Software Development",
            office="engineering",
            description="Writes, debugs, and refactors code. Supports development best practices and code quality.",
            systemPrompt="You are an Expert Developer. Generate: clean, well-documented code, debug existing code, suggest refactoring. Support: multiple languages, frameworks, design patterns. Code task: {prompt}",
            recommendedLLM="qwen2.5-coder:7b",
            supportedModels=["qwen2.5-coder:7b", "deepseek-coder:latest"],
            icon="fa-code",
            capabilities=["Code Generation", "Debugging", "Refactoring", "Code Review", "Documentation", "Testing"],
            quickActions=["Generate Code", "Debug Code", "Refactor", "Code Review", "Write Tests"],
            suggestedPrompts=["Write a Python async function", "Debug this TypeScript error", "Create REST API endpoint"],
            outputFormats=["markdown", "json"],
            responsibilities=["Code Development", "Code Quality", "Testing", "Documentation", "Technical Improvement"],
            collaborators=["qa-engineer", "architect"]
        ),
        
        Agent(
            name="QA Engineer",
            id="qa-engineer",
            role="Quality Assurance",
            office="engineering",
            description="Ensures software quality through testing, automation, and regression analysis.",
            systemPrompt="You are a QA Engineer ensuring software quality. Create: test cases, automation suggestions, regression analysis. Track: quality metrics, release readiness. Release context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-vial",
            capabilities=["Test Case Creation", "Automation Suggestions", "Regression Analysis", "Quality Metrics", "Release Quality"],
            quickActions=["Test Plan", "Automation Suggestions", "Regression Report", "Quality Metrics"],
            suggestedPrompts=["Create test cases for feature X", "Automation suggestions", "Release quality assessment"],
            outputFormats=["markdown", "json"],
            kpis=[{"name": "Test Coverage", "unit": "%"}, {"name": "Defect Density", "unit": "defects/KLOC"}],
            responsibilities=["Test Planning", "Test Automation", "Quality Assurance", "Defect Management", "Release Validation"],
            collaborators=["developer", "delivery-manager"]
        ),
        
        Agent(
            name="DevOps Engineer",
            id="devops-engineer",
            role="DevOps & Infrastructure",
            office="engineering",
            description="Manages infrastructure, CI/CD pipelines, deployment, and environment health.",
            systemPrompt="You are a DevOps Engineer managing infrastructure and deployment. Monitor: pipeline status, environment health, deployment readiness. Provide: rollback plans, environment recommendations. Infrastructure context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-server",
            capabilities=["Pipeline Management", "Deployment Coordination", "Environment Health", "Rollback Planning", "Infrastructure Scaling"],
            quickActions=["Pipeline Status", "Deployment Readiness", "Environment Health", "Rollback Plan"],
            suggestedPrompts=["Check deployment pipeline", "Environment health status", "Rollback procedure"],
            outputFormats=["markdown", "json"],
            responsibilities=["Infrastructure Management", "CI/CD Pipelines", "Deployment Coordination", "Environment Health", "Scalability"],
            collaborators=["architect", "delivery-manager"]
        ),
        
        Agent(
            name="Security Engineer",
            id="security-engineer",
            role="Security & Compliance",
            office="engineering",
            description="Ensures application security, compliance, and vulnerability management.",
            systemPrompt="You are a Security Engineer protecting applications. Review: OWASP compliance, dependency vulnerabilities, secret detection, security policies. Generate: security reports, remediation plans. Security context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-shield",
            capabilities=["OWASP Review", "Dependency Analysis", "Secret Detection", "Compliance Checking", "Vulnerability Remediation"],
            quickActions=["Security Review", "Vulnerability Report", "Compliance Check", "Remediation Plan"],
            suggestedPrompts=["OWASP compliance review", "Vulnerability analysis", "Security assessment"],
            outputFormats=["markdown", "json", "docx"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Security Reviews", "Vulnerability Management", "Compliance", "Security Policies", "Risk Mitigation"],
            collaborators=["architect", "devops-engineer"]
        ),
        
        # ========== DELIVERY INTELLIGENCE ==========
        Agent(
            name="RAID Manager",
            id="raid-manager",
            role="Risk & Issue Management",
            office="intelligence",
            description="Tracks and manages Risks, Assumptions, Issues, and Dependencies across the organization.",
            systemPrompt="You are a RAID Manager tracking organizational risks, assumptions, issues, and dependencies. Generate: RAID reports, impact analysis, mitigation plans. RAID context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-triangle-exclamation",
            capabilities=["Risk Tracking", "Issue Management", "Dependency Mapping", "Mitigation Planning", "RAID Reporting"],
            quickActions=["RAID Report", "Risk Dashboard", "Issue Escalation", "Dependency Map"],
            suggestedPrompts=["Generate RAID report", "Identify project dependencies", "Risk mitigation plan"],
            outputFormats=["markdown", "json", "docx"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Risk Management", "Issue Tracking", "Dependency Management", "Mitigation Planning"],
            collaborators=["program-manager", "delivery-manager"]
        ),
        
        Agent(
            name="Risk Prediction Engine",
            id="risk-prediction",
            role="Predictive Analytics",
            office="intelligence",
            description="Predicts delivery risks including delays, budget overruns, quality issues using ML/AI.",
            systemPrompt="You are a Risk Prediction Engine. Analyze: historical data, current project state, team capacity, technical metrics. Predict: delay probability, budget risk, quality risk, team burnout. Project data: {prompt}",
            recommendedLLM="deepseek:latest",
            supportedModels=["deepseek:latest", "qwen2.5:32b"],
            icon="fa-crystal-ball",
            capabilities=["Delay Prediction", "Budget Risk Forecasting", "Quality Risk Analysis", "Trend Analysis", "Proactive Alerts"],
            quickActions=["Risk Forecast", "Delay Prediction", "Budget Risk", "Quality Risk"],
            suggestedPrompts=["Predict delay probability", "Budget risk analysis", "Quality risk assessment"],
            outputFormats=["markdown", "json"],
            kpis=[{"name": "Prediction Accuracy", "unit": "%"}],
            responsibilities=["Risk Prediction", "Trend Analysis", "Proactive Alerting", "Historical Analysis"],
            collaborators=["raid-manager", "delivery-analytics"]
        ),
        
        Agent(
            name="Resource Manager",
            id="resource-manager",
            role="Resource Management",
            office="intelligence",
            description="Manages resource allocation, utilization, bench forecasting, and hiring needs.",
            systemPrompt="You are a Resource Manager optimizing allocation and utilization. Track: resource allocation, utilization rates, bench status, hiring needs. Forecast: capacity, hiring requirements. Resource context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-people-group",
            capabilities=["Allocation Planning", "Utilization Tracking", "Bench Forecasting", "Hiring Forecasting", "Capacity Planning"],
            quickActions=["Allocation Report", "Utilization Analysis", "Bench Status", "Hiring Forecast"],
            suggestedPrompts=["Resource allocation plan", "Utilization report", "Hiring forecast"],
            outputFormats=["markdown", "json"],
            kpis=[{"name": "Utilization", "unit": "%"}, {"name": "Bench Cost", "unit": "$"}],
            responsibilities=["Resource Allocation", "Utilization Optimization", "Hiring Planning", "Capacity Management"],
            collaborators=["program-manager", "engineering-manager"]
        ),
        
        Agent(
            name="Delivery Analytics",
            id="delivery-analytics",
            role="Business Intelligence",
            office="intelligence",
            description="Generates insights from delivery data: KPIs, forecasts, trends, and root cause analysis.",
            systemPrompt="You are a Delivery Analytics engine. Analyze: historical delivery data, team metrics, project KPIs. Generate: trend analysis, forecasts, root cause analysis, actionable insights. Analytics context: {prompt}",
            recommendedLLM="qwen2.5:32b",
            supportedModels=["qwen2.5:32b", "deepseek:latest"],
            icon="fa-chart-bar",
            capabilities=["KPI Tracking", "Forecasting", "Trend Analysis", "Root Cause Analysis", "Dashboard Generation"],
            quickActions=["KPI Dashboard", "Trend Report", "Forecast", "Root Cause Analysis"],
            suggestedPrompts=["Generate KPI dashboard", "Trend analysis", "Forecast next quarter"],
            outputFormats=["markdown", "json", "ppt"],
            exportOptions=["PDF", "PowerPoint"],
            kpis=[{"name": "Data Quality", "unit": "%"}],
            responsibilities=["Analytics", "Forecasting", "Trend Analysis", "Data Insights", "Performance Tracking"],
            collaborators=["risk-prediction", "program-manager"]
        ),
        
        Agent(
            name="Meeting Intelligence",
            id="meeting-intelligence",
            role="Meeting Management",
            office="intelligence",
            description="Summarizes meetings, extracts action items, tracks decisions, and generates minutes.",
            systemPrompt="You are a Meeting Intelligence system. Process meeting transcripts/notes to: generate summaries, extract action items, document decisions, track attendees. Meeting content: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-comments",
            capabilities=["Meeting Summaries", "Action Item Extraction", "Decision Tracking", "Minutes Generation", "Attendee Management"],
            quickActions=["Meeting Summary", "Action Items", "Decision Log", "Minutes"],
            suggestedPrompts=["Summarize meeting transcript", "Extract action items", "Generate meeting minutes"],
            outputFormats=["markdown", "json", "docx"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Meeting Management", "Action Tracking", "Decision Documentation", "Communication"],
            collaborators=["all"]
        ),
        
        Agent(
            name="Documentation Assistant",
            id="documentation-assistant",
            role="Knowledge Management",
            office="intelligence",
            description="Creates and maintains technical documentation, runbooks, and knowledge bases.",
            systemPrompt="You are a Documentation Assistant. Create: technical documentation, runbooks, knowledge base articles, API docs. Maintain: clarity, completeness, accuracy. Content: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-book",
            capabilities=["Technical Documentation", "Runbook Creation", "API Documentation", "Knowledge Base", "Content Maintenance"],
            quickActions=["Create Documentation", "Runbook Template", "API Docs", "Knowledge Base"],
            suggestedPrompts=["Create deployment runbook", "Write API documentation", "Knowledge base article"],
            outputFormats=["markdown", "docx", "html"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Documentation", "Knowledge Management", "Clarity", "Maintenance", "Training"],
            collaborators=["all"]
        ),
        
        Agent(
            name="Communication Assistant",
            id="communication-assistant",
            role="Communications",
            office="intelligence",
            description="Drafts status reports, client updates, escalations, and executive communications.",
            systemPrompt="You are a Communication Assistant crafting professional communications. Draft: status reports, client emails, leadership updates, escalation templates. Context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-envelope",
            capabilities=["Status Reporting", "Client Communication", "Leadership Updates", "Escalation Management", "Stakeholder Updates"],
            quickActions=["Status Report", "Client Email", "Leadership Update", "Escalation"],
            suggestedPrompts=["Draft status report", "Client update email", "Executive summary"],
            outputFormats=["markdown", "docx"],
            exportOptions=["PDF", "Word"],
            responsibilities=["Communications", "Stakeholder Management", "Escalation Handling", "Clarity", "Professionalism"],
            collaborators=["program-manager", "delivery-manager"]
        ),
        
        # ========== ADMINISTRATION ==========
        Agent(
            name="PMO Director",
            id="pmo",
            role="Program Management Office",
            office="admin",
            description="Oversees portfolio governance, cross-project dependencies, and financial reporting.",
            systemPrompt="You are a PMO Director managing portfolio governance. Generate: portfolio health reports, governance summaries, financial reports, dependency analysis. Portfolio context: {prompt}",
            recommendedLLM="qwen2.5:7b",
            supportedModels=["qwen2.5:7b", "mistral:7b"],
            icon="fa-building",
            capabilities=["Portfolio Management", "Governance Oversight", "Financial Reporting", "Dependency Management", "Portfolio Dashboards"],
            quickActions=["Portfolio Report", "Governance Review", "Financial Analysis", "Dependency Map"],
            suggestedPrompts=["Portfolio health status", "Governance review", "Financial reporting"],
            outputFormats=["markdown", "json", "ppt", "docx"],
            exportOptions=["PDF", "PowerPoint", "Word"],
            kpis=[{"name": "Portfolio Health", "unit": "%"}],
            responsibilities=["Portfolio Governance", "Financial Oversight", "Dependency Management", "Compliance", "Strategic Alignment"],
            collaborators=["program-manager", "executive-copilot"]
        ),
    ]
    
    for agent in agents:
        agent_registry.register(agent)
    
    logger.info(f"DeliveryAI initialized with {len(agents)} specialized agents")
    for office in ["executive", "delivery", "engineering", "intelligence", "admin"]:
        office_agents = [a for a in agents if a.office == office]
        logger.info(f"   {office.title()}: {len(office_agents)} agents")


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

@app.get("/api/agents/by-office/{office}")
def get_agents_by_office(office: str):
    """ Get agents grouped by office tier """
    all_agents = agent_registry.get_all_agents()
    office_agents = [a for a in all_agents if a.office == office.lower()]
    return {
        "office": office.lower(),
        "count": len(office_agents),
        "agents": [a.to_dict() for a in office_agents]
    }

@app.get("/api/organization")
def get_organization_structure():
    """ Get complete DeliveryAI organizational structure """
    all_agents = agent_registry.get_all_agents()
    
    offices = {
        "executive": {"title": "Executive Office", "agents": []},
        "delivery": {"title": "Delivery Office", "agents": []},
        "engineering": {"title": "Engineering Office", "agents": []},
        "intelligence": {"title": "Delivery Intelligence", "agents": []},
        "admin": {"title": "Administration", "agents": []},
    }
    
    for agent in all_agents:
        if agent.office in offices:
            offices[agent.office]["agents"].append({
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "icon": agent.icon,
                "description": agent.description,
            })
    
    return {
        "organization": "DeliveryAI",
        "structure": offices,
        "total_agents": len(all_agents)
    }

@app.get("/api/agent/{agent_id}/details")
def get_agent_details(agent_id: str):
    """ Get complete agent details with all capabilities """
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    return {
        "agent": agent.to_dict(),
        "capabilities": agent.capabilities,
        "quickActions": agent.quickActions,
        "suggestedPrompts": agent.suggestedPrompts,
        "outputFormats": agent.outputFormats,
        "kpis": agent.kpis,
        "collaborators": agent.collaborators,
    }

@app.get("/api/dashboard/health")
def get_dashboard_health():
    """ Get aggregated health metrics for dashboard """
    all_agents = agent_registry.get_all_agents()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "portfolioHealth": 85,  # TODO: calculate from project data
        "sprintHealth": 78,
        "deliveryConfidence": 82,
        "budgetHealth": 90,
        "velocity": 42,  # story points
        "agentCount": len(all_agents),
        "lastUpdate": datetime.now().isoformat(),
    }

@app.get("/api/dashboard/offices")
def get_dashboard_offices():
    """ Get office-level metrics """
    all_agents = agent_registry.get_all_agents()
    
    offices_data = {}
    for office_name in ["executive", "delivery", "engineering", "intelligence", "admin"]:
        agents = [a for a in all_agents if a.office == office_name]
        offices_data[office_name] = {
            "name": office_name.replace("_", " ").title(),
            "agentCount": len(agents),
            "agents": [{"id": a.id, "name": a.name, "role": a.role} for a in agents],
        }
    
    return offices_data

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
async def invoke_agent(agent_id: str, prompt: str = Form(...)):
    """
    Universal agent invocation endpoint
    Works with any registered agent
    """
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    logger.info(f"Invoking agent: {agent.name} ({agent_id})")
    
    # Build prompt from system prompt template
    final_prompt = build_prompt(agent, prompt=prompt)
    
    # Use first supported model
    model = agent.supportedModels[0] if agent.supportedModels else "mistral:7b"
    
    return call_ollama(model, final_prompt)


# ============================================================================
# BACKWARD COMPATIBILITY ENDPOINTS (Maps old routes to new agent system)
# ============================================================================

@app.post("/api/generate_code")
def generate_code(prompt: str = Form(...), mode: str = Form("generate")):
    """DEPRECATED: Use /api/agent/code-assistant/invoke instead"""
    agent = agent_registry.get_agent("code-assistant")
    if mode == "debug":
        prompt_text = f"Debug and fix the following code:\n{prompt}"
    else:
        prompt_text = f"Write clean, well-documented code for: {prompt}"
    
    model = agent.supportedModels[0]
    return call_ollama(model, prompt_text)

@app.post("/api/generate_content")
def generate_content(topic: str = Form(...), style: str = Form("professional")):
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
