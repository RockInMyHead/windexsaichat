from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import User as DBUser
from database import get_db
from utils.auth_utils import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token,
                              decode_token, get_password_hash, verify_password)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


# Pydantic models
class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    role: str = "user"  # Default role


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def get_user_by_username(db: Session, username: str) -> Optional[DBUser]:
    """Get user by username from database"""
    return db.query(DBUser).filter(DBUser.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[DBUser]:
    """Get user by email from database"""
    return db.query(DBUser).filter(DBUser.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[DBUser]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    db_user = get_user_by_username(db, username)
    if db_user is None:
        raise credentials_exception

    return User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at,
        role="user",  # Default role for now
    )


@router.post("/register", response_model=User)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)

    # Create new user
    db_user = DBUser(
        username=user.username, email=user.email, hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return User(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at,
        role="user"
    )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


# Subscription models
class SubscriptionActivationRequest(BaseModel):
    plan: str  # 'pro' or 'free'


class SubscriptionActivationResponse(BaseModel):
    success: bool
    message: str
    plan: str
    expires_at: Optional[datetime] = None


@router.post("/activate-subscription", response_model=SubscriptionActivationResponse)
async def activate_subscription(
    request: SubscriptionActivationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Activate subscription plan"""

    if request.plan not in ["free", "pro"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Must be 'free' or 'pro'",
        )

    try:
        # Получаем пользователя из базы данных
        db_user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if request.plan == "pro":
            # Активируем Pro подписку на 30 дней
            expires_at = datetime.now() + timedelta(days=30)

            # Обновляем пользователя в базе данных
            db_user.subscription_plan = "pro"
            db_user.subscription_expires_at = expires_at
            db.commit()

            return SubscriptionActivationResponse(
                success=True,
                message="Pro подписка успешно активирована на 30 дней!",
                plan="pro",
                expires_at=expires_at,
            )

        elif request.plan == "free":
            # Переход на бесплатный план
            db_user.subscription_plan = "free"
            db_user.subscription_expires_at = None
            db.commit()

            return SubscriptionActivationResponse(
                success=True,
                message="Переход на бесплатный план выполнен",
                plan="free",
                expires_at=None,
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating subscription: {str(e)}",
        )


@router.get("/api/auth/subscription-status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current subscription status"""

    try:
        db_user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        plan = db_user.subscription_plan or "free"
        expires_at = db_user.subscription_expires_at

        # Проверяем, не истекла ли подписка
        is_active = True
        if expires_at and expires_at < datetime.now():
            is_active = False
            plan = "free"
            # Обновляем статус в базе данных
            db_user.subscription_plan = "free"
            db_user.subscription_expires_at = None
            db.commit()

        return {
            "plan": plan,
            "is_active": is_active,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "days_remaining": (
                (expires_at - datetime.now()).days
                if expires_at and expires_at > datetime.now()
                else 0
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting subscription status: {str(e)}",
        )
