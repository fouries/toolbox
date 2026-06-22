import json
import logging
from pathlib import Path
from typing import Dict, Mapping

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from db.models import ToolClickStat, User, UserToolFavorite

logger = logging.getLogger(__name__)


class ToolStatsRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_counts(self) -> Dict[str, int]:
        rows = self.session.execute(select(ToolClickStat)).scalars().all()
        return {row.tool_id: int(row.clicks) for row in rows}

    def increment(self, tool_id: str) -> int:
        bind = self.session.get_bind()
        dialect = bind.dialect.name if bind else ""
        if dialect == "sqlite":
            stmt = sqlite_insert(ToolClickStat).values(tool_id=tool_id, clicks=1)
            stmt = stmt.on_conflict_do_update(
                index_elements=["tool_id"],
                set_={"clicks": ToolClickStat.clicks + 1},
            )
            self.session.execute(stmt)
            self.session.flush()
        else:
            row = self.session.execute(select(ToolClickStat).where(ToolClickStat.tool_id == tool_id).with_for_update()).scalar_one_or_none()
            if row is None:
                row = ToolClickStat(tool_id=tool_id, clicks=1)
                self.session.add(row)
            else:
                row.clicks += 1
            self.session.flush()

        clicks = self.session.execute(select(ToolClickStat.clicks).where(ToolClickStat.tool_id == tool_id)).scalar_one()
        return int(clicks)

    def fold_aliases(self, aliases: Mapping[str, str]) -> None:
        for legacy_id, current_id in aliases.items():
            if legacy_id == current_id:
                continue
            legacy_clicks = self.session.execute(
                select(ToolClickStat.clicks).where(ToolClickStat.tool_id == legacy_id)
            ).scalar_one_or_none()
            if not legacy_clicks:
                continue

            current_row = self.session.execute(
                select(ToolClickStat).where(ToolClickStat.tool_id == current_id).with_for_update()
            ).scalar_one_or_none()
            if current_row is None:
                self.session.add(ToolClickStat(tool_id=current_id, clicks=int(legacy_clicks)))
            else:
                current_row.clicks += int(legacy_clicks)
            self.session.execute(delete(ToolClickStat).where(ToolClickStat.tool_id == legacy_id))
            self.session.flush()

    def migrate_from_json(self, storage_path: Path, known_tools: list[str] | set[str], aliases: Mapping[str, str] | None = None) -> None:
        aliases = aliases or {}
        self.fold_aliases(aliases)
        if not storage_path.exists():
            return
        try:
            raw = json.loads(storage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("skip_tool_click_json_migration path=%s error=%s", storage_path, exc)
            return
        if not isinstance(raw, dict):
            return
        existing = self.get_counts()
        merged_counts: Dict[str, int] = {}
        for raw_tool_id, count in raw.items():
            if not isinstance(raw_tool_id, str) or raw_tool_id not in known_tools:
                continue
            tool_id = aliases.get(raw_tool_id, raw_tool_id)
            try:
                clicks = max(0, int(count))
            except (TypeError, ValueError):
                continue
            merged_counts[tool_id] = merged_counts.get(tool_id, 0) + clicks

        for tool_id, clicks in merged_counts.items():
            if tool_id in existing:
                continue
            self.session.add(ToolClickStat(tool_id=tool_id, clicks=clicks))


class UserFavoritesRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_user(self, user_key: str, user_type: str = "anonymous") -> User:
        user = self.session.execute(select(User).where(User.user_key == user_key)).scalar_one_or_none()
        if user is None:
            user = User(user_key=user_key, user_type=user_type)
            self.session.add(user)
            self.session.flush()
        else:
            user.user_type = user.user_type or user_type
            self.session.flush()
        return user

    def list_favorites(self, user_key: str) -> list[str]:
        user = self.get_or_create_user(user_key)
        rows = self.session.execute(
            select(UserToolFavorite.tool_id)
            .where(UserToolFavorite.user_id == user.id)
            .order_by(UserToolFavorite.id.desc())
        ).scalars().all()
        return [str(tool_id) for tool_id in rows]

    def add_favorite(self, user_key: str, tool_id: str) -> None:
        user = self.get_or_create_user(user_key)
        existing = self.session.execute(
            select(UserToolFavorite)
            .where(UserToolFavorite.user_id == user.id)
            .where(UserToolFavorite.tool_id == tool_id)
        ).scalar_one_or_none()
        if existing is None:
            self.session.add(UserToolFavorite(user_id=user.id, tool_id=tool_id))
            self.session.flush()

    def remove_favorite(self, user_key: str, tool_id: str) -> None:
        user = self.get_or_create_user(user_key)
        self.session.execute(
            delete(UserToolFavorite)
            .where(UserToolFavorite.user_id == user.id)
            .where(UserToolFavorite.tool_id == tool_id)
        )
        self.session.flush()
