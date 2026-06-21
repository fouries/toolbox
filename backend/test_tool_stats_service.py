import tempfile
from pathlib import Path

from api.tool_stats import ToolStatsService
from db.session import init_db


def _configure_temp_db(monkeypatch, tmp_path):
    import db.session as db_session
    import api.tool_stats as tool_stats
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"sqlite:///{tmp_path / 'toolbox-test.db'}", future=True, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_session, "engine", engine)
    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(tool_stats, "session_scope", db_session.session_scope)
    init_db()


def test_record_click_persists_and_popular_sorts_by_click_count(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    stats_file = tmp_path / "tool_clicks.json"
    service = ToolStatsService(storage_path=stats_file)

    service.record_click("weather")
    service.record_click("oil-price")
    service.record_click("weather")

    popular = service.get_popular(limit=2)

    assert popular == [
        {"id": "weather", "clicks": 2},
        {"id": "oil-price", "clicks": 1},
    ]

    reloaded = ToolStatsService(storage_path=stats_file)
    assert reloaded.get_popular(limit=2)[0] == {"id": "weather", "clicks": 2}


def test_record_click_rejects_unknown_tool_id(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = ToolStatsService(storage_path=tmp_path / "tool_clicks.json")

    result = service.record_click("unknown-tool")

    assert result["code"] == 400
    assert "未知工具" in result["msg"]


def test_get_popular_includes_known_tools_with_zero_clicks_as_fallback(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    service = ToolStatsService(storage_path=tmp_path / "tool_clicks.json")

    popular = service.get_popular(limit=4)

    assert len(popular) == 4
    assert popular[0]["id"] == "oil-price"
    assert all("clicks" in item for item in popular)


def test_migrate_legacy_json_to_database(monkeypatch, tmp_path):
    _configure_temp_db(monkeypatch, tmp_path)
    stats_file = tmp_path / "tool_clicks.json"
    stats_file.write_text('{"weather": 3, "qrcode": 2, "unknown": 99}', encoding="utf-8")
    service = ToolStatsService(storage_path=stats_file)

    service.migrate_legacy_json()

    popular = service.get_popular(limit=2)
    assert popular == [{"id": "weather", "clicks": 3}, {"id": "qrcode", "clicks": 2}]


if __name__ == "__main__":
    print("Run with pytest for isolated database fixtures")
