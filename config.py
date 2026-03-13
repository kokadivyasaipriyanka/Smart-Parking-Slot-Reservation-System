import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --------------------------------------------------
    # Flask Configuration
    # --------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "smart-parking-secret-key")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

    # --------------------------------------------------
    # Database Configuration
    # --------------------------------------------------
    DB_HOST = os.getenv("DB_HOST", "smart-parking-db.c14uquikc9sl.eu-west-1.rds.amazonaws.com")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "smart-parking-db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "adminpass")

    # --------------------------------------------------
    # AWS Configuration
    # --------------------------------------------------
    AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "smart-parking-frontend-files-2026")
    SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "arn:aws:sns:eu-west-1:313045748163:parking-booking-alerts")

    # --------------------------------------------------
    # Optional Upload / App Settings
    # --------------------------------------------------
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "5242880"))  # 5 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


    DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "System Admin")
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    DEFAULT_ADMIN_PHONE = os.getenv("DEFAULT_ADMIN_PHONE", "9999999999")

    @staticmethod
    def validate_config():
        """
        Optional helper to validate critical configuration values.
        """
        required_values = {
            "DB_HOST": Config.DB_HOST,
            "DB_NAME": Config.DB_NAME,
            "DB_USER": Config.DB_USER,
            "DB_PASSWORD": Config.DB_PASSWORD,
        }

        missing = [key for key, value in required_values.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration values: {', '.join(missing)}")