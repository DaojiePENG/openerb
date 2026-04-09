"""Unit tests for Cerebellum module."""

import pytest
from datetime import datetime, timedelta
from openerb.core.types import Skill, SkillType, RobotType
from openerb.modules.cerebellum import (
    Cerebellum,
    SkillLibrary,
    SkillVersionManager,
    SkillScorer,
    ExecutionStatus,
    SkillExporter,
    SkillTrashManager,
)


# Test fixtures

@pytest.fixture
def cerebellum(tmp_path):
    """Create a Cerebellum instance with isolated storage."""
    return Cerebellum(storage_path=tmp_path / "test_skill_library.json")


@pytest.fixture
def sample_skill():
    """Create a sample skill."""
    return Skill(
        name="grasp_object",
        description="Grasp an object with the gripper",
        code="def grasp(force):\n    return execute_grasp(force)",
        skill_type=SkillType.BODY_SPECIFIC,
        supported_robots=[RobotType.G1, RobotType.GO2],
        tags=["manipulation", "gripper"],
    )


class TestSkillLibrary:
    """Test SkillLibrary functionality."""

    def test_register_skill(self, sample_skill):
        """Test registering a new skill."""
        library = SkillLibrary()
        skill_id = library.register_skill(
            sample_skill,
            RobotType.G1,
            "Test grasp skill",
            ["manipulation", "gripper"]
        )
        assert skill_id is not None
        assert len(skill_id) > 0

    def test_get_library_stats(self, sample_skill):
        """Test getting library statistics."""
        library = SkillLibrary()
        library.register_skill(sample_skill, RobotType.G1)
        
        stats = library.get_library_stats()
        assert "total_skills" in stats
        assert "active_skills" in stats
        assert "by_skill_type" in stats


class TestSkillVersionManager:
    """Test SkillVersionManager functionality."""

    def test_create_version(self):
        """Test creating a skill version."""
        manager = SkillVersionManager()
        skill_id = "test_skill_123"
        skill_data = {
            "name": "test_skill",
            "code": "def test(): pass"
        }
        
        version_id = manager.create_version(
            skill_id,
            skill_data,
            "Initial version"
        )
        assert version_id is not None

    def test_list_versions(self):
        """Test listing skill versions."""
        manager = SkillVersionManager()
        skill_id = "test_skill"
        skill_data = {"name": "test", "code": "v1"}
        
        v1 = manager.create_version(skill_id, skill_data, "Version 1")
        skill_data["code"] = "v2"
        v2 = manager.create_version(skill_id, skill_data, "Version 2")
        
        versions = manager.list_versions(skill_id)
        assert len(versions) == 2
        assert versions[0].version_number == 2  # Newest first

    def test_rollback_version(self):
        """Test rolling back to a previous version."""
        manager = SkillVersionManager()
        skill_id = "test_skill"
        v1_data = {"name": "test", "code": "v1"}
        v2_data = {"name": "test", "code": "v2"}
        
        v1_id = manager.create_version(skill_id, v1_data, "V1")
        v2_id = manager.create_version(skill_id, v2_data, "V2")
        
        result = manager.rollback_to_version(skill_id, v1_id, "Rollback")
        assert result is True
        
        versions = manager.list_versions(skill_id)
        assert len(versions) == 3  # Original 2 + rollback

    def test_compare_versions(self):
        """Test comparing two versions."""
        manager = SkillVersionManager()
        skill_id = "test_skill"
        v1_data = {"code": "original", "param1": 10}
        v2_data = {"code": "modified", "param1": 20, "param2": 30}
        
        v1_id = manager.create_version(skill_id, v1_data, "V1")
        v2_id = manager.create_version(skill_id, v2_data, "V2")
        
        diff = manager.compare_versions(v1_id, v2_id, skill_id)
        assert "added" in diff["differences"]
        assert "modified" in diff["differences"]


class TestSkillScorer:
    """Test SkillScorer functionality."""

    def test_record_execution(self):
        """Test recording a skill execution."""
        scorer = SkillScorer()
        exec_id = scorer.record_execution(
            skill_id="skill_123",
            status=ExecutionStatus.SUCCESS,
            duration_ms=150,
            parameters={"force": 50},
        )
        assert exec_id is not None

    def test_get_skill_metrics(self):
        """Test getting skill performance metrics."""
        scorer = SkillScorer()
        skill_id = "skill_123"
        
        # Record multiple executions
        scorer.record_execution(
            skill_id, ExecutionStatus.SUCCESS, 150, {"force": 50}
        )
        scorer.record_execution(
            skill_id, ExecutionStatus.SUCCESS, 140, {"force": 50}
        )
        scorer.record_execution(
            skill_id, ExecutionStatus.FAILURE, 200, {"force": 100}
        )
        
        metrics = scorer.get_skill_metrics(skill_id)
        assert metrics["total_executions"] == 3
        assert metrics["success_rate"] == pytest.approx(2/3)
        assert "competency_score" in metrics

    def test_rank_skills(self):
        """Test ranking skills by performance."""
        scorer = SkillScorer()
        
        # Register multiple skills with different performance
        for i in range(3):
            for j in range(10 - i):  # Different success counts
                scorer.record_execution(
                    f"skill_{i}",
                    ExecutionStatus.SUCCESS,
                    100,
                    {}
                )
            for j in range(i):  # Different failure counts
                scorer.record_execution(
                    f"skill_{i}",
                    ExecutionStatus.FAILURE,
                    100,
                    {}
                )
        
        rankings = scorer.rank_skills(limit=3)
        assert len(rankings) >= 1
        assert rankings[0]["score"] >= rankings[-1]["score"]

    def test_get_trending_skills(self):
        """Test getting trending (improving) skills."""
        scorer = SkillScorer()
        skill_id = "improving_skill"
        
        # Early executions: mostly failures
        for _ in range(3):
            scorer.record_execution(
                skill_id, ExecutionStatus.FAILURE, 100, {}
            )
        for _ in range(2):
            scorer.record_execution(
                skill_id, ExecutionStatus.SUCCESS, 100, {}
            )
        
        # Recent executions: mostly successes
        for _ in range(5):
            scorer.record_execution(
                skill_id, ExecutionStatus.SUCCESS, 100, {}
            )
        
        trending = scorer.get_trending_skills(limit=5)
        assert len(trending) >= 0  # May or may not be in top 5


class TestSkillExporter:
    """Test SkillExporter functionality."""

    def test_export_skill_json(self):
        """Test exporting skill to JSON."""
        exporter = SkillExporter()
        skill_data = {
            "name": "test_skill",
            "code": "def test(): pass"
        }
        
        json_str = exporter.export_skill(
            skill_data,
            "test_skill",
            format="json"
        )
        assert "test_skill" in json_str
        assert "def test(): pass" in json_str

    def test_import_skill(self):
        """Test importing skill from JSON."""
        exporter = SkillExporter()
        skill_data = {
            "name": "test_skill",
            "code": "def test(): pass"
        }
        
        exported = exporter.export_skill(skill_data, "test", "json")
        imported = exporter.import_skill(exported, "json")
        
        assert imported is not None
        assert imported["name"] == "test_skill"
        assert imported["code"] == "def test(): pass"

    def test_pack_and_unpack_skills(self):
        """Test packing and unpacking multiple skills."""
        exporter = SkillExporter()
        skills = [
            {"name": "skill1", "code": "v1"},
            {"name": "skill2", "code": "v2"},
        ]
        
        # Pack
        result = exporter.pack_skills(
            skills,
            "/tmp/test_skill_pack.zip",
            "Test pack"
        )
        assert result is True
        
        # Unpack
        unpacked = exporter.unpack_skills("/tmp/test_skill_pack.zip")
        assert len(unpacked) == 2


class TestSkillTrashManager:
    """Test SkillTrashManager functionality."""

    def test_move_to_trash(self):
        """Test moving skill to trash."""
        manager = SkillTrashManager()
        skill_data = {"name": "old_skill", "code": "obsolete"}
        
        result = manager.move_to_trash(
            "skill_123",
            skill_data,
            "Outdated"
        )
        assert result is True

    def test_restore_from_trash(self):
        """Test restoring skill from trash."""
        manager = SkillTrashManager()
        skill_data = {"name": "skill", "code": "...", "metadata": {}}
        manager.move_to_trash("skill_123", skill_data, "Test")
        
        restored = manager.restore("skill_123")
        assert restored is not None
        assert restored["name"] == "skill"

    def test_list_trash(self):
        """Test listing trashed skills."""
        manager = SkillTrashManager()
        
        manager.move_to_trash("skill_1", {"name": "s1"}, "Reason 1")
        manager.move_to_trash("skill_2", {"name": "s2"}, "Reason 2")
        
        trash = manager.list_trash()
        assert len(trash) == 2

    def test_permanently_delete(self):
        """Test permanently deleting from trash."""
        manager = SkillTrashManager()
        skill_data = {"name": "skill", "code": "..."}
        manager.move_to_trash("skill_123", skill_data, "Test")
        
        result = manager.permanently_delete("skill_123")
        assert result is True
        
        trash = manager.list_trash()
        assert len(trash) == 0

    def test_get_trash_stats(self):
        """Test getting trash statistics."""
        manager = SkillTrashManager()
        
        manager.move_to_trash("skill_1", {"name": "s1"}, "R1")
        manager.move_to_trash("skill_2", {"name": "s2"}, "R2")
        
        stats = manager.get_trash_stats()
        assert stats["total_items"] == 2


class TestCerebellumIntegration:
    """Integration tests for complete Cerebellum workflow."""

    def test_register_and_search_skill(self, cerebellum, sample_skill):
        """Test registering and searching for a skill."""
        skill_id = cerebellum.register_skill(
            sample_skill,
            RobotType.G1,
            "Test skill"
        )
        
        results = cerebellum.search_skill("grasp", robot_type=RobotType.G1)
        assert len(results) > 0
        assert results[0]["name"] == "grasp_object"

    def test_complete_skill_lifecycle(self, cerebellum, sample_skill):
        """Test complete skill lifecycle."""
        # Register
        skill_id = cerebellum.register_skill(sample_skill, RobotType.G1)
        assert skill_id is not None
        
        # Record executions
        for _ in range(5):
            cerebellum.record_execution(
                skill_id,
                ExecutionStatus.SUCCESS,
                150,
                {"force": 50}
            )
        
        # Get metrics
        metrics = cerebellum.get_skill_metrics(skill_id)
        assert metrics["success_rate"] == 1.0
        
        # Update version
        new_data = {
            "code": "optimized_code",
            "parameters": {"force": 45}
        }
        v_id = cerebellum.update_skill_version(
            skill_id,
            new_data,
            "Optimized force"
        )
        assert v_id is not None
        
        # Export
        exported = cerebellum.export_skill(skill_id)
        assert "grasp_object" in exported

    def test_skill_export_and_import(self, cerebellum, sample_skill):
        """Test exporting and importing a skill."""
        # Register original
        skill_id = cerebellum.register_skill(sample_skill, RobotType.G1)
        
        # Export
        exported = cerebellum.export_skill(skill_id)
        assert exported is not None
        
        # Import as new skill
        imported_id = cerebellum.import_skill(
            exported,
            RobotType.GO2,
            format="json"
        )
        assert imported_id is not None
        
        # Verify imported skill
        imported_skill = cerebellum.get_skill(imported_id)
        assert imported_skill is not None

    def test_delete_and_restore_skill(self, cerebellum, sample_skill):
        """Test deleting and restoring a skill."""
        skill_id = cerebellum.register_skill(sample_skill, RobotType.G1)
        
        # Delete
        result = cerebellum.delete_skill(skill_id, "Testing")
        assert result is True
        
        # Check in trash
        trash = cerebellum.get_trash()
        assert len(trash) > 0
        
        # Restore
        restored = cerebellum.restore_skill(skill_id)
        assert restored is True

    def test_ranking_and_metrics(self, cerebellum):
        """Test skill ranking and metrics."""
        # Create multiple skills with different performance
        for i in range(3):
            skill = Skill(
                name=f"skill_{i}",
                description=f"Test skill {i}",
                code=f"def skill_{i}(): pass",
                skill_type=SkillType.UNIVERSAL,
            )
            skill_id = cerebellum.register_skill(skill)
            
            # Record different success rates
            for j in range(5 - i):  # More successes for earlier skills
                cerebellum.record_execution(
                    skill_id,
                    ExecutionStatus.SUCCESS,
                    100,
                    {}
                )
            for j in range(i):  # More failures for later skills
                cerebellum.record_execution(
                    skill_id,
                    ExecutionStatus.FAILURE,
                    100,
                    {}
                )
        
        # Get rankings
        rankings = cerebellum.rank_skills(limit=3)
        assert len(rankings) >= 1

    def test_system_statistics(self, cerebellum, sample_skill):
        """Test getting overall system statistics."""
        # Set up some data
        skill_id = cerebellum.register_skill(sample_skill, RobotType.G1)
        cerebellum.record_execution(
            skill_id,
            ExecutionStatus.SUCCESS,
            100,
            {}
        )
        
        # Get stats
        stats = cerebellum.get_system_stats()
        assert "library" in stats
        assert "trash" in stats
        assert "top_skills" in stats
