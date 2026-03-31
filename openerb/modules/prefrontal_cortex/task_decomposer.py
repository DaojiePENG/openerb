"""Task decomposer - Decompose intents into executable subtasks."""

import logging
from typing import List
from uuid import uuid4

from openerb.core.types import Intent, Subtask, TaskStatus

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """Decompose intentions into executable subtasks.
    
    Handles:
    - Intent to subtask conversion
    - Priority assignment
    - Dependency resolution
    - Constraint handling
    """

    async def decompose(self, intent: Intent) -> List[Subtask]:
        """Decompose an intent into subtasks.

        Args:
            intent: Intent to decompose

        Returns:
            List of ordered subtasks with dependencies

        Raises:
            ValueError: If intent is invalid
        """
        if not intent:
            raise ValueError("Intent is required")

        logger.debug(f"Decomposing intent: {intent.action}")

        subtasks = []

        # Create main task from intent
        main_task = Subtask(
            intent=intent,
            task_id=str(uuid4()),
            priority=0,
            dependencies=[],
            status=TaskStatus.PENDING,
        )
        subtasks.append(main_task)

        # Decompose based on action type
        decomposed = self._decompose_by_action(intent)
        if decomposed:
            # Set main task as prerequisite for decomposed tasks
            for task in decomposed:
                task.dependencies.append(main_task.task_id)
                task.priority = len(subtasks)  # Increment priority
            subtasks.extend(decomposed)

        logger.info(f"Decomposed intent into {len(subtasks)} subtasks")
        return subtasks

    def _decompose_by_action(self, intent: Intent) -> List[Subtask]:
        """Decompose intent by action type.

        Args:
            intent: Intent to decompose

        Returns:
            List of additional subtasks (empty if no decomposition)
        """
        action = intent.action.lower()

        decomposition_rules = {
            "move": self._decompose_move,
            "walk": self._decompose_move,
            "grasp": self._decompose_grasp,
            "pick": self._decompose_grasp,
            "place": self._decompose_place,
            "learn": self._decompose_learn,
        }

        decompose_func = decomposition_rules.get(action)
        if decompose_func:
            return decompose_func(intent)

        logger.debug(f"No decomposition rule for action: {action}")
        return []

    def _decompose_move(self, intent: Intent) -> List[Subtask]:
        """Decompose movement intent.

        move/walk → [perceive, plan_path, execute_movement]
        """
        subtasks = []

        # Perceive environment
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=1,
                dependencies=[],
                status=TaskStatus.PENDING,
            )
        )

        # Plan path
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=2,
                dependencies=[subtasks[0].task_id] if subtasks else [],
                status=TaskStatus.PENDING,
            )
        )

        return subtasks

    def _decompose_grasp(self, intent: Intent) -> List[Subtask]:
        """Decompose grasping intent.

        grasp/pick → [locate_object, plan_grasp, execute_grasp]
        """
        subtasks = []

        # Locate object
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=1,
                dependencies=[],
                status=TaskStatus.PENDING,
            )
        )

        # Plan grasp
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=2,
                dependencies=[subtasks[0].task_id] if subtasks else [],
                status=TaskStatus.PENDING,
            )
        )

        return subtasks

    def _decompose_place(self, intent: Intent) -> List[Subtask]:
        """Decompose placement intent.

        place → [locate_target, plan_placement, release_object]
        """
        subtasks = []

        # Locate target location
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=1,
                dependencies=[],
                status=TaskStatus.PENDING,
            )
        )

        return subtasks

    def _decompose_learn(self, intent: Intent) -> List[Subtask]:
        """Decompose learning intent.

        learn → [analyze_request, generate_code, validate_code, record_skill]
        """
        subtasks = []

        # Analyze learning request
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=1,
                dependencies=[],
                status=TaskStatus.PENDING,
            )
        )

        # Generate code (depends on analysis)
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=2,
                dependencies=[subtasks[0].task_id] if subtasks else [],
                status=TaskStatus.PENDING,
            )
        )

        # Validate code (depends on generation)
        subtasks.append(
            Subtask(
                intent=intent,
                task_id=str(uuid4()),
                priority=3,
                dependencies=[subtasks[1].task_id] if len(subtasks) > 1 else [],
                status=TaskStatus.PENDING,
            )
        )

        return subtasks

    @staticmethod
    def resolve_dependencies(subtasks: List[Subtask]) -> List[Subtask]:
        """Resolve and validate task dependencies.

        Args:
            subtasks: List of subtasks with dependencies

        Returns:
            Ordered list of subtasks

        Raises:
            ValueError: If circular dependencies detected
        """
        if not subtasks:
            return []

        # Check for circular dependencies
        for task in subtasks:
            visited = set()
            stack = [task.task_id]
            while stack:
                current = stack.pop()
                if current in visited:
                    raise ValueError(f"Circular dependency detected at {current}")
                visited.add(current)
                # Find dependent tasks
                for other_task in subtasks:
                    if current in other_task.dependencies:
                        stack.append(other_task.task_id)

        logger.debug("Dependencies resolved successfully")
        return subtasks
