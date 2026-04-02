"""Image processor module for visual cortex.

This module provides basic image processing capabilities:
- Image loading and format conversion
- Image resizing and normalization
- Color space conversions
- Image quality assessment
- Feature extraction
"""

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from uuid import uuid4

import numpy as np
from PIL import Image

from openerb.core.logger import get_logger
from openerb.core.types import ImageFormat, ImageAnnotation

logger = get_logger(__name__)


@dataclass
class ImageQuality:
    """Assessment of image quality."""
    brightness_level: float  # 0-1
    contrast_level: float  # 0-1
    sharpness_score: float  # 0-1
    noise_level: float  # 0-1
    is_usable: bool
    issues: List[str]  # List of quality issues


class ImageProcessor:
    """Image processing engine for visual cortex."""

    def __init__(self):
        """Initialize image processor."""
        self.cache: Dict[str, Any] = {}
        self.processed_count = 0
        logger.info("ImageProcessor initialized")

    def load_image(
        self,
        image_source: bytes | str | np.ndarray,
        format: ImageFormat = ImageFormat.RGB,
    ) -> Tuple[np.ndarray, int, int]:
        """Load image from various sources.
        
        Args:
            image_source: Image bytes, file path, or numpy array
            format: Expected image format
            
        Returns:
            Tuple of (image_array, width, height)
            
        Raises:
            ValueError: If image cannot be loaded
        """
        try:
            if isinstance(image_source, bytes):
                image = Image.open(io.BytesIO(image_source))
            elif isinstance(image_source, str):
                image = Image.open(image_source)
            elif isinstance(image_source, np.ndarray):
                image = Image.fromarray(image_source.astype("uint8"))
            else:
                raise ValueError(f"Unsupported image source type: {type(image_source)}")

            # Convert to specified format
            image_array = self._convert_format(image, format)
            width, height = image.size

            logger.debug(f"Image loaded: {width}x{height}, format={format}")
            return image_array, width, height

        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            raise ValueError(f"Failed to load image: {e}") from e

    def resize_image(
        self,
        image: np.ndarray,
        target_width: int,
        target_height: int,
        maintain_aspect: bool = True,
    ) -> np.ndarray:
        """Resize image to target dimensions.
        
        Args:
            image: Input image array
            target_width: Target width
            target_height: Target height
            maintain_aspect: Whether to maintain aspect ratio
            
        Returns:
            Resized image array
        """
        try:
            pil_image = Image.fromarray(image.astype("uint8"))

            if maintain_aspect:
                pil_image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            else:
                pil_image = pil_image.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS,
                )

            resized = np.array(pil_image)
            logger.debug(
                f"Image resized from {image.shape} to {resized.shape}"
            )
            return resized

        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            raise ValueError(f"Failed to resize image: {e}") from e

    def normalize_image(
        self,
        image: np.ndarray,
        mean: Optional[List[float]] = None,
        std: Optional[List[float]] = None,
    ) -> np.ndarray:
        """Normalize image using mean and std deviation.
        
        Args:
            image: Input image array (0-255)
            mean: Mean values for each channel (default: ImageNet mean)
            std: Standard deviation for each channel (default: ImageNet std)
            
        Returns:
            Normalized image array
        """
        try:
            # Default to ImageNet normalization
            if mean is None:
                mean = [0.485, 0.456, 0.406]
            if std is None:
                std = [0.229, 0.224, 0.225]

            # Convert to float and normalize to [0, 1]
            normalized = image.astype(np.float32) / 255.0

            # Apply mean and std normalization
            for i in range(min(3, normalized.shape[2] if len(normalized.shape) > 2 else 1)):
                normalized[..., i] = (normalized[..., i] - mean[i]) / std[i]

            logger.debug("Image normalized with ImageNet statistics")
            return normalized

        except Exception as e:
            logger.error(f"Failed to normalize image: {e}")
            raise ValueError(f"Failed to normalize image: {e}") from e

    def convert_format(
        self,
        image: np.ndarray,
        from_format: ImageFormat,
        to_format: ImageFormat,
    ) -> np.ndarray:
        """Convert image between different color formats.
        
        Args:
            image: Input image array
            from_format: Source format
            to_format: Target format
            
        Returns:
            Converted image array
        """
        try:
            pil_image = Image.fromarray(image.astype("uint8"))
            converted = self._convert_format(pil_image, to_format)
            logger.debug(f"Image converted from {from_format} to {to_format}")
            return converted

        except Exception as e:
            logger.error(f"Failed to convert image format: {e}")
            raise ValueError(f"Failed to convert image format: {e}") from e

    def assess_quality(self, image: np.ndarray) -> ImageQuality:
        """Assess image quality.
        
        Args:
            image: Input image array
            
        Returns:
            ImageQuality assessment
        """
        try:
            # Brightness assessment
            brightness = np.mean(image) / 255.0

            # Contrast assessment
            contrast = np.std(image) / 128.0

            # Sharpness assessment (using Laplacian variance)
            gray = np.mean(image, axis=2) if len(image.shape) == 3 else image
            sharpness = self._calculate_laplacian_variance(gray)

            # Noise level (inverse of sharpness)
            noise = max(0, 1.0 - sharpness)

            # Determine if image is usable
            issues = []
            if brightness < 0.1:
                issues.append("Too dark")
            if brightness > 0.95:
                issues.append("Too bright")
            if contrast < 0.2:
                issues.append("Low contrast")

            is_usable = len(issues) == 0

            return ImageQuality(
                brightness_level=min(1.0, brightness),
                contrast_level=min(1.0, contrast),
                sharpness_score=min(1.0, sharpness),
                noise_level=noise,
                is_usable=is_usable,
                issues=issues,
            )

        except Exception as e:
            logger.error(f"Failed to assess image quality: {e}")
            return ImageQuality(
                brightness_level=0.5,
                contrast_level=0.5,
                sharpness_score=0.0,
                noise_level=0.5,
                is_usable=False,
                issues=[str(e)],
            )

    def extract_color_histogram(
        self, image: np.ndarray, bins: int = 256
    ) -> Dict[str, List[float]]:
        """Extract color histogram from image.
        
        Args:
            image: Input image array
            bins: Number of histogram bins
            
        Returns:
            Dictionary with histogram for each channel
        """
        try:
            histograms = {}

            if len(image.shape) == 3:
                channel_names = ["red", "green", "blue"]
                for i, name in enumerate(channel_names):
                    hist, _ = np.histogram(image[:, :, i], bins=bins, range=(0, 256))
                    histograms[name] = (hist / hist.sum()).tolist()
            else:
                hist, _ = np.histogram(image, bins=bins, range=(0, 256))
                histograms["gray"] = (hist / hist.sum()).tolist()

            logger.debug("Color histograms extracted")
            return histograms

        except Exception as e:
            logger.error(f"Failed to extract color histogram: {e}")
            return {}

    def extract_edge_features(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract edge-based features from image.
        
        Args:
            image: Input image array
            
        Returns:
            Dictionary with edge features
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = np.mean(image, axis=2).astype(np.uint8)
            else:
                gray = image.astype(np.uint8)

            # Simple edge detection using Sobel approximation
            kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
            kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

            edges_x = self._convolve2d(gray, kernel_x)
            edges_y = self._convolve2d(gray, kernel_y)

            edge_magnitude = np.sqrt(edges_x**2 + edges_y**2)
            edge_density = np.count_nonzero(edge_magnitude > 50) / edge_magnitude.size

            return {
                "edge_density": float(edge_density),
                "edge_mean": float(np.mean(edge_magnitude)),
                "edge_max": float(np.max(edge_magnitude)),
            }

        except Exception as e:
            logger.error(f"Failed to extract edge features: {e}")
            return {}

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Dictionary with processing stats
        """
        return {"processed_images": self.processed_count, "cache_size": len(self.cache)}

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _convert_format(self, image: Image.Image, target_format: ImageFormat) -> np.ndarray:
        """Convert PIL image to target format."""
        if target_format == ImageFormat.RGB:
            if image.mode != "RGB":
                image = image.convert("RGB")
        elif target_format == ImageFormat.BGR:
            if image.mode != "RGB":
                image = image.convert("RGB")
            image = np.array(image)
            image = image[:, :, ::-1]  # RGB to BGR
            return image
        elif target_format == ImageFormat.RGBA:
            if image.mode != "RGBA":
                image = image.convert("RGBA")
        elif target_format == ImageFormat.GRAYSCALE:
            if image.mode != "L":
                image = image.convert("L")

        return np.array(image)

    def _calculate_laplacian_variance(self, image: np.ndarray) -> float:
        """Calculate Laplacian variance for sharpness estimation."""
        try:
            kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])
            laplacian = self._convolve2d(image, kernel)
            variance = float(np.var(laplacian))
            return min(1.0, variance / 1000.0)  # Normalize
        except Exception:
            return 0.0

    def _convolve2d(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Simple 2D convolution."""
        h, w = image.shape
        kh, kw = kernel.shape
        oh, ow = h - kh + 1, w - kw + 1

        output = np.zeros((oh, ow), dtype=np.float32)
        for i in range(oh):
            for j in range(ow):
                output[i, j] = np.sum(image[i : i + kh, j : j + kw] * kernel)

        return output
