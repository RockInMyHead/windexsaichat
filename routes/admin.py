from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from routes.auth import get_current_user, User
from database import get_db, User as DBUser

router = APIRouter()

@router.get("/api/admin/users")
async def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all registered users (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    users = db.query(DBUser).all()
    return {"users": [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "role": "user"  # Default role for now
        }
        for user in users
    ]}

@router.put("/api/admin/users/{user_id}/role")
async def update_user_role(user_id: int, role: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a user's role (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if role not in ('user', 'admin'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    
    # For now, we'll just return success since we don't have a role field in the database yet
    return {"message": f"Role for {user.username} would be updated to {role}"}
