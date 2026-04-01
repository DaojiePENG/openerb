"""Unit tests for Hippocampus module."""

import pytest
from datetime import datetime, timedelta
from openerb.core.types import Skill, RobotType, ExecutionResult
from openerb.modules.hippocampus import (
    LearningPreferences,
    SkillProgress,
    UserLearningProfile,
    LearningProfileManager,
    LearningEvent,
    LearningSession,
    LearningHistoryTracker,
    ConsolidationRecord,
    SpacedRepetitionSchedule,
    ConsolidationEngine,
    CompetencyScore,
    CompetencyMetrics,
    Hippocampus
)


class TestLearningProfileManager:
    """Test LearningProfileManager."""
    
    @pytest.fixture
    def manager(self):
        return LearningProfileManager()
    
    @pytest.fixture
    def sample_skill(self):
        skill = Skill(
            name="Basic Grasp",
            description="Basic grasping skill",
            code="def basic_grasp(): pass"
        )
        return skill
    
    def test_create_profile(self, manager):
        """Test creating a user profile."""
        profile = manager.create_profile("user_001", "Alice", RobotType.G1)
        
        assert profile.user_id == "user_001"
        assert profile.user_name == "Alice"
        assert profile.robot_type == RobotType.G1
        assert profile.total_skills_attempted == 0
    
    def test_get_profile(self, manager):
        """Test retrieving a user profile."""
        created = manager.create_profile("user_001", "Bob", RobotType.G1)
        retrieved = manager.get_profile("user_001")
        
        assert retrieved is not None
        assert retrieved.user_id == "user_001"
    
    def test_add_skill_progress(self, manager, sample_skill):
        """Test adding skill progress."""
        manager.create_profile("user_001", "Charlie", RobotType.G1)
        progress = manager.add_skill_progress("user_001", sample_skill)
        
        assert progress.skill_id == sample_skill.skill_id
        assert progress.execution_count == 0
        assert progress.success_rate == 0.0
    
    def test_update_skill_progress(self, manager, sample_skill):
        """Test updating skill progress."""
        manager.create_profile("user_001", "Diana", RobotType.G1)
        manager.add_skill_progress("user_001", sample_skill)
        
        manager.update_skill_progress("user_001", sample_skill.skill_id, success=True, execution_time=2.5)
        progress = manager.get_skill_progress("user_001", sample_skill.skill_id)
        
        assert progress.execution_count == 1
        assert progress.success_count == 1
        assert progress.success_rate == 1.0
    
    def test_mastery_level_progression(self, manager, sample_skill):
        """Test mastery level progression."""
        manager.create_profile("user_001", "Eve", RobotType.G1)
        manager.add_skill_progress("user_001", sample_skill)
        progress = manager.get_skill_progress("user_001", sample_skill.skill_id)
        
        assert progress.mastery_level == "novice"
        
        # Simulate successful executions
        for _ in range(15):
            manager.update_skill_progress("user_001", sample_skill.skill_id, success=True)
        
        progress = manager.get_skill_progress("user_001", sample_skill.skill_id)
        # Mastery should progress based on execution count
        assert progress.execution_count == 15


class TestLearningHistoryTracker:
    """Test LearningHistoryTracker."""
    
    @pytest.fixture
    def tracker(self):
        return LearningHistoryTracker()
    
    def test_start_and_end_session(self, tracker):
        """Test starting and ending sessions."""
        session = tracker.start_session("user_001", focus_skill="grasp_001")
        assert session is not None
        assert session.user_id == "user_001"
        
        ended = tracker.end_session()
        assert ended is not None
        assert ended.duration > 0
    
    def test_record_event(self, tracker):
        """Test recording learning events."""
        tracker.start_session("user_001")
        event = tracker.record_event(
            skill_id="grasp_001",
            skill_name="Basic Grasp",
            user_id="user_001",
            duration=2.5,
            success=True,
            confidence_before=0.5,
            confidence_after=0.6
        )
        
        assert event is not None
        assert event.success is True
        assert event.confidence_before == 0.5
    
    def test_get_user_history(self, tracker):
        """Test retrieving user history."""
        tracker.start_session("user_001")
        
        for i in range(5):
            tracker.record_event(
                skill_id="grasp_001",
                skill_name="Grasp",
                user_id="user_001",
                duration=2.0,
                success=(i % 2 == 0),
                confidence_before=0.5,
                confidence_after=0.6
            )
        
        history = tracker.get_user_history("user_001", limit=10)
        assert len(history) == 5
    
    def test_get_skill_history(self, tracker):
        """Test retrieving skill history."""
        tracker.start_session("user_001")
        
        for i in range(3):
            tracker.record_event(
                skill_id="grasp_001",
                skill_name="Grasp",
                user_id="user_001",
                duration=2.0,
                success=True,
                confidence_before=0.5,
                confidence_after=0.6
            )
        
        history = tracker.get_skill_history("grasp_001")
        assert len(history) == 3
    
    def test_learning_stats(self, tracker):
        """Test learning statistics."""
        tracker.start_session("user_001")
        
        for i in range(10):
            tracker.record_event(
                skill_id="grasp_001",
                skill_name="Grasp",
                user_id="user_001",
                duration=2.0 + i * 0.1,
                success=(i < 7),  # 70% success rate
                confidence_before=0.5,
                confidence_after=0.6
            )
        
        stats = tracker.get_learning_stats("user_001", days=7)
        assert stats["total_events"] == 10
        assert stats["success_rate"] == 0.7


class TestConsolidationEngine:
    """Test ConsolidationEngine."""
    
    @pytest.fixture
    def engine(self):
        return ConsolidationEngine()
    
    def test_consolidate_skill(self, engine):
        """Test skill consolidation."""
        consolidated, record = engine.consolidate_skill(
            skill_id="grasp_001",
            skill_name="Basic Grasp",
            user_id="user_001",
            confidence=0.8,
            success_rate=0.85,
            execution_count=10
        )
        
        assert record is not None
        assert record.skill_id == "grasp_001"
    
    def test_spaced_repetition_schedule(self, engine):
        """Test spaced repetition schedule."""
        engine.consolidate_skill(
            skill_id="grasp_001",
            skill_name="Grasp",
            user_id="user_001",
            confidence=0.8,
            success_rate=0.8,
            execution_count=10
        )
        
        schedule = engine.get_skill_schedule("grasp_001", "user_001")
        assert schedule is not None
        assert schedule.review_count == 0
    
    def test_record_review(self, engine):
        """Test recording reviews."""
        engine.consolidate_skill(
            skill_id="grasp_001",
            skill_name="Grasp",
            user_id="user_001",
            confidence=0.8,
            success_rate=0.8,
            execution_count=10
        )
        
        schedule = engine.record_review("grasp_001", "user_001", quality=4)
        assert schedule is not None
        assert schedule.review_count == 1
    
    def test_memory_decay_calculation(self, engine):
        """Test memory decay calculation."""
        consolidation_time = datetime.now() - timedelta(days=30)
        decay = engine.calculate_memory_decay(consolidation_time)
        
        assert 0.0 <= decay <= 1.0
        # After 30 days, decay should present but not too severe (depends on decay_rate)
        assert decay > 0.5


class TestCompetencyMetrics:
    """Test CompetencyMetrics."""
    
    @pytest.fixture
    def metrics(self):
        return CompetencyMetrics()
    
    def test_calculate_competency(self, metrics):
        """Test competency calculation."""
        score = metrics.calculate_competency(
            skill_id="grasp_001",
            skill_name="Grasp",
            user_id="user_001",
            success_rate=0.9,
            average_duration=2.0,
            execution_count=15,
            confidence=0.85
        )
        
        assert score is not None
        assert score.overall_score > 0
        assert score.technical_score > 0
    
    def test_competency_tier(self, metrics):
        """Test competency tier classification."""
        tier_novice = metrics.get_competency_tier(15)
        tier_advanced = metrics.get_competency_tier(55)
        tier_expert = metrics.get_competency_tier(75)
        
        assert tier_novice == "novice"
        assert tier_advanced == "advanced"
        assert tier_expert == "expert"
    
    def test_rank_skills(self, metrics):
        """Test skill ranking."""
        # Create multiple skill scores
        for i in range(5):
            metrics.calculate_competency(
                skill_id=f"skill_{i}",
                skill_name=f"Skill {i}",
                user_id="user_001",
                success_rate=0.7 + i * 0.05,
                average_duration=2.0,
                execution_count=10,
                confidence=0.7 + i * 0.05
            )
        
        ranked = metrics.rank_skills("user_001")
        assert len(ranked) == 5
        assert ranked[0].overall_score >= ranked[-1].overall_score
    
    def test_user_summary(self, metrics):
        """Test user competency summary."""
        metrics.calculate_competency(
            skill_id="grasp_001",
            skill_name="Grasp",
            user_id="user_001",
            success_rate=0.8,
            average_duration=2.0,
            execution_count=10,
            confidence=0.8
        )
        
        summary = metrics.get_user_summary("user_001")
        assert summary["total_skills"] == 1
        assert summary["average_overall_score"] > 0


class TestHippocampus:
    """Test Hippocampus main API."""
    
    @pytest.fixture
    def hippocampus(self):
        return Hippocampus()
    
    @pytest.fixture
    def sample_skill(self):
        skill = Skill(
            name="Basic Grasp",
            description="Basic grasping skill",
            code="def basic_grasp(): pass"
        )
        return skill
    
    def test_create_user_profile(self, hippocampus):
        """Test creating user profile through Hippocampus."""
        profile = hippocampus.create_user_profile(
            "user_001", "Alice", RobotType.G1
        )
        
        assert profile is not None
        assert profile.user_id == "user_001"
    
    def test_start_learning(self, hippocampus, sample_skill):
        """Test starting learning through Hippocampus."""
        hippocampus.create_user_profile("user_001", "Bob", RobotType.G1)
        progress, session = hippocampus.start_learning(
            "user_001", sample_skill
        )
        
        assert progress is not None
        assert session is not None
        assert progress.skill_id == sample_skill.skill_id
    
    def test_record_skill_execution(self, hippocampus, sample_skill):
        """Test recording skill execution."""
        hippocampus.create_user_profile("user_001", "Charlie", RobotType.G1)
        hippocampus.start_learning("user_001", sample_skill)
        
        progress, event = hippocampus.record_skill_execution(
            user_id="user_001",
            skill=sample_skill,
            success=True,
            duration=2.5
        )
        
        assert event is not None
        assert event.success is True
    
    def test_complete_learning_session(self, hippocampus, sample_skill):
        """Test completing learning session."""
        hippocampus.create_user_profile("user_001", "Diana", RobotType.G1)
        hippocampus.start_learning("user_001", sample_skill)
        
        session = hippocampus.complete_learning_session("user_001")
        assert session is not None
    
    def test_consolidate_learning(self, hippocampus, sample_skill):
        """Test consolidating learning."""
        hippocampus.create_user_profile("user_001", "Eve", RobotType.G1)
        hippocampus.start_learning("user_001", sample_skill)
        
        # Record successful executions
        for _ in range(5):
            hippocampus.record_skill_execution(
                "user_001", sample_skill, success=True, duration=2.0
            )
        
        consolidated, record = hippocampus.consolidate_learning(
            "user_001", sample_skill.skill_id
        )
        
        assert record is not None
    
    def test_calculate_competency(self, hippocampus, sample_skill):
        """Test calculating competency through Hippocampus."""
        hippocampus.create_user_profile("user_001", "Frank", RobotType.G1)
        hippocampus.start_learning("user_001", sample_skill)
        
        for _ in range(10):
            hippocampus.record_skill_execution(
                "user_001", sample_skill, success=True, duration=2.0
            )
        
        score = hippocampus.calculate_competency("user_001", sample_skill.skill_id)
        assert score is not None
        assert score.overall_score > 0
    
    def test_get_learning_summary(self, hippocampus, sample_skill):
        """Test getting learning summary."""
        hippocampus.create_user_profile("user_001", "Grace", RobotType.G1)
        hippocampus.start_learning("user_001", sample_skill)
        
        for _ in range(5):
            hippocampus.record_skill_execution(
                "user_001", sample_skill, success=True, duration=2.0
            )
        
        summary = hippocampus.get_learning_summary("user_001")
        assert summary["user_id"] == "user_001"
        assert "profile" in summary
        assert "stats" in summary
    
    def test_get_skill_insights(self, hippocampus, sample_skill):
        """Test getting skill insights."""
        hippocampus.create_user_profile("user_001", "Harper", RobotType.G1)
        hippocampus.start_learning("user_001", sample_skill)
        
        for _ in range(5):
            hippocampus.record_skill_execution(
                "user_001", sample_skill, success=True, duration=2.0
            )
        
        insights = hippocampus.get_skill_insights("user_001", sample_skill.skill_id)
        assert insights["skill_id"] == sample_skill.skill_id
        assert "progress" in insights
        assert "analytics" in insights
    
    def test_system_status(self, hippocampus):
        """Test system status."""
        status = hippocampus.get_system_status()
        
        assert status["status"] == "healthy"
        assert "components" in status
        assert "profile_manager" in status["components"]
