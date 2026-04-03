"""Unit tests for Communication module."""

import pytest

from openerb.core.types import (
    CommunicationNode,
    Message,
    ExperienceReport,
    RobotType,
    Skill,
)
from openerb.modules.communication import (
    NetworkProtocol,
    SkillSharingManager,
    DistributedLearningManager,
    CommunicationModule,
)


class TestNetworkProtocol:
    def test_register_and_discover_nodes(self):
        net = NetworkProtocol()
        node1 = CommunicationNode(node_id="node1", robot_type=RobotType.G1, address="192.168.0.1")
        node2 = CommunicationNode(node_id="node2", robot_type=RobotType.GO2, address="192.168.0.2")

        net.register_node(node1)
        net.register_node(node2)

        found = net.discover_nodes()
        assert len(found) == 2

        spark = net.discover_nodes(robot_type=RobotType.GO2.value)
        assert len(spark) == 1

    def test_send_message_to_handler(self):
        net = NetworkProtocol()
        node_recv = CommunicationNode(node_id="node_recv", robot_type=RobotType.G1, address="127.0.0.1")
        net.register_node(node_recv)

        received = []

        def handler(msg: Message):
            received.append(msg)

        net.register_message_handler("node_recv", handler)

        msg = Message(
            message_id="m1",
            sender_id="node_sender",
            receiver_id="node_recv",
            message_type="test",
            payload={"x": 1},
        )

        assert net.send_message(msg) is True
        assert len(received) == 1
        assert received[0].payload["x"] == 1


class TestSkillSharingManager:
    def test_package_and_request_skill(self):
        manager = SkillSharingManager()
        source_node = CommunicationNode(node_id="source", robot_type=RobotType.G1, address="1.1.1.1")
        skill = Skill(name="test", description="desc", code="pass")

        package = manager.package_skill(skill, source_node)
        assert package.skill.skill_id == skill.skill_id

        retrieved = manager.request_skill(skill.skill_id, source_node)
        assert retrieved is not None

        accepted = manager.accept_skill(package, source_node)
        assert accepted.name == skill.name
        assert accepted.skill_id != skill.skill_id


class TestDistributedLearningManager:
    def test_submit_and_aggregate_report(self):
        dlm = DistributedLearningManager()
        report1 = ExperienceReport(node_id="node1", skill_id="s1", success=True, duration_ms=100, confidence=0.8)
        report2 = ExperienceReport(node_id="node2", skill_id="s1", success=False, duration_ms=150, confidence=0.5)

        dlm.submit_report(report1)
        dlm.submit_report(report2)

        agg = dlm.aggregate_for_skill("s1")
        assert pytest.approx(agg["success_rate"], rel=1e-3) == 0.5
        assert agg["sample_size"] == 2

        trending = dlm.get_trending_skills(top_n=1)
        assert trending == ["s1"]


class TestCommunicationModule:
    def test_integration_skill_sharing_and_experience(self):
        comm = CommunicationModule()

        node_a = CommunicationNode(node_id="n_a", robot_type=RobotType.G1, address="10.0.0.1")
        node_b = CommunicationNode(node_id="n_b", robot_type=RobotType.GO2, address="10.0.0.2")

        comm.register_node(node_a)
        comm.register_node(node_b)

        # Register handler for node_b to receive skill share message
        received = []

        def handle(msg):
            received.append(msg)

        comm.register_message_handler("n_b", handle)

        # Share a skill via SkillSharingManager.
        skill = Skill(name="navigate", description="navigate", code="pass")
        pkg = comm.skill_sharing.package_skill(skill, node_a)

        msg = Message(
            message_id="mshare",
            sender_id="n_a",
            receiver_id="n_b",
            message_type="skill_share",
            payload={"skill_id": skill.skill_id},
        )

        assert comm.send_message(msg)
        assert len(received) == 1

        # Experience reports aggregation
        report = ExperienceReport(node_id="n_b", skill_id=skill.skill_id, success=True, duration_ms=200, confidence=0.9)
        comm.submit_experience(report)

        aggregated = comm.get_skill_learnings(skill.skill_id)
        assert aggregated["sample_size"] == 1
        assert aggregated["success_rate"] == 1.0
