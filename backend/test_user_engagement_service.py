from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.user_engagement import UserEngagementService
from db.session import init_db


def _configure_temp_db(monkeypatch, tmp_path):
    import db.session as db_session
    import api.user_engagement as user_engagement

    engine = create_engine(f"sqlite:///{tmp_path / 'toolbox-engagement-test.db'}", future=True, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_session, "engine", engine)
    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(user_engagement, "session_scope", db_session.session_scope)
    init_db()


def test_feedback_can_be_submitted_and_listed(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserEngagementService()

    submitted = service.submit_feedback(
        user_key="anon_feedback_001",
        category="bug",
        content="天气页面定位失败，希望可以手动选择城市。",
        contact="user@example.com",
        page="/pages/weather/index",
    )

    assert submitted["code"] == 200
    assert submitted["data"]["id"] > 0
    assert submitted["data"]["status"] == "submitted"
    assert submitted["data"]["category"] == "bug"

    listed = service.list_feedback("anon_feedback_001")
    assert listed["code"] == 200
    assert listed["data"][0]["content"] == "天气页面定位失败，希望可以手动选择城市。"
    assert listed["data"][0]["contact"] == "user@example.com"
    assert listed["data"][0]["page"] == "/pages/weather/index"


def test_feedback_rejects_invalid_payload(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserEngagementService()

    invalid_user = service.submit_feedback("bad key !", "idea", "希望加一个新功能")
    too_short = service.submit_feedback("anon_feedback_002", "idea", "短")
    unknown_category = service.submit_feedback("anon_feedback_002", "spam", "希望加一个新功能")

    assert invalid_user["code"] == 400
    assert "用户标识" in invalid_user["msg"]
    assert too_short["code"] == 400
    assert "反馈内容" in too_short["msg"]
    assert unknown_category["code"] == 400
    assert "反馈类型" in unknown_category["msg"]


def test_reminder_subscriptions_can_be_upserted_listed_and_disabled(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserEngagementService()

    created = service.upsert_reminder(
        user_key="anon_reminder_001",
        reminder_type="daily_brief",
        title="每日简报",
        reminder_time="08:30",
        enabled=True,
    )
    updated = service.upsert_reminder(
        user_key="anon_reminder_001",
        reminder_type="daily_brief",
        title="每日简报",
        reminder_time="09:00",
        enabled=True,
    )
    service.upsert_reminder(
        user_key="anon_reminder_001",
        reminder_type="weather",
        title="天气预报",
        reminder_time="07:40",
        enabled=True,
    )

    assert created["code"] == 200
    assert created["data"]["reminder_type"] == "daily_brief"
    assert updated["data"]["reminder_time"] == "09:00"

    listed = service.list_reminders("anon_reminder_001")
    assert listed["code"] == 200
    assert [item["reminder_type"] for item in listed["data"]] == ["weather", "daily_brief"]

    disabled = service.disable_reminder("anon_reminder_001", "daily_brief")
    assert disabled["code"] == 200
    assert disabled["data"]["enabled"] is False
    assert service.list_reminders("anon_reminder_001")["data"][1]["enabled"] is False


def test_reminders_reject_unknown_type_and_bad_time(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserEngagementService()

    unknown = service.upsert_reminder("anon_reminder_002", "lottery", "彩票开奖", "08:00", True)
    bad_time = service.upsert_reminder("anon_reminder_002", "weather", "天气预报", "25:99", True)

    assert unknown["code"] == 400
    assert "提醒类型" in unknown["msg"]
    assert bad_time["code"] == 400
    assert "提醒时间" in bad_time["msg"]


def test_reminder_can_store_wechat_subscription_flags(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserEngagementService()

    created = service.upsert_reminder(
        user_key="anon_reminder_wx_001",
        reminder_type="daily_brief",
        title="每日简报",
        reminder_time="08:30",
        enabled=True,
        wx_template_id="tmpl_daily",
        wx_subscribe_enabled=True,
    )

    assert created["code"] == 200
    assert created["data"]["wx_subscribe_enabled"] is True
    assert created["data"]["has_wechat_template"] is True

    disabled = service.disable_reminder("anon_reminder_wx_001", "daily_brief")
    assert disabled["code"] == 200
    assert disabled["data"]["enabled"] is False
    assert disabled["data"]["wx_subscribe_enabled"] is False
