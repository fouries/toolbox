import re
from typing import Any, Dict

from db.repositories import UserEngagementRepository
from db.session import session_scope

USER_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
FEEDBACK_CATEGORIES = {"bug", "idea", "content", "other"}
REMINDER_TYPES = {
    "daily_brief": "每日简报",
    "weather": "天气预报",
    "oil_price": "油价提醒",
    "hot_search": "热搜榜提醒",
    "gold_price": "黄金行情提醒",
}


class UserEngagementService:
    """反馈系统与订阅提醒服务。

    当前阶段保存用户订阅配置，后续可由定时任务按 enabled/reminder_time 发送消息。
    """

    def _validate_user_key(self, user_key: str) -> str | None:
        user_key = str(user_key or "").strip()
        if not USER_KEY_RE.fullmatch(user_key):
            return None
        return user_key

    def _feedback_to_dict(self, feedback) -> Dict[str, Any]:
        return {
            "id": int(feedback.id),
            "category": feedback.category,
            "content": feedback.content,
            "contact": feedback.contact or "",
            "page": feedback.page or "",
            "status": feedback.status,
            "created_at": feedback.created_at.isoformat() if feedback.created_at else "",
        }

    def _reminder_to_dict(self, reminder) -> Dict[str, Any]:
        return {
            "id": int(reminder.id),
            "reminder_type": reminder.reminder_type,
            "title": reminder.title,
            "reminder_time": reminder.reminder_time,
            "enabled": bool(reminder.enabled),
            "wx_subscribe_enabled": bool(getattr(reminder, "wx_subscribe_enabled", False)),
            "has_wechat_template": bool(getattr(reminder, "wx_template_id", "")),
            "created_at": reminder.created_at.isoformat() if reminder.created_at else "",
            "updated_at": reminder.updated_at.isoformat() if reminder.updated_at else "",
        }

    def submit_feedback(self, user_key: str, category: str, content: str, contact: str = "", page: str = "") -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        category = str(category or "").strip()
        if category not in FEEDBACK_CATEGORIES:
            return {"code": 400, "msg": "反馈类型无效"}
        content = str(content or "").strip()
        if len(content) < 5 or len(content) > 1000:
            return {"code": 400, "msg": "反馈内容需为 5-1000 字"}
        contact = str(contact or "").strip()[:128]
        page = str(page or "").strip()[:256]

        with session_scope() as session:
            feedback = UserEngagementRepository(session).add_feedback(user_key, category, content, contact, page)
            data = self._feedback_to_dict(feedback)
        return {"code": 200, "msg": "success", "data": data}

    def list_feedback(self, user_key: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        with session_scope() as session:
            rows = UserEngagementRepository(session).list_feedback(user_key)
            data = [self._feedback_to_dict(row) for row in rows]
        return {"code": 200, "msg": "success", "data": data}

    def list_reminders(self, user_key: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        with session_scope() as session:
            rows = UserEngagementRepository(session).list_reminders(user_key)
            data = [self._reminder_to_dict(row) for row in rows]
        return {"code": 200, "msg": "success", "data": data}

    def upsert_reminder(
        self,
        user_key: str,
        reminder_type: str,
        title: str,
        reminder_time: str,
        enabled: bool = True,
        wx_template_id: str = "",
        wx_subscribe_enabled: bool | None = None,
    ) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        reminder_type = str(reminder_type or "").strip()
        if reminder_type not in REMINDER_TYPES:
            return {"code": 400, "msg": "提醒类型无效"}
        reminder_time = str(reminder_time or "").strip()
        if not TIME_RE.fullmatch(reminder_time):
            return {"code": 400, "msg": "提醒时间无效"}
        title = str(title or REMINDER_TYPES[reminder_type]).strip()[:64] or REMINDER_TYPES[reminder_type]

        with session_scope() as session:
            reminder = UserEngagementRepository(session).upsert_reminder(
                user_key,
                reminder_type,
                title,
                reminder_time,
                bool(enabled),
                wx_template_id=str(wx_template_id or "").strip(),
                wx_subscribe_enabled=wx_subscribe_enabled,
            )
            data = self._reminder_to_dict(reminder)
        return {"code": 200, "msg": "success", "data": data}

    def disable_reminder(self, user_key: str, reminder_type: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        reminder_type = str(reminder_type or "").strip()
        if reminder_type not in REMINDER_TYPES:
            return {"code": 400, "msg": "提醒类型无效"}
        with session_scope() as session:
            reminder = UserEngagementRepository(session).disable_reminder(user_key, reminder_type)
            if reminder is None:
                return {"code": 404, "msg": "提醒不存在"}
            data = self._reminder_to_dict(reminder)
        return {"code": 200, "msg": "success", "data": data}


_user_engagement_service = UserEngagementService()


def get_user_engagement_service() -> UserEngagementService:
    return _user_engagement_service
