from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_APP_ROOT = Path(__file__).resolve().parents[1]
_LOG_DIR = _APP_ROOT / "data" / "server_logs"
_LOG_FILE = _LOG_DIR / "server.log"


def setup_server_logging(level: int = logging.INFO) -> Path:
    """Configure process-wide logging once and return log file path."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    if any(getattr(h, "name", "") == "marketngagents_server_file" for h in root.handlers):
        return _LOG_FILE

    root.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.name = "marketngagents_server_file"
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.name = "marketngagents_server_console"
    root.addHandler(console_handler)

    return _LOG_FILE


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
