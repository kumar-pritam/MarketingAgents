from __future__ import annotations

import json
import socket
from contextlib import closing
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.schemas.common import IntegrationStatus
from app.storage.repository import repo, utc_now_iso

router = APIRouter(prefix="/integrations", tags=["integrations"])
SUPPORTED_PROVIDERS = {"ga4", "google_ads", "gsc"}

INTEGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "integrations"


class IntegrationConnectRequest(BaseModel):
    workspace_id: str
    provider: str
    enabled: bool = True
    scopes: list[str] = Field(default_factory=list)
    auth_metadata: dict[str, str] = Field(default_factory=dict)


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.listen(1)
        return s.getsockname()[1]


@router.get("/auth-url/{provider}")
def get_auth_url(provider: str) -> dict[str, str]:
    if provider not in {"gsc", "ga4"}:
        raise HTTPException(
            status_code=400, detail=f"OAuth not supported for provider: {provider}"
        )

    try:
        if provider == "gsc":
            from integrations import gsc_client

            scopes = gsc_client.SCOPES
            credentials_file = gsc_client.CREDENTIALS_FILE
            token_file = gsc_client.TOKEN_FILE
        elif provider == "ga4":
            from integrations import ga4_client

            scopes = ga4_client.SCOPES
            credentials_file = ga4_client.CREDENTIALS_FILE
            token_file = ga4_client.TOKEN_FILE
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    except ImportError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to import integration client: {str(e)}"
        )

    if not credentials_file.exists():
        raise HTTPException(
            status_code=400,
            detail="OAuth credentials not configured. Please add credentials.json to the integrations folder.",
        )

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes)
        port = _find_free_port()
        redirect_uri = f"http://localhost:{port}/"
        flow.redirect_uri = redirect_uri

        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

        return {
            "auth_url": auth_url,
            "redirect_uri": redirect_uri,
            "provider": provider,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate auth URL: {str(e)}"
        )


@router.get("/callback/{provider}")
def oauth_callback(
    provider: str, code: str = None, error: str = None
) -> dict[str, Any]:
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        if provider == "gsc":
            from integrations import gsc_client

            scopes = gsc_client.SCOPES
            credentials_file = gsc_client.CREDENTIALS_FILE
            token_file = gsc_client.TOKEN_FILE
        elif provider == "ga4":
            from integrations import ga4_client

            scopes = ga4_client.SCOPES
            credentials_file = ga4_client.CREDENTIALS_FILE
            token_file = ga4_client.TOKEN_FILE
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    except ImportError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to import integration client: {str(e)}"
        )

    if not credentials_file.exists():
        raise HTTPException(status_code=400, detail="OAuth credentials not configured")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes)
        flow.redirect_uri = "postmessage"
        credentials = flow.fetch_token(code=code)

        if token_file.parent.exists():
            token_file.write_text(json.dumps(credentials, indent=2), encoding="utf-8")

        return {
            "success": True,
            "provider": provider,
            "message": f"{provider.upper()} connected successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to complete OAuth: {str(e)}"
        )


@router.get("/status/{provider}")
def get_integration_status(provider: str) -> dict[str, Any]:
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    try:
        if provider == "gsc":
            from integrations import gsc_client

            status = gsc_client.get_gsc_status()
            return {
                "provider": provider,
                "connected": status.connected,
                "message": status.message,
            }
        elif provider == "ga4":
            from integrations import ga4_client

            status = ga4_client.get_ga4_status()
            return {
                "provider": provider,
                "connected": status.connected,
                "message": status.message,
            }
        else:
            return {
                "provider": provider,
                "connected": False,
                "message": "Integration not yet implemented",
            }
    except ImportError as e:
        return {
            "provider": provider,
            "connected": False,
            "message": f"Integration module not available: {str(e)}",
        }


@router.post("/connect", response_model=IntegrationStatus)
def connect(req: IntegrationConnectRequest) -> IntegrationStatus:
    if req.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400, detail=f"Unsupported provider: {req.provider}"
        )

    connected = req.enabled

    if req.enabled:
        try:
            if req.provider == "gsc":
                from integrations import gsc_client

                status = gsc_client.get_gsc_status()
                connected = status.connected
            elif req.provider == "ga4":
                from integrations import ga4_client

                status = ga4_client.get_ga4_status()
                connected = status.connected
        except ImportError:
            pass

    status = {
        "provider": req.provider,
        "connected": connected,
        "scopes": req.scopes if connected else [],
        "connected_at": utc_now_iso() if connected else None,
    }
    repo.set_integration(req.workspace_id, req.provider, status)
    return IntegrationStatus(**status)


@router.get("/{workspace_id}", response_model=list[IntegrationStatus])
def list_integrations(workspace_id: str) -> list[IntegrationStatus]:
    statuses = repo.get_integrations(workspace_id)
    return [IntegrationStatus(**item) for item in statuses.values()]
