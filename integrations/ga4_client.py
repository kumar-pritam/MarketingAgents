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

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
]

INTEGRATIONS_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = INTEGRATIONS_DIR / "credentials.json"
TOKEN_FILE = INTEGRATIONS_DIR / "ga4_token.json"


@dataclass(slots=True)
class GA4Status:
    connected: bool
    message: str
    account_id: str | None = None
    property_id: str | None = None


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


def authenticate_ga4() -> tuple[bool, str]:
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
    return True, "Google Analytics 4 connected successfully."


def get_ga4_status() -> GA4Status:
    if not GOOGLE_DEPS_AVAILABLE:
        return GA4Status(
            connected=False,
            message="Google libraries missing. Install requirements.txt to enable GA4.",
        )
    if not CREDENTIALS_FILE.exists():
        return GA4Status(
            connected=False,
            message="GA4 not configured. Add OAuth Desktop credentials at integrations/credentials.json.",
        )

    creds = _load_credentials()
    if not creds:
        return GA4Status(
            connected=False,
            message="GA4 credentials found, but not authenticated yet. Click Connect Google Analytics.",
        )

    return GA4Status(connected=True, message="Google Analytics 4 is connected.")


def _get_service():
    if not GOOGLE_DEPS_AVAILABLE:
        raise RuntimeError(
            "Google libraries are missing. Install requirements.txt to use GA4."
        )
    creds = _load_credentials()
    if not creds:
        raise RuntimeError(
            "GA4 is not authenticated. Connect your Google account first."
        )
    return build("analyticsdata", "v2beta", credentials=creds)


def _get_analytics_admin_service():
    if not GOOGLE_DEPS_AVAILABLE:
        raise RuntimeError(
            "Google libraries are missing. Install requirements.txt to use GA4."
        )
    creds = _load_credentials()
    if not creds:
        raise RuntimeError(
            "GA4 is not authenticated. Connect your Google account first."
        )
    return build("analyticsadmin", "v1beta", credentials=creds)


def list_ga4_properties() -> list[dict[str, str]]:
    service = _get_analytics_admin_service()

    accounts = []
    next_page_token = None
    while True:
        request = service.accountSummaries().list(
            pageToken=next_page_token, pageSize=200
        )
        response = request.execute()

        for account in response.get("accountSummaries", []):
            for property_summary in account.get("propertySummaries", []):
                property_id = property_summary.get("property")
                if property_id.startswith("properties/"):
                    property_id = property_id.replace("properties/", "")
                accounts.append(
                    {
                        "account_id": account.get("account", "").replace(
                            "accounts/", ""
                        ),
                        "account_name": account.get("displayName", ""),
                        "property_id": property_id,
                        "property_name": property_summary.get("displayName", ""),
                        "property_uri": property_summary.get("property"),
                    }
                )

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return accounts


def fetch_ga4_realtime_data(property_id: str) -> dict:
    service = _get_service()

    try:
        response = (
            service.properties()
            .runRealtimeReport(
                property=f"properties/{property_id}",
                body={
                    "metrics": [
                        {"name": "activeUsers"},
                        {"name": "screenPageViews"},
                        {"eventCount": "user_engagement"},
                    ],
                    "dimensions": [
                        {"name": "unifiedPageScreen"},
                        {"name": "city"},
                    ],
                },
            )
            .execute()
        )

        rows = response.get("rows", [])
        return {
            "active_users": sum(
                int(row["metricValues"][0]["value"])
                for row in rows
                if row["dimensionValues"]
            ),
            "top_pages": [
                {
                    "page": row["dimensionValues"][0]["value"],
                    "city": row["dimensionValues"][1]["value"],
                    "active_users": int(row["metricValues"][0]["value"]),
                }
                for row in rows[:10]
            ],
            "total_events": sum(
                int(row["metricValues"][2]["value"])
                for row in rows
                if row["metricValues"]
            ),
        }
    except Exception as e:
        return {"error": str(e), "active_users": 0, "top_pages": [], "total_events": 0}


def fetch_ga4_reports(
    property_id: str,
    start_date: str = None,
    end_date: str = None,
    dimensions: list[str] = None,
    metrics: list[str] = None,
    days: int = 30,
    row_limit: int = 1000,
) -> dict:
    if start_date is None:
        start_date = (date.today() - timedelta(days=days)).isoformat()
    if end_date is None:
        end_date = date.today().isoformat()

    if dimensions is None:
        dimensions = ["country", "deviceCategory", "sessionDefaultChannelGrouping"]

    if metrics is None:
        metrics = [
            "sessions",
            "totalUsers",
            "newUsers",
            "bounceRate",
            "averageSessionDuration",
            "screenPageViews",
            "engagementRate",
        ]

    service = _get_service()

    try:
        request_body = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": dim} for dim in dimensions],
            "metrics": [{"name": metric} for metric in metrics],
            "limit": row_limit,
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        }

        response = (
            service.properties()
            .runReport(
                property=f"properties/{property_id}",
                body=request_body,
            )
            .execute()
        )

        rows = response.get("rows", [])
        dimension_headers = [d["name"] for d in response.get("dimensionHeaders", [])]
        metric_headers = [m["name"] for m in response.get("metricHeaders", [])]

        data = []
        for row in rows:
            dimension_values = [dv["value"] for dv in row.get("dimensionValues", [])]
            metric_values = [mv["value"] for mv in row.get("metricValues", [])]

            record = {}
            for i, dim in enumerate(dimension_headers):
                record[dim] = dimension_values[i] if i < len(dimension_values) else ""
            for i, metric in enumerate(metric_headers):
                try:
                    record[metric] = (
                        float(metric_values[i]) if i < len(metric_values) else 0
                    )
                except (ValueError, IndexError):
                    record[metric] = 0
            data.append(record)

        return {
            "rows": data,
            "row_count": len(data),
            "totals": response.get("totals", []),
            "metadata": {
                "property_id": property_id,
                "start_date": start_date,
                "end_date": end_date,
                "dimensions": dimensions,
                "metrics": metrics,
            },
        }
    except Exception as e:
        return {"error": str(e), "rows": [], "row_count": 0}


def fetch_ga4_traffic_sources(property_id: str, days: int = 30) -> dict:
    return fetch_ga4_reports(
        property_id=property_id,
        dimensions=["sessionSource", "sessionMedium", "sessionCampaign"],
        metrics=["sessions", "totalUsers", "bounceRate", "averageSessionDuration"],
        days=days,
    )


def fetch_ga4_top_pages(property_id: str, days: int = 30, limit: int = 20) -> dict:
    return fetch_ga4_reports(
        property_id=property_id,
        dimensions=["pagePath", "pageTitle"],
        metrics=[
            "screenPageViews",
            "totalUsers",
            "averageSessionDuration",
            "bounceRate",
            "engagementRate",
        ],
        days=days,
        row_limit=limit,
    )


def fetch_ga4_user_demographics(property_id: str, days: int = 30) -> dict:
    return fetch_ga4_reports(
        property_id=property_id,
        dimensions=["userAgeBracket", "userGender"],
        metrics=["totalUsers", "newUsers", "sessions"],
        days=days,
    )


def fetch_ga4_conversions(property_id: str, days: int = 30) -> dict:
    return fetch_ga4_reports(
        property_id=property_id,
        dimensions=["sessionDefaultChannelGrouping"],
        metrics=["conversions", "totalConversionRevenue"],
        days=days,
    )
