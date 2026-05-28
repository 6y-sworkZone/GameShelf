from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/friends", tags=["好友与推荐"])


@router.post("/", response_model=schemas.Friend)
def create_friend(friend: schemas.FriendCreate, db: Session = Depends(get_db)):
    db_friend = models.Friend(**friend.model_dump())
    db.add(db_friend)
    db.commit()
    db.refresh(db_friend)
    return db_friend


@router.get("/", response_model=List[schemas.Friend])
def get_friends(db: Session = Depends(get_db)):
    return db.query(models.Friend).all()


@router.get("/{friend_id}", response_model=schemas.Friend)
def get_friend(friend_id: int, db: Session = Depends(get_db)):
    friend = db.query(models.Friend).filter(models.Friend.id == friend_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="好友不存在")
    return friend


@router.put("/{friend_id}", response_model=schemas.Friend)
def update_friend(
    friend_id: int,
    friend_update: schemas.FriendCreate,
    db: Session = Depends(get_db)
):
    db_friend = db.query(models.Friend).filter(models.Friend.id == friend_id).first()
    if not db_friend:
        raise HTTPException(status_code=404, detail="好友不存在")
    
    update_data = friend_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_friend, key, value)
    
    db.commit()
    db.refresh(db_friend)
    return db_friend


@router.delete("/{friend_id}")
def delete_friend(friend_id: int, db: Session = Depends(get_db)):
    db_friend = db.query(models.Friend).filter(models.Friend.id == friend_id).first()
    if not db_friend:
        raise HTTPException(status_code=404, detail="好友不存在")
    db.delete(db_friend)
    db.commit()
    return {"message": "好友已删除"}


@router.post("/playing", response_model=schemas.FriendPlaying)
def add_friend_playing(playing: schemas.FriendPlayingCreate, db: Session = Depends(get_db)):
    friend = db.query(models.Friend).filter(models.Friend.id == playing.friend_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="好友不存在")
    
    db_playing = models.FriendPlaying(**playing.model_dump())
    db.add(db_playing)
    db.commit()
    db.refresh(db_playing)
    return db_playing


@router.get("/playing/all")
def get_friends_playing(db: Session = Depends(get_db)):
    results = db.query(models.FriendPlaying).all()
    
    return [
        {
            "id": r.id,
            "friend_name": r.friend.name if r.friend else None,
            "game_name": r.game_name,
            "platform": r.platform,
            "status": r.status,
            "last_played": r.last_played
        }
        for r in results
    ]


@router.get("/recommendations")
def get_game_recommendations(db: Session = Depends(get_db)):
    high_rated_games = db.query(models.Game).join(models.Rating).filter(
        models.Rating.overall >= 8,
        models.Game.tags.isnot(None)
    ).all()
    
    tags = set()
    for game in high_rated_games:
        if game.tags:
            tags.update([t.strip() for t in game.tags.split(",")])
    
    unplayed_games = db.query(models.Game).filter(
        models.Game.status == "未开始",
        models.Game.tags.isnot(None)
    ).all()
    
    recommendations = []
    for game in unplayed_games:
        game_tags = set([t.strip() for t in game.tags.split(",")]) if game.tags else set()
        match_count = len(tags & game_tags)
        if match_count > 0:
            matched_high_rated = [
                g.name for g in high_rated_games
                if g.tags and any(t in g.tags for t in game_tags)
            ]
            
            if matched_high_rated:
                ref_game = matched_high_rated[0]
                recommendations.append({
                    "game_id": game.id,
                    "game_name": game.name,
                    "platform": game.platform,
                    "cover_image": game.cover_image,
                    "matched_tags": list(tags & game_tags),
                    "match_count": match_count,
                    "recommendation_text": f"你都给《{ref_game}》打了高分，库存里还有个《{game.name}》还没拆封呢！"
                })
    
    recommendations.sort(key=lambda x: x["match_count"], reverse=True)
    
    return {
        "high_rated_tags": list(tags),
        "recommendations": recommendations[:10]
    }


@router.get("/leaderboard/playtime")
def get_playtime_leaderboard(db: Session = Depends(get_db)):
    games = db.query(models.Game).all()
    
    game_playtimes = []
    for game in games:
        total_minutes = sum(pr.duration_minutes for pr in game.play_records)
        if total_minutes > 0:
            game_playtimes.append({
                "game_id": game.id,
                "game_name": game.name,
                "platform": game.platform,
                "total_minutes": total_minutes,
                "total_hours": round(total_minutes / 60, 2)
            })
    
    game_playtimes.sort(key=lambda x: x["total_minutes"], reverse=True)
    
    return {
        "leaderboard": game_playtimes[:20]
    }
