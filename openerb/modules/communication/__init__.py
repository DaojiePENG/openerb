"""Communication module - robot cooperation and distributed learning."""

from openerb.modules.communication.communication import CommunicationModule
from openerb.modules.communication.network_protocol import NetworkProtocol
from openerb.modules.communication.skill_sharing import SkillSharingManager
from openerb.modules.communication.distributed_learning import DistributedLearningManager

__all__ = [
    "CommunicationModule",
    "NetworkProtocol",
    "SkillSharingManager",
    "DistributedLearningManager",
]
