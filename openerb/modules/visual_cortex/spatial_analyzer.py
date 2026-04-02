"""Spatial analyzer module for visual cortex.

This module provides spatial analysis capabilities:
- 3D spatial understanding from 2D images
- Depth estimation
- Distance calculation
- Spatial layout reconstruction
- Robot-centric spatial reasoning
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from uuid import uuid4

import numpy as np

from openerb.core.logger import get_logger
from openerb.core.types import (
    DetectedObject,
    BoundingBox,
    SpatialLayout,
    Relationship,
)

logger = get_logger(__name__)


@dataclass
class SpatialAnalysisConfig:
    """Configuration for spatial analyzer."""
    enable_depth_estimation: bool = True
    depth_estimation_method: str = "monocular"  # "monocular", "stereo", "lidar"
    max_distance: float = 10.0  # meters
    min_distance: float = 0.1  # meters
    camera_height: float = 0.6  # meters (from robot center)
    camera_fov: float = 60.0  # degrees


class SpatialAnalyzer:
    """Spatial analyzer for understanding scene geometry and distances."""

    def __init__(self, config: Optional[SpatialAnalysisConfig] = None):
        """Initialize spatial analyzer.
        
        Args:
            config: Spatial analysis configuration
        """
        self.config = config or SpatialAnalysisConfig()
        self.spatial_layouts: List[SpatialLayout] = []
        self.analysis_count = 0
        logger.info(f"SpatialAnalyzer initialized with config: {self.config}")

    def analyze_spatial_layout(
        self,
        objects: List[DetectedObject],
        image_width: int,
        image_height: int,
    ) -> SpatialLayout:
        """Analyze spatial layout of scene.
        
        Args:
            objects: List of detected objects
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            SpatialLayout with distance estimates
        """
        try:
            layout = SpatialLayout(
                objects=objects,
                robot_position=(0, 0, self.config.camera_height),
            )

            # Estimate distances for each object
            estimated_distances = {}
            for obj in objects:
                if obj.bbox is None:
                    continue

                distance = self._estimate_distance(
                    obj.bbox,
                    image_width,
                    image_height,
                )
                estimated_distances[obj.object_id] = float(distance)

            layout.estimated_distances = estimated_distances

            # Estimate depth map if enabled
            if self.config.enable_depth_estimation:
                depth_map = self._estimate_depth_map(
                    objects,
                    image_width,
                    image_height,
                )
                if depth_map is not None:
                    layout.depth_map = depth_map

            # Build spatial graph (relationships)
            relationships = self._build_spatial_graph(objects, estimated_distances)
            layout.relationships = relationships

            self.spatial_layouts.append(layout)
            self.analysis_count += 1

            logger.debug(f"Analyzed spatial layout with {len(objects)} objects")
            return layout

        except Exception as e:
            logger.error(f"Failed to analyze spatial layout: {e}")
            return SpatialLayout(objects=objects)

    def estimate_distance(
        self,
        bbox: BoundingBox,
        image_width: int,
        image_height: int,
    ) -> float:
        """Estimate distance to object from bounding box.
        
        Args:
            bbox: Bounding box of object
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            Estimated distance in meters
        """
        return self._estimate_distance(bbox, image_width, image_height)

    def estimate_object_position(
        self,
        bbox: BoundingBox,
        estimated_distance: float,
        image_width: int,
        image_height: int,
    ) -> Tuple[float, float, float]:
        """Estimate 3D position of object in robot-centric coordinates.
        
        Args:
            bbox: Bounding box of object
            estimated_distance: Estimated distance to object
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            Tuple of (x, y, z) coordinates in meters
        """
        try:
            # Object center in image coordinates (normalized)
            center_x = bbox.x + bbox.width / 2
            center_y = bbox.y + bbox.height / 2

            # Convert image coordinates to camera coordinates
            # Center of image is camera principal point
            pixel_x = (center_x - 0.5) * image_width
            pixel_y = (center_y - 0.5) * image_height

            # Estimate field of view angle
            fov_rad = np.radians(self.config.camera_fov)
            focal_length = image_width / (2 * np.tan(fov_rad / 2))

            # Convert pixel coordinates to camera coordinates using focal length
            cam_x = (pixel_x / focal_length) * estimated_distance
            cam_y = (pixel_y / focal_length) * estimated_distance
            cam_z = estimated_distance

            # Adjust for camera height above robot center
            world_z = cam_z - self.config.camera_height

            return (cam_x, cam_y, world_z)

        except Exception as e:
            logger.error(f"Failed to estimate object position: {e}")
            return (0.0, 0.0, 0.0)

    def calculate_relative_positions(
        self,
        layout: SpatialLayout,
    ) -> Dict[str, Dict[str, float]]:
        """Calculate relative positions of all objects in layout.
        
        Args:
            layout: Spatial layout
            
        Returns:
            Dictionary of relative positions
        """
        try:
            relative_positions = {}

            for obj in layout.objects:
                if obj.bbox is None or obj.object_id not in layout.estimated_distances:
                    continue

                distance = layout.estimated_distances[obj.object_id]
                position = self.estimate_object_position(
                    obj.bbox,
                    distance,
                    800,  # Assuming standard image size
                    600,
                )

                relative_positions[obj.object_id] = {
                    "x": position[0],
                    "y": position[1],
                    "z": position[2],
                    "distance": distance,
                }

            return relative_positions

        except Exception as e:
            logger.error(f"Failed to calculate relative positions: {e}")
            return {}

    def find_reachable_objects(
        self,
        layout: SpatialLayout,
        max_reach: float = 1.0,
    ) -> List[DetectedObject]:
        """Find objects within robot reaching distance.
        
        Args:
            layout: Spatial layout
            max_reach: Maximum reaching distance in meters
            
        Returns:
            List of reachable objects
        """
        try:
            reachable = []

            for obj in layout.objects:
                if obj.object_id not in layout.estimated_distances:
                    continue

                distance = layout.estimated_distances[obj.object_id]
                if distance <= max_reach:
                    reachable.append(obj)

            return reachable

        except Exception as e:
            logger.error(f"Failed to find reachable objects: {e}")
            return []

    def plan_navigation_path(
        self,
        target_object: DetectedObject,
        estimated_distance: float,
        obstacles: List[DetectedObject],
    ) -> Optional[List[Tuple[float, float]]]:
        """Plan simple navigation path to target object.
        
        Args:
            target_object: Target object
            estimated_distance: Estimated distance to target
            obstacles: List of obstacles to avoid
            
        Returns:
            List of waypoints (x, y) or None if unreachable
        """
        try:
            if target_object.bbox is None:
                return None

            # Simple straight path as default
            # In production, use RRT, A*, etc.
            target_x = (target_object.bbox.x + target_object.bbox.width / 2 - 0.5) * estimated_distance
            target_y = estimated_distance

            path = [
                (0.0, 0.0),  # Start position (robot)
                (target_x * 0.5, target_y * 0.5),  # Midpoint
                (target_x, target_y),  # Target
            ]

            return path

        except Exception as e:
            logger.error(f"Failed to plan navigation path: {e}")
            return None

    def get_spatial_stats(self) -> Dict[str, Any]:
        """Get spatial analysis statistics.
        
        Returns:
            Dictionary with spatial stats
        """
        return {
            "total_analyses": self.analysis_count,
            "layouts_stored": len(self.spatial_layouts),
            "average_objects_per_layout": self._calculate_average_objects(),
            "average_max_distance": self._calculate_average_max_distance(),
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _estimate_distance(
        self,
        bbox: BoundingBox,
        image_width: int,
        image_height: int,
    ) -> float:
        """Estimate distance using bounding box size."""
        # Simple heuristic: larger objects (in image) are closer
        # Assume a standard object size of ~0.3m

        box_size = bbox.width + bbox.height  # Average of width and height
        if box_size < 0.01:  # Too small
            return self.config.max_distance

        # Inverse relationship between image size and distance
        # Calibrated for typical robot cameras
        estimated_distance = (0.3 / box_size) * 0.5  # Rough calibration

        # Clamp to valid range
        return np.clip(
            estimated_distance,
            self.config.min_distance,
            self.config.max_distance,
        )

    def _estimate_depth_map(
        self,
        objects: List[DetectedObject],
        image_width: int,
        image_height: int,
    ) -> Optional[List[List[float]]]:
        """Estimate depth map for the scene."""
        try:
            # Create a simple depth map based on object positions
            depth_map = [[self.config.max_distance] * image_width for _ in range(image_height)]

            for obj in objects:
                if obj.bbox is None:
                    continue

                distance = self._estimate_distance(obj.bbox, image_width, image_height)

                # Fill depth map area
                x1 = int(obj.bbox.x * image_width)
                y1 = int(obj.bbox.y * image_height)
                x2 = int((obj.bbox.x + obj.bbox.width) * image_width)
                y2 = int((obj.bbox.y + obj.bbox.height) * image_height)

                for y in range(max(0, y1), min(image_height, y2)):
                    for x in range(max(0, x1), min(image_width, x2)):
                        depth_map[y][x] = min(depth_map[y][x], distance)

            return depth_map

        except Exception as e:
            logger.error(f"Failed to estimate depth map: {e}")
            return None

    def _build_spatial_graph(
        self,
        objects: List[DetectedObject],
        distances: Dict[str, float],
    ) -> List[Relationship]:
        """Build spatial relationship graph."""
        relationships = []

        for i, obj1 in enumerate(objects):
            for obj2 in objects[i + 1 :]:
                if obj1.bbox is None or obj2.bbox is None:
                    continue

                # Calculate distance between objects
                obj1_dist = distances.get(obj1.object_id, 0)
                obj2_dist = distances.get(obj2.object_id, 0)

                # Horizontal distance
                horizontal_dist = np.sqrt(
                    ((obj1.bbox.x - obj2.bbox.x) ** 2 +
                     (obj1.bbox.y - obj2.bbox.y) ** 2)
                )

                # Determine spatial relationship
                if horizontal_dist < 0.2:
                    relation = "adjacent_to"
                elif horizontal_dist < 0.5:
                    relation = "near_to"
                else:
                    relation = "separated_from"

                rel = Relationship(
                    object1_id=obj1.object_id,
                    object2_id=obj2.object_id,
                    relation_type=relation,
                    distance=abs(obj1_dist - obj2_dist),
                    confidence=min(obj1.confidence, obj2.confidence),
                )

                relationships.append(rel)

        return relationships

    def _calculate_average_objects(self) -> float:
        """Calculate average objects per layout."""
        if not self.spatial_layouts:
            return 0.0

        total = sum(len(layout.objects) for layout in self.spatial_layouts)
        return total / len(self.spatial_layouts)

    def _calculate_average_max_distance(self) -> float:
        """Calculate average maximum distance in layouts."""
        if not self.spatial_layouts:
            return 0.0

        distances = []
        for layout in self.spatial_layouts:
            if layout.estimated_distances:
                distances.append(max(layout.estimated_distances.values()))

        return sum(distances) / len(distances) if distances else 0.0
