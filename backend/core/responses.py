from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应模型。保留 code=200 成功约定，兼容现有前端。"""

    code: int = 200
    msg: str = "success"
    data: Optional[T] = None


def success(data: Any = None, msg: str = "success", **extra: Any) -> dict:
    payload = {"code": 200, "msg": msg}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return payload


def error(code: int = 500, msg: str = "服务器内部错误", **extra: Any) -> dict:
    payload = {"code": code, "msg": msg}
    payload.update(extra)
    return payload


def normalize_response(result: Any) -> Any:
    """Normalize common service dict responses without breaking legacy keys.

    Existing frontend code still reads `newslist`/`result` for TianAPI-style
    endpoints, so those keys are preserved. The unified `data` key is added when
    it can be derived safely.
    """
    if not isinstance(result, dict):
        return success(result)
    result.setdefault("code", 200)
    result.setdefault("msg", "success")
    if "data" not in result and "newslist" in result:
        result["data"] = result["newslist"]
    if "data" not in result and isinstance(result.get("result"), dict):
        raw = result["result"]
        for key in ("newslist", "list", "data"):
            value = raw.get(key)
            if value is not None:
                result["data"] = value
                break
        else:
            result["data"] = raw
    return result
