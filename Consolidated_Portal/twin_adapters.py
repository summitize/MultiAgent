"""
Data Source Adapters for Delivery Digital Twin

Each adapter fetches data from a specific source (Jira, Azure DevOps, GitHub, etc)
and normalizes it into the unified context models.

Uses adapter pattern for extensibility - new sources can be added without changing core code.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass

from twin_models import (
    SprintContext, ProgramContext, ResourceContext, SecurityContext,
    StoryStatus, BugStatus, SecurityFinding, Severity, SyncResult,
    ReleaseInfo, DependencyInfo
)


logger = logging.getLogger(__name__)


# ============================================================================
# BASE ADAPTER
# ============================================================================

class DataSourceAdapter(ABC):
    """
    Base class for all data source adapters.
    Each adapter implements connection and data fetching for a specific source.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with configuration.
        Config includes connection details, API keys, etc.
        """
        self.config = config
        self.source_name = self.__class__.__name__.replace('Adapter', '').lower()
        self.last_sync_time: Optional[datetime] = None
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Verify connectivity to data source.
        Return True if connection successful.
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Clean up connection"""
        pass
    
    @abstractmethod
    async def fetch_sprint_data(self, sprint_id: str) -> Optional[SprintContext]:
        """Fetch and normalize sprint data"""
        pass
    
    @abstractmethod
    async def fetch_program_data(self, program_id: str) -> Optional[ProgramContext]:
        """Fetch and normalize program data"""
        pass
    
    @abstractmethod
    async def fetch_resource_data(self) -> List[ResourceContext]:
        """Fetch and normalize resource/team member data"""
        pass
    
    @abstractmethod
    async def fetch_security_data(self) -> Optional[SecurityContext]:
        """Fetch security scan results"""
        pass
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """Get timestamp of last successful sync"""
        return self.last_sync_time
    
    def _update_last_sync(self):
        """Update last sync timestamp"""
        self.last_sync_time = datetime.now()


# ============================================================================
# JIRA ADAPTER
# ============================================================================

class JiraAdapter(DataSourceAdapter):
    """
    Fetches data from Jira Cloud/Server.
    
    Provides:
    - Sprint planning and tracking data
    - Story points, velocity calculations
    - Issue hierarchies and relationships
    - Team composition
    - Issue blockers and dependencies
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('jira_url')
        self.api_token = config.get('jira_token')
        self.board_id = config.get('board_id')
        self.jira_client = None
    
    async def connect(self) -> bool:
        """Verify Jira connection"""
        try:
            # Import here to avoid hard dependency
            from jira import JIRA
            
            self.jira_client = JIRA(
                server=self.base_url,
                basic_auth=('api', self.api_token)
            )
            
            # Test connection
            self.jira_client.myself()
            self.is_connected = True
            logger.info(f"✅ Connected to Jira: {self.base_url}")
            return True
            
        except ImportError:
            logger.warning("jira-python not installed. Install with: pip install jira")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Jira: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close Jira connection"""
        if self.jira_client:
            self.jira_client = None
            self.is_connected = False
    
    async def fetch_sprint_data(self, sprint_id: str) -> Optional[SprintContext]:
        """
        Fetch sprint data from Jira.
        
        Returns:
        - Current sprint status
        - Stories with points and status
        - Blockers and dependencies
        - Team velocity
        """
        if not self.is_connected:
            return None
        
        try:
            # GET /rest/api/3/board/{boardId}/sprint/{sprintId}
            sprint = self.jira_client.sprint(sprint_id)
            
            # GET /rest/api/3/search?jql=sprint={sprintId}
            jql = f"sprint = {sprint_id}"
            issues = self.jira_client.search_issues(jql, maxResults=1000)
            
            # Build SprintContext
            sprint_context = SprintContext(
                sprint_id=sprint.id,
                sprint_name=sprint.name,
                program_id=self.board_id,
                start_date=datetime.fromisoformat(sprint.startDate.replace('Z', '+00:00')),
                end_date=datetime.fromisoformat(sprint.endDate.replace('Z', '+00:00')),
                goal=sprint.goal or "No goal defined",
                planned_velocity=self._extract_planned_velocity(sprint),
                team_size=self._extract_team_size(issues),
                team_members=self._extract_team_members(issues),
                last_updated_by_source="jira",
            )
            
            # Extract stories and bugs
            sprint_context.stories = self._extract_stories(issues)
            sprint_context.bugs = self._extract_bugs(issues)
            
            # Calculate metrics
            sprint_context.remaining_points = sum(
                s.story_points for s in sprint_context.stories 
                if s.status not in ['done', 'closed']
            )
            sprint_context.completed_points = sum(
                s.story_points for s in sprint_context.stories 
                if s.status in ['done', 'closed']
            )
            sprint_context.in_progress_points = sum(
                s.story_points for s in sprint_context.stories 
                if s.status in ['in_progress', 'review']
            )
            
            # Calculate velocity and trends
            sprint_context.current_velocity = sprint_context.completed_points
            sprint_context.days_remaining = (sprint_context.end_date - datetime.now()).days
            if sprint_context.planned_velocity > 0:
                sprint_context.completion_percentage = (
                    sprint_context.completed_points / sprint_context.planned_velocity * 100
                )
            
            self._update_last_sync()
            return sprint_context
            
        except Exception as e:
            logger.error(f"Failed to fetch sprint data from Jira: {e}")
            return None
    
    async def fetch_program_data(self, program_id: str) -> Optional[ProgramContext]:
        """
        Fetch program/epic data from Jira.
        
        Aggregates data from multiple sprints.
        """
        if not self.is_connected:
            return None
        
        try:
            # Get all active sprints on board
            board_sprints = self.jira_client.sprints(self.board_id, state='active')
            
            program_context = ProgramContext(
                program_id=program_id,
                program_name=f"Board: {self.board_id}",
                program_manager_id="unknown",  # Not available in basic Jira API
                start_date=datetime.now() - timedelta(days=90),
                planned_end_date=datetime.now() + timedelta(days=90),
                total_planned_velocity=sum(
                    s.goal_estimate or 0 for s in board_sprints
                ),
                average_velocity=self._calculate_average_velocity(board_sprints),
                delivery_confidence=self._calculate_delivery_confidence(board_sprints),
            )
            
            self._update_last_sync()
            return program_context
            
        except Exception as e:
            logger.error(f"Failed to fetch program data from Jira: {e}")
            return None
    
    async def fetch_resource_data(self) -> List[ResourceContext]:
        """Fetch team members and their utilization"""
        if not self.is_connected:
            return []
        
        try:
            resources = []
            
            # Get all assignees on board
            jql = f"project = {self.board_id}"
            issues = self.jira_client.search_issues(jql, maxResults=1000)
            
            assignees = set(
                issue.fields.assignee.name 
                for issue in issues 
                if issue.fields.assignee
            )
            
            for assignee_name in assignees:
                resource = ResourceContext(
                    resource_id=assignee_name,
                    name=assignee_name,
                    role="Developer",  # Default, would be fetched from custom field
                    team="Default",
                    total_hours_available=40.0,  # Standard sprint week
                    hours_allocated=self._calculate_hours_allocated(assignee_name, issues),
                )
                resource.utilization = min(100, (resource.hours_allocated / resource.total_hours_available) * 100)
                resources.append(resource)
            
            self._update_last_sync()
            return resources
            
        except Exception as e:
            logger.error(f"Failed to fetch resource data from Jira: {e}")
            return []
    
    async def fetch_security_data(self) -> Optional[SecurityContext]:
        """
        Jira doesn't have native security scanning.
        This would require integration with external tools (GitHub, Snyk, etc).
        """
        logger.warning("Jira adapter does not provide security data. Use GitHub adapter instead.")
        return None
    
    # Helper methods
    
    def _extract_planned_velocity(self, sprint) -> float:
        """Extract planned velocity from sprint"""
        return getattr(sprint, 'goal_estimate', 0.0) or 0.0
    
    def _extract_team_size(self, issues) -> int:
        """Count unique team members"""
        assignees = set(
            issue.fields.assignee.name 
            for issue in issues 
            if issue.fields.assignee
        )
        return len(assignees)
    
    def _extract_team_members(self, issues) -> List[str]:
        """Extract list of team member IDs"""
        return list(set(
            issue.fields.assignee.name 
            for issue in issues 
            if issue.fields.assignee
        ))
    
    def _extract_stories(self, issues) -> List[StoryStatus]:
        """Convert Jira issues to StoryStatus"""
        stories = []
        for issue in issues:
            if issue.fields.issuetype.name not in ['Bug', 'Subtask']:
                story = StoryStatus(
                    id=issue.key,
                    title=issue.fields.summary,
                    story_points=getattr(issue.fields, 'customfield_10000', 0.0) or 0.0,
                    status=issue.fields.status.name.lower(),
                    assigned_to=issue.fields.assignee.name if issue.fields.assignee else None,
                    owner_team="Default",
                    is_blocked=self._is_blocked(issue),
                )
                stories.append(story)
        return stories
    
    def _extract_bugs(self, issues) -> List[BugStatus]:
        """Convert Jira bug issues to BugStatus"""
        bugs = []
        for issue in issues:
            if issue.fields.issuetype.name == 'Bug':
                bug = BugStatus(
                    id=issue.key,
                    title=issue.fields.summary,
                    severity=Severity.MEDIUM,
                    status=issue.fields.status.name.lower(),
                    assigned_to=issue.fields.assignee.name if issue.fields.assignee else None,
                )
                bugs.append(bug)
        return bugs
    
    def _is_blocked(self, issue) -> bool:
        """Check if issue is blocked"""
        for link in issue.fields.issuelinks:
            if link.type.name == 'Blocks':
                return True
        return False
    
    def _calculate_hours_allocated(self, assignee_name: str, issues) -> float:
        """Calculate hours allocated to assignee"""
        total = 0.0
        for issue in issues:
            if (issue.fields.assignee and 
                issue.fields.assignee.name == assignee_name):
                time_estimate = getattr(issue.fields, 'timeestimate', 0) or 0
                total += time_estimate / 3600  # Convert seconds to hours
        return total
    
    def _calculate_average_velocity(self, sprints) -> float:
        """Calculate average velocity across sprints"""
        if not sprints:
            return 0.0
        return sum(s.goal_estimate or 0 for s in sprints) / len(sprints)
    
    def _calculate_delivery_confidence(self, sprints) -> float:
        """Calculate delivery confidence based on sprint completion"""
        completed = sum(1 for s in sprints if s.state == 'closed')
        total = len(sprints)
        return (completed / total * 100) if total > 0 else 0.0


# ============================================================================
# GITHUB ADAPTER
# ============================================================================

class GitHubAdapter(DataSourceAdapter):
    """
    Fetches data from GitHub repositories.
    
    Provides:
    - PR metrics (review time, merge rate)
    - CI/CD pipeline status
    - Code quality metrics
    - Security findings (vulnerabilities)
    - Release schedules
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.owner = config.get('owner')
        self.repos = config.get('repos', [])
        self.token = config.get('github_token')
        self.github_client = None
    
    async def connect(self) -> bool:
        """Verify GitHub connection"""
        try:
            from github import Github
            
            self.github_client = Github(self.token)
            
            # Test connection
            self.github_client.get_user().login
            self.is_connected = True
            logger.info(f"✅ Connected to GitHub: {self.owner}")
            return True
            
        except ImportError:
            logger.warning("PyGithub not installed. Install with: pip install PyGithub")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to GitHub: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close GitHub connection"""
        if self.github_client:
            self.github_client = None
            self.is_connected = False
    
    async def fetch_sprint_data(self, sprint_id: str) -> Optional[SprintContext]:
        """GitHub doesn't have sprints. Use project boards or milestones instead."""
        logger.warning("GitHub adapter uses milestones instead of sprints")
        return None
    
    async def fetch_program_data(self, program_id: str) -> Optional[ProgramContext]:
        """Fetch program data from GitHub releases and projects"""
        if not self.is_connected:
            return None
        
        try:
            program_context = ProgramContext(
                program_id=program_id,
                program_name=self.owner,
                program_manager_id="unknown",
                start_date=datetime.now() - timedelta(days=90),
                planned_end_date=datetime.now() + timedelta(days=90),
            )
            
            self._update_last_sync()
            return program_context
            
        except Exception as e:
            logger.error(f"Failed to fetch program data from GitHub: {e}")
            return None
    
    async def fetch_resource_data(self) -> List[ResourceContext]:
        """Fetch GitHub contributors as resources"""
        if not self.is_connected:
            return []
        
        try:
            resources = []
            
            for repo_name in self.repos:
                repo = self.github_client.get_repo(f"{self.owner}/{repo_name}")
                
                for contributor in repo.get_contributors():
                    resource = ResourceContext(
                        resource_id=contributor.login,
                        name=contributor.name or contributor.login,
                        role="Developer",
                        team=repo_name,
                        total_hours_available=40.0,
                        hours_allocated=0.0,  # Would need time tracking data
                    )
                    resources.append(resource)
            
            self._update_last_sync()
            return resources
            
        except Exception as e:
            logger.error(f"Failed to fetch resource data from GitHub: {e}")
            return []
    
    async def fetch_security_data(self) -> Optional[SecurityContext]:
        """
        Fetch security findings from GitHub.
        Includes vulnerability alerts and code scanning results.
        """
        if not self.is_connected:
            return None
        
        try:
            security_context = SecurityContext(
                scan_id=f"github-{datetime.now().timestamp()}",
                scan_date=datetime.now(),
                source_system="github",
            )
            
            for repo_name in self.repos:
                repo = self.github_client.get_repo(f"{self.owner}/{repo_name}")
                
                # Get vulnerability alerts
                # This requires GitHub API with security scanning enabled
                # Note: This is a simplified example
                
                # Get code scanning alerts
                try:
                    alerts = repo.get_code_scanning_alerts()
                    for alert in alerts:
                        finding = SecurityFinding(
                            id=f"github-{alert.number}",
                            title=alert.rule.name,
                            severity=Severity.HIGH if alert.state == 'open' else Severity.LOW,
                            source="github",
                            category="code_scanning",
                            description=alert.rule.description or "",
                        )
                        security_context.vulnerabilities.append(finding)
                except:
                    pass  # Code scanning may not be enabled
            
            self._update_last_sync()
            return security_context
            
        except Exception as e:
            logger.error(f"Failed to fetch security data from GitHub: {e}")
            return None


# ============================================================================
# AZURE DEVOPS ADAPTER
# ============================================================================

class AzureDevOpsAdapter(DataSourceAdapter):
    """
    Fetches data from Azure DevOps.
    
    Provides:
    - Work items (user stories, bugs, tasks)
    - Iterations & velocity
    - Pipelines (build/release status)
    - Test results
    - Branch policies
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.organization = config.get('organization')
        self.project = config.get('project')
        self.pat_token = config.get('pat_token')
        self.base_url = f"https://dev.azure.com/{self.organization}"
        self.client = None
    
    async def connect(self) -> bool:
        """Verify Azure DevOps connection"""
        try:
            from azure.devops.connection import Connection
            from msrest.authentication import BasicAuthentication
            
            credentials = BasicAuthentication('', self.pat_token)
            self.client = Connection(base_url=self.base_url, creds=credentials)
            
            # Test connection
            self.client.get_client('wit').get_team_project(self.project)
            self.is_connected = True
            logger.info(f"✅ Connected to Azure DevOps: {self.organization}/{self.project}")
            return True
            
        except ImportError:
            logger.warning("azure-devops not installed. Install with: pip install azure-devops")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to Azure DevOps: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close Azure DevOps connection"""
        if self.client:
            self.client = None
            self.is_connected = False
    
    async def fetch_sprint_data(self, sprint_id: str) -> Optional[SprintContext]:
        """Fetch sprint data from Azure DevOps iteration"""
        if not self.is_connected:
            return None
        
        try:
            wit_client = self.client.get_client('wit')
            
            # GET _apis/work/teamsettings/iterations/{iterationId}
            iteration = wit_client.get_iteration(self.project, sprint_id)
            
            # Get work items for this iteration
            query = f"SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = '{self.project}' AND [System.IterationPath] = '{iteration.name}'"
            results = wit_client.query_by_wiql(query)
            
            sprint_context = SprintContext(
                sprint_id=iteration.id,
                sprint_name=iteration.name,
                program_id=self.project,
                start_date=datetime.fromisoformat(str(iteration.attributes['startDate'])),
                end_date=datetime.fromisoformat(str(iteration.attributes['finishDate'])),
                goal="Sprint Goal",  # Not available in API
                planned_velocity=0.0,  # Would need to sum story points
                team_size=0,
                last_updated_by_source="azure_devops",
            )
            
            self._update_last_sync()
            return sprint_context
            
        except Exception as e:
            logger.error(f"Failed to fetch sprint data from Azure DevOps: {e}")
            return None
    
    async def fetch_program_data(self, program_id: str) -> Optional[ProgramContext]:
        """Fetch program data"""
        if not self.is_connected:
            return None
        
        try:
            program_context = ProgramContext(
                program_id=program_id,
                program_name=self.project,
                program_manager_id="unknown",
                start_date=datetime.now() - timedelta(days=90),
                planned_end_date=datetime.now() + timedelta(days=90),
            )
            
            self._update_last_sync()
            return program_context
            
        except Exception as e:
            logger.error(f"Failed to fetch program data from Azure DevOps: {e}")
            return None
    
    async def fetch_resource_data(self) -> List[ResourceContext]:
        """Fetch team members"""
        if not self.is_connected:
            return []
        
        try:
            core_client = self.client.get_client('core')
            team_context = core_client.get_team(self.project, 'Default')
            members = core_client.get_team_members_with_extended_properties(
                self.project, 'Default'
            )
            
            resources = []
            for member in members:
                resource = ResourceContext(
                    resource_id=member.identity.id,
                    name=member.identity.display_name,
                    role="Developer",
                    team="Default",
                    total_hours_available=40.0,
                    hours_allocated=0.0,
                )
                resources.append(resource)
            
            self._update_last_sync()
            return resources
            
        except Exception as e:
            logger.error(f"Failed to fetch resource data from Azure DevOps: {e}")
            return []
    
    async def fetch_security_data(self) -> Optional[SecurityContext]:
        """Azure DevOps doesn't have native security scanning in same way as GitHub"""
        logger.warning("Azure DevOps adapter limited security data. Use GitHub adapter for vulnerabilities.")
        return None
