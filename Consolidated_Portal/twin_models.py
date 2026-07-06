"""
Delivery Digital Twin - Unified Data Models

This module defines the core data structures that represent the entire delivery organization.
All agents share and update these contexts in the centralized project memory.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class RiskType(Enum):
    """Types of risks the Digital Twin detects"""
    DELIVERY = "delivery"  # Schedule, completion risks
    RESOURCE = "resource"  # Capacity, utilization risks
    BUDGET = "budget"  # Financial risks
    QUALITY = "quality"  # Quality, testing risks
    SECURITY = "security"  # Security and compliance risks
    PEOPLE = "people"  # Team burnout, retention risks
    TECHNICAL = "technical"  # Technical debt, architecture risks
    DEPENDENCY = "dependency"  # Cross-team dependency risks


class Severity(Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StatusColor(Enum):
    """Status visualization"""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


# ============================================================================
# STORY/WORK ITEM MODELS
# ============================================================================

@dataclass
class StoryStatus:
    """Represents a work item/story in sprint"""
    id: str
    title: str
    story_points: float
    status: str  # todo, in_progress, review, done, blocked
    
    # Ownership
    assigned_to: Optional[str]  # Resource ID
    owner_team: str
    
    # Dependencies
    blocked_by: List[str] = field(default_factory=list)  # Other story IDs
    blocks: List[str] = field(default_factory=list)
    
    # Tracking
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    completed_date: Optional[datetime] = None
    
    # Risk flags
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    is_high_risk: bool = False
    risk_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_date'] = self.created_date.isoformat()
        data['updated_date'] = self.updated_date.isoformat()
        if self.completed_date:
            data['completed_date'] = self.completed_date.isoformat()
        return data


@dataclass
class BugStatus:
    """Represents a bug/defect"""
    id: str
    title: str
    severity: Severity
    
    status: str  # new, assigned, in_progress, done
    assigned_to: Optional[str]
    
    # Timing
    created_date: datetime = field(default_factory=datetime.now)
    target_fix_date: Optional[datetime] = None
    
    # Impact
    blocks_release: bool = False
    affects_production: bool = False


# ============================================================================
# SPRINT CONTEXT
# ============================================================================

@dataclass
class SprintContext:
    """
    Represents the current state of a sprint.
    Shared by all agents and continuously updated.
    """
    
    # Identity
    sprint_id: str
    sprint_name: str
    program_id: str
    
    # Dates
    start_date: datetime
    end_date: datetime
    
    # Planning
    goal: str
    planned_velocity: float
    team_size: int
    team_members: List[str] = field(default_factory=list)  # Resource IDs
    total_capacity_hours: float = 0.0
    allocated_capacity_hours: float = 0.0
    
    # Work Items
    stories: List[StoryStatus] = field(default_factory=list)
    bugs: List[BugStatus] = field(default_factory=list)
    technical_debt_items: List[StoryStatus] = field(default_factory=list)
    
    # Current Status
    current_velocity: float = 0.0
    completed_points: float = 0.0
    in_progress_points: float = 0.0
    remaining_points: float = 0.0
    
    # Metrics
    burn_rate: float = 0.0  # Points per day
    days_remaining: int = 0
    completion_percentage: float = 0.0
    
    # Trends
    velocity_history: List[float] = field(default_factory=list)  # Last N sprints
    team_velocity_trend: str = "stable"  # increasing, stable, declining
    
    # Risk Indicators
    spillover_probability: float = 0.0  # 0-100%
    quality_score: float = 0.0  # 0-100
    blocked_stories: List[str] = field(default_factory=list)
    num_blocked: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_updated_by_agent: str = "system"
    last_updated_by_source: str = "jira"  # jira, azure_devops, etc
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat()
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['stories'] = [s.to_dict() for s in self.stories]
        data['bugs'] = [b.asdict() for b in self.bugs]
        data['technical_debt_items'] = [t.to_dict() for t in self.technical_debt_items]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SprintContext':
        """Deserialize from dictionary"""
        # Parse dates
        data['start_date'] = datetime.fromisoformat(data['start_date'])
        data['end_date'] = datetime.fromisoformat(data['end_date'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Parse stories
        if 'stories' in data:
            data['stories'] = [StoryStatus(**s) for s in data['stories']]
        
        return cls(**data)


# ============================================================================
# PROGRAM CONTEXT
# ============================================================================

@dataclass
class ReleaseInfo:
    """Represents a planned release"""
    id: str
    name: str
    target_date: datetime
    components: List[str]
    status: str  # planned, in_progress, ready, released
    release_confidence: float  # 0-100%


@dataclass
class DependencyInfo:
    """Represents a dependency between two work items/teams"""
    from_id: str  # Story ID or Team ID
    to_id: str
    dependency_type: str  # blocks, requires, related
    risk_level: str  # low, medium, high
    status: str  # active, resolved, mitigated


@dataclass
class ProgramContext:
    """
    Represents the overall program health and status.
    Aggregates data from multiple sprints.
    """
    
    # Identity
    program_id: str
    program_name: str
    program_manager_id: str
    
    # Dates
    start_date: datetime
    planned_end_date: datetime
    
    # Portfolio View
    sprints: List[SprintContext] = field(default_factory=list)
    releases: List[ReleaseInfo] = field(default_factory=list)
    dependencies: List[DependencyInfo] = field(default_factory=list)
    
    # Health Metrics
    program_health: StatusColor = StatusColor.GREEN  # Green, Yellow, Red
    delivery_confidence: float = 0.0  # 0-100%
    budget_health: Dict[str, float] = field(default_factory=lambda: {
        'allocated': 0.0,
        'spent': 0.0,
        'forecast': 0.0,
        'variance': 0.0  # percentage
    })
    schedule_health: str = "on_track"  # on_track, at_risk, off_track
    
    # Aggregated Velocity
    total_planned_velocity: float = 0.0
    average_velocity: float = 0.0
    velocity_trend: str = "stable"
    
    # Risk Summary
    top_risks: List[Dict] = field(default_factory=list)  # {id, description, probability, impact}
    impediments: List[Dict] = field(default_factory=list)
    num_critical_risks: int = 0
    num_high_risks: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['planned_end_date'] = self.planned_end_date.isoformat()
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['program_health'] = self.program_health.value
        data['sprints'] = [s.to_dict() for s in self.sprints]
        return data


# ============================================================================
# RESOURCE CONTEXT
# ============================================================================

@dataclass
class ResourceContext:
    """
    Represents a team member and their utilization.
    Used to detect capacity bottlenecks.
    """
    
    # Identity
    resource_id: str
    name: str
    role: str  # Developer, QA, Architect, etc
    team: str
    
    # Availability
    total_hours_available: float  # per sprint
    hours_allocated: float
    utilization: float = 0.0  # percentage (0-100+)
    
    # Assignments
    current_assignments: List[Dict] = field(default_factory=list)  # {sprint_id, story_ids, hours}
    skills: List[str] = field(default_factory=list)
    
    # Performance
    velocity_per_task: float = 0.0
    bug_detection_rate: float = 0.0
    code_quality_score: float = 0.0
    
    # Health
    burnout_risk: str = "low"  # low, medium, high
    consecutive_sprints_at_high_util: int = 0
    last_break: Optional[datetime] = None
    
    # Metadata
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_break:
            data['last_break'] = self.last_break.isoformat()
        return data


# ============================================================================
# SECURITY CONTEXT
# ============================================================================

@dataclass
class SecurityFinding:
    """Represents a security vulnerability or policy violation"""
    id: str
    title: str
    severity: Severity
    
    source: str  # github, azure_devops, snyk, etc
    category: str  # vulnerability, policy_violation, dependency_issue
    
    description: str
    mitigation: Optional[str] = None
    
    created_date: datetime = field(default_factory=datetime.now)
    remediation_target_date: Optional[datetime] = None


@dataclass
class SecurityContext:
    """
    Represents security posture of the delivery organization.
    """
    
    scan_id: str
    scan_date: datetime
    source_system: str  # GitHub, Azure DevOps, etc
    
    # Findings
    vulnerabilities: List[SecurityFinding] = field(default_factory=list)
    policy_violations: List[SecurityFinding] = field(default_factory=list)
    dependency_issues: List[SecurityFinding] = field(default_factory=list)
    
    # Summary
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Remediation
    remediation_priority: List[str] = field(default_factory=list)
    last_remediation_date: Optional[datetime] = None
    remediation_rate: float = 0.0  # percentage fixed


# ============================================================================
# SHARED PROJECT MEMORY
# ============================================================================

@dataclass
class Decision:
    """Records a decision made by an agent"""
    id: str
    decision_text: str
    reasoning: str
    by_agent: str
    timestamp: datetime
    affects: List[str] = field(default_factory=list)  # What it affects (sprint_id, etc)
    

@dataclass
class SharedProjectMemory:
    """
    The unified, centralized memory shared by all 26 agents.
    Single source of truth for all project context.
    """
    
    # Organization Identity
    organization_id: str
    organization_name: str
    
    # Current State
    current_sprint: Optional[SprintContext] = None
    current_program: Optional[ProgramContext] = None
    resources: List[ResourceContext] = field(default_factory=list)
    security_context: Optional[SecurityContext] = None
    
    # Historical Data
    sprint_history: List[SprintContext] = field(default_factory=list)
    program_history: List[ProgramContext] = field(default_factory=list)
    velocity_history: List[float] = field(default_factory=list)
    
    # Shared Decisions
    decisions: List[Decision] = field(default_factory=list)
    
    # Known Impediments
    impediments: List[Dict] = field(default_factory=list)  # {id, description, reported_by, date}
    
    # Known Dependencies
    dependencies: List[DependencyInfo] = field(default_factory=list)
    
    # Lessons Learned
    lessons_learned: List[Dict] = field(default_factory=list)  # {lesson, context, applied, by_agent, date}
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    updated_by_agent: str = "system"
    version: str = "1.0"
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        data = {
            'organization_id': self.organization_id,
            'organization_name': self.organization_name,
            'current_sprint': self.current_sprint.to_dict() if self.current_sprint else None,
            'current_program': self.current_program.to_dict() if self.current_program else None,
            'resources': [r.to_dict() for r in self.resources],
            'security_context': self.security_context.asdict() if self.security_context else None,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'updated_by_agent': self.updated_by_agent,
            'version': self.version,
            'impediments': self.impediments,
            'lessons_learned': self.lessons_learned,
        }
        return data
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def create_empty(cls, org_id: str, org_name: str) -> 'SharedProjectMemory':
        """Create new empty memory for organization"""
        return cls(
            organization_id=org_id,
            organization_name=org_name,
        )


# ============================================================================
# RISK MODEL
# ============================================================================

@dataclass
class Risk:
    """
    Represents a detected risk in the delivery organization.
    """
    
    id: str
    risk_type: RiskType
    severity: Severity
    title: str
    description: str
    
    # Probability & Impact
    probability: float  # 0-1.0 (0-100%)
    impact: str  # Description of impact if risk materializes
    
    # Signals that triggered detection
    signals: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Status
    status: str = "new"  # new, acknowledged, mitigating, resolved
    owner_agent: Optional[str] = None
    
    # Dates
    detected_date: datetime = field(default_factory=datetime.now)
    target_resolution_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['risk_type'] = self.risk_type.value
        data['severity'] = self.severity.value
        data['detected_date'] = self.detected_date.isoformat()
        if self.target_resolution_date:
            data['target_resolution_date'] = self.target_resolution_date.isoformat()
        return data


@dataclass
class RiskReport:
    """
    Report generated by RiskDetectionEngine.
    """
    
    timestamp: datetime
    risks: List[Risk]
    summary: Dict = field(default_factory=dict)  # {critical: N, high: N, medium: N, low: N}
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'risks': [r.to_dict() for r in self.risks],
            'summary': self.summary,
        }


# ============================================================================
# COLLABORATION REQUEST/RESPONSE
# ============================================================================

@dataclass
class CollaborationRequest:
    """
    Agent A requests information/action from Agent B.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent_id: str = ""
    to_agent_id: str = ""
    request_type: str = ""  # ask_for_input, request_review, share_status, etc
    priority: str = "normal"  # critical, high, normal, low
    
    context: Dict = field(default_factory=dict)  # Request-specific data
    deadline: Optional[datetime] = None
    
    # Status
    status: str = "pending"  # pending, accepted, completed, rejected
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Response
    response: Optional[Dict] = None
    reasoning: Optional[str] = None  # Why this decision was made
    
    # Audit trail
    audit_trail: List[Dict] = field(default_factory=list)  # Timestamped events
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.deadline:
            data['deadline'] = self.deadline.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class CollaborationResponse:
    """
    Response from Agent B to Agent A's request.
    """
    
    request_id: str
    status: str  # accepted, completed, rejected
    response_data: Dict
    reasoning: str  # Transparent explanation of reasoning
    confidence: float  # 0-100%
    alternative_options: Optional[List[Dict]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


# ============================================================================
# SYNC RESULT
# ============================================================================

@dataclass
class SyncResult:
    """Result of syncing data from a single source"""
    source_name: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Data
    sprint_data: Optional[SprintContext] = None
    program_data: Optional[ProgramContext] = None
    resource_data: Optional[List[ResourceContext]] = None
    security_data: Optional[SecurityContext] = None
    
    # Error handling
    error: Optional[str] = None
    warning: Optional[str] = None
    records_processed: int = 0
    records_updated: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'source_name': self.source_name,
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'error': self.error,
            'warning': self.warning,
            'records_processed': self.records_processed,
            'records_updated': self.records_updated,
        }
