"""
PHASE 3: Agent Collaboration Engine

Enables autonomous inter-agent communication with transparent reasoning.
Agents can request information/actions from each other with audit trails.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
import json

from twin_models import CollaborationRequest, CollaborationResponse


logger = logging.getLogger(__name__)


# ============================================================================
# AGENT REGISTRY
# ============================================================================

class AgentRegistry:
    """Registry of all agents and their capabilities"""
    
    def __init__(self):
        self.agents: Dict[str, Dict] = {}
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        handler: Callable
    ):
        """Register an agent and its handler"""
        self.agents[agent_id] = {
            'name': name,
            'capabilities': capabilities,
            'handler': handler,
            'registered_at': datetime.now().isoformat(),
        }
        logger.info(f"✅ Agent registered: {agent_id} ({name})")
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent info"""
        return self.agents.get(agent_id)
    
    def get_agents_with_capability(self, capability: str) -> List[str]:
        """Find agents that can handle capability"""
        return [
            agent_id for agent_id, info in self.agents.items()
            if capability in info['capabilities']
        ]


# ============================================================================
# COLLABORATION REQUEST HANDLER
# ============================================================================

class CollaborationOrchestrator:
    """
    Manages inter-agent communication.
    Handles request routing, response collection, and audit trails.
    """
    
    def __init__(self, agent_registry: AgentRegistry):
        self.registry = agent_registry
        self.requests: Dict[str, CollaborationRequest] = {}
        self.responses: Dict[str, CollaborationResponse] = {}
        self.audit_log: List[Dict] = []
    
    async def create_request(
        self,
        from_agent_id: str,
        request_type: str,
        context: Dict,
        priority: str = "normal",
        deadline: Optional[datetime] = None,
    ) -> CollaborationRequest:
        """
        Create and route a collaboration request.
        
        Request types:
        - ask_for_input: "Need data from you"
        - request_review: "Review my decision"
        - share_status: "Here's my status"
        - request_action: "Take this action"
        - share_insight: "Here's what I discovered"
        """
        
        request = CollaborationRequest(
            from_agent_id=from_agent_id,
            request_type=request_type,
            priority=priority,
            context=context,
            deadline=deadline,
        )
        
        self.requests[request.id] = request
        
        # Log request creation
        self._log_audit(
            event='request_created',
            request_id=request.id,
            from_agent=from_agent_id,
            request_type=request_type,
            priority=priority,
        )
        
        logger.info(f"📤 Request created: {request.id} ({request_type}) from {from_agent_id}")
        
        return request
    
    async def submit_response(
        self,
        request_id: str,
        to_agent_id: str,
        status: str,  # accepted, completed, rejected
        response_data: Dict,
        reasoning: str,
        confidence: float = 0.8,
    ) -> CollaborationResponse:
        """
        Submit a response to a collaboration request.
        """
        
        request = self.requests.get(request_id)
        if not request:
            logger.error(f"Request not found: {request_id}")
            return None
        
        response = CollaborationResponse(
            request_id=request_id,
            status=status,
            response_data=response_data,
            reasoning=reasoning,
            confidence=confidence,
        )
        
        self.responses[request_id] = response
        
        # Update request status
        request.status = status
        request.response = response_data
        request.reasoning = reasoning
        request.completed_at = datetime.now()
        
        # Log response
        self._log_audit(
            event='response_submitted',
            request_id=request_id,
            from_agent=request.from_agent_id,
            to_agent=to_agent_id,
            status=status,
            confidence=confidence,
        )
        
        logger.info(f"📥 Response: {request_id} → {status} (confidence: {confidence:.0%})")
        
        return response
    
    async def request_and_wait(
        self,
        from_agent_id: str,
        to_agent_id: str,
        request_type: str,
        context: Dict,
        timeout_seconds: int = 30,
    ) -> Optional[CollaborationResponse]:
        """
        Request information from another agent and wait for response.
        This is a synchronous pattern for agent coordination.
        """
        
        # Check if target agent exists
        target_agent = self.registry.get_agent(to_agent_id)
        if not target_agent:
            logger.error(f"Target agent not found: {to_agent_id}")
            return None
        
        # Create request
        request = await self.create_request(
            from_agent_id=from_agent_id,
            request_type=request_type,
            context=context,
            priority="high",
            deadline=datetime.now() + timedelta(seconds=timeout_seconds),
        )
        
        # Route to handler
        handler = target_agent['handler']
        
        try:
            # Call handler with request
            logger.info(f"🔄 Routing request {request.id} to {to_agent_id}")
            
            response = await handler(request)
            
            if response:
                await self.submit_response(
                    request_id=request.id,
                    to_agent_id=to_agent_id,
                    status='completed',
                    response_data=response.get('data', {}),
                    reasoning=response.get('reasoning', ''),
                    confidence=response.get('confidence', 0.8),
                )
                
                return self.responses.get(request.id)
            else:
                logger.warning(f"Handler returned None for request {request.id}")
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"Request {request.id} timed out after {timeout_seconds}s")
            request.status = 'timeout'
            return None
        except Exception as e:
            logger.error(f"Error handling request {request.id}: {e}")
            request.status = 'error'
            return None
    
    def get_audit_trail(self, request_id: str) -> List[Dict]:
        """Get audit trail for specific request"""
        request = self.requests.get(request_id)
        if not request:
            return []
        
        trail = [entry for entry in self.audit_log if entry['request_id'] == request_id]
        return trail
    
    def get_collaboration_history(self, agent_id: str, limit: int = 50) -> List[Dict]:
        """Get collaboration history for agent"""
        history = [
            entry for entry in self.audit_log
            if entry.get('from_agent') == agent_id or entry.get('to_agent') == agent_id
        ]
        return history[-limit:]
    
    def _log_audit(self, **kwargs):
        """Add entry to audit log"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.audit_log.append(entry)
        logger.debug(f"Audit: {entry}")
    
    def export_audit_log(self) -> str:
        """Export audit log as JSON"""
        return json.dumps(self.audit_log, indent=2, default=str)


# ============================================================================
# COLLABORATION PATTERNS
# ============================================================================

class CollaborationPatterns:
    """
    Common inter-agent communication patterns.
    """
    
    @staticmethod
    async def ask_for_status(
        orchestrator: CollaborationOrchestrator,
        from_agent: str,
        to_agent: str,
        subject: str,  # What to get status on
    ) -> Optional[Dict]:
        """
        One agent asks another for status update.
        
        Example:
        - ExecutiveAgent asks ProjectManagerAgent for sprint status
        - ProjectManagerAgent asks DeveloperAgent for task status
        """
        
        request = await orchestrator.create_request(
            from_agent_id=from_agent,
            request_type='ask_for_input',
            context={'query': f'What is status of {subject}?'},
        )
        
        response = await orchestrator.request_and_wait(
            from_agent_id=from_agent,
            to_agent_id=to_agent,
            request_type='ask_for_input',
            context={'subject': subject},
        )
        
        return response.response_data if response else None
    
    @staticmethod
    async def request_decision(
        orchestrator: CollaborationOrchestrator,
        from_agent: str,
        to_agent: str,
        decision_context: Dict,
    ) -> Optional[Dict]:
        """
        One agent asks another to make a decision.
        
        Example:
        - RiskDetectionAgent asks ExecutiveAgent if we should delay release
        - ProjectManagerAgent asks ProductManagerAgent if scope should change
        """
        
        response = await orchestrator.request_and_wait(
            from_agent_id=from_agent,
            to_agent_id=to_agent,
            request_type='request_review',
            context=decision_context,
        )
        
        return {
            'decision': response.response_data.get('decision') if response else None,
            'reasoning': response.reasoning if response else None,
            'confidence': response.confidence if response else 0,
        }
    
    @staticmethod
    async def share_insight(
        orchestrator: CollaborationOrchestrator,
        from_agent: str,
        to_agent: str,
        insight: str,
        metadata: Dict = None,
    ) -> CollaborationRequest:
        """
        One agent shares an insight/finding with another.
        
        Example:
        - RiskDetectionEngine shares "82% spillover probability" with ProjectManagerAgent
        - SecurityAgent shares "12 unfixed vulnerabilities" with ExecutiveAgent
        """
        
        request = await orchestrator.create_request(
            from_agent_id=from_agent,
            request_type='share_insight',
            context={
                'insight': insight,
                'metadata': metadata or {},
            },
            priority='high',
        )
        
        return request


# ============================================================================
# EXAMPLE AGENT HANDLERS
# ============================================================================

async def project_manager_agent_handler(request: CollaborationRequest) -> Dict:
    """Example ProjectManagerAgent handler"""
    
    if request.request_type == 'ask_for_input':
        # Return sprint status
        return {
            'data': {
                'sprint_name': 'Sprint 42',
                'status': 'in_progress',
                'days_remaining': 3,
                'completion_percentage': 75,
            },
            'reasoning': 'Retrieved from current sprint context',
            'confidence': 0.95,
        }
    
    elif request.request_type == 'request_review':
        # Make a decision
        return {
            'data': {'decision': 'approve', 'action': 'continue_sprint'},
            'reasoning': 'Velocity trend is positive, no blockers detected',
            'confidence': 0.85,
        }
    
    return None


async def executive_agent_handler(request: CollaborationRequest) -> Dict:
    """Example ExecutiveAgent handler"""
    
    if request.request_type == 'request_review':
        decision_context = request.context
        
        # Make executive decision based on risks
        if decision_context.get('spillover_probability', 0) > 0.8:
            return {
                'data': {'decision': 'delay_release', 'reason': 'high_spillover_risk'},
                'reasoning': 'High spillover probability detected - recommend deferring release',
                'confidence': 0.9,
            }
        else:
            return {
                'data': {'decision': 'proceed', 'reason': 'acceptable_risk'},
                'reasoning': 'Spillover risk within acceptable range',
                'confidence': 0.8,
            }
    
    return None


async def risk_agent_handler(request: CollaborationRequest) -> Dict:
    """Example RiskAgent handler"""
    
    if request.request_type == 'ask_for_input':
        # Return risk summary
        return {
            'data': {
                'critical_risks': 2,
                'high_risks': 5,
                'top_risk': 'spillover_probability_82%',
            },
            'reasoning': 'Analyzed current memory state with all 6 detectors',
            'confidence': 0.92,
        }
    
    return None


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_agent_collaboration() -> tuple[AgentRegistry, CollaborationOrchestrator]:
    """Initialize collaboration system with agents"""
    
    registry = AgentRegistry()
    orchestrator = CollaborationOrchestrator(registry)
    
    # Register agents
    registry.register_agent(
        agent_id='project-manager',
        name='Project Manager Agent',
        capabilities=['ask_for_input', 'request_review', 'make_decision'],
        handler=project_manager_agent_handler,
    )
    
    registry.register_agent(
        agent_id='executive',
        name='Executive Agent',
        capabilities=['request_review', 'make_decision', 'escalate'],
        handler=executive_agent_handler,
    )
    
    registry.register_agent(
        agent_id='risk-agent',
        name='Risk Detection Agent',
        capabilities=['ask_for_input', 'share_insight', 'detect_risk'],
        handler=risk_agent_handler,
    )
    
    logger.info("✅ Agent collaboration system initialized")
    
    return registry, orchestrator
