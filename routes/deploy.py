from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

from database import get_db, Deployment, User
from utils.auth_utils import decode_token
from utils.deploy_utils import generate_unique_url, create_deployment_url, validate_deployment_url

router = APIRouter(prefix="/api/deploy", tags=["deployments"])

# Pydantic models
class DeploymentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    html_content: str
    css_content: Optional[str] = None
    js_content: Optional[str] = None

class DeploymentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    deploy_url: str
    full_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DeploymentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    html_content: Optional[str] = None
    css_content: Optional[str] = None
    js_content: Optional[str] = None
    is_active: Optional[bool] = None

# Helper function to get current user
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Try to find user by ID first, then by username
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
    except ValueError:
        # If user_id is not a number, try to find by username
        user = db.query(User).filter(User.username == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

@router.post("/", response_model=DeploymentResponse)
async def create_deployment(
    deployment: DeploymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new deployment"""
    
    # Generate unique URL
    url_slug = generate_unique_url()
    
    # Create deployment
    db_deployment = Deployment(
        title=deployment.title,
        description=deployment.description,
        deploy_url=url_slug,
        html_content=deployment.html_content,
        css_content=deployment.css_content,
        js_content=deployment.js_content,
        user_id=user.id
    )
    
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)
    
    # Create full URL (use ngrok URL if available)
    base_url = os.environ.get('NGROK_URL', "http://localhost:8003")
    full_url = create_deployment_url(base_url, url_slug)
    
    return DeploymentResponse(
        id=db_deployment.id,
        title=db_deployment.title,
        description=db_deployment.description,
        deploy_url=db_deployment.deploy_url,
        full_url=full_url,
        is_active=db_deployment.is_active,
        created_at=db_deployment.created_at,
        updated_at=db_deployment.updated_at
    )

@router.get("/", response_model=List[DeploymentResponse])
async def get_user_deployments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all deployments for current user"""
    
    deployments = db.query(Deployment).filter(
        Deployment.user_id == user.id
    ).order_by(Deployment.created_at.desc()).all()
    
    base_url = os.environ.get('NGROK_URL', "http://localhost:8003")
    
    return [
        DeploymentResponse(
            id=deployment.id,
            title=deployment.title,
            description=deployment.description,
            deploy_url=deployment.deploy_url,
            full_url=create_deployment_url(base_url, deployment.deploy_url),
            is_active=deployment.is_active,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at
        )
        for deployment in deployments
    ]

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific deployment by ID"""
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user.id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    base_url = os.environ.get('NGROK_URL', "http://localhost:8003")
    
    return DeploymentResponse(
        id=deployment.id,
        title=deployment.title,
        description=deployment.description,
        deploy_url=deployment.deploy_url,
        full_url=create_deployment_url(base_url, deployment.deploy_url),
        is_active=deployment.is_active,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at
    )

@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: int,
    deployment_update: DeploymentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update deployment"""
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user.id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    # Update fields
    update_data = deployment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deployment, field, value)
    
    deployment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(deployment)
    
    base_url = os.environ.get('NGROK_URL', "http://localhost:8003")
    
    return DeploymentResponse(
        id=deployment.id,
        title=deployment.title,
        description=deployment.description,
        deploy_url=deployment.deploy_url,
        full_url=create_deployment_url(base_url, deployment.deploy_url),
        is_active=deployment.is_active,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at
    )

@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete deployment"""
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user.id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    db.delete(deployment)
    db.commit()
    
    return {"message": "Deployment deleted successfully"}

@router.get("/public/{deploy_url}", response_class=HTMLResponse)
async def serve_deployment(
    deploy_url: str,
    db: Session = Depends(get_db)
):
    """Serve deployed website"""
    deployment = db.query(Deployment).filter(
        Deployment.deploy_url == deploy_url,
        Deployment.is_active == True
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or inactive"
        )
    
    # Combine HTML, CSS, and JS
    html_content = deployment.html_content
    
    # Add CSS if exists
    if deployment.css_content:
        css_tag = f"<style>{deployment.css_content}</style>"
        # Insert CSS before closing head tag or at the beginning
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{css_tag}\n</head>")
        else:
            html_content = f"{css_tag}\n{html_content}"
    
    # Add JS if exists
    if deployment.js_content:
        js_tag = f"<script>{deployment.js_content}</script>"
        # Insert JS before closing body tag or at the end
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{js_tag}\n</body>")
        else:
            html_content = f"{html_content}\n{js_tag}"
    
    return HTMLResponse(content=html_content)
