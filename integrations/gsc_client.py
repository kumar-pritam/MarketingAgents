from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    GOOGLE_DEPS_AVAILABLE = True
except ImportError:
    Request = None  # type: ignore[assignment]
    Credentials = None  # type: ignore[assignment]
    InstalledAppFlow = None  # type: ignore[assignment]
    build = None  # type: ignore[assignment]
    GOOGLE_DEPS_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
INTEGRATIONS_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = INTEGRATIONS_DIR / "credentials.json"
TOKEN_FILE = INTEGRATIONS_DIR / "token.json"


@dataclass(slots=True)
class GSCStatus:
    connected: bool
    message: str


def _load_credentials() -> Credentials | None:
    if not GOOGLE_DEPS_AVAILABLE:
        return None
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    if creds and creds.valid:
        return creds
    return None


def authenticate_gsc() -> tuple[bool, str]:
    if not GOOGLE_DEPS_AVAILABLE:
        return (
            False,
            "Google auth libraries are not installed. Run: pip install google-auth-oauthlib google-api-python-client",
        )
    if not CREDENTIALS_FILE.exists():
        return False, (
            "Missing integrations/credentials.json. Create OAuth Desktop credentials in Google Cloud "
            "and place the file there."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return True, "Google Search Console connected successfully."


def get_gsc_status() -> GSCStatus:
    if not GOOGLE_DEPS_AVAILABLE:
        return GSCStatus(
            connected=False,
            message="Google libraries missing. Install requirements.txt to enable GSC.",
        )
    if not CREDENTIALS_FILE.exists():
        return GSCStatus(
            connected=False,
            message="GSC not configured. Add OAuth Desktop credentials at integrations/credentials.json.",
        )

    creds = _load_credentials()
    if not creds:
        return GSCStatus(
            connected=False,
            message="GSC credentials found, but not authenticated yet. Click Connect Google Search Console.",
        )

    return GSCStatus(connected=True, message="Google Search Console is connected.")


def _get_service():
    if not GOOGLE_DEPS_AVAILABLE:
        raise RuntimeError("Google libraries are missing. Install requirements.txt to use GSC.")
    creds = _load_credentials()
    if not creds:
        raise RuntimeError("GSC is not authenticated. Connect your Google account first.")
    return build("searchconsole", "v1", credentials=creds)


def list_gsc_properties() -> list[str]:
    service = _get_service()
    response = service.sites().list().execute()
    entries = response.get("siteEntry", [])
    return [
        item["siteUrl"]
        for item in entries
        if item.get("permissionLevel") not in {"siteUnverifiedUser"} and item.get("siteUrl")
    ]


def fetch_top_queries(site_url: str, days: int = 30, row_limit: int = 20) -> list[dict[str, str | int | float]]:
    service = _get_service()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    request = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query"],
        "rowLimit": row_limit,
        "startRow": 0,
    }

    response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
    rows = response.get("rows", [])
    output: list[dict[str, str | int | float]] = []
    for row in rows:
        keys = row.get("keys", [])
        output.append(
            {
                "query": keys[0] if keys else "",
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0.0),
                "position": row.get("position", 0.0),
            }
        )
    return output
