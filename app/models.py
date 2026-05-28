from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    platform = Column(String, nullable=False)
    purchase_date = Column(Date)
    purchase_price = Column(Float)
    discount_rate = Column(Float)
    cover_image = Column(String)
    developer = Column(String)
    publisher = Column(String)
    release_date = Column(Date)
    tags = Column(String)
    status = Column(String, default="未开始")
    progress_percent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ratings = relationship("Rating", back_populates="game", cascade="all, delete-orphan")
    play_records = relationship("PlayRecord", back_populates="game", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="game", cascade="all, delete-orphan")
    speedruns = relationship("Speedrun", back_populates="game", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="game", cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    graphics = Column(Integer)
    gameplay = Column(Integer)
    story = Column(Integer)
    music = Column(Integer)
    overall = Column(Float)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="ratings")


class PlayRecord(Base):
    __tablename__ = "play_records"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, default=0)
    progress_description = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="play_records")


class Speedrun(Base):
    __tablename__ = "speedruns"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    completion_time_seconds = Column(Integer)
    date = Column(Date)
    notes = Column(Text)
    is_personal_best = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="speedruns")


class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    file_path = Column(String)
    description = Column(String)
    date_taken = Column(Date)
    is_completion = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="screenshots")


class WishlistItem(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    platform = Column(String)
    expected_price = Column(Float)
    expected_discount = Column(String)
    priority = Column(Integer, default=0)
    current_price = Column(Float)
    store_url = Column(String)
    lowest_price = Column(Float)
    lowest_price_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    rarity = Column(String)
    unlocked_date = Column(Date)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="achievements")


class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    steam_id = Column(String)
    epic_id = Column(String)
    psn_id = Column(String)
    xbox_id = Column(String)
    switch_friend_code = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class FriendPlaying(Base):
    __tablename__ = "friend_playing"

    id = Column(Integer, primary_key=True, index=True)
    friend_id = Column(Integer, ForeignKey("friends.id"))
    game_name = Column(String)
    platform = Column(String)
    status = Column(String)
    last_played = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnnualPlan(Base):
    __tablename__ = "annual_plans"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer)
    target_games = Column(Integer)
    budget = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
