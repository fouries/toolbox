import logging
import time
from datetime import datetime
from typing import Any, Dict

import httpx

from config import get_settings
from db.repositories import UserEngagementRepository, UserFavoritesRepository
from db.session import session_scope

logger = logging.getLogger(__name__)

REMINDER_TEMPLATE_SETTING = {
    "daily_brief": "WECHAT_SUBSCRIBE_TEMPLATE_DAILY_BRIEF",
    "weather": "WECHAT_SUBSCRIBE_TEMPLATE_WEATHER",
    "hot_search": "WECHAT_SUBSCRIBE_TEMPLATE_HOT_SEARCH",
    "gold_price": "WECHAT_SUBSCRIBE_TEMPLATE_GOLD_PRICE",
}

DEFAULT_REMINDER_TITLE = {
    "daily_brief": "每日简报",
    "weather": "天气预报",
    "hot_search": "热搜榜提醒",
    "gold_price": "黄金行情提醒",
}


class WechatSubscribeService:
    """微信小程序登录和订阅消息发送服务。

    Template ID 需要在微信小程序后台申请后通过环境变量配置；AppSecret 只从环境变量/.env 读取，不能写入代码。
    """

    def __init__(self, settings_obj=None):
        self.settings = settings_obj or get_settings()
        self._access_token = ""
        self._access_token_expires_at = 0.0

    def template_id_for(self, reminder_type: str) -> str:
        setting_name = REMINDER_TEMPLATE_SETTING.get(str(reminder_type or ""), "")
        return str(getattr(self.settings, setting_name, "") or "").strip()

    def configured_templates(self) -> Dict[str, str]:
        return {key: self.template_id_for(key) for key in REMINDER_TEMPLATE_SETTING}

    def _validate_user_key(self, user_key: str) -> str:
        # 复用 engagement 服务的 user_key 规则，避免导入私有方法。
        user_key = str(user_key or "").strip()
        if len(user_key) < 8 or len(user_key) > 128:
            return ""
        if not all(ch.isalnum() or ch in "_-" for ch in user_key):
            return ""
        return user_key

    async def bind_openid(self, user_key: str, code: str) -> Dict[str, Any]:
        user_key = self._validate_user_key(user_key)
        if not user_key:
            return {"code": 400, "msg": "用户标识无效"}
        if not self.settings.WECHAT_MINI_APP_ID or not self.settings.WECHAT_MINI_APP_SECRET:
            return {"code": 503, "msg": "微信小程序 AppID/AppSecret 未配置"}
        code = str(code or "").strip()
        if not code:
            return {"code": 400, "msg": "微信登录 code 不能为空"}

        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": self.settings.WECHAT_MINI_APP_ID,
            "secret": self.settings.WECHAT_MINI_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
        openid = str(data.get("openid") or "")
        if not openid:
            logger.warning("wechat_jscode2session_failed errcode=%s errmsg=%s", data.get("errcode"), data.get("errmsg"))
            return {"code": 400, "msg": "微信登录失败，请稍后重试"}

        with session_scope() as session:
            UserFavoritesRepository(session).bind_wechat_openid(user_key, openid)
        return {"code": 200, "msg": "success", "data": {"bound": True}}

    async def get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._access_token_expires_at - 120:
            return self._access_token
        if not self.settings.WECHAT_MINI_APP_ID or not self.settings.WECHAT_MINI_APP_SECRET:
            raise RuntimeError("微信小程序 AppID/AppSecret 未配置")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": self.settings.WECHAT_MINI_APP_ID,
                    "secret": self.settings.WECHAT_MINI_APP_SECRET,
                },
            )
            data = resp.json()
        token = str(data.get("access_token") or "")
        if not token:
            raise RuntimeError(f"获取微信 access_token 失败: {data.get('errcode')} {data.get('errmsg')}")
        self._access_token = token
        self._access_token_expires_at = now + int(data.get("expires_in") or 7200)
        return token

    def build_message_data(self, title: str, reminder_time: str, reminder_type: str) -> Dict[str, Dict[str, str]]:
        keys = [item.strip() for item in str(self.settings.WECHAT_SUBSCRIBE_TEMPLATE_DATA_KEYS or "").split(",") if item.strip()]
        if len(keys) < 3:
            keys = ["thing1", "time2", "thing3"]
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        remark = f"你订阅的{title or DEFAULT_REMINDER_TITLE.get(reminder_type, '提醒')}已到时间"
        return {
            keys[0]: {"value": str(title or DEFAULT_REMINDER_TITLE.get(reminder_type, "订阅提醒"))[:20]},
            keys[1]: {"value": now_text},
            keys[2]: {"value": remark[:20]},
        }

    async def send_subscribe_message(self, openid: str, template_id: str, title: str, reminder_time: str, reminder_type: str) -> Dict[str, Any]:
        access_token = await self.get_access_token()
        payload = {
            "touser": openid,
            "template_id": template_id,
            "page": "pages/settings/index",
            "data": self.build_message_data(title, reminder_time, reminder_type),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.weixin.qq.com/cgi-bin/message/subscribe/send",
                params={"access_token": access_token},
                json=payload,
            )
            data = resp.json()
        return data

    async def send_due_reminders(self, now: datetime | None = None) -> Dict[str, Any]:
        if not self.settings.WECHAT_SUBSCRIBE_ENABLED:
            return {"checked": 0, "sent": 0, "failed": 0, "skipped": 0, "enabled": False}
        now = now or datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")
        due_rows = []
        with session_scope() as session:
            due_rows = UserEngagementRepository(session).list_due_wechat_reminders(current_time, today)

        sent = failed = skipped = 0
        for row in due_rows:
            template_id = row.wx_template_id or self.template_id_for(row.reminder_type)
            openid = getattr(row.user, "wx_openid", "") or ""
            if not template_id or not openid:
                skipped += 1
                continue
            try:
                result = await self.send_subscribe_message(openid, template_id, row.title, row.reminder_time, row.reminder_type)
                if int(result.get("errcode", -1)) == 0:
                    with session_scope() as session:
                        UserEngagementRepository(session).mark_reminder_sent(int(row.id), today)
                    sent += 1
                else:
                    failed += 1
                    logger.warning("wechat_subscribe_send_failed reminder_id=%s errcode=%s errmsg=%s", row.id, result.get("errcode"), result.get("errmsg"))
            except Exception as exc:
                failed += 1
                logger.warning("wechat_subscribe_send_exception reminder_id=%s error=%s", row.id, exc)
        return {"checked": len(due_rows), "sent": sent, "failed": failed, "skipped": skipped, "enabled": True}


_wechat_subscribe_service = WechatSubscribeService()


def get_wechat_subscribe_service() -> WechatSubscribeService:
    return _wechat_subscribe_service
