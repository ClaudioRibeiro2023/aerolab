"""
Agno Team Orchestrator v2.0 - Task System

Advanced task management with dependencies and scheduling.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
import heapq

from .types import (
    Task, TaskResult, TaskStatus, TaskType,
    Priority, AssignmentStrategy, AgentProfile
)


# ============================================================
# TASK TEMPLATES
# ============================================================

TASK_TEMPLATES: Dict[str, Dict] = {
    # Research Tasks
    "web_research": {
        "name": "Web Research",
        "type": TaskType.RESEARCH,
        "description": "Conduct web research on a given topic",
        "expected_output": "Comprehensive research report with sources",
        "tools_required": ["web_search"],
        "estimated_duration_minutes": 15,
    },
    "data_gathering": {
        "name": "Data Gathering",
        "type": TaskType.DATA,
        "description": "Gather and compile data from multiple sources",
        "expected_output": "Structured dataset",
        "tools_required": ["data_extractor"],
        "estimated_duration_minutes": 20,
    },
    "competitive_analysis": {
        "name": "Competitive Analysis",
        "type": TaskType.ANALYSIS,
        "description": "Analyze competitors and market landscape",
        "expected_output": "Competitive analysis report",
        "tools_required": ["web_search", "analysis_tools"],
        "estimated_duration_minutes": 30,
    },
    
    # Content Tasks
    "content_writing": {
        "name": "Content Writing",
        "type": TaskType.CREATION,
        "description": "Create written content based on brief",
        "expected_output": "Polished written content",
        "tools_required": ["text_generator"],
        "estimated_duration_minutes": 25,
    },
    "content_editing": {
        "name": "Content Editing",
        "type": TaskType.REVIEW,
        "description": "Edit and improve existing content",
        "expected_output": "Edited content with tracked changes",
        "tools_required": ["grammar_check"],
        "estimated_duration_minutes": 15,
    },
    "summarization": {
        "name": "Summarization",
        "type": TaskType.CREATION,
        "description": "Summarize long-form content",
        "expected_output": "Concise summary",
        "tools_required": [],
        "estimated_duration_minutes": 10,
    },
    
    # Analysis Tasks
    "data_analysis": {
        "name": "Data Analysis",
        "type": TaskType.ANALYSIS,
        "description": "Analyze data and extract insights",
        "expected_output": "Analysis report with visualizations",
        "tools_required": ["data_analyzer", "chart_generator"],
        "estimated_duration_minutes": 30,
    },
    "sentiment_analysis": {
        "name": "Sentiment Analysis",
        "type": TaskType.ANALYSIS,
        "description": "Analyze sentiment in text data",
        "expected_output": "Sentiment report with scores",
        "tools_required": ["sentiment_analyzer"],
        "estimated_duration_minutes": 15,
    },
    
    # Code Tasks
    "code_generation": {
        "name": "Code Generation",
        "type": TaskType.CODE,
        "description": "Generate code based on requirements",
        "expected_output": "Working code with documentation",
        "tools_required": ["code_executor"],
        "estimated_duration_minutes": 30,
    },
    "code_review": {
        "name": "Code Review",
        "type": TaskType.REVIEW,
        "description": "Review code for quality and issues",
        "expected_output": "Code review report with suggestions",
        "tools_required": ["code_analyzer"],
        "estimated_duration_minutes": 20,
    },
    "bug_fixing": {
        "name": "Bug Fixing",
        "type": TaskType.CODE,
        "description": "Identify and fix bugs in code",
        "expected_output": "Fixed code with explanation",
        "tools_required": ["code_executor", "debugger"],
        "estimated_duration_minutes": 25,
    },
    
    # Design Tasks
    "ui_design": {
        "name": "UI Design",
        "type": TaskType.DESIGN,
        "description": "Design user interface components",
        "expected_output": "UI design mockups",
        "tools_required": ["design_tools"],
        "estimated_duration_minutes": 40,
    },
    "ux_review": {
        "name": "UX Review",
        "type": TaskType.REVIEW,
        "description": "Review user experience of a product",
        "expected_output": "UX review report with recommendations",
        "tools_required": ["ux_analyzer"],
        "estimated_duration_minutes": 25,
    },
    
    # Decision Tasks
    "decision_making": {
        "name": "Decision Making",
        "type": TaskType.DECISION,
        "description": "Make a decision based on available information",
        "expected_output": "Decision with rationale",
        "tools_required": [],
        "estimated_duration_minutes": 15,
    },
    "prioritization": {
        "name": "Prioritization",
        "type": TaskType.DECISION,
        "description": "Prioritize items based on criteria",
        "expected_output": "Prioritized list with justification",
        "tools_required": [],
        "estimated_duration_minutes": 15,
    },
    
    # Communication Tasks
    "email_drafting": {
        "name": "Email Drafting",
        "type": TaskType.COMMUNICATION,
        "description": "Draft professional email",
        "expected_output": "Ready-to-send email",
        "tools_required": [],
        "estimated_duration_minutes": 10,
    },
    "presentation_creation": {
        "name": "Presentation Creation",
        "type": TaskType.COMMUNICATION,
        "description": "Create presentation slides",
        "expected_output": "Presentation deck",
        "tools_required": ["presentation_tools"],
        "estimated_duration_minutes": 45,
    },
}


# ============================================================
# TASK MANAGER
# ============================================================

class TaskManager:
    """Manages tasks and their execution."""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._dependencies: Dict[str, List[str]] = defaultdict(list)
        self._dependents: Dict[str, List[str]] = defaultdict(list)
    
    def create_task(
        self,
        name: str,
        description: str,
        task_type: TaskType = TaskType.CUSTOM,
        **kwargs
    ) -> Task:
        """Create a new task."""
        task = Task(
            name=name,
            description=description,
            type=task_type,
            **kwargs
        )
        self._tasks[task.id] = task
        
        # Register dependencies
        for dep_id in task.dependencies:
            self._dependencies[task.id].append(dep_id)
            self._dependents[dep_id].append(task.id)
        
        return task
    
    def from_template(self, template_key: str, **overrides) -> Task:
        """Create task from template."""
        if template_key not in TASK_TEMPLATES:
            raise ValueError(f"Unknown task template: {template_key}")
        
        template = TASK_TEMPLATES[template_key].copy()
        template.update(overrides)
        
        # Extract and convert type
        task_type = template.pop("type", TaskType.CUSTOM)
        if isinstance(task_type, str):
            task_type = TaskType(task_type)
        
        # Extract name and description
        name = template.pop("name", "Task")
        description = template.pop("description", "")
        
        # Remove non-Task fields
        template.pop("estimated_duration_minutes", None)
        
        return self.create_task(name=name, description=description, task_type=task_type, **template)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """List tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        """Update task status."""
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            if status == TaskStatus.IN_PROGRESS:
                task.started_at = datetime.now()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.now()
        return task
    
    def assign_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """Assign task to an agent."""
        task = self._tasks.get(task_id)
        if task:
            task.assigned_to = agent_id
            task.status = TaskStatus.ASSIGNED
        return task
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_met = all(
                self._tasks.get(dep_id, Task()).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_met:
                ready.append(task)
        
        return ready
    
    def get_task_order(self) -> List[str]:
        """Get topological order of tasks."""
        # Kahn's algorithm for topological sort
        in_degree = {task_id: len(deps) for task_id, deps in self._dependencies.items()}
        for task_id in self._tasks:
            if task_id not in in_degree:
                in_degree[task_id] = 0
        
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order = []
        
        while queue:
            task_id = queue.pop(0)
            order.append(task_id)
            
            for dependent in self._dependents.get(task_id, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return order
    
    def add_dependency(self, task_id: str, dependency_id: str):
        """Add a dependency to a task."""
        task = self._tasks.get(task_id)
        if task and dependency_id not in task.dependencies:
            task.dependencies.append(dependency_id)
            self._dependencies[task_id].append(dependency_id)
            self._dependents[dependency_id].append(task_id)
    
    def remove_dependency(self, task_id: str, dependency_id: str):
        """Remove a dependency from a task."""
        task = self._tasks.get(task_id)
        if task and dependency_id in task.dependencies:
            task.dependencies.remove(dependency_id)
            self._dependencies[task_id].remove(dependency_id)
            self._dependents[dependency_id].remove(task_id)
    
    @staticmethod
    def list_templates() -> List[str]:
        """List available task templates."""
        return list(TASK_TEMPLATES.keys())
    
    @staticmethod
    def get_template_info(template_key: str) -> Optional[Dict]:
        """Get template information."""
        return TASK_TEMPLATES.get(template_key)


# ============================================================
# TASK SCHEDULER
# ============================================================

class TaskScheduler:
    """Schedules tasks based on priority and dependencies."""
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
    
    def schedule(
        self,
        agents: List[AgentProfile],
        strategy: AssignmentStrategy = AssignmentStrategy.BEST_FIT
    ) -> Dict[str, str]:
        """
        Schedule tasks to agents.
        
        Returns:
            Dict mapping task_id -> agent_id
        """
        assignments = {}
        ready_tasks = self.task_manager.get_ready_tasks()
        
        # Sort by priority
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }
        ready_tasks.sort(key=lambda t: priority_order.get(t.priority, 2))
        
        if strategy == AssignmentStrategy.BEST_FIT:
            assignments = self._best_fit_schedule(ready_tasks, agents)
        elif strategy == AssignmentStrategy.ROUND_ROBIN:
            assignments = self._round_robin_schedule(ready_tasks, agents)
        elif strategy == AssignmentStrategy.LEAST_LOADED:
            assignments = self._least_loaded_schedule(ready_tasks, agents)
        
        # Apply assignments
        for task_id, agent_id in assignments.items():
            self.task_manager.assign_task(task_id, agent_id)
        
        return assignments
    
    def _best_fit_schedule(
        self,
        tasks: List[Task],
        agents: List[AgentProfile]
    ) -> Dict[str, str]:
        """Assign tasks to best matching agents."""
        assignments = {}
        
        for task in tasks:
            best_agent = None
            best_score = -1
            
            for agent in agents:
                score = self._calculate_fit_score(task, agent)
                if score > best_score:
                    best_score = score
                    best_agent = agent
            
            if best_agent:
                assignments[task.id] = best_agent.id
        
        return assignments
    
    def _round_robin_schedule(
        self,
        tasks: List[Task],
        agents: List[AgentProfile]
    ) -> Dict[str, str]:
        """Assign tasks in round-robin fashion."""
        assignments = {}
        
        for i, task in enumerate(tasks):
            agent_idx = i % len(agents)
            assignments[task.id] = agents[agent_idx].id
        
        return assignments
    
    def _least_loaded_schedule(
        self,
        tasks: List[Task],
        agents: List[AgentProfile]
    ) -> Dict[str, str]:
        """Assign tasks to least loaded agents."""
        assignments = {}
        agent_loads = {a.id: 0 for a in agents}
        
        for task in tasks:
            # Find agent with lowest load
            min_load_agent = min(agents, key=lambda a: agent_loads[a.id])
            assignments[task.id] = min_load_agent.id
            agent_loads[min_load_agent.id] += 1
        
        return assignments
    
    def _calculate_fit_score(self, task: Task, agent: AgentProfile) -> float:
        """Calculate how well an agent fits a task."""
        score = 0.0
        
        # Check required tools
        agent_tools = set(agent.tools)
        required_tools = set(task.tools_required)
        if required_tools:
            tool_match = len(agent_tools & required_tools) / len(required_tools)
            score += 0.4 * tool_match
        else:
            score += 0.4
        
        # Check skills
        task_type_skills = {
            TaskType.RESEARCH: ["Research", "Analysis"],
            TaskType.CREATION: ["Writing", "Creativity"],
            TaskType.ANALYSIS: ["Analysis", "Data Analysis"],
            TaskType.CODE: ["Python", "Programming"],
            TaskType.REVIEW: ["Quality Assurance", "Critical Analysis"],
            TaskType.DESIGN: ["UX Design", "Visual Design"],
        }
        
        relevant_skills = task_type_skills.get(task.type, [])
        if relevant_skills:
            skill_score = sum(
                agent.get_skill_level(s) / 100.0
                for s in relevant_skills
            ) / len(relevant_skills)
            score += 0.4 * skill_score
        else:
            score += 0.4 * 0.5
        
        # Check personality fit
        if task.type in [TaskType.CREATION, TaskType.DESIGN]:
            score += 0.2 * agent.personality.openness
        elif task.type in [TaskType.ANALYSIS, TaskType.CODE]:
            score += 0.2 * agent.personality.conscientiousness
        else:
            score += 0.2 * 0.5
        
        return score
