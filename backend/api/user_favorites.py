import re
from typing import Any, Dict

from api.tool_stats import KNOWN_TOOLS
from db.repositories import UserFavoritesRepository
from db.session import session_scope

USER_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


class UserFavoritesService:
    """轻量用户身份与工具收藏服务。

    第一阶段只做匿名 user_key：H5 本地生成，小程序后续可替换为 openid。
    """

    def _validate_user_key(self, user_key: str) -> str | None:
        user_key = str(user_key or "").strip()
        if not USER_KEY_RE.fullmatch(user_key):
            return None
        return user_key

    def _validate_tool_id(self, tool_id: str) -> str | None:
        tool_id = str(tool_id or "").strip()
        if tool_id not in KNOWN_TOOLS:
            return None
        return tool_id

    def ensure_user(self, user_key: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}

        with session_scope() as session:
            user = UserFavoritesRepository(session).get_or_create_user(user_key)
            data = {"id": user.id, "user_key": user.user_key, "user_type": user.user_type}
        return {"code": 200, "msg": "success", "data": data}

    def list_favorites(self, user_key: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}

        with session_scope() as session:
            favorites = UserFavoritesRepository(session).list_favorites(user_key)
        return {"code": 200, "msg": "success", "data": favorites}

    def add_favorite(self, user_key: str, tool_id: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        tool_id = self._validate_tool_id(tool_id)
        if not tool_id:
            return {"code": 400, "msg": "未知工具"}

        with session_scope() as session:
            UserFavoritesRepository(session).add_favorite(user_key, tool_id)
        return {"code": 200, "msg": "success", "data": {"tool_id": tool_id, "favorited": True}}

    def remove_favorite(self, user_key: str, tool_id: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        tool_id = self._validate_tool_id(tool_id)
        if not tool_id:
            return {"code": 400, "msg": "未知工具"}

        with session_scope() as session:
            UserFavoritesRepository(session).remove_favorite(user_key, tool_id)
        return {"code": 200, "msg": "success", "data": {"tool_id": tool_id, "favorited": False}}


_user_favorites_service = UserFavoritesService()


def get_user_favorites_service() -> UserFavoritesService:
    return _user_favorites_service
