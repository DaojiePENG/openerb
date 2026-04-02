"""Visual Cortex - Main visual processing engine.

This module integrates all visual perception capabilities:
- Multi-modal image input handling
- Object detection and tracking
- Face recognition and identification
- Scene understanding and description
- Spatial layout analysis
- Robot-centric visual reasoning
"""

import io
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from openerb.core.logger import get_logger
from openerb.core.types import (
    ImageAnnotation,
    ImageFormat,
    VisualAnalysisResult,
    UserProfile,
    RobotType,
)
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

logger = get_logger(__name__)


class VisualCortex:
    """Main visual processing engine for the robot.
    
    Integrates all visual perception modules:
    - ImageProcessor: Low-level image processing
    - ObjectDetector: Object detection and tracking
    - FaceRecognizer: Face detection and recognition
    - SceneUnderstander: High-level scene understanding
    - SpatialAnalyzer: 3D spatial reasoning
    """

    def __init__(
        self,
        robot_type: RobotType = RobotType.G1,
        enable_object_detection: bool = True,
        enable_face_recognition: bool = True,
        enable_scene_understanding: bool = True,
        enable_spatial_analysis: bool = True,
    ):
        """Initialize Visual Cortex.
        
        Args:
            robot_type: Type of robot for spatial calibration
            enable_object_detection: Enable object detection
            enable_face_recognition: Enable face recognition
            enable_scene_understanding: Enable scene understanding
            enable_spatial_analysis: Enable spatial analysis
        """
        self.robot_type = robot_type

        # Initialize components
        self.image_processor = ImageProcessor()

        self.object_detector = (
            ObjectDetector(DetectionConfig()) if enable_object_detection else None
        )

        self.face_recognizer = (
            FaceRecognizer(FaceRecognitionConfig()) if enable_face_recognition else None
        )

        self.scene_understander = (
            SceneUnderstander(SceneUnderstandingConfig())
            if enable_scene_understanding
            else None
        )

        self.spatial_analyzer = (
            SpatialAnalyzer(SpatialAnalysisConfig()) if enable_spatial_analysis else None
        )

        # User database for face recognition
        self.user_database: Dict[str, UserProfile] = {}

        # Analysis history
        self.analysis_history: List[VisualAnalysisResult] = []
        self.total_analyses = 0

        logger.info(
            f"VisualCortex initialized for {robot_type} "
            f"with components: "
            f"ObjDet={enable_object_detection}, "
            f"FaceRec={enable_face_recognition}, "
            f"SceneUnd={enable_scene_understanding}, "
            f"SpatialAnal={enable_spatial_analysis}"
        )

    async def process_image(
        self,
        image_source,
        image_format: ImageFormat = ImageFormat.RGB,
        analyze_objects: bool = True,
        analyze_faces: bool = True,
        analyze_scene: bool = True,
        analyze_spatial: bool = True,
    ) -> VisualAnalysisResult:
        """Process an image comprehensively.
        
        Args:
            image_source: Image bytes, file path, or numpy array
            image_format: Image format
            analyze_objects: Perform object detection
            analyze_faces: Perform face detection
            analyze_scene: Perform scene understanding
            analyze_spatial: Perform spatial analysis
            
        Returns:
            VisualAnalysisResult with all analyses
        """
        try:
            # Load and process image
            image_array, width, height = self.image_processor.load_image(
                image_source,
                image_format,
            )

            # Assess image quality
            quality = self.image_processor.assess_quality(image_array)

            # Create annotation object
            annotation = ImageAnnotation(
                image_bytes=self._array_to_bytes(image_array),
                image_width=width,
                image_height=height,
                format=image_format,
            )

            # Object detection
            if analyze_objects and self.object_detector:
                detection_result = await self._detect_objects(
                    image_array,
                    width,
                    height,
                )
                annotation.objects = detection_result

            # Face detection and recognition
            if analyze_faces and self.face_recognizer:
                faces = await self._recognize_faces(image_array, width, height)
                annotation.faces = faces

            # Scene understanding
            if analyze_scene and self.scene_understander:
                scene_result = self.scene_understander.understand_scene(annotation)
                annotation.scene_description = scene_result.get(
                    "scene_description",
                    "",
                )
                annotation.main_objects = scene_result.get("main_objects", [])
                annotation.spatial_layout = scene_result.get("spatial_layout", "")

            # Spatial analysis
            if analyze_spatial and self.spatial_analyzer:
                layout = self.spatial_analyzer.analyze_spatial_layout(
                    annotation.objects,
                    width,
                    height,
                )
            else:
                layout = None

            # Compile results
            result = VisualAnalysisResult(
                annotation=annotation,
                spatial_layout=layout,
                recognized_users=[f.identified_user for f in annotation.faces if f.identified_user],
                analysis_confidence=quality.brightness_level,
                metadata={
                    "image_quality": {
                        "brightness": quality.brightness_level,
                        "contrast": quality.contrast_level,
                        "sharpness": quality.sharpness_score,
                        "usable": quality.is_usable,
                    },
                    "processing_time_ms": 0,
                },
            )

            self.analysis_history.append(result)
            self.total_analyses += 1

            logger.debug(
                f"Processed image: {width}x{height}, "
                f"objects={len(annotation.objects)}, "
                f"faces={len(annotation.faces)}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            raise

    def register_user(
        self,
        user: UserProfile,
        face_image: Optional[bytes] = None,
    ) -> bool:
        """Register a user in the database.
        
        Args:
            user: User profile
            face_image: Optional face image for embedding extraction
            
        Returns:
            True if registration successful
        """
        try:
            self.user_database[user.user_id] = user

            # Extract face embedding if provided
            if face_image and self.face_recognizer:
                image_array, width, height = self.image_processor.load_image(
                    face_image,
                    ImageFormat.RGB,
                )
                faces = self._simulate_face_detection(image_array, width, height)

                if faces:
                    # Use first detected face
                    face = faces[0]
                    user.face_embedding = face.face_embedding
                    self.face_recognizer.register_user_embedding(
                        user.user_id,
                        face.face_embedding,
                    )

            logger.info(f"Registered user {user.user_id} ({user.name})")
            return True

        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            return False

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get visual analysis statistics.
        
        Returns:
            Dictionary with comprehensive stats
        """
        stats = {
            "total_images_analyzed": self.total_analyses,
            "analysis_history_size": len(self.analysis_history),
            "registered_users": len(self.user_database),
            "robot_type": self.robot_type.value,
        }

        # Add stats from sub-modules
        if self.object_detector:
            stats["detector_stats"] = self.object_detector.get_detection_stats()

        if self.face_recognizer:
            stats["recognizer_stats"] = self.face_recognizer.get_recognition_stats()

        if self.scene_understander:
            stats["scene_stats"] = self.scene_understander.get_understanding_stats()

        if self.spatial_analyzer:
            stats["spatial_stats"] = self.spatial_analyzer.get_spatial_stats()

        return stats

    def clear_history(self) -> None:
        """Clear analysis history."""
        self.analysis_history.clear()
        logger.info("Analysis history cleared")

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _detect_objects(
        self,
        image: Any,
        width: int,
        height: int,
    ) -> List:
        """Detect objects in image."""
        if self.object_detector is None:
            return []

        return self.object_detector.detect_objects(image, width, height)

    async def _recognize_faces(
        self,
        image: Any,
        width: int,
        height: int,
    ) -> List:
        """Detect and recognize faces."""
        if self.face_recognizer is None:
            return []

        # Detect faces
        faces = self.face_recognizer.detect_faces(image, width, height)

        # Recognize faces (identify users)
        recognized_faces = self.face_recognizer.recognize_faces(
            faces,
            self.user_database,
        )

        # Extract attributes
        for face in recognized_faces:
            self.face_recognizer.extract_face_attributes(image, face)

        return recognized_faces

    def _simulate_face_detection(self, image: Any, width: int, height: int) -> List:
        """Simulate face detection."""
        if self.face_recognizer is None:
            return []

        return self.face_recognizer.detect_faces(image, width, height)

    def _array_to_bytes(self, image_array: Any) -> bytes:
        """Convert image array to bytes."""
        try:
            from PIL import Image
            import numpy as np

            if isinstance(image_array, np.ndarray):
                image = Image.fromarray(image_array.astype("uint8"))
            else:
                image = image_array

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to convert array to bytes: {e}")
            return b""
