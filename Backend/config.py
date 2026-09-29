import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration — reads from environment variables."""

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv(
        "SUPABASE_SERVICE_KEY",
        "",
    )

    FLASK_SECRET_KEY: str = os.getenv(
        "FLASK_SECRET_KEY",
        "change-me",
    )

    FLASK_DEBUG: bool = (
        os.getenv("FLASK_DEBUG", "false").lower()
        == "true"
    )

    FACE_MATCH_THRESHOLD: float = float(
        os.getenv("FACE_MATCH_THRESHOLD", "0.45")
    )

    FACE_DETECTION_SIZE: int = int(
        os.getenv("FACE_DETECTION_SIZE", "150")
    )

    FACE_DETECTION_MODEL: int = int(
        os.getenv("FACE_DETECTION_MODEL", "1")
    )

    SHAPE_PREDICTOR_PATH: str = os.getenv(
        "SHAPE_PREDICTOR_PATH",
        "models/shape_predictor_68_face_landmarks.dat",
    )

    FACE_RECOGNITION_MODEL_PATH: str = os.getenv(
        "FACE_RECOGNITION_MODEL_PATH",
        "models/dlib_face_recognition_resnet_model_v1.dat",
    )

    ROOM_CODE_LENGTH: int = int(
        os.getenv("ROOM_CODE_LENGTH", "6")
    )

    ROOM_CODE_TTL_SECONDS: int = int(
        os.getenv("ROOM_CODE_TTL_SECONDS", "120")
    )

    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "*",
    )

    MAX_CONTENT_LENGTH: int = int(
        os.getenv(
            "MAX_CONTENT_LENGTH",
            str(16 * 1024 * 1024),
        )
    )


config = Config()