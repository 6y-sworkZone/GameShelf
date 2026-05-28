from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import os

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/progress", tags=["进度追踪"])

UPLOAD_DIR = "uploads/screenshots"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/play-records", response_model=schemas.PlayRecord)
def create_play_record(record: schemas.PlayRecordCreate, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == record.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    db_record = models.PlayRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/play-records", response_model=List[schemas.PlayRecord])
def get_play_records(
    game_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.PlayRecord)
    if game_id:
        query = query.filter(models.PlayRecord.game_id == game_id)
    if start_date:
        query = query.filter(models.PlayRecord.date >= start_date)
    if end_date:
        query = query.filter(models.PlayRecord.date <= end_date)
    return query.order_by(models.PlayRecord.date.desc()).all()


@router.get("/calendar")
def get_play_calendar(year: int, month: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.PlayRecord).filter(
        models.PlayRecord.date >= date(year, month or 1, 1)
    )
    if month:
        next_month = month + 1 if month < 12 else 12
        query = query.filter(models.PlayRecord.date < date(year, next_month, 1))
    else:
        query = query.filter(models.PlayRecord.date < date(year + 1, 1, 1))
    
    records = query.all()
    
    calendar = {}
    for record in records:
        day_key = record.date.isoformat()
        if day_key not in calendar:
            calendar[day_key] = {"total_minutes": 0, "games": []}
        calendar[day_key]["total_minutes"] += record.duration_minutes
        calendar[day_key]["games"].append({
            "game_id": record.game_id,
            "game_name": record.game.name,
            "duration_minutes": record.duration_minutes
        })
    
    return calendar


@router.put("/games/{game_id}/status")
def update_game_status(game_id: int, status: str, db: Session = Depends(get_db)):
    valid_statuses = ["未开始", "游玩中", "主线通关", "全成就", "暂停", "弃坑"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效的状态，可选值: {valid_statuses}")
    
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    game.status = status
    if status == "全成就":
        game.progress_percent = 100
    db.commit()
    return {"message": "状态已更新", "status": status}


@router.put("/games/{game_id}/progress")
def update_progress_percent(game_id: int, progress: int, db: Session = Depends(get_db)):
    if progress < 0 or progress > 100:
        raise HTTPException(status_code=400, detail="进度必须在 0-100 之间")
    
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    game.progress_percent = progress
    db.commit()
    return {"message": "进度已更新", "progress": progress}


@router.post("/speedruns", response_model=schemas.Speedrun)
def create_speedrun(speedrun: schemas.SpeedrunCreate, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == speedrun.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    if speedrun.is_personal_best:
        db.query(models.Speedrun).filter(
            models.Speedrun.game_id == speedrun.game_id
        ).update({"is_personal_best": False})
    
    db_speedrun = models.Speedrun(**speedrun.model_dump())
    db.add(db_speedrun)
    db.commit()
    db.refresh(db_speedrun)
    return db_speedrun


@router.get("/games/{game_id}/speedruns", response_model=List[schemas.Speedrun])
def get_game_speedruns(game_id: int, db: Session = Depends(get_db)):
    return db.query(models.Speedrun).filter(
        models.Speedrun.game_id == game_id
    ).order_by(models.Speedrun.completion_time_seconds).all()


@router.post("/screenshots/upload")
async def upload_screenshot(
    game_id: int,
    description: Optional[str] = None,
    is_completion: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = os.path.splitext(file.filename)[1]
    file_path = f"{UPLOAD_DIR}/game_{game_id}_{timestamp}{file_ext}"
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    db_screenshot = models.Screenshot(
        game_id=game_id,
        file_path=file_path,
        description=description,
        date_taken=date.today(),
        is_completion=is_completion
    )
    db.add(db_screenshot)
    db.commit()
    db.refresh(db_screenshot)
    
    return schemas.Screenshot.model_validate(db_screenshot)


@router.get("/games/{game_id}/screenshots", response_model=List[schemas.Screenshot])
def get_game_screenshots(game_id: int, db: Session = Depends(get_db)):
    return db.query(models.Screenshot).filter(
        models.Screenshot.game_id == game_id
    ).order_by(models.Screenshot.date_taken.desc()).all()
