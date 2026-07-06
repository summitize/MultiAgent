"""
Data Sync Orchestrator for Delivery Digital Twin

Manages all data source adapters, runs them on schedule, merges results,
and maintains the centralized shared project memory.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from twin_models import (
    SharedProjectMemory, SprintContext, ProgramContext, ResourceContext,
    SecurityContext, SyncResult
)
from twin_adapters import DataSourceAdapter


logger = logging.getLogger(__name__)


class DataSyncOrchestrator:
    """
    Orchestrates data synchronization from multiple sources.
    
    Responsibilities:
    - Initialize and manage adapters
    - Run syncs on configurable schedule
    - Merge data from multiple sources
    - Maintain centralized project memory
    - Handle failures gracefully
    - Provide sync status
    """
    
    def __init__(self, config_file: str):
        """
        Initialize orchestrator with configuration.
        
        Config should be JSON with:
        {
            "organization_id": "...",
            "organization_name": "...",
            "adapters": {
                "jira": { config... },
                "github": { config... },
                ...
            },
            "sync_schedule": {
                "jira": 5,  # minutes
                "github": 10,
                ...
            }
        }
        """
        self.config = self._load_config(config_file)
        self.adapters: Dict[str, DataSourceAdapter] = {}
        self.sync_schedule = self.config.get('sync_schedule', {})
        
        # Shared memory
        self.memory: Optional[SharedProjectMemory] = None
        self.memory_file = self.config.get('memory_file', 'memory.json')
        
        # Sync tracking
        self.sync_history: List[Dict] = []
        self.last_sync_times: Dict[str, datetime] = {}
        self.is_running = False
        
        # Initialize memory
        org_id = self.config.get('organization_id', 'default-org')
        org_name = self.config.get('organization_name', 'Default Organization')
        self.memory = SharedProjectMemory.create_empty(org_id, org_name)
        
        logger.info("✅ DataSyncOrchestrator initialized")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found. Using defaults.")
            return {
                'organization_id': 'default-org',
                'organization_name': 'Default Organization',
                'adapters': {},
                'sync_schedule': {}
            }
    
    def register_adapter(self, name: str, adapter: DataSourceAdapter):
        """Register a data source adapter"""
        self.adapters[name] = adapter
        logger.info(f"Registered adapter: {name}")
    
    async def initialize(self) -> bool:
        """
        Initialize all adapters.
        Connect to all data sources to verify configuration.
        """
        logger.info("Initializing adapters...")
        
        success_count = 0
        for name, adapter in self.adapters.items():
            try:
                if await adapter.connect():
                    logger.info(f"✅ {name} adapter connected")
                    success_count += 1
                else:
                    logger.warning(f"⚠️  {name} adapter failed to connect")
            except Exception as e:
                logger.error(f"❌ Error initializing {name} adapter: {e}")
        
        if success_count == 0:
            logger.error("No adapters could be initialized!")
            return False
        
        logger.info(f"✅ {success_count}/{len(self.adapters)} adapters ready")
        return True
    
    async def start(self):
        """
        Start background sync loop.
        Runs adapters on their configured schedule.
        """
        if self.is_running:
            logger.warning("Sync orchestrator already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting sync orchestrator...")
        
        while self.is_running:
            await self._check_and_sync()
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def stop(self):
        """Stop background sync loop"""
        self.is_running = False
        
        # Disconnect all adapters
        for adapter in self.adapters.values():
            await adapter.disconnect()
        
        logger.info("Sync orchestrator stopped")
    
    async def _check_and_sync(self):
        """Check if any adapter should be synced based on schedule"""
        now = datetime.now()
        
        for adapter_name, adapter in self.adapters.items():
            last_sync = self.last_sync_times.get(adapter_name)
            interval_minutes = self.sync_schedule.get(adapter_name, 60)
            
            # Check if sync is needed
            if last_sync is None or (now - last_sync).total_seconds() > interval_minutes * 60:
                await self.sync_adapter(adapter_name)
    
    async def sync_adapter(self, adapter_name: str) -> Optional[SyncResult]:
        """Sync single adapter"""
        if adapter_name not in self.adapters:
            logger.error(f"Adapter not found: {adapter_name}")
            return None
        
        adapter = self.adapters[adapter_name]
        
        logger.info(f"🔄 Syncing {adapter_name}...")
        
        try:
            result = await self._fetch_from_adapter(adapter)
            
            if result.success:
                # Merge into shared memory
                await self._merge_into_memory(result)
                self.last_sync_times[adapter_name] = datetime.now()
                logger.info(f"✅ {adapter_name} sync complete: {result.records_updated} updates")
            else:
                logger.warning(f"⚠️  {adapter_name} sync failed: {result.error}")
            
            # Record in history
            self.sync_history.append(result.to_dict())
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error syncing {adapter_name}: {e}")
            return None
    
    async def sync_all(self) -> Dict[str, SyncResult]:
        """
        Run all adapters in parallel.
        Merge all results into shared memory.
        """
        logger.info("🔄 Syncing ALL adapters...")
        
        tasks = [
            self.sync_adapter(name)
            for name in self.adapters.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert results to dict
        result_dict = {}
        for adapter_name, result in zip(self.adapters.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Exception syncing {adapter_name}: {result}")
                result_dict[adapter_name] = None
            else:
                result_dict[adapter_name] = result
        
        logger.info("✅ All adapters synced")
        
        return result_dict
    
    async def _fetch_from_adapter(self, adapter: DataSourceAdapter) -> SyncResult:
        """Fetch data from single adapter"""
        result = SyncResult(
            source_name=adapter.source_name,
            success=False,
        )
        
        try:
            # Fetch all data types
            sprint_data = await adapter.fetch_sprint_data(
                self.config.get('current_sprint_id', 'default')
            )
            program_data = await adapter.fetch_program_data(
                self.config.get('current_program_id', 'default')
            )
            resource_data = await adapter.fetch_resource_data()
            security_data = await adapter.fetch_security_data()
            
            result.sprint_data = sprint_data
            result.program_data = program_data
            result.resource_data = resource_data
            security_data = security_data
            
            result.records_processed = 1
            result.records_updated = 1 if any([sprint_data, program_data, resource_data, security_data]) else 0
            result.success = True
            
        except Exception as e:
            result.error = str(e)
            result.success = False
        
        return result
    
    async def _merge_into_memory(self, result: SyncResult):
        """Merge adapter results into shared project memory"""
        if result.sprint_data:
            self.memory.current_sprint = result.sprint_data
            logger.debug(f"Updated sprint: {result.sprint_data.sprint_name}")
        
        if result.program_data:
            self.memory.current_program = result.program_data
            logger.debug(f"Updated program: {result.program_data.program_name}")
        
        if result.resource_data:
            self.memory.resources = result.resource_data
            logger.debug(f"Updated {len(result.resource_data)} resources")
        
        if result.security_data:
            self.memory.security_context = result.security_data
            logger.debug("Updated security context")
        
        # Update metadata
        self.memory.last_updated = datetime.now()
        self.memory.updated_by_agent = result.source_name
        
        # Validate consistency
        self._validate_memory_consistency()
        
        # Save to disk
        await self.save_memory()
    
    def _validate_memory_consistency(self):
        """Check for conflicts in shared memory"""
        if not self.memory.current_sprint:
            return
        
        # Validate that resources match allocations
        allocated_capacity = sum(r.hours_allocated for r in self.memory.resources)
        if allocated_capacity > 200 and len(self.memory.resources) > 0:
            logger.warning(f"⚠️  High total allocation: {allocated_capacity} hours")
        
        # Validate dependencies
        for dep in self.memory.dependencies:
            if dep.risk_level not in ['low', 'medium', 'high']:
                logger.warning(f"Invalid risk level: {dep.risk_level}")
    
    async def save_memory(self):
        """Persist shared memory to disk"""
        try:
            with open(self.memory_file, 'w') as f:
                f.write(self.memory.to_json())
            logger.debug(f"Memory saved to {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    async def load_memory(self):
        """Load shared memory from disk"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            # Deserialize - simplified, would need full implementation
            self.memory = SharedProjectMemory.create_empty(
                data.get('organization_id'),
                data.get('organization_name')
            )
            logger.info(f"Memory loaded from {self.memory_file}")
        except FileNotFoundError:
            logger.info("Memory file not found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
    
    def get_memory(self) -> SharedProjectMemory:
        """Get current shared memory (read-only for agents)"""
        return self.memory
    
    def get_sync_status(self) -> Dict:
        """Get status of all adapters"""
        return {
            'is_running': self.is_running,
            'adapters': {
                name: {
                    'connected': adapter.is_connected,
                    'last_sync': self.last_sync_times.get(name),
                    'schedule_minutes': self.sync_schedule.get(name, 'N/A')
                }
                for name, adapter in self.adapters.items()
            },
            'memory_updated': self.memory.last_updated.isoformat() if self.memory else None,
            'sync_history_count': len(self.sync_history),
        }
    
    def get_sync_history(self, limit: int = 20) -> List[Dict]:
        """Get recent sync history"""
        return self.sync_history[-limit:]


# ============================================================================
# MEMORY SERVICE (Thread-safe access to shared memory)
# ============================================================================

class MemoryService:
    """
    Thread-safe service for managing shared project memory.
    Provides atomic reads/writes and versioning.
    """
    
    def __init__(self, memory: SharedProjectMemory):
        self.memory = memory
        self.lock = asyncio.Lock()
        self.version_history: List[Dict] = []
    
    async def get_memory(self) -> SharedProjectMemory:
        """Get current shared memory"""
        async with self.lock:
            return self.memory
    
    async def update_memory(
        self,
        agent_id: str,
        updates: Dict,
        reason: str
    ) -> SharedProjectMemory:
        """
        Update shared memory with explicit agent and reason.
        All updates are logged for audit trail.
        """
        async with self.lock:
            # Apply updates
            if 'current_sprint' in updates and updates['current_sprint']:
                self.memory.current_sprint = updates['current_sprint']
            
            if 'current_program' in updates and updates['current_program']:
                self.memory.current_program = updates['current_program']
            
            if 'resources' in updates and updates['resources']:
                self.memory.resources = updates['resources']
            
            # Update metadata
            self.memory.last_updated = datetime.now()
            self.memory.updated_by_agent = agent_id
            
            # Record version
            self.version_history.append({
                'timestamp': datetime.now().isoformat(),
                'agent_id': agent_id,
                'reason': reason,
                'version': len(self.version_history) + 1,
            })
            
            return self.memory
    
    async def get_memory_at_time(self, timestamp: datetime) -> Optional[SharedProjectMemory]:
        """
        Get memory state at specific point in time.
        Enables replay of agent reasoning.
        """
        # Find closest version before timestamp
        matching_versions = [
            v for v in self.version_history
            if datetime.fromisoformat(v['timestamp']) <= timestamp
        ]
        
        if not matching_versions:
            return None
        
        latest_version = matching_versions[-1]
        return self.memory  # Simplified - would need full history tracking
    
    def get_version_history(self, limit: int = 50) -> List[Dict]:
        """Get recent update history"""
        return self.version_history[-limit:]
