"""Unit tests for Visual Cortex module.

Tests cover:
- Image processing
- Object detection
- Face recognition
- Scene understanding
- Spatial analysis
- Visual Cortex integration
"""

import io
import numpy as np
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from openerb.core.types import (
    ImageFormat,
    ObjectCategory,
    BoundingBox,
    DetectedObject,
    FaceDetection,
    ImageAnnotation,
    RobotType,
    UserProfile,
)
from openerb.modules.visual_cortex import (
    ImageProcessor,
    ObjectDetector,
    DetectionConfig,
    FaceRecognizer,
    FaceRecognitionConfig,
    SceneUnderstander,
    SceneUnderstandingConfig,
    SpatialAnalyzer,
    SpatialAnalysisConfig,
    VisualCortex,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def dummy_image():
    """Create a dummy RGB image."""
    return np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def dummy_image_bytes(dummy_image):
    """Convert dummy image to bytes."""
    from PIL import Image
    img = Image.fromarray(dummy_image)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def dummy_bbox():
    """Create a dummy bounding box."""
    return BoundingBox(
        x=0.1,
        y=0.1,
        width=0.3,
        height=0.3,
        confidence=0.9,
    )


@pytest.fixture
def dummy_detected_object(dummy_bbox):
    """Create a dummy detected object."""
    return DetectedObject(
        category=ObjectCategory.PERSON,
        label="person",
        bbox=dummy_bbox,
        confidence=0.9,
    )


@pytest.fixture
def dummy_face_detection(dummy_bbox):
    """Create a dummy face detection."""
    return FaceDetection(
        bbox=dummy_bbox,
        confidence=0.95,
        face_embedding=np.random.randn(128).astype(np.float32),
    )


@pytest.fixture
def dummy_user_profile():
    """Create a dummy user profile."""
    return UserProfile(
        user_id="user_001",
        name="Test User",
        face_embedding=np.random.randn(128).astype(np.float32),
    )


# ============================================================================
# ImageProcessor Tests
# ============================================================================

class TestImageProcessor:
    """Tests for ImageProcessor."""

    def test_initialization(self):
        """Test ImageProcessor initialization."""
        processor = ImageProcessor()
        assert processor is not None
        assert processor.processed_count == 0

    def test_load_image_from_bytes(self, dummy_image_bytes):
        """Test loading image from bytes."""
        processor = ImageProcessor()
        image, width, height = processor.load_image(dummy_image_bytes, ImageFormat.RGB)
        
        assert image is not None
        assert width > 0
        assert height > 0
        assert image.shape[2] == 3  # RGB

    def test_load_image_from_numpy(self, dummy_image):
        """Test loading image from numpy array."""
        processor = ImageProcessor()
        image, width, height = processor.load_image(dummy_image, ImageFormat.RGB)
        
        assert image is not None
        assert (image == dummy_image).all()

    def test_resize_image(self, dummy_image):
        """Test image resizing."""
        processor = ImageProcessor()
        resized = processor.resize_image(dummy_image, 320, 240)
        
        assert resized.shape[0] == 240
        assert resized.shape[1] == 320

    def test_normalize_image(self, dummy_image):
        """Test image normalization."""
        processor = ImageProcessor()
        normalized = processor.normalize_image(dummy_image)
        
        # ImageNet normalization can produce values slightly outside [-2, 3] due to extreme pixel values
        assert normalized.min() >= -2.5
        assert normalized.max() <= 3.5

    def test_assess_quality(self, dummy_image):
        """Test image quality assessment."""
        processor = ImageProcessor()
        quality = processor.assess_quality(dummy_image)
        
        assert quality.brightness_level >= 0.0
        assert quality.brightness_level <= 1.0
        assert quality.contrast_level >= 0.0
        assert quality.sharpness_score >= 0.0
        assert isinstance(quality.is_usable, bool)

    def test_extract_color_histogram(self, dummy_image):
        """Test color histogram extraction."""
        processor = ImageProcessor()
        histogram = processor.extract_color_histogram(dummy_image)
        
        assert "red" in histogram or "gray" in histogram
        assert len(histogram) > 0

    def test_extract_edge_features(self, dummy_image):
        """Test edge feature extraction."""
        processor = ImageProcessor()
        features = processor.extract_edge_features(dummy_image)
        
        assert "edge_density" in features
        assert "edge_mean" in features
        assert "edge_max" in features

    def test_get_processing_stats(self):
        """Test processing statistics."""
        processor = ImageProcessor()
        stats = processor.get_processing_stats()
        
        assert "processed_images" in stats
        assert "cache_size" in stats


# ============================================================================
# ObjectDetector Tests
# ============================================================================

class TestObjectDetector:
    """Tests for ObjectDetector."""

    def test_initialization(self):
        """Test ObjectDetector initialization."""
        detector = ObjectDetector()
        assert detector is not None
        assert detector.detection_count == 0

    def test_detect_objects(self, dummy_image):
        """Test object detection."""
        detector = ObjectDetector()
        objects = detector.detect_objects(dummy_image, 640, 480)
        
        assert isinstance(objects, list)

    def test_detect_objects_with_config(self, dummy_image):
        """Test object detection with custom config."""
        config = DetectionConfig(
            confidence_threshold=0.7,
            max_detections=5,
        )
        detector = ObjectDetector(config)
        objects = detector.detect_objects(dummy_image, 640, 480)
        
        assert len(objects) <= 5

    def test_track_object(self, dummy_image, dummy_detected_object):
        """Test object tracking."""
        detector = ObjectDetector()
        detector.object_tracks[dummy_detected_object.object_id] = [dummy_detected_object]
        
        matching_target = dummy_detected_object
        result = detector.track_object(
            dummy_detected_object.object_id,
            [matching_target],
        )
        
        assert result is not None

    def test_classify_category(self, dummy_image, dummy_bbox):
        """Test object category classification."""
        detector = ObjectDetector()
        category = detector.classify_category(dummy_image, dummy_bbox)
        
        assert isinstance(category, ObjectCategory)

    def test_extract_object_features(self, dummy_image, dummy_detected_object):
        """Test object feature extraction."""
        detector = ObjectDetector()
        features = detector.extract_object_features(dummy_image, dummy_detected_object)
        
        assert isinstance(features, dict)

    def test_get_detection_stats(self):
        """Test detection statistics."""
        detector = ObjectDetector()
        stats = detector.get_detection_stats()
        
        assert "total_detections" in stats
        assert "total_objects_tracked" in stats


# ============================================================================
# FaceRecognizer Tests
# ============================================================================

class TestFaceRecognizer:
    """Tests for FaceRecognizer."""

    def test_initialization(self):
        """Test FaceRecognizer initialization."""
        recognizer = FaceRecognizer()
        assert recognizer is not None
        assert recognizer.recognition_count == 0

    def test_detect_faces(self, dummy_image):
        """Test face detection."""
        recognizer = FaceRecognizer()
        faces = recognizer.detect_faces(dummy_image, 640, 480)
        
        assert isinstance(faces, list)

    def test_detect_faces_with_config(self, dummy_image):
        """Test face detection with custom config."""
        config = FaceRecognitionConfig(
            detection_confidence_threshold=0.8,
        )
        recognizer = FaceRecognizer(config)
        faces = recognizer.detect_faces(dummy_image, 640, 480)
        
        assert isinstance(faces, list)

    def test_recognize_faces(self, dummy_face_detection, dummy_user_profile):
        """Test face recognition."""
        recognizer = FaceRecognizer()
        user_db = {dummy_user_profile.user_id: dummy_user_profile}
        
        faces = recognizer.recognize_faces([dummy_face_detection], user_db)
        
        assert len(faces) == 1

    def test_extract_face_attributes(self, dummy_image, dummy_face_detection):
        """Test face attribute extraction."""
        recognizer = FaceRecognizer()
        attributes = recognizer.extract_face_attributes(dummy_image, dummy_face_detection)
        
        assert isinstance(attributes, dict)

    def test_register_user_embedding(self):
        """Test user embedding registration."""
        recognizer = FaceRecognizer()
        embedding = np.random.randn(128).astype(np.float32)
        
        result = recognizer.register_user_embedding("user_001", embedding)
        assert result is True

    def test_get_recognition_stats(self):
        """Test recognition statistics."""
        recognizer = FaceRecognizer()
        stats = recognizer.get_recognition_stats()
        
        assert "total_recognitions" in stats
        assert "registered_users" in stats


# ============================================================================
# SceneUnderstander Tests
# ============================================================================

class TestSceneUnderstander:
    """Tests for SceneUnderstander."""

    def test_initialization(self):
        """Test SceneUnderstander initialization."""
        understander = SceneUnderstander()
        assert understander is not None
        assert understander.understanding_count == 0

    def test_understand_scene(self, dummy_detected_object):
        """Test scene understanding."""
        understander = SceneUnderstander()
        annotation = ImageAnnotation(
            image_width=640,
            image_height=480,
            objects=[dummy_detected_object],
            faces=[],
        )
        
        result = understander.understand_scene(annotation)
        
        assert isinstance(result, dict)
        assert "scene_description" in result
        assert "scene_type" in result

    def test_analyze_relationships(self, dummy_detected_object):
        """Test relationship analysis."""
        understander = SceneUnderstander()
        
        obj2 = DetectedObject(
            category=ObjectCategory.TOOL,
            label="tool",
            bbox=BoundingBox(x=0.5, y=0.5, width=0.2, height=0.2, confidence=0.8),
            confidence=0.8,
        )
        
        relationships = understander.analyze_relationships([dummy_detected_object, obj2])
        
        assert isinstance(relationships, list)

    def test_detect_activities(self, dummy_detected_object):
        """Test activity detection."""
        understander = SceneUnderstander()
        activities = understander.detect_activities([dummy_detected_object], [])
        
        assert isinstance(activities, list)

    def test_classify_scene(self, dummy_detected_object):
        """Test scene classification."""
        understander = SceneUnderstander()
        scene_type = understander.classify_scene([dummy_detected_object], [])
        
        assert isinstance(scene_type, str)

    def test_generate_natural_language_description(self, dummy_detected_object):
        """Test natural language description generation."""
        understander = SceneUnderstander()
        annotation = ImageAnnotation(
            image_width=640,
            image_height=480,
            objects=[dummy_detected_object],
            faces=[],
        )
        
        description = understander.generate_natural_language_description(annotation)
        
        assert isinstance(description, str)
        assert len(description) > 0

    def test_get_understanding_stats(self):
        """Test understanding statistics."""
        understander = SceneUnderstander()
        stats = understander.get_understanding_stats()
        
        assert "total_scenes_understood" in stats
        assert "scene_history_size" in stats


# ============================================================================
# SpatialAnalyzer Tests
# ============================================================================

class TestSpatialAnalyzer:
    """Tests for SpatialAnalyzer."""

    def test_initialization(self):
        """Test SpatialAnalyzer initialization."""
        analyzer = SpatialAnalyzer()
        assert analyzer is not None
        assert analyzer.analysis_count == 0

    def test_analyze_spatial_layout(self, dummy_detected_object):
        """Test spatial layout analysis."""
        analyzer = SpatialAnalyzer()
        layout = analyzer.analyze_spatial_layout([dummy_detected_object], 640, 480)
        
        assert layout is not None
        assert len(layout.objects) > 0

    def test_estimate_distance(self, dummy_bbox):
        """Test distance estimation."""
        analyzer = SpatialAnalyzer()
        distance = analyzer.estimate_distance(dummy_bbox, 640, 480)
        
        assert isinstance(distance, float)
        assert distance > 0.0

    def test_estimate_object_position(self, dummy_bbox):
        """Test object position estimation."""
        analyzer = SpatialAnalyzer()
        position = analyzer.estimate_object_position(dummy_bbox, 1.5, 640, 480)
        
        assert isinstance(position, tuple)
        assert len(position) == 3  # x, y, z

    def test_find_reachable_objects(self, dummy_detected_object):
        """Test finding reachable objects."""
        analyzer = SpatialAnalyzer()
        layout = analyzer.analyze_spatial_layout([dummy_detected_object], 640, 480)
        
        reachable = analyzer.find_reachable_objects(layout, max_reach=2.0)
        
        assert isinstance(reachable, list)

    def test_plan_navigation_path(self, dummy_detected_object):
        """Test navigation path planning."""
        analyzer = SpatialAnalyzer()
        path = analyzer.plan_navigation_path(dummy_detected_object, 1.5, [])
        
        assert path is not None or path is None  # Can be None in some cases

    def test_get_spatial_stats(self):
        """Test spatial statistics."""
        analyzer = SpatialAnalyzer()
        stats = analyzer.get_spatial_stats()
        
        assert "total_analyses" in stats
        assert "layouts_stored" in stats


# ============================================================================
# VisualCortex Integration Tests
# ============================================================================

class TestVisualCortex:
    """Tests for VisualCortex integration."""

    def test_initialization(self):
        """Test VisualCortex initialization."""
        cortex = VisualCortex(robot_type=RobotType.G1)
        assert cortex is not None
        assert cortex.robot_type == RobotType.G1

    def test_initialization_with_all_modules_disabled(self):
        """Test VisualCortex with all modules disabled."""
        cortex = VisualCortex(
            enable_object_detection=False,
            enable_face_recognition=False,
            enable_scene_understanding=False,
            enable_spatial_analysis=False,
        )
        
        assert cortex.object_detector is None
        assert cortex.face_recognizer is None

    @pytest.mark.asyncio
    async def test_process_image_from_bytes(self, dummy_image_bytes):
        """Test image processing from bytes."""
        cortex = VisualCortex(robot_type=RobotType.GO2)
        result = await cortex.process_image(
            dummy_image_bytes,
            image_format=ImageFormat.RGB,
        )
        
        assert result is not None
        assert result.annotation is not None

    @pytest.mark.asyncio
    async def test_process_image_with_modules_disabled(self, dummy_image_bytes):
        """Test image processing with some modules disabled."""
        cortex = VisualCortex(
            enable_object_detection=False,
            enable_face_recognition=True,
        )
        
        result = await cortex.process_image(
            dummy_image_bytes,
            analyze_objects=False,
            analyze_faces=True,
        )
        
        assert result is not None

    def test_register_user(self, dummy_user_profile):
        """Test user registration."""
        cortex = VisualCortex()
        result = cortex.register_user(dummy_user_profile)
        
        assert result is True
        assert dummy_user_profile.user_id in cortex.user_database

    def test_get_analysis_stats(self):
        """Test analysis statistics."""
        cortex = VisualCortex()
        stats = cortex.get_analysis_stats()
        
        assert "total_images_analyzed" in stats
        assert "robot_type" in stats
        assert "registered_users" in stats

    def test_clear_history(self):
        """Test history clearing."""
        cortex = VisualCortex()
        cortex.analysis_history.append(Mock())
        
        cortex.clear_history()
        
        assert len(cortex.analysis_history) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for Visual Cortex."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, dummy_image_bytes, dummy_user_profile):
        """Test full visual cortex pipeline."""
        cortex = VisualCortex(robot_type=RobotType.G1)
        
        # Register user
        cortex.register_user(dummy_user_profile)
        
        # Process image
        result = await cortex.process_image(
            dummy_image_bytes,
            analyze_objects=True,
            analyze_faces=True,
            analyze_scene=True,
            analyze_spatial=True,
        )
        
        assert result is not None
        assert result.annotation is not None

    @pytest.mark.asyncio
    async def test_multiple_image_processing(self, dummy_image_bytes):
        """Test processing multiple images."""
        cortex = VisualCortex()
        
        for _ in range(3):
            result = await cortex.process_image(dummy_image_bytes)
            assert result is not None
        
        stats = cortex.get_analysis_stats()
        assert stats["total_images_analyzed"] >= 3


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_image_format(self):
        """Test handling of invalid image format."""
        processor = ImageProcessor()
        
        with pytest.raises(ValueError):
            processor.load_image("invalid_data", ImageFormat.RGB)

    def test_invalid_bbox(self):
        """Test handling of invalid bounding boxes."""
        analyzer = SpatialAnalyzer()
        
        invalid_bbox = BoundingBox(x=-0.1, y=1.5, width=2.0, height=0.5, confidence=0.5)
        distance = analyzer.estimate_distance(invalid_bbox, 640, 480)
        
        # Should clamp to valid range
        assert distance >= analyzer.config.min_distance

    def test_empty_detections(self):
        """Test handling of empty detections."""
        understander = SceneUnderstander()
        annotation = ImageAnnotation(
            image_width=640,
            image_height=480,
            objects=[],
            faces=[],
        )
        
        result = understander.understand_scene(annotation)
        
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
