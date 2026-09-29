"""
Face recognition pipeline using dlib ResNet-34 → 128-D embeddings.

Responsibilities
----------------
1. Decode base64 images.
2. Detect a single face in an image.
3. Compute a 128-D face embedding.
4. Compare two embeddings using Euclidean distance.
5. Decide MATCH / NO_MATCH using a configurable threshold.
"""

import base64
import io
import logging
from pathlib import Path

import cv2
import dlib
import numpy as np
from PIL import Image

from config import config

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────────────────────
# Base64 image decoding
# ───────────────────────────────────────────────────────────────────────

def decode_base64_image(image_data: str) -> np.ndarray:
    """
    Decode a base64 image string and return an RGB numpy array.

    Supports:
        - Normal base64 strings
        - data:image/jpeg;base64,... format
        - data:image/png;base64,... format
    """

    if not image_data:
        raise ValueError("Image data is empty.")

    # Remove data URI prefix if present
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(image_data)

        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        return np.array(image)

    except Exception as e:
        raise ValueError(
            f"Invalid base64 image: {e}"
        )


# ───────────────────────────────────────────────────────────────────────
# Lazy-loaded dlib models
# ───────────────────────────────────────────────────────────────────────

_detector = None
_sp = None
_fr = None


def _load_models() -> None:
    """
    Load dlib models only once.
    """

    global _detector, _sp, _fr

    if _detector is not None:
        return

    shape_path = Path(
        config.SHAPE_PREDICTOR_PATH
    )

    fr_path = Path(
        config.FACE_RECOGNITION_MODEL_PATH
    )

    # Check shape predictor
    if not shape_path.exists():
        raise FileNotFoundError(
            f"Shape predictor not found at {shape_path}"
        )

    # Check face recognition model
    if not fr_path.exists():
        raise FileNotFoundError(
            f"Face recognition model not found at {fr_path}"
        )

    # ────────────────────────────────────────────────────────────────
    # Face detector
    # ────────────────────────────────────────────────────────────────

    if config.FACE_DETECTION_MODEL == 0:

        cnn_model_path = (
            fr_path.parent
            / "mmod_human_face_detector.dat"
        )

        if not cnn_model_path.exists():
            raise FileNotFoundError(
                f"CNN face detector model not found at "
                f"{cnn_model_path}"
            )

        _detector = (
            dlib.cnn_face_detection_model_v1(
                str(cnn_model_path)
            )
        )

    else:
        # HOG face detector
        _detector = (
            dlib.get_frontal_face_detector()
        )

    # ────────────────────────────────────────────────────────────────
    # 68-point landmark model
    # ────────────────────────────────────────────────────────────────

    _sp = dlib.shape_predictor(
        str(shape_path)
    )

    # ────────────────────────────────────────────────────────────────
    # dlib ResNet face recognition model
    # ────────────────────────────────────────────────────────────────

    _fr = dlib.face_recognition_model_v1(
        str(fr_path)
    )

    logger.info(
        "dlib models loaded (detector=%s)",
        "cnn"
        if config.FACE_DETECTION_MODEL == 0
        else "hog"
    )


# ───────────────────────────────────────────────────────────────────────
# Image loading helpers
# ───────────────────────────────────────────────────────────────────────

def _load_image_from_bytes(
    data: bytes
) -> np.ndarray:
    """
    Load raw image bytes into a BGR numpy array.
    """

    if not data:
        raise ValueError(
            "Image data is empty."
        )

    nparr = np.frombuffer(
        data,
        np.uint8
    )

    img = cv2.imdecode(
        nparr,
        cv2.IMREAD_COLOR
    )

    if img is None:
        raise ValueError(
            "Could not decode image bytes"
        )

    return img


def _load_image_from_base64(
    b64: str
) -> np.ndarray:
    """
    Load a base64-encoded image into a BGR numpy array.
    """

    if not b64:
        raise ValueError(
            "Base64 image data is empty."
        )

    # Remove data URI prefix
    if "," in b64:
        b64 = b64.split(",", 1)[1]

    try:
        data = base64.b64decode(b64)
    except Exception as e:
        raise ValueError(
            f"Invalid base64 data: {e}"
        )

    return _load_image_from_bytes(data)


def _to_rgb(
    bgr: np.ndarray
) -> np.ndarray:
    """
    Convert BGR image to RGB.
    """

    return cv2.cvtColor(
        bgr,
        cv2.COLOR_BGR2RGB
    )


def _to_dlib_rgb_image(
    rgb: np.ndarray
) -> object:
    """
    dlib accepts the RGB numpy array directly.
    """

    return rgb


# ───────────────────────────────────────────────────────────────────────
# Face detection
# ───────────────────────────────────────────────────────────────────────

def detect_face(
    image_bgr: np.ndarray
):
    """
    Detect the largest face in a BGR image.

    Returns:
        dlib.rectangle if a face is found
        None if no face is found
    """

    if image_bgr is None:
        raise ValueError(
            "Image is empty."
        )

    _load_models()

    # BGR → RGB
    rgb = _to_rgb(
        image_bgr
    )

    dlib_img = _to_dlib_rgb_image(
        rgb
    )

    # ────────────────────────────────────────────────────────────────
    # CNN detector
    # ────────────────────────────────────────────────────────────────

    if config.FACE_DETECTION_MODEL == 0:

        detections = _detector(
            dlib_img,
            1
        )

        if not detections:
            return None

        # Select largest face
        best = max(
            detections,
            key=lambda d: d.rect.area()
        )

        return best.rect

    # ────────────────────────────────────────────────────────────────
    # HOG detector
    # ────────────────────────────────────────────────────────────────

    detections = _detector(
        dlib_img,
        1
    )

    if not detections:
        return None

    # Select largest face
    return max(
        detections,
        key=lambda d: d.area()
    )


# ───────────────────────────────────────────────────────────────────────
# Face embedding
# ───────────────────────────────────────────────────────────────────────

def compute_embedding(
    image_bgr: np.ndarray
) -> list[float]:
    """
    Compute a 128-D face embedding from a BGR image.

    Pipeline:

        Image
          ↓
        Face Detection
          ↓
        68 Facial Landmarks
          ↓
        dlib ResNet
          ↓
        128-D Face Embedding
    """

    if image_bgr is None:
        raise ValueError(
            "Image is empty."
        )

    _load_models()

    # Detect face
    face = detect_face(
        image_bgr
    )

    if face is None:
        raise ValueError(
            "No face detected in the image"
        )

    # BGR → RGB
    rgb = _to_rgb(
        image_bgr
    )

    dlib_img = _to_dlib_rgb_image(
        rgb
    )

    # Detect 68 facial landmarks
    shape = _sp(
        dlib_img,
        face
    )

    # Generate 128-D face descriptor
    descriptor = (
        _fr.compute_face_descriptor(
            dlib_img,
            shape
        )
    )

    embedding = [
        float(value)
        for value in descriptor
    ]

    # Confirm 128 dimensions
    if len(embedding) != 128:
        raise ValueError(
            f"Expected 128-D embedding, "
            f"but received {len(embedding)} dimensions."
        )

    return embedding


# ───────────────────────────────────────────────────────────────────────
# get_face_embedding
# ───────────────────────────────────────────────────────────────────────

def get_face_embedding(
    image: np.ndarray
) -> list[float]:
    """
    Generate a 128-D face embedding from an RGB numpy image.

    decode_base64_image() returns RGB,
    while compute_embedding() expects BGR.
    """

    if image is None:
        raise ValueError(
            "Image is empty."
        )

    if not isinstance(
        image,
        np.ndarray
    ):
        raise ValueError(
            "Image must be a numpy array."
        )

    if len(image.shape) != 3:
        raise ValueError(
            "Invalid image format."
        )

    if image.shape[2] != 3:
        raise ValueError(
            "Image must have 3 color channels."
        )

    # RGB → BGR
    image_bgr = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2BGR
    )

    return compute_embedding(
        image_bgr
    )


# ───────────────────────────────────────────────────────────────────────
# Euclidean distance
# ───────────────────────────────────────────────────────────────────────

def euclidean_distance(
    emb1: list[float],
    emb2: list[float]
) -> float:
    """
    Calculate Euclidean distance between
    two 128-D face embeddings.
    """

    if not emb1 or not emb2:
        raise ValueError(
            "Embeddings cannot be empty."
        )

    if len(emb1) != 128:
        raise ValueError(
            f"First embedding must contain "
            f"128 values, got {len(emb1)}."
        )

    if len(emb2) != 128:
        raise ValueError(
            f"Second embedding must contain "
            f"128 values, got {len(emb2)}."
        )

    a = np.array(
        emb1,
        dtype=np.float64
    )

    b = np.array(
        emb2,
        dtype=np.float64
    )

    return float(
        np.linalg.norm(a - b)
    )


# ───────────────────────────────────────────────────────────────────────
# compare_embeddings
# ───────────────────────────────────────────────────────────────────────

def compare_embeddings(
    embedding1: list[float],
    embedding2: list[float],
    threshold: float | None = None,
) -> dict:
    """
    Compare two 128-D face embeddings.

    Returns:

        {
            "match": True/False,
            "distance": float,
            "threshold": float
        }
    """

    if threshold is None:
        threshold = config.FACE_MATCH_THRESHOLD

    # Validate dimensions
    if len(embedding1) != 128:
        raise ValueError(
            "First embedding must be 128-D."
        )

    if len(embedding2) != 128:
        raise ValueError(
            "Second embedding must be 128-D."
        )

    # Calculate distance
    distance = euclidean_distance(
        embedding1,
        embedding2
    )

    # Face match decision
    match = distance <= threshold

    return {
        "match": match,
        "distance": round(
            distance,
            4
        ),
        "threshold": threshold,
    }


# ───────────────────────────────────────────────────────────────────────
# verify_face
# ───────────────────────────────────────────────────────────────────────

def verify_face(
    captured_embedding: list[float],
    stored_embedding: list[float],
    threshold: float | None = None,
) -> dict:
    """
    Compare captured face embedding
    with stored face embedding.

    Returns:

        {
            "match": True/False,
            "distance": float,
            "threshold": float
        }
    """

    return compare_embeddings(
        captured_embedding,
        stored_embedding,
        threshold
    )


# ───────────────────────────────────────────────────────────────────────
# Convenience functions
# ───────────────────────────────────────────────────────────────────────

def embedding_from_base64(
    b64_string: str
) -> list[float]:
    """
    Base64 image → 128-D face embedding.
    """

    bgr = _load_image_from_base64(
        b64_string
    )

    return compute_embedding(
        bgr
    )


def embedding_from_bytes(
    data: bytes
) -> list[float]:
    """
    Raw image bytes → 128-D face embedding.
    """

    bgr = _load_image_from_bytes(
        data
    )

    return compute_embedding(
        bgr
    )


def embedding_from_file(
    path: str
) -> list[float]:
    """
    Image file → 128-D face embedding.
    """

    bgr = cv2.imread(
        path
    )

    if bgr is None:
        raise ValueError(
            f"Could not read image from {path}"
        )

    return compute_embedding(
        bgr
    )