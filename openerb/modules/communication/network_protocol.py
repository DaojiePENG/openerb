from datetime import datetime
from typing import Dict, List, Optional, Callable

from openerb.core.logger import get_logger
from openerb.core.types import CommunicationNode, Message

logger = get_logger("network_protocol")


class NetworkProtocol:
    """Basic robot-to-robot network protocol for registration and message exchange."""

    def __init__(self):
        self.nodes: Dict[str, CommunicationNode] = {}
        self._message_handlers: Dict[str, Callable[[Message], None]] = {}

    def register_node(self, node: CommunicationNode):
        logger.debug("Registering node: {}", node)
        node.last_seen = datetime.now()
        self.nodes[node.node_id] = node

    def unregister_node(self, node_id: str):
        if node_id in self.nodes:
            logger.debug("Unregistering node: {}", node_id)
            del self.nodes[node_id]

    def discover_nodes(self, robot_type: Optional[str] = None) -> List[CommunicationNode]:
        if robot_type:
            result = [n for n in self.nodes.values() if n.robot_type.value == robot_type]
        else:
            result = list(self.nodes.values())
        logger.debug("Discover nodes for robot_type={} -> {}", robot_type, len(result))
        return result

    def register_message_handler(self, node_id: str, handler: Callable[[Message], None]):
        logger.debug("Register message handler for {}", node_id)
        self._message_handlers[node_id] = handler

    def send_message(self, message: Message) -> bool:
        logger.debug("Sending message {} from {} to {}", message.message_type, message.sender_id, message.receiver_id)
        target_handler = self._message_handlers.get(message.receiver_id)
        if not target_handler:
            logger.warning("No message handler found for node %s", message.receiver_id)
            return False

        # Simulate network delivery with callback
        target_handler(message)
        return True
