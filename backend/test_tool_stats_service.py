import tempfile
from pathlib import Path

from api.tool_stats import ToolStatsService


def test_record_click_persists_and_popular_sorts_by_click_count():
    with tempfile.TemporaryDirectory() as tmpdir:
        stats_file = Path(tmpdir) / "tool_clicks.json"
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


def test_record_click_rejects_unknown_tool_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = ToolStatsService(storage_path=Path(tmpdir) / "tool_clicks.json")

        result = service.record_click("unknown-tool")

        assert result["code"] == 400
        assert "未知工具" in result["msg"]


def test_get_popular_includes_known_tools_with_zero_clicks_as_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = ToolStatsService(storage_path=Path(tmpdir) / "tool_clicks.json")

        popular = service.get_popular(limit=4)

        assert len(popular) == 4
        assert popular[0]["id"] == "oil-price"
        assert all("clicks" in item for item in popular)


if __name__ == "__main__":
    test_record_click_persists_and_popular_sorts_by_click_count()
    test_record_click_rejects_unknown_tool_id()
    test_get_popular_includes_known_tools_with_zero_clicks_as_fallback()
    print("tool stats service tests passed")
