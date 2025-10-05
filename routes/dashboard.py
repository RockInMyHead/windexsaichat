"""
API endpoints для личного кабинета и аналитики сайтов
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import Deployment, SiteAnalytics, User, get_db
from routes.auth import get_current_user

router = APIRouter()


@router.get("/api/dashboard/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получить общую статистику пользователя"""

    # Получаем все деплои пользователя
    deployments = (
        db.query(Deployment)
        .filter(Deployment.user_id == current_user.id, Deployment.is_active == True)
        .all()
    )

    # Подсчитываем общую статистику
    total_deployments = len(deployments)
    total_views = 0
    total_visitors = 0
    total_errors = 0

    for deployment in deployments:
        analytics = (
            db.query(SiteAnalytics)
            .filter(SiteAnalytics.deployment_id == deployment.id)
            .first()
        )

        if analytics:
            total_views += analytics.page_views
            total_visitors += analytics.unique_visitors
            total_errors += analytics.error_count

    # Статистика за последние 7 дней
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_deployments = (
        db.query(Deployment)
        .filter(
            Deployment.user_id == current_user.id, Deployment.created_at >= week_ago
        )
        .count()
    )

    return {
        "total_deployments": total_deployments,
        "total_views": total_views,
        "total_visitors": total_visitors,
        "total_errors": total_errors,
        "recent_deployments": recent_deployments,
        "success_rate": round(
            (total_views - total_errors) / max(total_views, 1) * 100, 1
        ),
    }


@router.get("/api/dashboard/deployments")
async def get_user_deployments(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получить все деплои пользователя с аналитикой"""

    deployments = (
        db.query(Deployment)
        .filter(Deployment.user_id == current_user.id)
        .order_by(Deployment.created_at.desc())
        .all()
    )

    deployment_list = []
    for deployment in deployments:
        analytics = (
            db.query(SiteAnalytics)
            .filter(SiteAnalytics.deployment_id == deployment.id)
            .first()
        )

        # Если аналитики нет, создаем базовую запись
        if not analytics:
            analytics = SiteAnalytics(
                deployment_id=deployment.id,
                page_views=0,
                unique_visitors=0,
                avg_load_time=0.0,
                bounce_rate=0.0,
                session_duration=0.0,
                error_count=0,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
            )
            db.add(analytics)
            db.commit()
            db.refresh(analytics)

        deployment_list.append(
            {
                "id": deployment.id,
                "title": deployment.title,
                "description": deployment.description,
                "deploy_url": deployment.deploy_url,
                "is_active": deployment.is_active,
                "created_at": deployment.created_at.isoformat(),
                "updated_at": deployment.updated_at.isoformat(),
                "analytics": {
                    "page_views": analytics.page_views,
                    "unique_visitors": analytics.unique_visitors,
                    "avg_load_time": analytics.avg_load_time,
                    "bounce_rate": analytics.bounce_rate,
                    "session_duration": analytics.session_duration,
                    "error_count": analytics.error_count,
                    "total_requests": analytics.total_requests,
                    "successful_requests": analytics.successful_requests,
                    "failed_requests": analytics.failed_requests,
                    "last_error": analytics.last_error,
                    "last_error_time": (
                        analytics.last_error_time.isoformat()
                        if analytics.last_error_time
                        else None
                    ),
                },
            }
        )

    return {"deployments": deployment_list}


@router.get("/api/dashboard/deployments/{deployment_id}/analytics")
async def get_deployment_analytics(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить детальную аналитику конкретного деплоя"""

    # Проверяем, что деплой принадлежит пользователю
    deployment = (
        db.query(Deployment)
        .filter(Deployment.id == deployment_id, Deployment.user_id == current_user.id)
        .first()
    )

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found"
        )

    analytics = (
        db.query(SiteAnalytics)
        .filter(SiteAnalytics.deployment_id == deployment_id)
        .first()
    )

    if not analytics:
        # Создаем базовую аналитику
        analytics = SiteAnalytics(
            deployment_id=deployment_id,
            page_views=0,
            unique_visitors=0,
            avg_load_time=0.0,
            bounce_rate=0.0,
            session_duration=0.0,
            error_count=0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
        )
        db.add(analytics)
        db.commit()
        db.refresh(analytics)

    # Генерируем демо-данные для графика (в реальном приложении это будет реальная аналитика)
    days = 7
    chart_data = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - 1 - i)
        chart_data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "views": random.randint(10, 100),
                "visitors": random.randint(5, 50),
                "errors": random.randint(0, 5),
            }
        )

    return {
        "deployment": {
            "id": deployment.id,
            "title": deployment.title,
            "deploy_url": deployment.deploy_url,
            "created_at": deployment.created_at.isoformat(),
        },
        "analytics": {
            "page_views": analytics.page_views,
            "unique_visitors": analytics.unique_visitors,
            "avg_load_time": analytics.avg_load_time,
            "bounce_rate": analytics.bounce_rate,
            "session_duration": analytics.session_duration,
            "error_count": analytics.error_count,
            "total_requests": analytics.total_requests,
            "successful_requests": analytics.successful_requests,
            "failed_requests": analytics.failed_requests,
            "last_error": analytics.last_error,
            "last_error_time": (
                analytics.last_error_time.isoformat()
                if analytics.last_error_time
                else None
            ),
        },
        "chart_data": chart_data,
    }


@router.post("/api/dashboard/deployments/{deployment_id}/track")
async def track_deployment_visit(deployment_id: int, db: Session = Depends(get_db)):
    """Отслеживание посещения сайта (вызывается с деплоя)"""

    deployment = (
        db.query(Deployment)
        .filter(Deployment.id == deployment_id, Deployment.is_active == True)
        .first()
    )

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found"
        )

    analytics = (
        db.query(SiteAnalytics)
        .filter(SiteAnalytics.deployment_id == deployment_id)
        .first()
    )

    if not analytics:
        analytics = SiteAnalytics(
            deployment_id=deployment_id,
            page_views=0,
            unique_visitors=0,
            avg_load_time=0.0,
            bounce_rate=0.0,
            session_duration=0.0,
            error_count=0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
        )
        db.add(analytics)

    # Обновляем статистику
    analytics.page_views += 1
    analytics.unique_visitors += (
        1  # В реальном приложении нужно отслеживать уникальность
    )
    analytics.total_requests += 1
    analytics.successful_requests += 1
    analytics.avg_load_time = round(random.uniform(0.5, 3.0), 2)  # Демо-данные
    analytics.session_duration = round(random.uniform(30, 300), 1)  # Демо-данные
    analytics.bounce_rate = round(random.uniform(20, 80), 1)  # Демо-данные

    db.commit()
    db.refresh(analytics)

    return {"status": "tracked", "views": analytics.page_views}


@router.delete("/api/dashboard/deployments/{deployment_id}")
async def delete_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удалить деплой и его аналитику"""

    deployment = (
        db.query(Deployment)
        .filter(Deployment.id == deployment_id, Deployment.user_id == current_user.id)
        .first()
    )

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found"
        )

    # Удаляем аналитику
    analytics = (
        db.query(SiteAnalytics)
        .filter(SiteAnalytics.deployment_id == deployment_id)
        .first()
    )

    if analytics:
        db.delete(analytics)

    # Удаляем деплой
    db.delete(deployment)
    db.commit()

    return {"status": "deleted"}


@router.get("/api/dashboard/page")
async def get_dashboard_page():
    """Сервировать страницу личного кабинета"""
    from fastapi.responses import FileResponse

    return FileResponse("static/dashboard.html")
