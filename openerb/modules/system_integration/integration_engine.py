import logging
from typing import Optional, Dict, Any

from openerb.core.types import Intent, UserProfile, RobotType, Skill, CommunicationNode, SkillType, SkillStatus
from openerb.modules.cerebellum import Cerebellum
from openerb.modules.hippocampus import Hippocampus
from openerb.modules.communication import CommunicationModule
from openerb.modules.motor_cortex import MotorCortex

logger = logging.getLogger(__name__)


class IntegrationEngine:
    """Orchestrates cross-module workflows for autonomous decision making."""

    def __init__(
        self,
        cerebellum: Optional[Cerebellum] = None,
        hippocampus: Optional[Hippocampus] = None,
        communication: Optional[CommunicationModule] = None,
        motor_cortex: Optional[MotorCortex] = None,
    ):
        self.cerebellum = cerebellum or Cerebellum()
        self.hippocampus = hippocampus or Hippocampus()
        self.communication = communication or CommunicationModule()
        self.motor_cortex = motor_cortex or MotorCortex(simulation_mode=True)

    async def execute_intent(
        self,
        intent: Intent,
        user: Optional[UserProfile] = None,
        robot_type: RobotType = RobotType.G1,
    ) -> Dict[str, Any]:
        """Process intent end-to-end and share learned skill."""
        logger.info("IntegrationEngine.execute_intent: %s", intent.action)

        # 1. Search existing skill from Cerebellum
        existing = self.cerebellum.search_skill(intent.action, robot_type=robot_type)

        if existing:
            selected_skill = self.cerebellum.get_skill(existing[0]["skill_id"])
            logger.info("Found existing skill %s for intent %s", selected_skill.get("name"), intent.action)
            from_existing = True
        else:
            selected_skill = None
            from_existing = False

        # 2. Generate skill if needed
        generated_skill_obj = None
        if not selected_skill:
            # Use MotorCortex for new skill generation
            generated_skill_obj = await self.motor_cortex.generate_skill(intent)
            if not generated_skill_obj:
                raise RuntimeError("Motor cortex failed to generate skill")

            # Register generated skill in cerebellum
            skill_id = self.cerebellum.register_skill(generated_skill_obj, robot_type)
            logger.info("Registered new skill %s in Cerebellum with id %s", generated_skill_obj.name, skill_id)
            selected_skill = self.cerebellum.get_skill(skill_id)

        # 3. Record in hippocampus for user learning
        if user:
            self.hippocampus.create_user_profile(user.user_id, user.name or "anonymous", robot_type)
            # Convert dict to Skill object properly - map cerebellum dict to Skill fields
            skill_dict = {
                "skill_id": selected_skill.get("id"),
                "name": selected_skill.get("name"),
                "description": selected_skill.get("description"),
                "code": selected_skill.get("code"),
                "skill_type": SkillType(selected_skill.get("skill_type")),
                "dependencies": selected_skill.get("dependencies", []),
                "tags": selected_skill.get("tags", []),
                "supported_robots": [RobotType(r) for r in selected_skill.get("supported_robots", [])],
                "status": SkillStatus(selected_skill.get("status")),
            }
            skill_obj = Skill(**skill_dict)
            self.hippocampus.start_learning(user.user_id, skill_obj)
        else:
            logger.debug("No user context available for Hippocampus record")

        # 4. Share skill with peers (if discovered)
        peers = self.communication.discover_nodes(robot_type=robot_type.value)
        if peers:
            # Create Skill object for packaging - same mapping as above
            skill_dict = {
                "skill_id": selected_skill.get("id"),
                "name": selected_skill.get("name"),
                "description": selected_skill.get("description"),
                "code": selected_skill.get("code"),
                "skill_type": SkillType(selected_skill.get("skill_type")),
                "dependencies": selected_skill.get("dependencies", []),
                "tags": selected_skill.get("tags", []),
                "supported_robots": [RobotType(r) for r in selected_skill.get("supported_robots", [])],
                "status": SkillStatus(selected_skill.get("status")),
            }
            skill_obj = Skill(**skill_dict)
            pkg = self.communication.skill_sharing.package_skill(skill_obj,
                                                              CommunicationNode(node_id="self", robot_type=robot_type, address="127.0.0.1"))
            for peer in peers:
                try:
                    self.communication.share_skill(pkg.skill.skill_id, peer.node_id)
                except Exception as e:
                    logger.warning("Failed to share skill with %s: %s", peer.node_id, e)

        # Prepare skill dict for return (ensure skill_id key exists)
        skill_return = dict(selected_skill)
        if "id" in skill_return and "skill_id" not in skill_return:
            skill_return["skill_id"] = skill_return["id"]

        return {
            "intent": intent.action,
            "skill": skill_return,
            "from_existing": from_existing,
            "user_id": user.user_id if user else None,
        }
