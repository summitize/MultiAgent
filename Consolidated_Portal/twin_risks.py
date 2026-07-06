"""
PHASE 2: Risk Detection Engine

Detects proactive risks across the delivery organization.
6 specialized detectors identify patterns that predict delivery problems.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

from twin_models import (
    SharedProjectMemory, Risk, RiskType, Severity, RiskReport
)


logger = logging.getLogger(__name__)


# ============================================================================
# RISK DETECTORS
# ============================================================================

class RiskDetector:
    """Base class for all risk detectors"""
    
    def __init__(self, memory: SharedProjectMemory):
        self.memory = memory
        self.name = self.__class__.__name__
        self.risks: List[Risk] = []
    
    async def detect(self) -> List[Risk]:
        """Detect risks based on current memory state"""
        raise NotImplementedError
    
    def _create_risk(
        self,
        risk_type: RiskType,
        title: str,
        description: str,
        probability: float,  # 0-1.0
        impact: str,
        signals: List[str],
        recommendations: List[str]
    ) -> Risk:
        """Factory method to create risk"""
        return Risk(
            id=f"risk-{risk_type.value}-{datetime.now().timestamp()}",
            risk_type=risk_type,
            severity=self._calculate_severity(probability),
            title=title,
            description=description,
            probability=probability,
            impact=impact,
            signals=signals,
            recommendations=recommendations,
            owner_agent="RiskDetectionEngine",
        )
    
    def _calculate_severity(self, probability: float) -> Severity:
        """Map probability to severity"""
        if probability >= 0.8:
            return Severity.CRITICAL
        elif probability >= 0.6:
            return Severity.HIGH
        elif probability >= 0.4:
            return Severity.MEDIUM
        else:
            return Severity.LOW


class SpilloverRiskDetector(RiskDetector):
    """
    Detects probability of sprint overflow.
    Signals: declining velocity, high remaining points, few days left
    """
    
    async def detect(self) -> List[Risk]:
        """Detect spillover risk"""
        self.risks = []
        
        if not self.memory.current_sprint:
            return self.risks
        
        sprint = self.memory.current_sprint
        
        # Signal 1: Declining velocity trend
        velocity_declining = False
        if len(sprint.velocity_history) >= 3:
            recent_velocities = sprint.velocity_history[-3:]
            if recent_velocities[0] > recent_velocities[1] > recent_velocities[2]:
                velocity_declining = True
        
        # Signal 2: High remaining points vs burn rate
        if sprint.days_remaining > 0 and sprint.current_velocity > 0:
            points_per_day = sprint.current_velocity / max(1, (len(sprint.stories) - len([s for s in sprint.stories if s.status == 'done'])))
            
            if points_per_day > 0:
                days_to_complete = sprint.remaining_points / points_per_day
                
                if days_to_complete > sprint.days_remaining:
                    # Calculate probability
                    overflow_probability = min(0.95, (days_to_complete / sprint.days_remaining) * 0.8)
                    
                    signals = [
                        f"Remaining points: {sprint.remaining_points}",
                        f"Burn rate: {points_per_day:.1f} points/day",
                        f"Days to complete: {days_to_complete:.1f}",
                        f"Sprint days remaining: {sprint.days_remaining}",
                    ]
                    
                    if velocity_declining:
                        signals.append("Velocity declining 3+ consecutive sprints")
                        overflow_probability += 0.15
                    
                    risk = self._create_risk(
                        risk_type=RiskType.DELIVERY,
                        title=f"Sprint Spillover Risk: {overflow_probability*100:.0f}% probability",
                        description=f"At current burn rate, {sprint.remaining_points:.0f} points won't complete in {sprint.days_remaining} days",
                        probability=min(0.95, overflow_probability),
                        impact="Stories will spill into next sprint, delaying downstream work",
                        signals=signals,
                        recommendations=[
                            f"Reduce scope by {(sprint.remaining_points - (sprint.days_remaining * points_per_day)):.0f} points",
                            "Add team members to increase burn rate",
                            "Identify low-priority items for next sprint",
                            "Check for hidden blockers reducing velocity"
                        ]
                    )
                    
                    self.risks.append(risk)
        
        return self.risks


class CapacityBottleneckDetector(RiskDetector):
    """
    Detects resource utilization spikes and capacity constraints.
    Signals: developer at high %, many tasks queued, declining performance
    """
    
    async def detect(self) -> List[Risk]:
        """Detect capacity bottlenecks"""
        self.risks = []
        
        if not self.memory.resources:
            return self.risks
        
        high_util_resources = []
        
        for resource in self.memory.resources:
            # Flag high utilization
            if resource.utilization > 90:
                high_util_resources.append(resource)
                
                # Check burnout risk
                burnout_probability = (resource.utilization / 100.0) * 0.7
                if resource.consecutive_sprints_at_high_util > 2:
                    burnout_probability += 0.2
                
                signals = [
                    f"Current utilization: {resource.utilization:.0f}%",
                    f"Hours allocated: {resource.hours_allocated:.1f} / {resource.total_hours_available:.1f}",
                    f"Consecutive high-util sprints: {resource.consecutive_sprints_at_high_util}",
                ]
                
                risk = self._create_risk(
                    risk_type=RiskType.RESOURCE,
                    title=f"High Utilization Alert: {resource.name} at {resource.utilization:.0f}%",
                    description=f"{resource.name} ({resource.role}) is over-allocated at {resource.utilization:.0f}% utilization",
                    probability=min(0.85, burnout_probability),
                    impact="Risk of burnout, quality degradation, or key person dependency",
                    signals=signals,
                    recommendations=[
                        f"Redistribute {resource.hours_allocated * 0.2:.1f} hours to team members",
                        "Review task priorities and defer lower-priority work",
                        f"Schedule break/lighter sprint after current sprint",
                        "Identify knowledge transfer opportunities to reduce bottleneck"
                    ]
                )
                
                self.risks.append(risk)
        
        return self.risks


class BudgetOverrunDetector(RiskDetector):
    """
    Detects financial risk and budget tracking.
    Signals: spending accelerating, percentage over, trajectory
    """
    
    async def detect(self) -> List[Risk]:
        """Detect budget overrun risks"""
        self.risks = []
        
        if not self.memory.current_program:
            return self.risks
        
        program = self.memory.current_program
        budget = program.budget_health
        
        if budget['allocated'] == 0:
            return self.risks
        
        # Calculate variance and trajectory
        variance_pct = budget['variance']
        
        if variance_pct > 0:  # Already over budget
            # Calculate projection
            if program.planned_end_date and datetime.now() < program.planned_end_date:
                days_elapsed = (datetime.now() - program.start_date).days
                days_total = (program.planned_end_date - program.start_date).days
                
                if days_total > 0:
                    completion_pct = days_elapsed / days_total
                    
                    # Trend analysis
                    if completion_pct > 0:
                        overage_trajectory = (budget['spent'] / budget['allocated']) / completion_pct
                        projected_overage = (overage_trajectory - 1) * 100
                        
                        probability = min(0.9, (variance_pct / 100.0) * 0.6 + (projected_overage / 100.0) * 0.4)
                        
                        signals = [
                            f"Current variance: {variance_pct:.1f}%",
                            f"Spent: ${budget['spent']:.0f} / ${budget['allocated']:.0f}",
                            f"Projected overage: {projected_overage:.1f}%",
                            f"Forecast: ${budget['forecast']:.0f}",
                        ]
                        
                        risk = self._create_risk(
                            risk_type=RiskType.BUDGET,
                            title=f"Budget Overrun: {variance_pct:.1f}% over, {projected_overage:.1f}% by end",
                            description=f"Program over budget by {variance_pct:.1f}%. At current burn rate, will exceed budget by {projected_overage:.1f}%",
                            probability=probability,
                            impact=f"Projected final cost: ${budget['forecast']:.0f} vs ${budget['allocated']:.0f} budget",
                            signals=signals,
                            recommendations=[
                                "Review resource allocation and reduce headcount if possible",
                                "Reduce scope to minimize remaining spend",
                                "Request budget increase with business case",
                                "Identify cost-saving opportunities (tools, contractors, etc)"
                            ]
                        )
                        
                        self.risks.append(risk)
        
        return self.risks


class DependencyConflictDetector(RiskDetector):
    """
    Detects dependency conflicts and circular dependencies.
    Signals: blocked by relationships, critical path issues
    """
    
    async def detect(self) -> List[Risk]:
        """Detect dependency conflicts"""
        self.risks = []
        
        if not self.memory.current_sprint:
            return self.risks
        
        sprint = self.memory.current_sprint
        
        # Find stories with blockers
        blocked_stories = [s for s in sprint.stories if s.is_blocked]
        
        if len(blocked_stories) > 2:
            # Check for circular dependencies
            circular_deps = self._find_circular_dependencies(sprint.stories)
            
            probability = min(0.85, len(blocked_stories) / len(sprint.stories) * 0.7)
            if circular_deps:
                probability += 0.2
            
            signals = [
                f"Blocked stories: {len(blocked_stories)}",
                f"Blocked by relationships: {sum(len(s.blocked_by) for s in blocked_stories)}",
            ]
            
            if circular_deps:
                signals.append(f"Circular dependencies detected: {len(circular_deps)}")
            
            risk = self._create_risk(
                risk_type=RiskType.DEPENDENCY,
                title=f"Dependency Conflicts: {len(blocked_stories)} blocked stories",
                description=f"{len(blocked_stories)} stories are blocked by dependencies, creating critical path risk",
                probability=probability,
                impact="Delays in dependent work, potential sprint spillover",
                signals=signals,
                recommendations=[
                    "Prioritize unblocking dependencies immediately",
                    "Review blocking story status and accelerate completion",
                    f"Consider reordering {len(blocked_stories)} stories for parallelization",
                    "Escalate if external team dependencies are blocking"
                ]
            )
            
            self.risks.append(risk)
        
        return self.risks
    
    def _find_circular_dependencies(self, stories) -> List[str]:
        """Find circular dependency chains"""
        circular = []
        visited = set()
        rec_stack = set()
        
        def has_cycle(story_id: str, path: List[str]):
            visited.add(story_id)
            rec_stack.add(story_id)
            path.append(story_id)
            
            story = next((s for s in stories if s.id == story_id), None)
            if story:
                for blocked_by_id in story.blocked_by:
                    if blocked_by_id not in visited:
                        if has_cycle(blocked_by_id, path.copy()):
                            circular.append(" → ".join(path))
                    elif blocked_by_id in rec_stack:
                        circular.append(" → ".join(path + [blocked_by_id]))
            
            rec_stack.discard(story_id)
        
        for story in stories:
            if story.id not in visited:
                has_cycle(story.id, [])
        
        return circular


class ReleaseReadinessDetector(RiskDetector):
    """
    Detects release blocking issues and readiness.
    Signals: critical bugs, blocking dependencies, untested features
    """
    
    async def detect(self) -> List[Risk]:
        """Detect release readiness issues"""
        self.risks = []
        
        if not self.memory.current_sprint or not self.memory.current_program:
            return self.risks
        
        sprint = self.memory.current_sprint
        program = self.memory.current_program
        
        # Count critical/high severity bugs
        critical_bugs = [b for b in sprint.bugs if b.severity in ['critical', 'high']]
        
        if len(critical_bugs) > 0:
            # Check if any target this release
            releases = program.releases if program.releases else []
            upcoming_release = next((r for r in releases if r.status in ['planned', 'in_progress']), None)
            
            if upcoming_release:
                days_to_release = (upcoming_release.target_date - datetime.now()).days
                
                # Calculate probability
                probability = min(0.9, (len(critical_bugs) / max(1, len(sprint.bugs))) * 0.8)
                if days_to_release < 5:
                    probability += 0.15
                
                signals = [
                    f"Critical/High bugs: {len(critical_bugs)}",
                    f"Days to release: {days_to_release}",
                    f"Release: {upcoming_release.name}",
                ]
                
                risk = self._create_risk(
                    risk_type=RiskType.QUALITY,
                    title=f"Release at Risk: {len(critical_bugs)} critical bugs",
                    description=f"{len(critical_bugs)} critical/high severity bugs found with {days_to_release} days until release",
                    probability=probability,
                    impact="Release may need to be delayed or shipped with known defects",
                    signals=signals,
                    recommendations=[
                        f"Prioritize fixing {len(critical_bugs)} critical bugs immediately",
                        f"Delay release by {max(5, days_to_release)} days if needed",
                        "Consider release with limited scope and hotfix plan",
                        "Increase QA resources for expedited testing"
                    ]
                )
                
                self.risks.append(risk)
        
        return self.risks


class SecurityTrendDetector(RiskDetector):
    """
    Detects security and compliance risks.
    Signals: unfixed vulnerabilities, policy violations, remediation lag
    """
    
    async def detect(self) -> List[Risk]:
        """Detect security risks"""
        self.risks = []
        
        if not self.memory.security_context:
            return self.risks
        
        security = self.memory.security_context
        
        # Find old unfixed vulnerabilities
        old_threshold = datetime.now() - timedelta(days=30)
        old_vulns = [
            v for v in security.vulnerabilities
            if v.created_date < old_threshold and v.severity.value in ['critical', 'high']
        ]
        
        if len(old_vulns) > 0:
            probability = min(0.9, (len(old_vulns) / max(1, len(security.vulnerabilities))) * 0.7)
            
            signals = [
                f"Unfixed high-severity: {len(old_vulns)}",
                f"Days oldest unfixed: {(datetime.now() - old_vulns[0].created_date).days}",
                f"Total vulnerabilities: {len(security.vulnerabilities)}",
                f"Remediation rate: {security.remediation_rate:.0f}%",
            ]
            
            risk = self._create_risk(
                risk_type=RiskType.SECURITY,
                title=f"Security Backlog: {len(old_vulns)} unfixed high-severity issues",
                description=f"{len(old_vulns)} critical/high security issues unfixed for 30+ days",
                probability=probability,
                impact="Increased attack surface, compliance violations, regulatory risk",
                signals=signals,
                recommendations=[
                    f"Create task to fix {len(old_vulns)} oldest vulnerabilities",
                    "Allocate security engineering capacity to backlog reduction",
                    "Review remediation process for delays",
                    "Escalate compliance violations to security team"
                ]
            )
            
            self.risks.append(risk)
        
        return self.risks


# ============================================================================
# RISK DETECTION ENGINE
# ============================================================================

class RiskDetectionEngine:
    """
    Central risk detection orchestrator.
    Runs all detectors and generates comprehensive risk report.
    """
    
    def __init__(self, memory: SharedProjectMemory):
        self.memory = memory
        self.detectors = [
            SpilloverRiskDetector(memory),
            CapacityBottleneckDetector(memory),
            BudgetOverrunDetector(memory),
            DependencyConflictDetector(memory),
            ReleaseReadinessDetector(memory),
            SecurityTrendDetector(memory),
        ]
        self.last_report: Optional[RiskReport] = None
    
    async def detect_all(self) -> RiskReport:
        """
        Run all detectors in parallel and generate report.
        """
        logger.info("🔍 Running risk detection on all 6 detectors...")
        
        # Run all detectors in parallel
        tasks = [detector.detect() for detector in self.detectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_risks: List[Risk] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in {self.detectors[i].name}: {result}")
            else:
                all_risks.extend(result)
        
        # Sort by severity and probability
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        all_risks.sort(key=lambda r: (severity_order.get(r.severity, 99), -r.probability))
        
        # Generate summary
        summary = {
            'critical': sum(1 for r in all_risks if r.severity == Severity.CRITICAL),
            'high': sum(1 for r in all_risks if r.severity == Severity.HIGH),
            'medium': sum(1 for r in all_risks if r.severity == Severity.MEDIUM),
            'low': sum(1 for r in all_risks if r.severity == Severity.LOW),
        }
        
        # Create report
        report = RiskReport(
            timestamp=datetime.now(),
            risks=all_risks,
            summary=summary,
        )
        
        self.last_report = report
        
        # Log summary
        logger.info(f"✅ Risk detection complete:")
        logger.info(f"   Critical: {summary['critical']}")
        logger.info(f"   High: {summary['high']}")
        logger.info(f"   Medium: {summary['medium']}")
        logger.info(f"   Low: {summary['low']}")
        logger.info(f"   Total: {len(all_risks)}")
        
        return report
    
    def get_critical_risks(self) -> List[Risk]:
        """Get only critical severity risks"""
        if not self.last_report:
            return []
        return [r for r in self.last_report.risks if r.severity == Severity.CRITICAL]
    
    def get_risks_by_type(self, risk_type: RiskType) -> List[Risk]:
        """Get risks of specific type"""
        if not self.last_report:
            return []
        return [r for r in self.last_report.risks if r.risk_type == risk_type]
    
    def get_high_probability_risks(self, threshold: float = 0.7) -> List[Risk]:
        """Get risks above probability threshold"""
        if not self.last_report:
            return []
        return [r for r in self.last_report.risks if r.probability >= threshold]
