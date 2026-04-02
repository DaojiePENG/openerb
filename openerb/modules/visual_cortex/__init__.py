"""Visual Cortex module - Multimodal visual perception engine.

This module provides comprehensive visual perception capabilities:
- Image processing and quality assessment
- Real-time object detection and tracking
- Face detection, attributes, and recognition
- Scene understanding and description
- Spatial layout analysis and 3D reasoning
- Robot-centric visual reasoning
"""

from openerb.modules.visual_cortex.visual_cortex import VisualCortex
from openerb.modules.visual_cortex.image_processor import (
    ImageProcessor,
    ImageQuality,
)
from openerb.modules.visual_cortex.object_detector import (
    ObjectDetector,
    DetectionConfig,
)
from openerb.modules.visual_cortex.face_recognizer import (
    FaceRecognizer,
    FaceRecognitionConfig,
)
from openerb.modules.visual_cortex.scene_understander import (
    SceneUnderstander,
    SceneUnderstandingConfig,
)
from openerb.modules.visual_cortex.spatial_analyzer import (
    SpatialAnalyzer,
    SpatialAnalysisConfig,
)

__all__ = [
    # Main API
    "VisualCortex",
    
    # Image Processing
    "ImageProcessor",
    "ImageQuality",
    
    # Object Detection
    "ObjectDetector",
    "DetectionConfig",
    
    # Face Recognition
    "FaceRecognizer",
    "FaceRecognitionConfig",
    
    # Scene Understanding
    "SceneUnderstander",
    "SceneUnderstandingConfig",
    
    # Spatial Analysis
    "SpatialAnalyzer",
    "SpatialAnalysisConfig",
]
