from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.user_favorites import UserFavoritesService
from db.session import init_db


def _configure_temp_db(monkeypatch, tmp_path):
    import db.session as db_session
    import api.user_favorites as user_favorites

    engine = create_engine(f"sqlite:///{tmp_path / 'toolbox-user-test.db'}", future=True, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_session, "engine", engine)
    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(user_favorites, "session_scope", db_session.session_scope)
    init_db()


def test_ensure_anonymous_user_creates_and_reuses_user(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserFavoritesService()

    first = service.ensure_user("anon_test_001")
    second = service.ensure_user("anon_test_001")

    assert first["code"] == 200
    assert second["code"] == 200
    assert first["data"]["user_key"] == "anon_test_001"
    assert first["data"]["id"] == second["data"]["id"]


def test_favorites_can_be_added_listed_and_removed(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserFavoritesService()

    assert service.add_favorite("anon_test_002", "weather") == {
        "code": 200,
        "msg": "success",
        "data": {"tool_id": "weather", "favorited": True},
    }
    service.add_favorite("anon_test_002", "calendar")
    service.add_favorite("anon_test_002", "weather")

    listed = service.list_favorites("anon_test_002")
    assert listed["code"] == 200
    assert listed["data"] == ["calendar", "weather"]

    assert service.remove_favorite("anon_test_002", "weather") == {
        "code": 200,
        "msg": "success",
        "data": {"tool_id": "weather", "favorited": False},
    }
    assert service.list_favorites("anon_test_002")["data"] == ["calendar"]


def test_favorites_reject_unknown_tool_and_invalid_user_key(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = UserFavoritesService()

    unknown = service.add_favorite("anon_test_003", "unknown-tool")
    invalid_user = service.list_favorites("bad key !")

    assert unknown["code"] == 400
    assert "未知工具" in unknown["msg"]
    assert invalid_user["code"] == 400
    assert "用户标识" in invalid_user["msg"]
