"""Scene understander module for visual cortex.

This module provides scene understanding capabilities:
- Object relationship analysis
- Scene classification
- Context understanding
- Language description generation
- Activity recognition
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

import numpy as np

from openerb.core.logger import get_logger
from openerb.core.types import (
    DetectedObject,
    FaceDetection,
    ImageAnnotation,
    Relationship,
    SpatialLayout,
)

logger = get_logger(__name__)


@dataclass
class SceneUnderstandingConfig:
    """Configuration for scene understander."""
    min_object_confidence: float = 0.5
    describe_max_objects: int = 10
    generate_relationships: bool = True
    estimate_distances: bool = True


class SceneUnderstander:
    """Scene understanding engine for interpreting visual scenes."""

    def __init__(self, config: Optional[SceneUnderstandingConfig] = None):
        """Initialize scene understander.
        
        Args:
            config: Scene understanding configuration
        """
        self.config = config or SceneUnderstandingConfig()
        self.scene_history: List[ImageAnnotation] = []
        self.understanding_count = 0
        logger.info(f"SceneUnderstander initialized with config: {self.config}")

    def understand_scene(
        self,
        annotation: ImageAnnotation,
    ) -> Dict[str, Any]:
        """Understand and describe a scene.
        
        Args:
            annotation: Image annotation with detections
            
        Returns:
            Dictionary with scene understanding results
        """
        try:
            # Filter by confidence
            main_objects = [
                obj for obj in annotation.objects
                if obj.confidence >= self.config.min_object_confidence
            ]

            # Describe scene
            description = self._generate_scene_description(
                main_objects,
                annotation.faces,
            )

            # Analyze relationships
            relationships = []
            if self.config.generate_relationships:
                relationships = self._analyze_relationships(main_objects)

            # Detect activities
            activities = self._detect_activities(main_objects, annotation.faces)

            # Scene classification
            scene_type = self._classify_scene(main_objects, annotation.faces)

            self.understanding_count += 1

            result = {
                "scene_description": description,
                "scene_type": scene_type,
                "main_objects": [obj.label for obj in main_objects[: self.config.describe_max_objects]],
                "number_of_people": len(annotation.faces),
                "number_of_objects": len(main_objects),
                "relationships": relationships,
                "activities": activities,
                "timestamp": datetime.now(),
            }

            logger.debug(f"Scene understood: {scene_type}")
            self.scene_history.append(annotation)

            return result

        except Exception as e:
            logger.error(f"Failed to understand scene: {e}")
            return {"error": str(e)}

    def analyze_relationships(
        self,
        objects: List[DetectedObject],
        layout: Optional[SpatialLayout] = None,
    ) -> List[Relationship]:
        """Analyze spatial relationships between objects.
        
        Args:
            objects: List of detected objects
            layout: Optional spatial layout information
            
        Returns:
            List of relationships
        """
        return self._analyze_relationships(objects)

    def detect_activities(
        self,
        objects: List[DetectedObject],
        faces: List[FaceDetection],
    ) -> List[str]:
        """Detect activities in the scene.
        
        Args:
            objects: List of detected objects
            faces: List of detected faces
            
        Returns:
            List of detected activities
        """
        return self._detect_activities(objects, faces)

    def classify_scene(
        self,
        objects: List[DetectedObject],
        faces: List[FaceDetection],
    ) -> str:
        """Classify the type of scene.
        
        Args:
            objects: List of detected objects
            faces: List of detected faces
            
        Returns:
            Scene type classification
        """
        return self._classify_scene(objects, faces)

    def generate_natural_language_description(
        self,
        annotation: ImageAnnotation,
        max_detail_level: int = 2,
    ) -> str:
        """Generate natural language description of scene.
        
        Args:
            annotation: Image annotation
            max_detail_level: Level of detail (1-3)
            
        Returns:
            Natural language description
        """
        try:
            description_parts = []

            # Scene context
            scene_type = self._classify_scene(annotation.objects, annotation.faces)
            description_parts.append(f"This is a {scene_type} scene.")

            # People
            if annotation.faces:
                description_parts.append(
                    f"There are {len(annotation.faces)} people in the scene."
                )

            # Main objects
            main_objects = [
                obj for obj in annotation.objects
                if obj.confidence >= self.config.min_object_confidence
            ][: self.config.describe_max_objects]

            if main_objects:
                obj_list = ", ".join(obj.label for obj in main_objects)
                description_parts.append(f"Main objects: {obj_list}.")

            # Relationships
            if self.config.generate_relationships and max_detail_level >= 2:
                relationships = self._analyze_relationships(annotation.objects)
                if relationships:
                    for rel in relationships[:3]:  # Limit to top 3
                        description_parts.append(f"{rel.object1_id} is {rel.relation_type} {rel.object2_id}.")

            # Activities
            activities = self._detect_activities(annotation.objects, annotation.faces)
            if activities and max_detail_level >= 3:
                activity_list = ", ".join(activities)
                description_parts.append(f"Activities: {activity_list}.")

            full_description = " ".join(description_parts)
            return full_description

        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return ""

    def get_understanding_stats(self) -> Dict[str, Any]:
        """Get scene understanding statistics.
        
        Returns:
            Dictionary with understanding stats
        """
        return {
            "total_scenes_understood": self.understanding_count,
            "scene_history_size": len(self.scene_history),
            "average_objects_per_scene": self._calculate_average_objects(),
            "average_people_per_scene": self._calculate_average_people(),
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _generate_scene_description(
        self,
        objects: List[DetectedObject],
        faces: List[FaceDetection],
    ) -> str:
        """Generate basic scene description."""
        if len(objects) == 0 and len(faces) == 0:
            return "Empty scene"

        scene_type = self._classify_scene(objects, faces)
        obj_count = len(objects)
        person_count = len(faces)

        if obj_count > 0 and person_count > 0:
            return f"{scene_type} with {person_count} people and {obj_count} objects"
        elif person_count > 0:
            return f"{scene_type} with {person_count} people"
        elif obj_count > 0:
            return f"{scene_type} with {obj_count} objects"
        else:
            return scene_type

    def _analyze_relationships(
        self,
        objects: List[DetectedObject],
    ) -> List[Relationship]:
        """Analyze spatial relationships between objects."""
        relationships = []

        for i, obj1 in enumerate(objects):
            for obj2 in objects[i + 1 :]:
                if obj1.bbox is None or obj2.bbox is None:
                    continue

                # Calculate relative positions
                obj1_center_x = obj1.bbox.x + obj1.bbox.width / 2
                obj1_center_y = obj1.bbox.y + obj1.bbox.height / 2
                obj2_center_x = obj2.bbox.x + obj2.bbox.width / 2
                obj2_center_y = obj2.bbox.y + obj2.bbox.height / 2

                # Determine relationship
                dx = obj2_center_x - obj1_center_x
                dy = obj2_center_y - obj1_center_y
                distance = np.sqrt(dx**2 + dy**2)

                if distance < 0.1:
                    relation = "very_close_to"
                elif distance < 0.3:
                    relation = "near"
                else:
                    relation = "far_from"

                # Add directional relationship
                if abs(dx) > abs(dy):
                    if dx > 0:
                        relation = f"right_of ({relation})"
                    else:
                        relation = f"left_of ({relation})"
                else:
                    if dy > 0:
                        relation = f"below ({relation})"
                    else:
                        relation = f"above ({relation})"

                rel = Relationship(
                    object1_id=obj1.object_id,
                    object2_id=obj2.object_id,
                    relation_type=relation,
                    distance=float(distance),
                    confidence=min(obj1.confidence, obj2.confidence),
                )

                relationships.append(rel)

        return relationships

    def _detect_activities(
        self,
        objects: List[DetectedObject],
        faces: List[FaceDetection],
    ) -> List[str]:
        """Detect activities in the scene."""
        activities = []

        # Check for people doing things
        if len(faces) > 0:
            activities.append("people_present")

            # Check for emotions/attributes
            for face in faces:
                if hasattr(face, "attributes") and face.attributes:
                    emotion = face.attributes.get("emotion", "neutral")
                    if emotion != "neutral":
                        activities.append(f"people_looking_{emotion}")

        # Check for objects that suggest activities
        for obj in objects:
            if "chair" in obj.label.lower():
                activities.append("sitting_possible")
            elif "computer" in obj.label.lower():
                activities.append("working")
            elif "phone" in obj.label.lower():
                activities.append("communication")

        return activities

    def _classify_scene(
        self,
        objects: List[DetectedObject],
        faces: List[FaceDetection],
    ) -> str:
        """Classify the scene type."""
        # Count object categories
        obj_labels = [obj.label.lower() for obj in objects]

        # Check for specific keywords
        if any("desk" in label or "chair" in label or "computer" in label for label in obj_labels):
            return "office"
        elif any("table" in label or "food" in label or "plate" in label for label in obj_labels):
            return "dining"
        elif any("couch" in label or "sofa" in label or "tv" in label for label in obj_labels):
            return "living_room"
        elif any("bed" in label or "bedroom" in label for label in obj_labels):
            return "bedroom"
        elif len(obj_labels) == 0 and len(faces) > 0:
            return "portrait"
        elif len(obj_labels) == 0:
            return "outdoor"
        else:
            return "general"

    def _calculate_average_objects(self) -> float:
        """Calculate average number of objects per scene."""
        if not self.scene_history:
            return 0.0

        total_objects = sum(len(ann.objects) for ann in self.scene_history)
        return total_objects / len(self.scene_history)

    def _calculate_average_people(self) -> float:
        """Calculate average number of people per scene."""
        if not self.scene_history:
            return 0.0

        total_people = sum(len(ann.faces) for ann in self.scene_history)
        return total_people / len(self.scene_history)
