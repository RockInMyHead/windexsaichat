from fastapi import APIRouter, Depends, HTTPException, status

from routes.auth import get_current_user, User, users_db

router = APIRouter()

@router.get("/api/admin/users")
async def list_users(current_user: User = Depends(get_current_user)):
    """List all registered users (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return {"users": [u for u in users_db.values()]}  

@router.put("/api/admin/users/{username}/role")
async def update_user_role(username: str, role: str, current_user: User = Depends(get_current_user)):
    """Update a user's role (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if username not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if role not in ('user', 'admin'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    users_db[username]['role'] = role
    return {"message": f"Role for {username} updated to {role}"}
