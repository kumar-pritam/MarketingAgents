from __future__ import annotations

import json
import logging
import os
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import certifi  # type: ignore
except ImportError:  # pragma: no cover
    certifi = None

from app.core.config import settings

LOGGER = logging.getLogger("app.llm.openrouter")


def _resolve_api_key() -> str | None:
    return (
        settings.openrouter_api_key
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPEN_ROUTER_API_KEY")
    )


def _build_ssl_context() -> ssl.SSLContext:
    if not settings.openrouter_ssl_verify:
        LOGGER.warning("OPENROUTER_SSL_VERIFY is disabled. This is insecure and should be used only for local debugging.")
        return ssl._create_unverified_context()

    cafile = settings.openrouter_ca_bundle
    if not cafile and certifi is not None:
        cafile = certifi.where()
    if cafile:
        return ssl.create_default_context(cafile=cafile)
    # Fallback to OS/Python default trust store if certifi is unavailable.
    return ssl.create_default_context()


def _call_openrouter_http(request: Request) -> str:
    with urlopen(request, timeout=60, context=_build_ssl_context()) as response:
        return response.read().decode("utf-8")


def _extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "\n".join(parts)
    return str(content)


def call_openrouter(messages: list[dict[str, str]], *, temperature: float = 0.4, max_tokens: int = 1200) -> str:
    api_key = _resolve_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    endpoint = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    body = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    encoded = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "MarketingAgents",
    }
    request = Request(endpoint, data=encoded, headers=headers, method="POST")
    LOGGER.debug("OPENROUTER_REQUEST model=%s endpoint=%s body=%s", settings.openrouter_model, endpoint, body)
    try:
        raw = _call_openrouter_http(request)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        LOGGER.exception("OPENROUTER_HTTP_ERROR status=%s detail=%s", exc.code, detail)
        raise RuntimeError(f"OpenRouter HTTP error: {exc.code}") from exc
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            if settings.app_env == "development" and settings.openrouter_dev_insecure_fallback:
                LOGGER.warning("OPENROUTER_SSL_VERIFY_FAILED error=%s", exc)
                LOGGER.warning(
                    "OPENROUTER_SSL_DEV_FALLBACK enabled. Retrying without certificate verification for local development."
                )
                try:
                    with urlopen(request, timeout=60, context=ssl._create_unverified_context()) as response:
                        raw = response.read().decode("utf-8")
                    payload = json.loads(raw)
                    text = _extract_text(payload)
                    LOGGER.debug("OPENROUTER_RESPONSE text=%s", text)
                    return text
                except Exception as retry_exc:
                    LOGGER.exception("OPENROUTER_SSL_DEV_FALLBACK_FAILED error=%s", retry_exc)
            raise RuntimeError(
                "OpenRouter SSL certificate verification failed. "
                "Install/update certifi, or set OPENROUTER_CA_BUNDLE to a valid CA bundle path."
            ) from exc
        LOGGER.exception("OPENROUTER_NETWORK_ERROR error=%s", exc)
        raise RuntimeError("OpenRouter network error.") from exc

    payload = json.loads(raw)
    text = _extract_text(payload)
    LOGGER.debug("OPENROUTER_RESPONSE text=%s", text)
    return text
