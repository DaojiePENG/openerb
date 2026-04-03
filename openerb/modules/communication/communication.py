from typing import List, Optional

from openerb.core.logger import get_logger
from openerb.core.types import CommunicationNode, Message, ExperienceReport, CollaborationPolicy
from openerb.modules.communication.network_protocol import NetworkProtocol
from openerb.modules.communication.skill_sharing import SkillSharingManager
from openerb.modules.communication.distributed_learning import DistributedLearningManager

logger = get_logger("communication")


class CommunicationModule:
    """High-level communication and collaboration manager."""

    def __init__(self, policy: Optional[CollaborationPolicy] = None):
        self.network = NetworkProtocol()
        self.skill_sharing = SkillSharingManager()
        self.distributed_learning = DistributedLearningManager()
        self.policy = policy or CollaborationPolicy()

    def register_node(self, node: CommunicationNode):
        logger.info("Register node %s", node.node_id)
        self.network.register_node(node)

    def unregister_node(self, node_id: str):
        logger.info("Unregister node %s", node_id)
        self.network.unregister_node(node_id)

    def discover_nodes(self, robot_type: Optional[str] = None) -> List[CommunicationNode]:
        return self.network.discover_nodes(robot_type)

    def register_message_handler(self, node_id: str, handler):
        self.network.register_message_handler(node_id, handler)

    def send_message(self, message: Message) -> bool:
        return self.network.send_message(message)

    def share_skill(self, skill_package_id: str, target_node_id: str) -> bool:
        package = self.skill_sharing.get_skill_package(skill_package_id)
        if not package:
            logger.warning("Skill package %s not found", skill_package_id)
            return False

        skill_request = Message(
            message_id=f"share-{package.skill.skill_id}-{target_node_id}",
            sender_id=package.source_robot_id or "unknown",
            receiver_id=target_node_id,
            message_type="skill_share",
            payload={"skill_id": package.skill.skill_id, "skill_data": package.skill},
        )
        return self.send_message(skill_request)

    def submit_experience(self, report: ExperienceReport):
        self.distributed_learning.submit_report(report)

    def get_skill_learnings(self, skill_id: str):
        return self.distributed_learning.aggregate_for_skill(skill_id)

    def get_trending_skills(self, top_n: int = 5):
        return self.distributed_learning.get_trending_skills(top_n)

    def clear(self):
        self.network = NetworkProtocol()
        self.skill_sharing = SkillSharingManager()
        self.distributed_learning = DistributedLearningManager()
