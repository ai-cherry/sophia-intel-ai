from __future__ import annotations

import base64
import os
import time
from typing import Any, Dict, Optional

import httpx

try:
    import msal  # type: ignore
except Exception:  # pragma: no cover - runtime dependency
    msal = None  # type: ignore


class MicrosoftGraphClient:
    """Microsoft Graph client with certificate and client secret support.

    Supports both authentication methods with automatic fallback:
    1. Certificate-based (preferred): MICROSOFT_CERTIFICATE_ID + MICROSOFT_SIGNING_CERTIFICATE
    2. Client secret: MS_CLIENT_SECRET|MICROSOFT_SECRET_KEY

    Environment variables:
    - MS_TENANT_ID|MICROSOFT_TENANT_ID (required)
    - MS_CLIENT_ID|MICROSOFT_CLIENT_ID (required)
    - MS_CLIENT_SECRET|MICROSOFT_SECRET_KEY (for secret auth)
    - MICROSOFT_CERTIFICATE_ID (thumbprint for cert auth)
    - MICROSOFT_SIGNING_CERTIFICATE (PEM cert content)
    - MICROSOFT_SIGNING_CERTIFICATE_BASE64 (base64-encoded PEM, alternative)
    """

    GRAPH_BASE = os.getenv("MS_GRAPH_BASE", "https://graph.microsoft.com/v1.0")

    def __init__(self) -> None:
        self.tenant_id = os.getenv("MS_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID")
        self.client_id = os.getenv("MS_CLIENT_ID") or os.getenv("MICROSOFT_CLIENT_ID")
        
        if not (self.tenant_id and self.client_id):
            raise RuntimeError(
                "Microsoft Graph tenant_id and client_id required. "
                "Set MS_TENANT_ID/MICROSOFT_TENANT_ID and MS_CLIENT_ID/MICROSOFT_CLIENT_ID"
            )

        if msal is None:
            raise RuntimeError("msal not installed. Run: pip install msal")

        # Try certificate auth first, fall back to client secret
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        client_credential = self._get_client_credential()
        
        self._msal_app = msal.ConfidentialClientApplication(
            self.client_id, authority=authority, client_credential=client_credential
        )
        self._token: Optional[Dict[str, Any]] = None
        self._token_exp: float = 0
        self._auth_method = self._detect_auth_method()

    def _get_client_credential(self) -> Dict[str, Any] | str:
        """Get client credential, preferring certificate over secret."""
        # Try certificate authentication first
        cert_id = os.getenv("MICROSOFT_CERTIFICATE_ID")
        cert_pem = self._get_certificate_pem()
        
        if cert_id and cert_pem:
            return {
                "private_key": cert_pem,
                "thumbprint": cert_id
            }
        
        # Fall back to client secret
        client_secret = os.getenv("MS_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET_KEY")
        if client_secret:
            return client_secret
        
        raise RuntimeError(
            "Neither certificate nor client secret configured. Set either:\n"
            "  Certificate auth: MICROSOFT_CERTIFICATE_ID + MICROSOFT_SIGNING_CERTIFICATE\n"
            "  Secret auth: MS_CLIENT_SECRET or MICROSOFT_SECRET_KEY\n\n"
            "Note: Ensure you're using the client secret VALUE, not the client secret ID."
        )

    def _get_certificate_pem(self) -> Optional[str]:
        """Get certificate PEM content, supporting both direct and base64-encoded."""
        # Try direct PEM content first
        cert_pem = os.getenv("MICROSOFT_SIGNING_CERTIFICATE")
        if cert_pem and "-----BEGIN" in cert_pem:
            return cert_pem
        
        # Try base64-encoded PEM (avoids multiline .env issues)
        cert_b64 = os.getenv("MICROSOFT_SIGNING_CERTIFICATE_BASE64")
        if cert_b64:
            try:
                return base64.b64decode(cert_b64).decode("utf-8")
            except Exception as e:
                raise RuntimeError(f"Failed to decode MICROSOFT_SIGNING_CERTIFICATE_BASE64: {e}")
        
        return None

    def _detect_auth_method(self) -> str:
        """Detect which authentication method is being used."""
        if os.getenv("MICROSOFT_CERTIFICATE_ID") and self._get_certificate_pem():
            return "certificate"
        elif os.getenv("MS_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET_KEY"):
            return "client_secret"
        else:
            return "unknown"

    def _ensure_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp - 60:
            return self._token["access_token"]
        
        scopes = ["https://graph.microsoft.com/.default"]
        token = self._msal_app.acquire_token_for_client(scopes=scopes)
        
        if not token or not token.get("access_token"):
            error_msg = f"MSAL token acquisition failed using {self._auth_method} auth"
            
            # Enhanced error messages for common issues
            if token and "error" in token:
                error_code = token.get("error")
                error_desc = token.get("error_description", "")
                
                if error_code == "invalid_client":
                    if "AADSTS7000215" in error_desc:
                        error_msg += (
                            "\n\nAADSTS7000215: Invalid client secret provided.\n"
                            "This usually means:\n"
                            "1. You're using the client secret ID instead of the client secret VALUE\n"
                            "2. The secret has expired\n"
                            "3. Check Azure Portal > App Registrations > Your App > Certificates & secrets\n"
                            "   Use the 'Value' column, not the 'Secret ID' column"
                        )
                    elif "certificate" in error_desc.lower():
                        error_msg += (
                            "\n\nCertificate authentication failed.\n"
                            "Verify:\n"
                            "1. MICROSOFT_CERTIFICATE_ID matches the certificate thumbprint in Azure\n"
                            "2. MICROSOFT_SIGNING_CERTIFICATE contains the full PEM private key\n"
                            "3. Certificate is uploaded and enabled in Azure Portal"
                        )
                    else:
                        error_msg += f"\n\nClient authentication failed: {error_desc}"
                        
                elif error_code == "unauthorized_client":
                    error_msg += (
                        "\n\nApplication not authorized for client credentials flow.\n"
                        "Required Azure AD configuration:\n"
                        "1. Application permissions (not delegated): User.Read.All, Group.Read.All, Files.Read.All\n"
                        "2. Admin consent granted for these permissions\n"
                        "3. Application ID URI configured if needed"
                    )
                else:
                    error_msg += f"\n\nError: {error_code}\nDescription: {error_desc}"
            
            error_msg += f"\n\nFull response: {token}"
            raise RuntimeError(error_msg)
        
        self._token = token
        self._token_exp = now + float(token.get("expires_in", 3600))
        
        # Log successful authentication for debugging
        print(f"✅ Microsoft Graph authenticated using {self._auth_method} method")
        return token["access_token"]

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        token = self._ensure_token()
        url = f"{self.GRAPH_BASE}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    # --------- Convenience APIs ---------

    async def list_users(self, top: int = 5) -> Dict[str, Any]:
        return await self._get("/users", params={"$top": str(top)})

    async def list_teams(self, top: int = 5) -> Dict[str, Any]:
        # Teams listing via groups endpoint (teams are backed by groups)
        # Requires app permission: Team.ReadBasic.All or Group.Read.All
        return await self._get("/groups", params={"$top": str(top), "$select": "id,displayName,resourceProvisioningOptions"})

    async def drive_root(self) -> Dict[str, Any]:
        # Root drive (SharePoint default site), requires Files.Read.All / Sites.Read.All (app)
        return await self._get("/sites/root/drive")
