import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from db.repositories import ToolStatsRepository
from db.session import session_scope

logger = logging.getLogger(__name__)

KNOWN_TOOLS = [
    "oil-price",
    "weather",
    "calendar",
    "gold-price",
    "qrcode",
    "password",
    "history-today",
    "solar-terms",
    "baidu-hot",
    "douyin-hot",
    "daily-brief",
    "info-news",
]

# Legacy ids are kept readable so historical counters can be folded into the
# current frontend tool ids instead of appearing as dead/unknown热门工具 entries.
LEGACY_TOOL_ALIASES = {
    "internet-news": "info-news",
    "esports-news": "info-news",
    "auto-news": "info-news",
}
ACCEPTED_TOOL_IDS = set(KNOWN_TOOLS) | set(LEGACY_TOOL_ALIASES)


class ToolStatsService:
    """全站工具点击统计服务。默认使用数据库，启动时可从旧 JSON 迁移。"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).resolve().parents[1] / "data" / "tool_clicks.json"

    def migrate_legacy_json(self) -> None:
        with session_scope() as session:
            ToolStatsRepository(session).migrate_from_json(self.storage_path, ACCEPTED_TOOL_IDS, LEGACY_TOOL_ALIASES)

    def record_click(self, tool_id: str) -> Dict[str, Any]:
        tool_id = LEGACY_TOOL_ALIASES.get(tool_id, tool_id)
        if tool_id not in KNOWN_TOOLS:
            return {"code": 400, "msg": "未知工具"}

        with session_scope() as session:
            clicks = ToolStatsRepository(session).increment(tool_id)

        return {"code": 200, "msg": "success", "data": {"id": tool_id, "clicks": clicks}}

    def get_popular(self, limit: int = 4) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit or 4), len(KNOWN_TOOLS)))
        with session_scope() as session:
            counts = ToolStatsRepository(session).get_counts()
        ranked = sorted(
            KNOWN_TOOLS,
            key=lambda tool_id: (-counts.get(tool_id, 0), KNOWN_TOOLS.index(tool_id)),
        )
        return [{"id": tool_id, "clicks": counts.get(tool_id, 0)} for tool_id in ranked[:limit]]


_tool_stats_service = ToolStatsService()


def get_tool_stats_service() -> ToolStatsService:
    return _tool_stats_service
