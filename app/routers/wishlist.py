from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/wishlist", tags=["愿望单"])


@router.post("/", response_model=schemas.WishlistItem)
def create_wishlist_item(item: schemas.WishlistItemCreate, db: Session = Depends(get_db)):
    db_item = models.WishlistItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[schemas.WishlistItem])
def get_wishlist(
    platform: Optional[str] = None,
    sort_by_priority: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(models.WishlistItem)
    if platform:
        query = query.filter(models.WishlistItem.platform == platform)
    if sort_by_priority:
        query = query.order_by(models.WishlistItem.priority.desc())
    return query.all()


@router.get("/alerts")
def get_price_alerts(db: Session = Depends(get_db)):
    items = db.query(models.WishlistItem).filter(
        models.WishlistItem.current_price.isnot(None),
        models.WishlistItem.expected_price.isnot(None),
        models.WishlistItem.current_price <= models.WishlistItem.expected_price
    ).all()
    
    return {
        "count": len(items),
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "current_price": item.current_price,
                "expected_price": item.expected_price,
                "savings": item.expected_price - item.current_price
            }
            for item in items
        ]
    }


@router.get("/{item_id}", response_model=schemas.WishlistItem)
def get_wishlist_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.WishlistItem).filter(models.WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="愿望单项目不存在")
    return item


@router.put("/{item_id}", response_model=schemas.WishlistItem)
def update_wishlist_item(
    item_id: int,
    item_update: schemas.WishlistItemUpdate,
    db: Session = Depends(get_db)
):
    db_item = db.query(models.WishlistItem).filter(models.WishlistItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="愿望单项目不存在")
    
    update_data = item_update.model_dump(exclude_unset=True)
    
    if "current_price" in update_data:
        new_price = update_data["current_price"]
        if db_item.lowest_price is None or new_price < db_item.lowest_price:
            from datetime import date
            db_item.lowest_price = new_price
            db_item.lowest_price_date = date.today()
    
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_wishlist_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.WishlistItem).filter(models.WishlistItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="愿望单项目不存在")
    db.delete(db_item)
    db.commit()
    return {"message": "已从愿望单移除"}


@router.get("/share/{share_id}")
def share_wishlist(share_id: str, db: Session = Depends(get_db)):
    items = db.query(models.WishlistItem).order_by(models.WishlistItem.priority.desc()).all()
    return {
        "share_id": share_id,
        "generated_at": "now",
        "items": [
            {
                "name": item.name,
                "platform": item.platform,
                "expected_price": item.expected_price,
                "expected_discount": item.expected_discount,
                "current_price": item.current_price
            }
            for item in items
        ]
    }


@router.get("/stats/total-value")
def get_wishlist_total_value(db: Session = Depends(get_db)):
    items = db.query(models.WishlistItem).all()
    total_current = sum(item.current_price or 0 for item in items)
    total_expected = sum(item.expected_price or 0 for item in items)
    
    return {
        "total_current_price": round(total_current, 2),
        "total_expected_price": round(total_expected, 2),
        "item_count": len(items)
    }
