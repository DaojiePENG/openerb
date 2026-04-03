from typing import Dict, Optional, List

from openerb.core.logger import get_logger
from openerb.core.types import SkillPackage, Skill, CommunicationNode

logger = get_logger("skill_sharing")


class SkillSharingManager:
    """Handles shared skills between robots in a communication network."""

    def __init__(self):
        self.shared_skill_store: Dict[str, SkillPackage] = {}

    def package_skill(self, skill: Skill, source_node: CommunicationNode) -> SkillPackage:
        package = SkillPackage(
            skill=skill,
            metadata={
                "source_node": source_node.node_id,
                "shared_at": source_node.last_seen.isoformat(),
            },
            source_robot_id=source_node.node_id,
        )
        self.shared_skill_store[skill.skill_id] = package
        logger.debug("Packaged skill %s from %s", skill.skill_id, source_node.node_id)
        return package

    def get_skill_package(self, skill_id: str) -> Optional[SkillPackage]:
        return self.shared_skill_store.get(skill_id)

    def list_shared_skills(self) -> List[SkillPackage]:
        return list(self.shared_skill_store.values())

    def request_skill(self, skill_id: str, target_node: CommunicationNode) -> Optional[SkillPackage]:
        package = self.shared_skill_store.get(skill_id)
        if not package:
            logger.warning("Skill %s not found in shared store", skill_id)
            return None
        logger.info("Node %s requested skill %s", target_node.node_id, skill_id)
        return package

    def accept_skill(self, package: SkillPackage, target_node: CommunicationNode) -> Skill:
        cloned = Skill(
            name=package.skill.name,
            description=package.skill.description,
            code=package.skill.code,
            dependencies=list(package.skill.dependencies),
            tags=list(package.skill.tags),
            supported_robots=list(package.skill.supported_robots),
            status=package.skill.status,
            skill_type=package.skill.skill_type,
        )
        logger.info("Node %s accepted skill %s", target_node.node_id, cloned.skill_id)
        return cloned
