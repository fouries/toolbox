from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.user_engagement import UserEngagementService
from api.wechat_subscribe import WechatSubscribeService
from db.repositories import UserFavoritesRepository
from db.session import init_db, session_scope


def _configure_temp_db(monkeypatch, tmp_path):
    import db.session as db_session
    import api.user_engagement as user_engagement
    import api.wechat_subscribe as wechat_subscribe

    engine = create_engine(f"sqlite:///{tmp_path / 'toolbox-wechat-test.db'}", future=True, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_session, "engine", engine)
    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(user_engagement, "session_scope", db_session.session_scope)
    monkeypatch.setattr(wechat_subscribe, "session_scope", db_session.session_scope)
    init_db()


class FakeSettings:
    WECHAT_MINI_APP_ID = "wx-test"
    WECHAT_MINI_APP_SECRET = "secret-test"
    WECHAT_SUBSCRIBE_ENABLED = True
    WECHAT_SUBSCRIBE_TEMPLATE_DAILY_BRIEF = "tmpl_daily"
    WECHAT_SUBSCRIBE_TEMPLATE_WEATHER = "tmpl_weather"
    WECHAT_SUBSCRIBE_TEMPLATE_HOT_SEARCH = "tmpl_hot"
    WECHAT_SUBSCRIBE_TEMPLATE_GOLD_PRICE = "tmpl_gold"
    WECHAT_SUBSCRIBE_TEMPLATE_DATA_KEYS = "thing1,time2,thing3"


def test_template_config_and_message_payload():
    service = WechatSubscribeService(FakeSettings())
    assert service.template_id_for("daily_brief") == "tmpl_daily"
    data = service.build_message_data("每日简报", "08:30", "daily_brief")
    assert data["thing1"]["value"] == "每日简报"
    assert "你订阅的每日简报" in data["thing3"]["value"]


def test_send_due_reminders_marks_sent(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    UserEngagementService().upsert_reminder(
        user_key="anon_wechat_001",
        reminder_type="daily_brief",
        title="每日简报",
        reminder_time="08:30",
        enabled=True,
        wx_template_id="tmpl_daily",
        wx_subscribe_enabled=True,
    )
    with session_scope() as session:
        UserFavoritesRepository(session).bind_wechat_openid("anon_wechat_001", "openid-test")

    service = WechatSubscribeService(FakeSettings())
    sent_payloads = []

    async def fake_send(openid, template_id, title, reminder_time, reminder_type):
        sent_payloads.append((openid, template_id, title, reminder_time, reminder_type))
        return {"errcode": 0}

    monkeypatch.setattr(service, "send_subscribe_message", fake_send)

    import asyncio
    result = asyncio.run(service.send_due_reminders(datetime(2026, 6, 22, 8, 30)))
    assert result["sent"] == 1
    assert sent_payloads == [("openid-test", "tmpl_daily", "每日简报", "08:30", "daily_brief")]

    result_again = asyncio.run(service.send_due_reminders(datetime(2026, 6, 22, 8, 30)))
    assert result_again["checked"] == 0
