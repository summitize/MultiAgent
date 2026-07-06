"""
Delivery Digital Twin Integration

This module integrates the Digital Twin components into the MultiAgent platform.
Exposes twin data and insights through FastAPI endpoints.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from twin_models import SharedProjectMemory, SprintContext, ProgramContext, Risk, RiskReport
from twin_orchestrator import DataSyncOrchestrator, MemoryService
from twin_adapters import JiraAdapter, GitHubAdapter, AzureDevOpsAdapter


logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS FOR API
# ============================================================================

class TwinStatusResponse(BaseModel):
    """Response for twin status endpoint"""
    status: str
    is_running: bool
    adapters_connected: int
    total_adapters: int
    memory_updated: str
    sync_history_count: int


class ContextResponse(BaseModel):
    """Response for context data"""
    sprint: Optional[Dict]
    program: Optional[Dict]
    resources_count: int
    security_findings_count: int
    last_updated: str


class RiskAlertResponse(BaseModel):
    """Response for risk detection"""
    risks_detected: int
    critical_risks: int
    high_risks: int
    medium_risks: int
    risks: List[Dict]


class SyncResponse(BaseModel):
    """Response for sync operation"""
    success: bool
    adapters_synced: int
    timestamp: str


# ============================================================================
# DIGITAL TWIN CONTROLLER
# ============================================================================

class DeliveryDigitalTwin:
    """
    Main controller for the Delivery Digital Twin.
    Manages all operations and coordinates with adapters.
    """
    
    def __init__(self, config_file: str = 'twin_config.json'):
        self.orchestrator = DataSyncOrchestrator(config_file)
        self.memory_service: Optional[MemoryService] = None
        self.is_initialized = False
        self.background_task = None
    
    async def initialize(self) -> bool:
        """Initialize twin with all adapters"""
        logger.info("🚀 Initializing Delivery Digital Twin...")
        
        try:
            # Register adapters from config
            adapters_config = self.orchestrator.config.get('adapters', {})
            
            # Jira
            if adapters_config.get('jira', {}).get('enabled'):
                jira_adapter = JiraAdapter(adapters_config['jira'])
                self.orchestrator.register_adapter('jira', jira_adapter)
            
            # GitHub
            if adapters_config.get('github', {}).get('enabled'):
                github_adapter = GitHubAdapter(adapters_config['github'])
                self.orchestrator.register_adapter('github', github_adapter)
            
            # Azure DevOps
            if adapters_config.get('azure_devops', {}).get('enabled'):
                azdo_adapter = AzureDevOpsAdapter(adapters_config['azure_devops'])
                self.orchestrator.register_adapter('azure_devops', azdo_adapter)
            
            # Initialize adapters
            if not await self.orchestrator.initialize():
                logger.warning("⚠️  Some adapters failed to initialize")
            
            # Initialize memory service
            self.memory_service = MemoryService(self.orchestrator.memory)
            
            self.is_initialized = True
            logger.info("✅ Digital Twin initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Digital Twin: {e}")
            self.is_initialized = False
            return False
    
    async def start(self):
        """Start the digital twin (background sync loop)"""
        if not self.is_initialized:
            logger.error("Twin not initialized. Call initialize() first.")
            return
        
        if self.background_task:
            logger.warning("Twin already running")
            return
        
        logger.info("Starting Digital Twin sync loop...")
        self.background_task = asyncio.create_task(self.orchestrator.start())
    
    async def stop(self):
        """Stop the digital twin"""
        if self.background_task:
            await self.orchestrator.stop()
            self.background_task.cancel()
            self.background_task = None
            logger.info("Digital Twin stopped")
    
    async def sync_now(self) -> SyncResponse:
        """Manually trigger sync of all adapters"""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Twin not initialized")
        
        logger.info("🔄 Manual sync triggered...")
        results = await self.orchestrator.sync_all()
        
        success_count = sum(1 for r in results.values() if r and r.success)
        
        return SyncResponse(
            success=success_count > 0,
            adapters_synced=success_count,
            timestamp=datetime.now().isoformat()
        )
    
    async def get_status(self) -> TwinStatusResponse:
        """Get twin status"""
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Twin not initialized")
        
        status = self.orchestrator.get_sync_status()
        
        connected_count = sum(
            1 for adapter_info in status['adapters'].values()
            if adapter_info['connected']
        )
        
        return TwinStatusResponse(
            status="running" if status['is_running'] else "stopped",
            is_running=status['is_running'],
            adapters_connected=connected_count,
            total_adapters=len(self.orchestrator.adapters),
            memory_updated=status.get('memory_updated', 'never'),
            sync_history_count=status.get('sync_history_count', 0)
        )
    
    async def get_context(self) -> ContextResponse:
        """Get current project context"""
        if not self.memory_service:
            raise HTTPException(status_code=503, detail="Twin not ready")
        
        memory = await self.memory_service.get_memory()
        
        security_findings = 0
        if memory.security_context:
            security_findings = (
                len(memory.security_context.vulnerabilities) +
                len(memory.security_context.policy_violations) +
                len(memory.security_context.dependency_issues)
            )
        
        return ContextResponse(
            sprint=memory.current_sprint.to_dict() if memory.current_sprint else None,
            program=memory.current_program.to_dict() if memory.current_program else None,
            resources_count=len(memory.resources),
            security_findings_count=security_findings,
            last_updated=memory.last_updated.isoformat()
        )
    
    async def get_risks(self) -> RiskAlertResponse:
        """
        Get detected risks.
        This will be populated by RiskDetectionEngine in next phase.
        """
        if not self.memory_service:
            raise HTTPException(status_code=503, detail="Twin not ready")
        
        memory = await self.memory_service.get_memory()
        
        # For now, return empty risks
        # In Phase 2, this will be populated by RiskDetectionEngine
        
        return RiskAlertResponse(
            risks_detected=0,
            critical_risks=0,
            high_risks=0,
            medium_risks=0,
            risks=[]
        )
    
    async def get_memory_snapshot(self) -> Dict:
        """Get full memory snapshot (for debugging)"""
        if not self.memory_service:
            raise HTTPException(status_code=503, detail="Twin not ready")
        
        memory = await self.memory_service.get_memory()
        return memory.to_dict()
    
    async def get_sync_history(self, limit: int = 20) -> List[Dict]:
        """Get sync operation history"""
        return self.orchestrator.get_sync_history(limit)


# ============================================================================
# FASTAPI ROUTES
# ============================================================================

def create_twin_routes(twin: DeliveryDigitalTwin) -> APIRouter:
    """Create FastAPI router for twin endpoints"""
    
    router = APIRouter(prefix="/api/twin", tags=["digital-twin"])
    
    @router.get("/status", response_model=TwinStatusResponse)
    async def get_twin_status():
        """Get status of the Delivery Digital Twin"""
        return await twin.get_status()
    
    @router.get("/context", response_model=ContextResponse)
    async def get_twin_context():
        """Get current project context from shared memory"""
        return await twin.get_context()
    
    @router.get("/risks", response_model=RiskAlertResponse)
    async def get_detected_risks():
        """Get detected risks and proactive alerts"""
        return await twin.get_risks()
    
    @router.post("/sync", response_model=SyncResponse)
    async def sync_all_adapters():
        """Manually trigger sync of all data sources"""
        return await twin.sync_now()
    
    @router.get("/memory", response_model=Dict)
    async def get_memory_snapshot():
        """Get full memory snapshot (debug endpoint)"""
        return await twin.get_memory_snapshot()
    
    @router.get("/sync-history")
    async def get_sync_history(limit: int = 20):
        """Get recent sync operation history"""
        return await twin.get_sync_history(limit)
    
    @router.get("/health")
    async def twin_health_check():
        """Health check for digital twin"""
        status = await twin.get_status()
        return {
            "healthy": status.is_running,
            "adapters_connected": status.adapters_connected,
            "timestamp": datetime.now().isoformat()
        }
    
    return router


# ============================================================================
# INITIALIZATION HELPER
# ============================================================================

async def initialize_twin() -> DeliveryDigitalTwin:
    """
    Initialize the Delivery Digital Twin.
    Call this during application startup.
    """
    logger.info("=" * 60)
    logger.info("DELIVERY DIGITAL TWIN - INITIALIZATION")
    logger.info("=" * 60)
    
    twin = DeliveryDigitalTwin('twin_config.json')
    
    if await twin.initialize():
        logger.info("✅ Twin ready for use")
        return twin
    else:
        logger.warning("⚠️  Twin initialized but some adapters are offline")
        return twin


async def start_twin(twin: DeliveryDigitalTwin):
    """
    Start the digital twin background sync.
    Call this during application startup.
    """
    try:
        await twin.start()
        logger.info("🚀 Digital Twin sync loop started")
    except Exception as e:
        logger.error(f"Failed to start twin: {e}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Initialize and run twin
    async def main():
        twin = await initialize_twin()
        
        # Run sync once
        logger.info("\n" + "=" * 60)
        logger.info("Running initial sync...")
        logger.info("=" * 60 + "\n")
        
        result = await twin.sync_now()
        logger.info(f"Sync result: {result}")
        
        # Get status
        status = await twin.get_status()
        logger.info(f"Twin status: {status}")
        
        # Get context
        context = await twin.get_context()
        logger.info(f"Context: {context}")
        
        await twin.stop()
    
    asyncio.run(main())
