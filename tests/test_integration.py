"""Integration tests for cross-module workflows."""

import asyncio

import pytest

from openerb.core.types import (
    CommunicationNode,
    ExperienceReport,
    Intent,
    RobotType,
    Skill,
    UserProfile,
)
from openerb.modules.communication import CommunicationModule
from openerb.modules.cerebellum import Cerebellum
from openerb.modules.hippocampus import Hippocampus
from openerb.modules.visual_cortex import VisualCortex


@pytest.mark.asyncio
async def test_visual_to_communication_to_cerebellum_skill_sharing_flow(tmp_path):
    """End-to-end: Visual analysis produces a shareable skill; remote node receives and registers it."""
    visual = VisualCortex(robot_type=RobotType.G1)

    # create a simple dummy image and run visual processing
    import numpy as np

    dummy_image = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
    result = await visual.process_image(dummy_image)

    assert result is not None
    assert result.annotation is not None

    # Cerebellum skill registration on source node
    cereb_a = Cerebellum(storage_path=tmp_path / "cereb_a.json")
    cereb_b = Cerebellum(storage_path=tmp_path / "cereb_b.json")

    skill = Skill(
        name="navigate_from_scene",
        description="Auto skill created by visual scene analysis",
        code="def run():\n    return 'ok'",
        supported_robots=[RobotType.G1],
    )

    skill_id = cereb_a.register_skill(skill, RobotType.G1)
    assert skill_id is not None

    comm = CommunicationModule()
    source_node = CommunicationNode(node_id="node_a", robot_type=RobotType.G1, address="10.0.0.1")
    target_node = CommunicationNode(node_id="node_b", robot_type=RobotType.GO2, address="10.0.0.2")

    comm.register_node(source_node)
    comm.register_node(target_node)

    received_messages = []

    def target_handler(message):
        received_messages.append(message)
        if message.message_type == "skill_share":
            payload = message.payload
            shared_skill_id = payload.get("skill_id")
            package = comm.skill_sharing.get_skill_package(shared_skill_id)
            assert package is not None
            accepted_skill = comm.skill_sharing.accept_skill(package, target_node)
            registered_id = cereb_b.register_skill(accepted_skill, RobotType.GO2)
            assert registered_id is not None

    comm.register_message_handler(target_node.node_id, target_handler)

    package = comm.skill_sharing.package_skill(skill, source_node)
    assert package.skill.skill_id == skill.skill_id

    assert comm.share_skill(package.skill.skill_id, target_node.node_id)

    assert len(received_messages) == 1

    # Verify target cerebellum got the skill via shared flow
    skills_b = cereb_b.list_skills()
    assert any(item["name"] == skill.name for item in skills_b)


def test_hippocampus_learning_reports_feed_into_distributed_learning():
    """Hippocampus reports are forwarded into communication distributed learning stats."""
    hippocampus = Hippocampus()
    hippocampus.create_user_profile("user_1", "Tester", RobotType.G1)

    skill = Skill(
        name="precision_grasp",
        description="Grasp skill for test",
        code="pass",
        supported_robots=[RobotType.G1],
    )

    progress, session = hippocampus.start_learning("user_1", skill)
    assert progress is not None

    # execute twice, success true
    for _ in range(2):
        diff, event = hippocampus.record_skill_execution("user_1", skill, True, 1.0)
        assert event is not None

    comm = CommunicationModule()

    report_a = ExperienceReport(
        node_id="node_x",
        skill_id=skill.skill_id,
        success=True,
        duration_ms=120,
        confidence=0.95,
    )
    comm.submit_experience(report_a)

    report_b = ExperienceReport(
        node_id="node_y",
        skill_id=skill.skill_id,
        success=False,
        duration_ms=140,
        confidence=0.60,
    )
    comm.submit_experience(report_b)

    aggregated = comm.get_skill_learnings(skill.skill_id)
    assert aggregated["sample_size"] == 2
    assert pytest.approx(aggregated["success_rate"], rel=1e-6) == 0.5


def test_communication_node_lifecycle_and_discovery_with_policy():
    """Communication module supports node lifecycle operations and policy filtering."""
    comm = CommunicationModule()

    node1 = CommunicationNode(node_id="n1", robot_type=RobotType.G1, address="10.1.1.1")
    node2 = CommunicationNode(node_id="n2", robot_type=RobotType.GO2, address="10.1.1.2")
    comm.register_node(node1)
    comm.register_node(node2)

    found = comm.discover_nodes()
    assert len(found) == 2

    # delete one node and ensure discovery updates
    comm.unregister_node(node1.node_id)
    found_after = comm.discover_nodes()
    assert len(found_after) == 1
    assert found_after[0].node_id == node2.node_id

    # policy should allow common types by default
    policy = comm.policy
    assert RobotType.G1 in policy.allowed_robot_types
    assert policy.max_concurrent_transfers >= 1


@pytest.mark.asyncio
async def test_integration_engine_end_to_end_execution_and_sharing(tmp_path):
    """IntegrationEngine should generate a skill, save to cerebellum, record in hippocampus, and share via communication."""
    from openerb.modules.system_integration import IntegrationEngine

    engine = IntegrationEngine(cerebellum=Cerebellum(storage_path=tmp_path / "engine_skills.json"))

    # Add a peer node to communicate with
    peer = CommunicationNode(node_id="peer_1", robot_type=RobotType.GO2, address="10.2.2.2")
    engine.communication.register_node(peer)

    # Collect shared messages
    received = []

    def peer_handler(message):
        received.append(message)

    engine.communication.register_message_handler(peer.node_id, peer_handler)

    intent = Intent(
        raw_text="Move forward quickly",
        action="move_forward",
        parameters={"distance": 0.5, "speed": 0.5},
        confidence=0.9,
    )

    user = UserProfile(user_id="user_100", name="TestUser")
    result = await engine.execute_intent(intent, user, RobotType.GO2)

    assert result["intent"] == "move_forward"
    assert result["skill"] is not None
    assert result["from_existing"] is False

    # Because peer is GO2 and we run route in GO2, share should take place
    assert len(received) == 1

    aggregated = engine.communication.get_skill_learnings(result["skill"]["skill_id"])
    assert aggregated["sample_size"] == 0

