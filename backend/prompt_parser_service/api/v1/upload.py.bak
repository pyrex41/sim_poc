from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Optional
import base64
from ....auth import verify_auth
from ....database import save_creative_brief  # For direct save if needed

router = APIRouter(prefix="/creative", tags=["creative"])

@router.post("/upload")
async def upload_media(
    brief_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    base64_data: Optional[str] = Form(None),
    is_image: bool = Form(True),
    current_user = Depends(verify_auth)
):
    if not file and not base64_data:
        raise HTTPException(400, "Provide file or base64_data")
    
    data = None
    if file:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(413, "File too large")
        data = content
    elif base64_data:
        try:
            data = base64.b64decode(base64_data)
            if len(data) > 10 * 1024 * 1024:
                raise HTTPException(413, "Base64 data too large")
        except:
            raise HTTPException(400, "Invalid base64")
    
    if not data:
        raise HTTPException(400, "No data received")
    
    # Save to brief BLOB (assume brief exists)
    from database import get_creative_brief, update_brief
    brief = get_creative_brief(brief_id, current_user["id"])
    if not brief:
        raise HTTPException(404, "Brief not found")
    
    if is_image:
        update_brief(brief_id, current_user["id"], image_data=data)
    else:
        update_brief(brief_id, current_user["id"], video_data=data)
    
    return {"brief_id": brief_id, "size": len(data), "type": "image" if is_image else "video"}