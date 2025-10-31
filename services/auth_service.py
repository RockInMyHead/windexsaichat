"""
Authentication service with business logic
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.user import TokenData, User, UserCreate

# Import the actual User model
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import User as DBUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[DBUser]:
        """Authenticate a user"""
        user = db.query(DBUser).filter(DBUser.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, db: Session, user: UserCreate) -> DBUser:
        """Create a new user"""
        hashed_password = self.get_password_hash(user.password)
        db_user = DBUser(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_user_by_username(self, db: Session, username: str) -> Optional[DBUser]:
        """Get user by username"""
        return db.query(DBUser).filter(DBUser.username == username).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[DBUser]:
        """Get user by email"""
        return db.query(DBUser).filter(DBUser.email == email).first()

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return TokenData(username=username)
        except JWTError:
            return None
