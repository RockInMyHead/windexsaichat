import secrets
import string
from typing import Optional

from database import Deployment, SessionLocal


def generate_unique_url(length: int = 8) -> str:
    """Гenerate a unique URL slug for deployment"""
    alphabet = string.ascii_lowercase + string.digits
    while True:
        url_slug = "".join(secrets.choice(alphabet) for _ in range(length))

        # Check if URL already exists
        db = SessionLocal()
        try:
            existing_deployment = (
                db.query(Deployment).filter(Deployment.deploy_url == url_slug).first()
            )
            if not existing_deployment:
                return url_slug
        finally:
            db.close()


def create_deployment_url(base_url: str, slug: str) -> str:
    """Create full deployment URL"""
    return f"{base_url}/deploy/{slug}"


def validate_deployment_url(url: str) -> bool:
    """Validate deployment URL format"""
    if not url or len(url) < 3:
        return False

    # Check if URL contains only allowed characters
    allowed_chars = string.ascii_lowercase + string.digits + "-"
    return all(c in allowed_chars for c in url)
