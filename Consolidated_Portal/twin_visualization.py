"""
PHASE 4: Visualization Components

Generates data structures for frontend visualization:
- React Flow dependency graphs
- Risk dashboards
- Memory timeline
- Agent collaboration graphs
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from twin_models import (
    SharedProjectMemory, Risk, CollaborationRequest, StoryStatus
)


logger = logging.getLogger(__name__)


# ============================================================================
# REACT FLOW VISUALIZATION
# ============================================================================

class ReactFlowGenerator:
    """Generates React Flow nodes and edges for visualization"""
    
    @staticmethod
    def generate_dependency_graph(memory: SharedProjectMemory) -> Dict[str, Any]:
        """
        Generate React Flow graph of story dependencies.
        
        Returns: {nodes: [...], edges: [...]}
        """
        
        if not memory.current_sprint:
            return {'nodes': [], 'edges': []}
        
        sprint = memory.current_sprint
        nodes = []
        edges = []
        
        # Color mapping for story status
        status_colors = {
            'todo': '#e74c3c',           # Red
            'in_progress': '#f39c12',    # Orange
            'review': '#3498db',         # Blue
            'done': '#27ae60',           # Green
            'blocked': '#8b0000',        # Dark red
        }
        
        # Create nodes for each story
        for story in sprint.stories:
            node = {
                'id': story.id,
                'data': {
                    'label': story.title,
                    'story_points': story.story_points,
                    'status': story.status,
                    'assigned_to': story.assigned_to or 'Unassigned',
                    'blocked': story.is_blocked,
                },
                'position': {'x': 0, 'y': 0},  # Layout engine will position
                'style': {
                    'background': status_colors.get(story.status, '#95a5a6'),
                    'color': '#fff',
                    'border': '2px solid #2c3e50' if story.is_blocked else '1px solid #34495e',
                    'borderRadius': '8px',
                    'padding': '10px',
                    'fontWeight': 'bold' if story.is_blocked else 'normal',
                },
            }
            nodes.append(node)
        
        # Create edges for dependencies
        for story in sprint.stories:
            for blocked_by_id in story.blocked_by:
                edge = {
                    'id': f"{blocked_by_id}-{story.id}",
                    'source': blocked_by_id,
                    'target': story.id,
                    'animated': True,
                    'style': {
                        'stroke': '#e74c3c',
                        'strokeWidth': 2,
                    },
                    'label': 'blocks',
                    'markerEnd': {'type': 'arrowclosed'},
                }
                edges.append(edge)
        
        logger.info(f"Generated dependency graph: {len(nodes)} nodes, {len(edges)} edges")
        
        return {'nodes': nodes, 'edges': edges}
    
    @staticmethod
    def generate_resource_utilization_graph(memory: SharedProjectMemory) -> Dict[str, Any]:
        """
        Generate React Flow visualization of resource utilization.
        Each resource is a node, sized by utilization.
        """
        
        if not memory.resources:
            return {'nodes': [], 'edges': []}
        
        nodes = []
        
        for resource in memory.resources:
            # Color based on utilization level
            if resource.utilization > 90:
                color = '#c0392b'  # Dark red
            elif resource.utilization > 80:
                color = '#e74c3c'  # Red
            elif resource.utilization > 70:
                color = '#f39c12'  # Orange
            else:
                color = '#27ae60'  # Green
            
            # Size node based on utilization
            size_multiplier = 1 + (resource.utilization / 100) * 0.5
            
            node = {
                'id': resource.resource_id,
                'data': {
                    'label': resource.name,
                    'utilization': f"{resource.utilization:.0f}%",
                    'role': resource.role,
                    'hours': f"{resource.hours_allocated:.1f}/{resource.total_hours_available:.1f}h",
                    'burnout_risk': resource.burnout_risk,
                },
                'position': {'x': 0, 'y': 0},
                'style': {
                    'background': color,
                    'color': '#fff',
                    'border': '2px solid #2c3e50',
                    'borderRadius': '12px',
                    'padding': '15px',
                    'fontWeight': 'bold',
                    'width': f"{100 * size_multiplier}px",
                    'height': f"{80 * size_multiplier}px",
                },
            }
            nodes.append(node)
        
        return {'nodes': nodes, 'edges': []}


# ============================================================================
# RISK DASHBOARD
# ============================================================================

class RiskDashboard:
    """Generates risk dashboard data for visualization"""
    
    @staticmethod
    def generate_risk_summary(risks: List[Risk]) -> Dict[str, Any]:
        """
        Generate risk summary for dashboard.
        """
        
        # Categorize risks
        by_severity = {}
        by_type = {}
        high_probability = []
        
        for risk in risks:
            # By severity
            severity_key = risk.severity.value
            if severity_key not in by_severity:
                by_severity[severity_key] = []
            by_severity[severity_key].append(risk)
            
            # By type
            type_key = risk.risk_type.value
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append(risk)
            
            # High probability
            if risk.probability > 0.7:
                high_probability.append(risk)
        
        # Sort by probability
        high_probability.sort(key=lambda r: r.probability, reverse=True)
        
        dashboard = {
            'summary': {
                'total_risks': len(risks),
                'critical': len(by_severity.get('critical', [])),
                'high': len(by_severity.get('high', [])),
                'medium': len(by_severity.get('medium', [])),
                'low': len(by_severity.get('low', [])),
            },
            'by_type': {
                risk_type: len(risk_list)
                for risk_type, risk_list in by_type.items()
            },
            'high_probability': [
                {
                    'id': risk.id,
                    'title': risk.title,
                    'probability': f"{risk.probability * 100:.0f}%",
                    'severity': risk.severity.value,
                    'description': risk.description,
                    'recommendations': risk.recommendations[:3],  # Top 3
                }
                for risk in high_probability[:5]  # Top 5
            ],
        }
        
        return dashboard
    
    @staticmethod
    def generate_risk_cards(risks: List[Risk]) -> List[Dict[str, Any]]:
        """Generate individual risk cards for display"""
        
        cards = []
        
        for risk in risks:
            card = {
                'id': risk.id,
                'title': risk.title,
                'type': risk.risk_type.value,
                'severity': risk.severity.value,
                'probability': f"{risk.probability * 100:.0f}%",
                'description': risk.description,
                'impact': risk.impact,
                'signals': risk.signals,
                'recommendations': risk.recommendations,
                'status': risk.status,
                'detected_at': risk.detected_date.isoformat(),
            }
            cards.append(card)
        
        return cards


# ============================================================================
# MEMORY TIMELINE
# ============================================================================

class MemoryTimeline:
    """Generates memory update timeline for visualization"""
    
    @staticmethod
    def generate_timeline(version_history: List[Dict]) -> List[Dict[str, Any]]:
        """
        Generate timeline of memory updates.
        """
        
        timeline = []
        
        for entry in version_history:
            timeline_entry = {
                'timestamp': entry['timestamp'],
                'agent': entry.get('agent_id', 'system'),
                'action': entry.get('reason', 'update'),
                'version': entry.get('version'),
                'formatted_time': datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            }
            timeline.append(timeline_entry)
        
        return timeline


# ============================================================================
# COLLABORATION GRAPH
# ============================================================================

class CollaborationGraph:
    """Generates collaboration network visualization"""
    
    @staticmethod
    def generate_agent_collaboration_graph(
        audit_log: List[Dict],
        agent_registry: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Generate React Flow graph showing agent communication patterns.
        Nodes are agents, edges are requests/responses.
        """
        
        nodes = []
        edges = []
        agent_positions = {}
        
        # Create nodes for each agent
        agent_ids = set()
        for entry in audit_log:
            if 'from_agent' in entry:
                agent_ids.add(entry['from_agent'])
            if 'to_agent' in entry:
                agent_ids.add(entry['to_agent'])
        
        # Arrange agents in circle
        angle_step = 360 / max(len(agent_ids), 1)
        radius = 200
        
        for idx, agent_id in enumerate(agent_ids):
            angle = idx * angle_step
            x = radius * (angle / 180) * 3.14159 / 3.14159
            y = radius * ((angle + 90) / 180) * 3.14159 / 3.14159
            
            agent_positions[agent_id] = {'x': x, 'y': y}
            
            node = {
                'id': agent_id,
                'data': {'label': agent_id},
                'position': agent_positions[agent_id],
                'style': {
                    'background': '#3498db',
                    'color': '#fff',
                    'border': '2px solid #2c3e50',
                    'borderRadius': '50%',
                    'padding': '10px',
                    'fontWeight': 'bold',
                    'width': '80px',
                    'height': '80px',
                },
            }
            nodes.append(node)
        
        # Create edges for communications
        request_counts = {}
        for entry in audit_log:
            if entry['event'] == 'request_created':
                from_agent = entry.get('from_agent')
                # We need to infer the to_agent somehow
                # For now, create a generic collaboration edge
                
                edge_key = (from_agent, 'collaboration')
                if edge_key not in request_counts:
                    request_counts[edge_key] = 0
                request_counts[edge_key] += 1
        
        edge_id = 0
        for (from_agent, _), count in request_counts.items():
            # Find other agents involved
            to_agents = set(
                entry.get('to_agent')
                for entry in audit_log
                if entry.get('from_agent') == from_agent and 'to_agent' in entry
            )
            
            for to_agent in to_agents:
                if to_agent and from_agent != to_agent:
                    edge = {
                        'id': f"edge-{edge_id}",
                        'source': from_agent,
                        'target': to_agent,
                        'animated': True,
                        'style': {'stroke': '#2ecc71', 'strokeWidth': 2},
                        'label': f"{count} requests",
                        'markerEnd': {'type': 'arrowclosed'},
                    }
                    edges.append(edge)
                    edge_id += 1
        
        return {'nodes': nodes, 'edges': edges}


# ============================================================================
# SPRINT BURNDOWN CHART
# ============================================================================

class BurndownChart:
    """Generates sprint burndown data"""
    
    @staticmethod
    def generate_burndown_data(memory: SharedProjectMemory) -> Dict[str, Any]:
        """
        Generate burndown chart data (points remaining over time).
        """
        
        if not memory.current_sprint:
            return {}
        
        sprint = memory.current_sprint
        
        # Calculate ideal burndown line
        total_sprint_days = (sprint.end_date - sprint.start_date).days
        total_points = sprint.planned_velocity
        
        ideal_line = []
        for day in range(total_sprint_days + 1):
            points_remaining = total_points * (1 - day / max(1, total_sprint_days))
            ideal_line.append({
                'day': day,
                'date': (sprint.start_date + timedelta(days=day)).isoformat(),
                'points': points_remaining,
            })
        
        # Actual burndown (approximation based on completed points)
        actual_line = [
            {
                'day': 0,
                'date': sprint.start_date.isoformat(),
                'points': sprint.planned_velocity,
            },
            {
                'day': (datetime.now() - sprint.start_date).days,
                'date': datetime.now().isoformat(),
                'points': sprint.remaining_points,
            },
        ]
        
        burndown = {
            'sprint_name': sprint.sprint_name,
            'start_date': sprint.start_date.isoformat(),
            'end_date': sprint.end_date.isoformat(),
            'total_days': total_sprint_days,
            'days_elapsed': (datetime.now() - sprint.start_date).days,
            'days_remaining': sprint.days_remaining,
            'total_points': sprint.planned_velocity,
            'completed_points': sprint.completed_points,
            'remaining_points': sprint.remaining_points,
            'ideal_line': ideal_line,
            'actual_line': actual_line,
        }
        
        return burndown


# ============================================================================
# EXPORT UTILITIES
# ============================================================================

class VisualizationExporter:
    """Export visualization data"""
    
    @staticmethod
    def export_full_dashboard(memory: SharedProjectMemory, risks: List[Risk]) -> Dict[str, Any]:
        """
        Export complete dashboard data.
        Ready to send to frontend.
        """
        
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'sprint': {
                'name': memory.current_sprint.sprint_name if memory.current_sprint else None,
                'status': memory.current_sprint.completion_percentage if memory.current_sprint else 0,
            },
            'dependency_graph': ReactFlowGenerator.generate_dependency_graph(memory),
            'resource_utilization': ReactFlowGenerator.generate_resource_utilization_graph(memory),
            'risks': RiskDashboard.generate_risk_summary(risks),
            'risk_cards': RiskDashboard.generate_risk_cards(risks),
            'burndown': BurndownChart.generate_burndown_data(memory),
        }
        
        return dashboard


# ============================================================================
# INITIALIZATION
# ============================================================================

from datetime import timedelta

if __name__ == "__main__":
    # Example usage
    logger.info("Visualization components ready for use")
