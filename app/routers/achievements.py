from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/achievements", tags=["成就系统"])


@router.post("/", response_model=schemas.Achievement)
def create_achievement(achievement: schemas.AchievementCreate, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == achievement.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    if achievement.is_pinned:
        db.query(models.Achievement).filter(
            models.Achievement.is_pinned == True
        ).update({"is_pinned": False})
    
    db_achievement = models.Achievement(**achievement.model_dump())
    db.add(db_achievement)
    db.commit()
    db.refresh(db_achievement)
    return db_achievement


@router.get("/", response_model=List[schemas.Achievement])
def get_achievements(
    game_id: Optional[int] = None,
    rarity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Achievement)
    if game_id:
        query = query.filter(models.Achievement.game_id == game_id)
    if rarity:
        query = query.filter(models.Achievement.rarity == rarity)
    return query.order_by(models.Achievement.unlocked_date.desc()).all()


@router.get("/pinned")
def get_pinned_achievement(db: Session = Depends(get_db)):
    achievement = db.query(models.Achievement).filter(
        models.Achievement.is_pinned == True
    ).first()
    if not achievement:
        return {"message": "没有置顶的成就"}
    return achievement


@router.get("/games/{game_id}/completion")
def get_game_achievement_completion(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    unlocked = db.query(models.Achievement).filter(
        models.Achievement.game_id == game_id,
        models.Achievement.unlocked_date.isnot(None)
    ).count()
    
    total = db.query(models.Achievement).filter(
        models.Achievement.game_id == game_id
    ).count()
    
    completion_percent = (unlocked / total * 100) if total > 0 else 0
    
    return {
        "game_id": game_id,
        "game_name": game.name,
        "unlocked": unlocked,
        "total": total,
        "completion_percent": round(completion_percent, 2),
        "is_platinum": total > 0 and unlocked == total
    }


@router.get("/rare")
def get_rare_achievements(db: Session = Depends(get_db)):
    rare_achievements = db.query(models.Achievement).filter(
        models.Achievement.rarity.in_(["史诗", "传奇"])
    ).all()
    
    return {
        "rare_count": len(rare_achievements),
        "achievements": rare_achievements
    }


@router.get("/platinum-games")
def get_platinum_games(db: Session = Depends(get_db)):
    games = db.query(models.Game).filter(models.Game.status == "全成就").all()
    
    return {
        "platinum_count": len(games),
        "games": [
            {
                "id": game.id,
                "name": game.name,
                "platform": game.platform,
                "cover_image": game.cover_image
            }
            for game in games
        ]
    }


@router.put("/{achievement_id}/pin")
def pin_achievement(achievement_id: int, db: Session = Depends(get_db)):
    achievement = db.query(models.Achievement).filter(
        models.Achievement.id == achievement_id
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="成就不存在")
    
    db.query(models.Achievement).filter(
        models.Achievement.is_pinned == True
    ).update({"is_pinned": False})
    
    achievement.is_pinned = True
    db.commit()
    return {"message": "成就已置顶"}


@router.delete("/{achievement_id}")
def delete_achievement(achievement_id: int, db: Session = Depends(get_db)):
    achievement = db.query(models.Achievement).filter(
        models.Achievement.id == achievement_id
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="成就不存在")
    db.delete(achievement)
    db.commit()
    return {"message": "成就已删除"}
