from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/games", tags=["游戏库"])


@router.post("/", response_model=schemas.Game)
def create_game(game: schemas.GameCreate, db: Session = Depends(get_db)):
    db_game = models.Game(**game.model_dump())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


@router.get("/", response_model=List[schemas.Game])
def get_games(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    platform: Optional[str] = None,
    tags: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Game)
    if name:
        query = query.filter(models.Game.name.contains(name))
    if platform:
        query = query.filter(models.Game.platform == platform)
    if tags:
        query = query.filter(models.Game.tags.contains(tags))
    if status:
        query = query.filter(models.Game.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/graveyard", response_model=List[schemas.Game])
def get_graveyard(db: Session = Depends(get_db)):
    return db.query(models.Game).filter(
        models.Game.status == "未开始"
    ).all()


@router.get("/{game_id}", response_model=schemas.GameDetail)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    total_play_time = sum(pr.duration_minutes for pr in game.play_records)
    
    cost_per_hour = None
    if game.purchase_price and total_play_time > 0:
        cost_per_hour = game.purchase_price / (total_play_time / 60)
    
    return {
        **game.__dict__,
        "ratings": game.ratings,
        "play_records": game.play_records,
        "achievements": game.achievements,
        "speedruns": game.speedruns,
        "screenshots": game.screenshots,
        "total_play_time": total_play_time,
        "cost_per_hour": round(cost_per_hour, 2) if cost_per_hour else None
    }


@router.put("/{game_id}", response_model=schemas.Game)
def update_game(game_id: int, game_update: schemas.GameUpdate, db: Session = Depends(get_db)):
    db_game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not db_game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    update_data = game_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_game, key, value)
    
    db.commit()
    db.refresh(db_game)
    return db_game


@router.delete("/{game_id}")
def delete_game(game_id: int, db: Session = Depends(get_db)):
    db_game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not db_game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    db.delete(db_game)
    db.commit()
    return {"message": "游戏已删除"}


@router.post("/{game_id}/ratings", response_model=schemas.Rating)
def create_rating(game_id: int, rating: schemas.RatingCreate, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    graphics = rating.graphics or 0
    gameplay = rating.gameplay or 0
    story = rating.story or 0
    music = rating.music or 0
    
    valid_scores = [s for s in [graphics, gameplay, story, music] if s > 0]
    overall = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    db_rating = models.Rating(
        game_id=game_id,
        graphics=graphics,
        gameplay=gameplay,
        story=story,
        music=music,
        overall=overall,
        comment=rating.comment
    )
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating
