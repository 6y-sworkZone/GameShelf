from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import date

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/annual", tags=["年度回顾"])


@router.get("/report/{year}")
def get_annual_report(year: int, db: Session = Depends(get_db)):
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)
    
    games_played = db.query(models.PlayRecord).filter(
        models.PlayRecord.date >= start_date,
        models.PlayRecord.date < end_date
    ).with_entities(models.PlayRecord.game_id).distinct().count()
    
    games_purchased = db.query(models.Game).filter(
        models.Game.purchase_date >= start_date,
        models.Game.purchase_date < end_date
    ).count()
    
    completed_game_ids = db.query(models.PlayRecord.game_id).filter(
        models.PlayRecord.date >= start_date,
        models.PlayRecord.date < end_date
    ).distinct().subquery()
    
    games_completed = db.query(models.Game).filter(
        models.Game.id.in_(completed_game_ids),
        models.Game.status.in_(["主线通关", "全成就"])
    ).count()
    
    total_playtime = db.query(func.sum(models.PlayRecord.duration_minutes)).filter(
        models.PlayRecord.date >= start_date,
        models.PlayRecord.date < end_date
    ).scalar() or 0
    
    total_spent = db.query(func.sum(models.Game.purchase_price)).filter(
        models.Game.purchase_date >= start_date,
        models.Game.purchase_date < end_date
    ).scalar() or 0
    
    platform_counts = db.query(
        models.Game.platform,
        func.count(models.Game.id)
    ).filter(
        models.Game.purchase_date >= start_date,
        models.Game.purchase_date < end_date
    ).group_by(models.Game.platform).all()
    
    top_rated = db.query(models.Game).join(models.Rating).filter(
        models.Rating.created_at >= start_date,
        models.Rating.created_at < end_date
    ).order_by(models.Rating.overall.desc()).limit(5).all()
    
    platform_playtime = {}
    records = db.query(models.PlayRecord).filter(
        models.PlayRecord.date >= start_date,
        models.PlayRecord.date < end_date
    ).all()
    
    for r in records:
        platform = r.game.platform if r.game else "未知"
        platform_playtime[platform] = platform_playtime.get(platform, 0) + r.duration_minutes
    
    return {
        "year": year,
        "summary": {
            "games_played": games_played,
            "games_purchased": games_purchased,
            "games_completed": games_completed,
            "total_playtime_minutes": total_playtime,
            "total_playtime_hours": round(total_playtime / 60, 2),
            "total_spent": round(total_spent, 2),
            "avg_daily_playtime": round(total_playtime / 365, 2) if total_playtime > 0 else 0
        },
        "platform_distribution": [
            {"platform": p, "count": c} for p, c in platform_counts
        ],
        "platform_playtime": [
            {"platform": p, "minutes": t, "hours": round(t / 60, 2)}
            for p, t in sorted(platform_playtime.items(), key=lambda x: x[1], reverse=True)
        ],
        "top_rated_games": [
            {
                "id": g.id,
                "name": g.name,
                "platform": g.platform,
                "rating": g.ratings[0].overall if g.ratings else 0
            }
            for g in top_rated
        ]
    }


@router.get("/play-trend/{year}")
def get_play_trend(year: int, db: Session = Depends(get_db)):
    monthly_data = {}
    
    for month in range(1, 13):
        monthly_data[month] = {
            "total_minutes": 0,
            "game_count": 0
        }
    
    records = db.query(models.PlayRecord).filter(
        extract('year', models.PlayRecord.date) == year
    ).all()
    
    for r in records:
        month = r.date.month
        monthly_data[month]["total_minutes"] += r.duration_minutes
        monthly_data[month]["game_count"] += 1
    
    return {
        "year": year,
        "monthly_trend": [
            {
                "month": month,
                "total_minutes": monthly_data[month]["total_minutes"],
                "total_hours": round(monthly_data[month]["total_minutes"] / 60, 2),
                "game_count": monthly_data[month]["game_count"]
            }
            for month in range(1, 13)
        ]
    }


@router.get("/platform-shift/{year}")
def get_platform_shift(year: int, db: Session = Depends(get_db)):
    first_half_playtime = {}
    second_half_playtime = {}
    
    first_half = db.query(models.PlayRecord).filter(
        extract('year', models.PlayRecord.date) == year,
        extract('month', models.PlayRecord.date) <= 6
    ).all()
    
    second_half = db.query(models.PlayRecord).filter(
        extract('year', models.PlayRecord.date) == year,
        extract('month', models.PlayRecord.date) > 6
    ).all()
    
    for r in first_half:
        platform = r.game.platform if r.game else "未知"
        first_half_playtime[platform] = first_half_playtime.get(platform, 0) + r.duration_minutes
    
    for r in second_half:
        platform = r.game.platform if r.game else "未知"
        second_half_playtime[platform] = second_half_playtime.get(platform, 0) + r.duration_minutes
    
    all_platforms = set(list(first_half_playtime.keys()) + list(second_half_playtime.keys()))
    
    return {
        "year": year,
        "platforms": [
            {
                "platform": p,
                "first_half_minutes": first_half_playtime.get(p, 0),
                "first_half_hours": round(first_half_playtime.get(p, 0) / 60, 2),
                "second_half_minutes": second_half_playtime.get(p, 0),
                "second_half_hours": round(second_half_playtime.get(p, 0) / 60, 2)
            }
            for p in all_platforms
        ]
    }


@router.get("/most-addicted/{year}")
def get_most_addicted_month(year: int, db: Session = Depends(get_db)):
    monthly_playtime = {}
    
    records = db.query(models.PlayRecord).filter(
        extract('year', models.PlayRecord.date) == year
    ).all()
    
    for r in records:
        month = r.date.month
        monthly_playtime[month] = monthly_playtime.get(month, 0) + r.duration_minutes
    
    if not monthly_playtime:
        return {"message": "该年度暂无游玩数据"}
    
    most_addicted_month = max(monthly_playtime.items(), key=lambda x: x[1])
    
    return {
        "year": year,
        "most_addicted_month": most_addicted_month[0],
        "total_minutes": most_addicted_month[1],
        "total_hours": round(most_addicted_month[1] / 60, 2),
        "avg_daily_hours": round(most_addicted_month[1] / 30 / 60, 2)
    }


@router.post("/plan", response_model=schemas.AnnualPlan)
def create_annual_plan(plan: schemas.AnnualPlanCreate, db: Session = Depends(get_db)):
    existing = db.query(models.AnnualPlan).filter(models.AnnualPlan.year == plan.year).first()
    if existing:
        update_data = plan.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    db_plan = models.AnnualPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.get("/plan/{year}")
def get_annual_plan(year: int, db: Session = Depends(get_db)):
    plan = db.query(models.AnnualPlan).filter(models.AnnualPlan.year == year).first()
    if not plan:
        raise HTTPException(status_code=404, detail="年度计划不存在")
    return plan
