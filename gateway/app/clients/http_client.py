import httpx


class ServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=20.0))

    async def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/') }"
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text

    async def get(self, path: str, **kwargs):
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs):
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs):
        return await self._request("DELETE", path, **kwargs)
