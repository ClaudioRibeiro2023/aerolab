"""
Agno Team Orchestrator v2.0 - Tests

Comprehensive tests for all components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Types
from ..types import (
    AgentProfile, PersonalityTraits, Skill,
    Task, TaskType, TaskStatus, TaskResult,
    TeamConfiguration, TeamExecution, ExecutionStatus,
    OrchestrationMode, Message, MessageType,
    MemoryScope, MemoryItem, Priority,
    Conflict, ConflictType, Resolution, ResolutionStrategy
)

# Core
from ..profiles import AgentProfileManager, PERSONA_LIBRARY, get_profile_manager
from ..tasks import TaskManager, TaskScheduler, TASK_TEMPLATES
from ..engine import TeamOrchestrationEngine, get_orchestration_engine
from ..communication import MessageBus, ConversationManager
from ..memory import TeamMemorySpace, get_memory_manager

# AI
from ..ai.nl_builder import NLTeamBuilder, TEAM_TEMPLATES
from ..ai.optimizer import TeamOptimizer, OptimizationObjective
from ..ai.conflict_resolver import ConflictResolver
from ..ai.learning import AgentLearningSystem, Feedback


# ============================================================
# TYPES TESTS
# ============================================================

class TestTypes:
    """Test type definitions."""
    
    def test_personality_traits(self):
        """Test PersonalityTraits."""
        traits = PersonalityTraits(
            openness=0.8,
            conscientiousness=0.7,
            extraversion=0.6,
            agreeableness=0.9,
            neuroticism=0.3
        )
        
        assert traits.openness == 0.8
        assert traits.conscientiousness == 0.7
        
        data = traits.to_dict()
        assert "openness" in data
        
        restored = PersonalityTraits.from_dict(data)
        assert restored.openness == 0.8
    
    def test_skill(self):
        """Test Skill."""
        skill = Skill(
            name="Python",
            level=90,
            category="programming"
        )
        
        assert skill.name == "Python"
        assert skill.level == 90
        
        data = skill.to_dict()
        assert data["name"] == "Python"
    
    def test_agent_profile(self):
        """Test AgentProfile."""
        profile = AgentProfile(
            name="Test Agent",
            role="Tester",
            goal="Test everything",
            skills=[Skill(name="Testing", level=95, category="quality")]
        )
        
        assert profile.name == "Test Agent"
        assert len(profile.skills) == 1
        assert profile.get_skill_level("Testing") == 95
        assert profile.get_skill_level("Unknown") == 0
        
        data = profile.to_dict()
        assert data["name"] == "Test Agent"
        
        restored = AgentProfile.from_dict(data)
        assert restored.name == "Test Agent"
    
    def test_agent_compatibility(self):
        """Test agent compatibility calculation."""
        agent1 = AgentProfile(
            name="Agent 1",
            personality=PersonalityTraits(extraversion=0.8, agreeableness=0.7),
            skills=[Skill(name="Research", level=90, category="research")]
        )
        
        agent2 = AgentProfile(
            name="Agent 2",
            personality=PersonalityTraits(extraversion=0.3, agreeableness=0.7),
            skills=[Skill(name="Writing", level=85, category="content")]
        )
        
        compatibility = agent1.calculate_compatibility(agent2)
        assert 0 <= compatibility <= 1
    
    def test_task(self):
        """Test Task."""
        task = Task(
            name="Test Task",
            description="A test task",
            type=TaskType.RESEARCH,
            priority=Priority.HIGH
        )
        
        assert task.name == "Test Task"
        assert task.type == TaskType.RESEARCH
        assert task.status == TaskStatus.PENDING
        
        data = task.to_dict()
        restored = Task.from_dict(data)
        assert restored.name == "Test Task"
    
    def test_team_configuration(self):
        """Test TeamConfiguration."""
        agent = AgentProfile(name="Agent", role="Worker", goal="Work")
        task = Task(name="Task", description="Do work")
        
        config = TeamConfiguration(
            name="Test Team",
            agents=[agent],
            tasks=[task],
            mode=OrchestrationMode.SEQUENTIAL
        )
        
        assert config.name == "Test Team"
        assert len(config.agents) == 1
        assert config.mode == OrchestrationMode.SEQUENTIAL
        
        data = config.to_dict()
        assert data["mode"] == "sequential"
    
    def test_message(self):
        """Test Message."""
        msg = Message(
            sender="agent1",
            recipients=["agent2"],
            content="Hello",
            type=MessageType.INFORM
        )
        
        assert msg.sender == "agent1"
        assert msg.content == "Hello"
        assert not msg.processed


# ============================================================
# PROFILES TESTS
# ============================================================

class TestProfiles:
    """Test agent profile management."""
    
    def test_persona_library_loaded(self):
        """Test persona library is loaded."""
        assert len(PERSONA_LIBRARY) > 0
        assert "senior_researcher" in PERSONA_LIBRARY
        assert "content_writer" in PERSONA_LIBRARY
    
    def test_create_profile(self):
        """Test profile creation."""
        manager = AgentProfileManager()
        
        profile = manager.create_profile(
            name="Custom Agent",
            role="Custom Role",
            goal="Custom goal"
        )
        
        assert profile.name == "Custom Agent"
        assert profile.id is not None
    
    def test_from_persona(self):
        """Test creating from persona."""
        manager = AgentProfileManager()
        
        profile = manager.from_persona("senior_researcher")
        
        assert profile.name == "Senior Researcher"
        assert len(profile.skills) > 0
    
    def test_from_persona_with_overrides(self):
        """Test creating from persona with overrides."""
        manager = AgentProfileManager()
        
        profile = manager.from_persona(
            "content_writer",
            name="Custom Writer",
            model="gpt-4"
        )
        
        assert profile.name == "Custom Writer"
        assert profile.model == "gpt-4"
    
    def test_team_compatibility(self):
        """Test team compatibility calculation."""
        manager = AgentProfileManager()
        
        profiles = [
            manager.from_persona("senior_researcher"),
            manager.from_persona("content_writer"),
            manager.from_persona("quality_assurer"),
        ]
        
        compatibility = manager.calculate_team_compatibility(profiles)
        assert 0 <= compatibility <= 1
    
    def test_find_best_match(self):
        """Test finding best agent for skills."""
        manager = AgentProfileManager()
        
        manager.from_persona("senior_researcher")
        manager.from_persona("content_writer")
        manager.from_persona("data_analyst")
        
        best = manager.find_best_match("analysis", ["Research", "Analysis"])
        assert best is not None


# ============================================================
# TASKS TESTS
# ============================================================

class TestTasks:
    """Test task management."""
    
    def test_task_templates_loaded(self):
        """Test task templates are loaded."""
        assert len(TASK_TEMPLATES) > 0
        assert "web_research" in TASK_TEMPLATES
    
    def test_create_task(self):
        """Test task creation."""
        manager = TaskManager()
        
        task = manager.create_task(
            name="Test Task",
            description="A test task",
            task_type=TaskType.RESEARCH
        )
        
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
    
    def test_from_template(self):
        """Test creating from template."""
        manager = TaskManager()
        
        task = manager.from_template("web_research")
        
        assert task.name == "Web Research"
        assert task.type == TaskType.RESEARCH
    
    def test_task_dependencies(self):
        """Test task dependencies."""
        manager = TaskManager()
        
        task1 = manager.create_task(name="Task 1", description="First")
        task2 = manager.create_task(
            name="Task 2",
            description="Second",
            dependencies=[task1.id]
        )
        
        assert task1.id in task2.dependencies
    
    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        manager = TaskManager()
        
        task1 = manager.create_task(name="Task 1", description="First")
        task2 = manager.create_task(
            name="Task 2",
            description="Second",
            dependencies=[task1.id]
        )
        
        ready = manager.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == task1.id
        
        # Complete task 1
        manager.update_status(task1.id, TaskStatus.COMPLETED)
        
        ready = manager.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == task2.id


# ============================================================
# ENGINE TESTS
# ============================================================

class TestEngine:
    """Test orchestration engine."""
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test sequential orchestration."""
        manager = AgentProfileManager()
        agents = [
            manager.from_persona("senior_researcher"),
            manager.from_persona("content_writer"),
        ]
        
        config = TeamConfiguration(
            name="Test Team",
            agents=agents,
            mode=OrchestrationMode.SEQUENTIAL
        )
        
        engine = TeamOrchestrationEngine()
        execution = await engine.execute(config, {"topic": "AI trends"})
        
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.output is not None
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel orchestration."""
        manager = AgentProfileManager()
        agents = [
            manager.from_persona("data_analyst"),
            manager.from_persona("financial_analyst"),
        ]
        
        config = TeamConfiguration(
            name="Test Team",
            agents=agents,
            mode=OrchestrationMode.PARALLEL
        )
        
        engine = TeamOrchestrationEngine()
        execution = await engine.execute(config, {"data": "test"})
        
        assert execution.status == ExecutionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_hierarchical_execution(self):
        """Test hierarchical orchestration."""
        manager = AgentProfileManager()
        agents = [
            manager.from_persona("supervisor"),
            manager.from_persona("content_writer"),
            manager.from_persona("quality_assurer"),
        ]
        
        config = TeamConfiguration(
            name="Test Team",
            agents=agents,
            mode=OrchestrationMode.HIERARCHICAL
        )
        
        engine = TeamOrchestrationEngine()
        execution = await engine.execute(config, {"task": "write article"})
        
        assert execution.status == ExecutionStatus.COMPLETED
    
    def test_list_modes(self):
        """Test listing orchestration modes."""
        modes = TeamOrchestrationEngine.list_modes()
        
        assert len(modes) > 0
        assert "sequential" in modes
        assert "parallel" in modes


# ============================================================
# COMMUNICATION TESTS
# ============================================================

class TestCommunication:
    """Test communication layer."""
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message."""
        bus = MessageBus()
        
        msg = await bus.send(
            sender="agent1",
            recipients=["agent2"],
            content="Hello"
        )
        
        assert msg.id is not None
        assert msg.sender == "agent1"
    
    @pytest.mark.asyncio
    async def test_get_inbox(self):
        """Test getting inbox."""
        bus = MessageBus()
        
        await bus.send(
            sender="agent1",
            recipients=["agent2"],
            content="Message 1"
        )
        await bus.send(
            sender="agent1",
            recipients=["agent2"],
            content="Message 2"
        )
        
        inbox = bus.get_inbox("agent2")
        assert len(inbox) == 2
    
    @pytest.mark.asyncio
    async def test_reply(self):
        """Test replying to message."""
        bus = MessageBus()
        
        original = await bus.send(
            sender="agent1",
            recipients=["agent2"],
            content="Hello"
        )
        
        reply = await bus.reply(
            original.id,
            sender="agent2",
            content="Hi back"
        )
        
        assert reply.in_reply_to == original.id
    
    @pytest.mark.asyncio
    async def test_conversation(self):
        """Test conversation management."""
        bus = MessageBus()
        conv_manager = ConversationManager(bus)
        
        conv = conv_manager.create_conversation(
            participants=["agent1", "agent2"],
            topic="Discussion"
        )
        
        await conv_manager.add_message(conv.id, "agent1", "Hello")
        await conv_manager.add_message(conv.id, "agent2", "Hi")
        
        retrieved = conv_manager.get_conversation(conv.id)
        assert len(retrieved.messages) == 2


# ============================================================
# MEMORY TESTS
# ============================================================

class TestMemory:
    """Test memory system."""
    
    @pytest.mark.asyncio
    async def test_store_retrieve(self):
        """Test storing and retrieving."""
        memory = TeamMemorySpace("team1")
        
        await memory.store("key1", "value1", MemoryScope.WORKING)
        
        value = await memory.retrieve("key1", MemoryScope.WORKING)
        assert value == "value1"
    
    @pytest.mark.asyncio
    async def test_search(self):
        """Test memory search."""
        memory = TeamMemorySpace("team1")
        
        await memory.store("research_results", {"data": "test"}, MemoryScope.SEMANTIC)
        await memory.store("analysis_output", {"insights": []}, MemoryScope.SEMANTIC)
        
        results = await memory.search("research")
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_forget(self):
        """Test forgetting."""
        memory = TeamMemorySpace("team1")
        
        await memory.store("temp", "data", MemoryScope.WORKING)
        await memory.forget("temp", MemoryScope.WORKING)
        
        value = await memory.retrieve("temp", MemoryScope.WORKING)
        assert value is None
    
    @pytest.mark.asyncio
    async def test_shared_context(self):
        """Test getting shared context."""
        memory = TeamMemorySpace("team1")
        
        await memory.store("context1", "Data 1", MemoryScope.WORKING)
        await memory.store("context2", "Data 2", MemoryScope.WORKING)
        
        context = memory.get_shared_context()
        assert "Data 1" in context


# ============================================================
# AI TESTS
# ============================================================

class TestNLBuilder:
    """Test NL Team Builder."""
    
    @pytest.mark.asyncio
    async def test_build_content_team(self):
        """Test building content team."""
        builder = NLTeamBuilder()
        
        config = await builder.build_team(
            "Crie um time para escrever artigos sobre tecnologia"
        )
        
        assert config.name is not None
        assert len(config.agents) >= 2
    
    @pytest.mark.asyncio
    async def test_build_analysis_team(self):
        """Test building analysis team."""
        builder = NLTeamBuilder()
        
        config = await builder.build_team(
            "Preciso de um time de análise de dados com 3 especialistas"
        )
        
        assert len(config.agents) == 3
    
    @pytest.mark.asyncio
    async def test_suggest_mode(self):
        """Test mode suggestion."""
        builder = NLTeamBuilder()
        
        config = await builder.build_team(
            "Time hierárquico com supervisor para gerenciar desenvolvedores"
        )
        
        assert config.mode == OrchestrationMode.HIERARCHICAL


class TestOptimizer:
    """Test Team Optimizer."""
    
    @pytest.mark.asyncio
    async def test_optimize_team(self):
        """Test team optimization."""
        manager = AgentProfileManager()
        agents = [manager.from_persona("content_writer")]
        
        config = TeamConfiguration(
            name="Small Team",
            agents=agents,
            mode=OrchestrationMode.SEQUENTIAL
        )
        
        optimizer = TeamOptimizer()
        result = await optimizer.optimize(config, OptimizationObjective.BALANCED)
        
        assert len(result.suggestions) > 0
        assert result.confidence > 0


class TestConflictResolver:
    """Test Conflict Resolver."""
    
    @pytest.mark.asyncio
    async def test_resolve_voting(self):
        """Test voting resolution."""
        conflict = Conflict(
            type=ConflictType.OPINION_DIFFERENCE,
            parties=["agent1", "agent2", "agent3"],
            positions={
                "agent1": {"stance": "Option A"},
                "agent2": {"stance": "Option B"},
                "agent3": {"stance": "Option A"},
            }
        )
        
        resolver = ConflictResolver()
        resolution = await resolver.resolve(conflict, ResolutionStrategy.VOTING)
        
        assert resolution.outcome is not None


class TestLearning:
    """Test Agent Learning System."""
    
    @pytest.mark.asyncio
    async def test_learn_from_feedback(self):
        """Test learning from feedback."""
        learning = AgentLearningSystem()
        
        feedback = Feedback(
            execution_id="exec1",
            agent_id="agent1",
            rating=4.5,
            aspects={"quality": 4.0, "speed": 5.0}
        )
        
        result = await learning.learn_from_feedback(
            "agent1",
            "exec1",
            feedback
        )
        
        assert result["feedback_count"] == 1


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full team workflow."""
        # 1. Build team from NL
        builder = NLTeamBuilder()
        config = await builder.build_team(
            "Time para pesquisar e escrever sobre IA"
        )
        
        # 2. Execute team
        engine = get_orchestration_engine()
        execution = await engine.execute(config, {"topic": "AI 2024"})
        
        assert execution.status == ExecutionStatus.COMPLETED
        
        # 3. Optimize team
        optimizer = TeamOptimizer()
        optimization = await optimizer.optimize(
            config,
            OptimizationObjective.PERFORMANCE,
            history=[execution]
        )
        
        assert optimization.confidence > 0
    
    @pytest.mark.asyncio
    async def test_team_with_memory(self):
        """Test team with shared memory."""
        manager = AgentProfileManager()
        memory = TeamMemorySpace("team_test")
        
        # Store initial context
        await memory.store("topic", "AI Trends", MemoryScope.WORKING)
        
        agents = [
            manager.from_persona("senior_researcher"),
            manager.from_persona("content_writer"),
        ]
        
        config = TeamConfiguration(
            name="Memory Team",
            agents=agents,
            mode=OrchestrationMode.SEQUENTIAL,
            shared_memory_enabled=True
        )
        
        engine = TeamOrchestrationEngine()
        execution = await engine.execute(config, {
            "context": memory.get_shared_context()
        })
        
        assert execution.status == ExecutionStatus.COMPLETED


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
