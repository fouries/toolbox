import httpx
import asyncio
from typing import Optional, Dict, Any
import json

class HttpClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def get(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("HttpClient not initialized")
        
        try:
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}", "data": None}
        except Exception as e:
            return {"error": str(e), "data": None}

    async def get_text(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> str:
        if not self._client:
            raise RuntimeError("HttpClient not initialized")

        response = await self._client.get(url, params=params, headers=headers)
        response.raise_for_status()
        if not response.encoding:
            response.encoding = "utf-8"
        return response.text
    
    async def post(self, url: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("HttpClient not initialized")
        
        try:
            response = await self._client.post(url, data=data, json=json_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "data": None}

# 同步版本（用于测试）
def sync_get(url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "data": None}
