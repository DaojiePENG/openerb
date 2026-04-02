"""Object detector module for visual cortex.

This module provides object detection capabilities:
- Real-time object detection
- Multiple object tracking
- Category classification
- Confidence scoring
- Integration with robot knowledge
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

import numpy as np

from openerb.core.logger import get_logger
from openerb.core.types import (
    DetectedObject,
    ObjectCategory,
    BoundingBox,
    ImageAnnotation,
    ImageFormat,
)

logger = get_logger(__name__)


@dataclass
class DetectionConfig:
    """Configuration for object detector."""
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.5  # Non-maximum suppression threshold
    max_detections: int = 100
    enable_tracking: bool = True
    tracking_history_size: int = 30


class ObjectDetector:
    """Object detector for identifying objects in images."""

    def __init__(self, config: Optional[DetectionConfig] = None):
        """Initialize object detector.
        
        Args:
            config: Detection configuration
        """
        self.config = config or DetectionConfig()
        self.detection_history: Dict[str, List[DetectedObject]] = {}
        self.object_tracks: Dict[str, List[DetectedObject]] = {}
        self.detection_count = 0
        logger.info(f"ObjectDetector initialized with config: {self.config}")

    def detect_objects(
        self,
        image: np.ndarray,
        image_width: int,
        image_height: int,
    ) -> List[DetectedObject]:
        """Detect objects in image.
        
        Args:
            image: Input image array
            image_width: Image width
            image_height: Image height
            
        Returns:
            List of detected objects
        """
        try:
            detections = []

            # Simulated object detection
            # In production, this would call a real detector like YOLO, Faster R-CNN, etc.
            # For now, we implement a template with mock detections

            # Mock detection based on image statistics
            # In real implementation, would use a pre-trained model
            detections = self._simulate_detections(image, image_width, image_height)

            # Apply confidence threshold
            filtered = [
                d for d in detections
                if d.confidence >= self.config.confidence_threshold
            ]

            # Apply NMS
            filtered = self._apply_nms(filtered)

            # Track objects if enabled
            if self.config.enable_tracking:
                filtered = self._track_objects(filtered)

            self.detection_count += 1
            logger.debug(f"Detected {len(filtered)} objects")

            return filtered

        except Exception as e:
            logger.error(f"Failed to detect objects: {e}")
            return []

    def track_object(
        self,
        object_id: str,
        detections: List[DetectedObject],
    ) -> Optional[DetectedObject]:
        """Track a specific object across frames.
        
        Args:
            object_id: ID of object to track
            detections: List of current detections
            
        Returns:
            Tracked object or None if lost
        """
        try:
            if object_id not in self.object_tracks:
                self.object_tracks[object_id] = []

            # Find matching detection
            matched = None
            best_iou = 0.0

            if object_id in self.object_tracks:
                last_detection = self.object_tracks[object_id][-1]
                for detection in detections:
                    iou = self._calculate_iou(last_detection.bbox, detection.bbox)
                    if iou > best_iou:
                        best_iou = iou
                        matched = detection

            if matched and best_iou > self.config.iou_threshold:
                # Maintain same ID for consistency
                matched.object_id = object_id
                self.object_tracks[object_id].append(matched)

                # Trim history
                if len(self.object_tracks[object_id]) > self.config.tracking_history_size:
                    self.object_tracks[object_id] = self.object_tracks[object_id][
                        -self.config.tracking_history_size :
                    ]

                return matched

            return None

        except Exception as e:
            logger.error(f"Failed to track object {object_id}: {e}")
            return None

    def classify_category(
        self,
        image: np.ndarray,
        bbox: BoundingBox,
    ) -> ObjectCategory:
        """Classify object category.
        
        Args:
            image: Input image array
            bbox: Bounding box of object
            
        Returns:
            Classified object category
        """
        try:
            # Extract patch
            h, w = image.shape[:2]
            x1 = int(bbox.x * w)
            y1 = int(bbox.y * h)
            x2 = int((bbox.x + bbox.width) * w)
            y2 = int((bbox.y + bbox.height) * h)

            patch = image[y1:y2, x1:x2]

            # In production, use a CNN for classification
            # For now, use simple heuristics
            category = self._classify_by_features(patch)
            return category

        except Exception as e:
            logger.error(f"Failed to classify category: {e}")
            return ObjectCategory.UNKNOWN

    def extract_object_features(
        self,
        image: np.ndarray,
        detection: DetectedObject,
    ) -> Dict[str, Any]:
        """Extract features from detected object.
        
        Args:
            image: Input image array
            detection: Detected object
            
        Returns:
            Feature dictionary
        """
        try:
            if detection.bbox is None:
                return {}

            # Extract patch
            h, w = image.shape[:2]
            x1 = int(detection.bbox.x * w)
            y1 = int(detection.bbox.y * h)
            x2 = int((detection.bbox.x + detection.bbox.width) * w)
            y2 = int((detection.bbox.y + detection.bbox.height) * h)

            patch = image[max(0, y1) : min(h, y2), max(0, x1) : min(w, x2)]

            if patch.size == 0:
                return {}

            # Extract color features
            features = {}

            if len(patch.shape) == 3:
                features["dominant_color"] = self._get_dominant_color(patch)
                features["color_histogram"] = self._extract_color_histogram(patch)
            else:
                features["mean_intensity"] = float(np.mean(patch))
                features["std_intensity"] = float(np.std(patch))

            # Size features
            features["object_size"] = detection.bbox.width * detection.bbox.height
            features["aspect_ratio"] = detection.bbox.width / max(
                detection.bbox.height, 1e-5
            )

            return features

        except Exception as e:
            logger.error(f"Failed to extract object features: {e}")
            return {}

    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics.
        
        Returns:
            Dictionary with detection stats
        """
        total_objects = sum(len(objs) for objs in self.detection_history.values())
        return {
            "total_detections": self.detection_count,
            "total_objects_tracked": len(self.object_tracks),
            "average_confidence": self._calculate_average_confidence(),
            "tracked_history_size": total_objects,
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _simulate_detections(
        self,
        image: np.ndarray,
        image_width: int,
        image_height: int,
    ) -> List[DetectedObject]:
        """Simulate object detections (placeholder for real detector)."""
        detections = []

        # In production, replace with actual detector
        # This is a mock implementation for testing

        # Example: Detect bright regions as potential objects
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image

        # Find bright regions
        threshold = np.mean(gray) + np.std(gray)
        bright_mask = gray > threshold

        # Simple connected components to find blobs
        labeled, count = self._label_connected_components(bright_mask)

        for obj_id in range(1, min(count + 1, self.config.max_detections)):
            component = labeled == obj_id
            if np.sum(component) < 100:  # Skip small components
                continue

            # Find bounding box
            rows, cols = np.where(component)
            y_min, y_max = rows.min(), rows.max()
            x_min, x_max = cols.min(), cols.max()

            bbox = BoundingBox(
                x=x_min / image_width,
                y=y_min / image_height,
                width=(x_max - x_min) / image_width,
                height=(y_max - y_min) / image_height,
                confidence=min(1.0, np.mean(gray[component]) / 255.0),
            )

            detection = DetectedObject(
                category=ObjectCategory.UNKNOWN,
                bbox=bbox,
                confidence=bbox.confidence,
                label=f"object_{obj_id}",
            )

            detections.append(detection)

        return detections

    def _apply_nms(self, detections: List[DetectedObject]) -> List[DetectedObject]:
        """Apply non-maximum suppression."""
        if not detections or all(d.bbox is None for d in detections):
            return detections

        # Sort by confidence
        sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
        keep = []
        suppressed = set()

        for i, det in enumerate(sorted_dets):
            if i in suppressed:
                continue

            keep.append(det)

            # Suppress lower confidence detections with high IoU
            for j in range(i + 1, len(sorted_dets)):
                if j in suppressed:
                    continue

                iou = self._calculate_iou(det.bbox, sorted_dets[j].bbox)
                if iou > self.config.iou_threshold:
                    suppressed.add(j)

        return keep

    def _track_objects(
        self,
        detections: List[DetectedObject],
    ) -> List[DetectedObject]:
        """Track objects across frames."""
        # Simple tracking: assign IDs based on spatial proximity
        for detection in detections:
            # Check if this matches any existing track
            best_match = None
            best_iou = 0.0

            for track_id, track_history in self.object_tracks.items():
                if not track_history:
                    continue
                last_det = track_history[-1]
                iou = self._calculate_iou(last_det.bbox, detection.bbox)

                if iou > best_iou:
                    best_iou = iou
                    best_match = track_id

            if best_match and best_iou > self.config.iou_threshold:
                detection.object_id = best_match

        return detections

    def _calculate_iou(
        self,
        bbox1: Optional[BoundingBox],
        bbox2: Optional[BoundingBox],
    ) -> float:
        """Calculate intersection over union."""
        if bbox1 is None or bbox2 is None:
            return 0.0

        # Calculate intersection
        x_left = max(bbox1.x, bbox2.x)
        y_top = max(bbox1.y, bbox2.y)
        x_right = min(bbox1.x + bbox1.width, bbox2.x + bbox2.width)
        y_bottom = min(bbox1.y + bbox1.height, bbox2.y + bbox2.height)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection = (x_right - x_left) * (y_bottom - y_top)
        bbox1_area = bbox1.width * bbox1.height
        bbox2_area = bbox2.width * bbox2.height
        union = bbox1_area + bbox2_area - intersection

        return intersection / union if union > 0 else 0.0

    def _classify_by_features(self, patch: np.ndarray) -> ObjectCategory:
        """Classify using simple heuristics."""
        # In production, use a proper classifier
        if patch.size < 100:
            return ObjectCategory.UNKNOWN

        if len(patch.shape) == 3:
            # Check colors
            mean_color = np.mean(patch, axis=(0, 1))
            r, g, b = mean_color[:3]

            # Skin-like color detection
            if r > 95 and g > 40 and b > 20 and r > g > b:
                return ObjectCategory.PERSON

        return ObjectCategory.UNKNOWN

    def _get_dominant_color(self, patch: np.ndarray) -> str:
        """Extract dominant color."""
        if len(patch.shape) != 3:
            return "unknown"

        mean_color = np.mean(patch, axis=(0, 1)).astype(int)
        r, g, b = mean_color[:3]

        if r > g and r > b:
            return "red"
        elif g > r and g > b:
            return "green"
        elif b > r and b > g:
            return "blue"
        else:
            return "gray"

    def _extract_color_histogram(self, patch: np.ndarray) -> Dict[str, float]:
        """Extract color histogram."""
        if len(patch.shape) != 3:
            return {}

        mean_colors = {}
        for i, name in enumerate(["red", "green", "blue"]):
            mean_colors[f"mean_{name}"] = float(np.mean(patch[:, :, i]))

        return mean_colors

    def _label_connected_components(self, binary_mask: np.ndarray) -> Tuple[np.ndarray, int]:
        """Label connected components in binary mask."""
        labeled = np.zeros_like(binary_mask, dtype=int)
        label = 0

        for i in range(binary_mask.shape[0]):
            for j in range(binary_mask.shape[1]):
                if binary_mask[i, j] and labeled[i, j] == 0:
                    label += 1
                    self._flood_fill(binary_mask, labeled, i, j, label)

        return labeled, label

    def _flood_fill(
        self,
        binary_mask: np.ndarray,
        labeled: np.ndarray,
        i: int,
        j: int,
        label: int,
    ) -> None:
        """Flood fill for connected component labeling."""
        stack = [(i, j)]
        h, w = binary_mask.shape

        while stack:
            i, j = stack.pop()

            if i < 0 or i >= h or j < 0 or j >= w:
                continue
            if labeled[i, j] != 0 or not binary_mask[i, j]:
                continue

            labeled[i, j] = label
            stack.extend([(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)])

    def _calculate_average_confidence(self) -> float:
        """Calculate average detection confidence."""
        if self.detection_count == 0:
            return 0.0

        total_confidence = 0.0
        total_objects = 0

        for detections in self.detection_history.values():
            for det in detections:
                total_confidence += det.confidence
                total_objects += 1

        return total_confidence / total_objects if total_objects > 0 else 0.0
