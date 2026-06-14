import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional


KNOWN_TOOLS = [
    "oil-price",
    "weather",
    "calendar",
    "internet-news",
    "esports-news",
    "auto-news",
    "gold-price",
    "qrcode",
]


class ToolStatsService:
    """全站工具点击统计服务。使用服务端 JSON 文件持久化点击次数。"""

    _lock = threading.Lock()

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).resolve().parents[1] / "data" / "tool_clicks.json"

    def _read_counts(self) -> Dict[str, int]:
        if not self.storage_path.exists():
            return {}
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {tool_id: int(count) for tool_id, count in data.items() if tool_id in KNOWN_TOOLS and isinstance(count, int)}

    def _write_counts(self, counts: Dict[str, int]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")

    def record_click(self, tool_id: str) -> Dict[str, Any]:
        if tool_id not in KNOWN_TOOLS:
            return {"code": 400, "msg": "未知工具"}

        with self._lock:
            counts = self._read_counts()
            counts[tool_id] = counts.get(tool_id, 0) + 1
            self._write_counts(counts)
            clicks = counts[tool_id]

        return {"code": 200, "msg": "success", "data": {"id": tool_id, "clicks": clicks}}

    def get_popular(self, limit: int = 4) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit or 4), len(KNOWN_TOOLS)))
        counts = self._read_counts()
        ranked = sorted(
            KNOWN_TOOLS,
            key=lambda tool_id: (-counts.get(tool_id, 0), KNOWN_TOOLS.index(tool_id)),
        )
        return [{"id": tool_id, "clicks": counts.get(tool_id, 0)} for tool_id in ranked[:limit]]


_tool_stats_service = ToolStatsService()


def get_tool_stats_service() -> ToolStatsService:
    return _tool_stats_service
