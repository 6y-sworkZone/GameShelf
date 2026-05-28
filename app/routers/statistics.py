from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/statistics", tags=["开销统计"])


@router.get("/spending/platform")
def get_spending_by_platform(db: Session = Depends(get_db)):
    results = db.query(
        models.Game.platform,
        func.sum(models.Game.purchase_price).label("total"),
        func.count(models.Game.id).label("count")
    ).filter(
        models.Game.purchase_price.isnot(None)
    ).group_by(models.Game.platform).all()
    
    return {
        "by_platform": [
            {
                "platform": r.platform,
                "total_spent": round(r.total, 2),
                "game_count": r.count,
                "avg_price": round(r.total / r.count, 2)
            }
            for r in results
        ]
    }


@router.get("/spending/yearly")
def get_spending_by_year(db: Session = Depends(get_db)):
    from sqlalchemy import extract
    
    results = db.query(
        extract('year', models.Game.purchase_date).label('year'),
        func.sum(models.Game.purchase_price).label("total"),
        func.count(models.Game.id).label("count")
    ).filter(
        models.Game.purchase_price.isnot(None),
        models.Game.purchase_date.isnot(None)
    ).group_by('year').order_by('year').all()
    
    return {
        "by_year": [
            {
                "year": int(r.year),
                "total_spent": round(r.total, 2),
                "game_count": r.count,
                "avg_price": round(r.total / r.count, 2)
            }
            for r in results
        ]
    }


@router.get("/spending/monthly/{year}")
def get_spending_by_month(year: int, db: Session = Depends(get_db)):
    from sqlalchemy import extract
    
    results = db.query(
        extract('month', models.Game.purchase_date).label('month'),
        func.sum(models.Game.purchase_price).label("total"),
        func.count(models.Game.id).label("count")
    ).filter(
        models.Game.purchase_price.isnot(None),
        models.Game.purchase_date.isnot(None),
        extract('year', models.Game.purchase_date) == year
    ).group_by('month').order_by('month').all()
    
    monthly_data = {int(r.month): r for r in results}
    
    return {
        "year": year,
        "by_month": [
            {
                "month": month,
                "total_spent": round(monthly_data[month].total, 2) if month in monthly_data else 0,
                "game_count": monthly_data[month].count if month in monthly_data else 0
            }
            for month in range(1, 13)
        ]
    }


@router.get("/discount-savings")
def get_discount_savings(db: Session = Depends(get_db)):
    games = db.query(models.Game).filter(
        models.Game.purchase_price.isnot(None),
        models.Game.discount_rate.isnot(None)
    ).all()
    
    total_savings = 0
    for game in games:
        if game.discount_rate > 0:
            original_price = game.purchase_price / (1 - game.discount_rate / 100)
            total_savings += (original_price - game.purchase_price)
    
    return {
        "total_savings": round(total_savings, 2),
        "game_count": len(games),
        "message": f"通过折扣，你已经省下了 ¥{round(total_savings, 2)}！相当于白嫖了好几款游戏！"
    }


@router.get("/cost-effectiveness")
def get_cost_effectiveness(db: Session = Depends(get_db)):
    games = db.query(models.Game).all()
    
    results = []
    for game in games:
        if game.purchase_price:
            total_minutes = sum(pr.duration_minutes for pr in game.play_records)
            total_hours = total_minutes / 60
            if total_hours > 0:
                cost_per_hour = game.purchase_price / total_hours
                results.append({
                    "game_id": game.id,
                    "game_name": game.name,
                    "purchase_price": game.purchase_price,
                    "total_hours": round(total_hours, 2),
                    "cost_per_hour": round(cost_per_hour, 2),
                    "rating": "超划算" if cost_per_hour < 5 else "值回票价" if cost_per_hour < 20 else "有点贵"
                })
    
    results.sort(key=lambda x: x["cost_per_hour"])
    
    return {
        "best_value": results[:5],
        "worst_value": results[-5:],
        "all_games": results
    }


@router.get("/graveyard-waste")
def get_graveyard_waste(db: Session = Depends(get_db)):
    graveyard_games = db.query(models.Game).filter(
        models.Game.status == "未开始",
        models.Game.purchase_price.isnot(None)
    ).all()
    
    total_wasted = sum(g.purchase_price for g in graveyard_games)
    
    return {
        "graveyard_count": len(graveyard_games),
        "total_wasted": round(total_wasted, 2),
        "games": [
            {
                "id": g.id,
                "name": g.name,
                "purchase_price": g.purchase_price,
                "purchase_date": g.purchase_date
            }
            for g in graveyard_games
        ],
        "message": f"买了没玩的游戏总价值 ¥{round(total_wasted, 2)}，别再剁手了！"
    }


@router.post("/budget", response_model=schemas.Budget)
def set_budget(budget: schemas.BudgetCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Budget).filter(models.Budget.year == budget.year).first()
    if existing:
        existing.amount = budget.amount
        db.commit()
        db.refresh(existing)
        return existing
    
    db_budget = models.Budget(**budget.model_dump())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


@router.get("/budget/{year}")
def get_budget_status(year: int, db: Session = Depends(get_db)):
    from sqlalchemy import extract
    
    budget = db.query(models.Budget).filter(models.Budget.year == year).first()
    
    spent = db.query(
        func.sum(models.Game.purchase_price)
    ).filter(
        models.Game.purchase_price.isnot(None),
        models.Game.purchase_date.isnot(None),
        extract('year', models.Game.purchase_date) == year
    ).scalar() or 0
    
    remaining = (budget.amount if budget else 0) - spent
    
    return {
        "year": year,
        "budget": budget.amount if budget else 0,
        "spent": round(spent, 2),
        "remaining": round(remaining, 2),
        "is_over_budget": spent > (budget.amount if budget else 0),
        "usage_percent": round((spent / budget.amount * 100), 2) if budget and budget.amount > 0 else 0
    }
