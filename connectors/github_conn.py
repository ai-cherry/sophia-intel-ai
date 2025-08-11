import httpx
import jwt
import time
from typing import Optional, Dict, Any

class GitHubConnector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = httpx.AsyncClient(base_url="https://api.github.com")
        self._token = None
        self._token_expires_at = 0

    async def _get_auth_headers(self) -> Dict[str, str]:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    async def _get_token(self) -> str:
        if self.config["github"]["mode"] == "app":
            if not self._token or time.time() >= self._token_expires_at:
                await self._refresh_app_token()
            return self._token
        elif self.config["github"]["mode"] == "pat":
            return self.config["github"]["fine_grained_token"]
        else:
            # Fallback to classic PAT with a warning
            print("Warning: Using classic PAT. Write actions may be restricted.")
            return self.config["github"].get("classic_pat_token")

    async def _refresh_app_token(self):
        # This part will be implemented later when the GitHub App is ready
        raise NotImplementedError("GitHub App authentication is not yet implemented.")

    async def get_pr_details(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        headers = await self._get_auth_headers()
        response = await self.client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}", headers=headers)
        response.raise_for_status()
        return response.json()

    async def read_file(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> bytes:
        headers = await self._get_auth_headers()
        url = f"/repos/{owner}/{repo}/contents/{path}"
        if ref:
            url += f"?ref={ref}"
        
        # Add 'Accept' header to get raw content
        headers["Accept"] = "application/vnd.github.v3.raw"
        
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.content

    async def create_pr(self, owner: str, repo: str, title: str, body: str, head: str, base: str) -> Dict[str, Any]:
        headers = await self._get_auth_headers()
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        response = await self.client.post(f"/repos/{owner}/{repo}/pulls", headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()