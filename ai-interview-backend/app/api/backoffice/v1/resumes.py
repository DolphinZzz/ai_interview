import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.backoffice.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.models.resume import Resume
from app.models.user import User
from app.schemas.response import ApiResponse
from app.core.config import settings
from app.services.client.resume_service import sanitize_resume_filename

router = APIRouter()


def _json_value(value: Optional[str]):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _user_data(user: Optional[User]) -> Optional[dict]:
    if not user:
        return None
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@router.get("")
async def list_resumes(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """分页查看用户上传的简历。"""
    query = select(Resume, User).join(User, Resume.user_id == User.id)
    count_query = select(func.count()).select_from(Resume).join(User, Resume.user_id == User.id)

    if keyword:
        keyword_filter = (
            User.email.ilike(f"%{keyword}%")
            | User.first_name.ilike(f"%{keyword}%")
            | User.last_name.ilike(f"%{keyword}%")
        )
        query = query.where(keyword_filter)
        count_query = count_query.where(keyword_filter)
    if status:
        query = query.where(Resume.status == status)
        count_query = count_query.where(Resume.status == status)

    total = await db.scalar(count_query)
    result = await db.execute(
        query.order_by(Resume.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    rows = result.all()
    return ApiResponse.success(data={
        "items": [
            {
                "id": resume.id,
                "user_id": user.id,
                "user_email": user.email,
                "user_name": " ".join(filter(None, [user.first_name, user.last_name])) or None,
                "file_name": resume.file_name,
                "target_position": resume.target_position,
                "status": resume.status,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
            }
            for resume, user in rows
        ],
        "total": total or 0,
        "page": page,
        "per_page": per_page,
    })


@router.get("/{resume_id}")
async def get_resume_detail(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """查看简历原始 PDF 文本及 AI 解析结果。"""
    resume = await db.get(Resume, resume_id)
    if not resume:
        return ApiResponse.failed(message="简历不存在", body_code=404, http_code=404)

    user = await db.get(User, resume.user_id)
    return ApiResponse.success(data={
        "id": resume.id,
        "user": _user_data(user),
        "file_name": resume.file_name,
        "target_position": resume.target_position,
        "status": resume.status,
        "extracted_text": resume.extracted_text,
        "parsed_content": _json_value(resume.parsed_content),
        "analysis": _json_value(resume.analysis),
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
    })


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """下载管理员已授权查看的简历 PDF。"""
    resume = await db.get(Resume, resume_id)
    if not resume or not resume.file_url:
        return ApiResponse.failed(message="简历文件不存在", body_code=404, http_code=404)

    resume_root = (Path(settings.UPLOAD_ROOT) / "resumes").resolve()
    file_path = Path(resume.file_url).resolve()
    try:
        file_path.relative_to(resume_root)
    except ValueError:
        return ApiResponse.failed(message="简历文件不存在", body_code=404, http_code=404)
    if not file_path.is_file():
        return ApiResponse.failed(message="简历文件不存在", body_code=404, http_code=404)

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=sanitize_resume_filename(resume.file_name or file_path.name),
    )
