from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class GameBase(BaseModel):
    name: str
    platform: str
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    discount_rate: Optional[float] = None
    cover_image: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None
    release_date: Optional[date] = None
    tags: Optional[str] = None
    status: Optional[str] = "未开始"
    progress_percent: Optional[int] = 0


class GameCreate(GameBase):
    pass


class GameUpdate(GameBase):
    name: Optional[str] = None
    platform: Optional[str] = None


class Game(GameBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RatingBase(BaseModel):
    game_id: int
    graphics: Optional[int] = None
    gameplay: Optional[int] = None
    story: Optional[int] = None
    music: Optional[int] = None
    overall: Optional[float] = None
    comment: Optional[str] = None


class RatingCreate(RatingBase):
    pass


class Rating(RatingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PlayRecordBase(BaseModel):
    game_id: int
    date: date
    duration_minutes: int = 0
    progress_description: Optional[str] = None
    notes: Optional[str] = None


class PlayRecordCreate(PlayRecordBase):
    pass


class PlayRecord(PlayRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SpeedrunBase(BaseModel):
    game_id: int
    completion_time_seconds: int
    date: Optional[date] = None
    notes: Optional[str] = None
    is_personal_best: bool = False


class SpeedrunCreate(SpeedrunBase):
    pass


class Speedrun(SpeedrunBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScreenshotBase(BaseModel):
    game_id: int
    file_path: str
    description: Optional[str] = None
    date_taken: Optional[date] = None
    is_completion: bool = False


class ScreenshotCreate(ScreenshotBase):
    pass


class Screenshot(ScreenshotBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WishlistItemBase(BaseModel):
    name: str
    platform: Optional[str] = None
    expected_price: Optional[float] = None
    expected_discount: Optional[str] = None
    priority: int = 0
    current_price: Optional[float] = None
    store_url: Optional[str] = None
    lowest_price: Optional[float] = None
    lowest_price_date: Optional[date] = None
    notes: Optional[str] = None


class WishlistItemCreate(WishlistItemBase):
    pass


class WishlistItemUpdate(WishlistItemBase):
    name: Optional[str] = None


class WishlistItem(WishlistItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AchievementBase(BaseModel):
    game_id: int
    name: str
    description: Optional[str] = None
    rarity: Optional[str] = None
    unlocked_date: Optional[date] = None
    is_pinned: bool = False


class AchievementCreate(AchievementBase):
    pass


class Achievement(AchievementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FriendBase(BaseModel):
    name: str
    steam_id: Optional[str] = None
    epic_id: Optional[str] = None
    psn_id: Optional[str] = None
    xbox_id: Optional[str] = None
    switch_friend_code: Optional[str] = None
    notes: Optional[str] = None


class FriendCreate(FriendBase):
    pass


class Friend(FriendBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FriendPlayingBase(BaseModel):
    friend_id: int
    game_name: str
    platform: Optional[str] = None
    status: Optional[str] = None
    last_played: Optional[date] = None


class FriendPlayingCreate(FriendPlayingBase):
    pass


class FriendPlaying(FriendPlayingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    year: int
    amount: float


class BudgetCreate(BudgetBase):
    pass


class Budget(BudgetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnualPlanBase(BaseModel):
    year: int
    target_games: Optional[int] = None
    budget: Optional[float] = None
    notes: Optional[str] = None


class AnnualPlanCreate(AnnualPlanBase):
    pass


class AnnualPlan(AnnualPlanBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GameDetail(Game):
    ratings: List[Rating] = []
    play_records: List[PlayRecord] = []
    achievements: List[Achievement] = []
    speedruns: List[Speedrun] = []
    screenshots: List[Screenshot] = []
    total_play_time: int = 0
    cost_per_hour: Optional[float] = None
