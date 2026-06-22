from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class ToolClickStat(Base):
    __tablename__ = "tool_click_stats"
    __table_args__ = (UniqueConstraint("tool_id", name="uq_tool_click_stats_tool_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("user_key", name="uq_users_user_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_type: Mapped[str] = mapped_column(String(32), nullable=False, default="anonymous")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    favorites: Mapped[list["UserToolFavorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserToolFavorite(Base):
    __tablename__ = "user_tool_favorites"
    __table_args__ = (UniqueConstraint("user_id", "tool_id", name="uq_user_tool_favorites_user_tool"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="favorites")
