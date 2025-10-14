"""
Mock Cloud API endpoints for testing the cloud integration
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from datetime import datetime

router = APIRouter()

# Mock data
mock_files = [
    {
        "id": "file_1",
        "name": "document.pdf",
        "type": "file",
        "size": 1024000,
        "path": "/document.pdf",
        "createdAt": "2024-01-15T10:30:00Z",
        "modifiedAt": "2024-01-15T10:30:00Z",
        "parentId": None
    },
    {
        "id": "folder_1",
        "name": "Documents",
        "type": "folder",
        "path": "/Documents",
        "createdAt": "2024-01-15T09:00:00Z",
        "modifiedAt": "2024-01-15T09:00:00Z"
    },
    {
        "id": "file_2",
        "name": "image.jpg",
        "type": "file",
        "size": 512000,
        "path": "/Documents/image.jpg",
        "createdAt": "2024-01-15T11:00:00Z",
        "modifiedAt": "2024-01-15T11:00:00Z",
        "parentId": "folder_1"
    }
]

@router.get("/api/files")
async def get_files(path: str = "/"):
    """Get list of files and folders"""
    if path == "/":
        return [f for f in mock_files if f["path"] == "/" or f["path"].startswith("/") and f["path"].count("/") == 1]
    else:
        return [f for f in mock_files if f["path"].startswith(path)]

@router.post("/api/upload")
async def upload_file():
    """Mock file upload"""
    return {
        "success": True,
        "file": {
            "id": "file_new",
            "name": "uploaded_file.pdf",
            "type": "file",
            "size": 2048000,
            "path": "/uploaded_file.pdf",
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "modifiedAt": datetime.utcnow().isoformat() + "Z"
        }
    }

@router.get("/api/files/{file_id}")
async def get_file_info(file_id: str):
    """Get file information"""
    file = next((f for f in mock_files if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.get("/api/files/{file_id}/download")
async def download_file(file_id: str):
    """Mock file download"""
    file = next((f for f in mock_files if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return a mock file content
    return JSONResponse(
        content={"message": f"Mock download for {file['name']}"},
        headers={"Content-Disposition": f"attachment; filename={file['name']}"}
    )

@router.get("/api/files/{file_id}/view")
async def view_file(file_id: str):
    """Mock file view"""
    file = next((f for f in mock_files if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return JSONResponse(
        content={"message": f"Mock view for {file['name']}", "file": file}
    )

@router.post("/api/folders")
async def create_folder():
    """Mock folder creation"""
    return {
        "success": True,
        "folder": {
            "id": "folder_new",
            "name": "New folder",
            "type": "folder",
            "path": "/New folder",
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "modifiedAt": datetime.utcnow().isoformat() + "Z"
        }
    }

@router.put("/api/files/{file_id}")
async def rename_file(file_id: str):
    """Mock file rename"""
    file = next((f for f in mock_files if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "success": True,
        "file": file
    }

@router.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """Mock file deletion"""
    file = next((f for f in mock_files if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"success": True, "message": f"File {file['name']} deleted"}

@router.get("/api/search")
async def search_files(q: str, type: Optional[str] = None, path: Optional[str] = None):
    """Mock file search"""
    results = []
    for file in mock_files:
        if q.lower() in file["name"].lower():
            if type and file["type"] != type:
                continue
            if path and not file["path"].startswith(path):
                continue
            results.append(file)
    
    return results
