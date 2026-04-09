from __future__ import annotations

import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", "-")
        extra = getattr(record, "extra_data", {})
        
        base = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {record.levelname:8} | {record.name} | {record.getMessage()}"
        
        if request_id != "-":
            base = f"{base} | Request ID: {request_id}"
        
        if extra:
            base = f"{base} | Extra: {json.dumps(extra)}"
        
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        
        return base


def configure_logging(use_json: bool = False) -> Path:
    root = Path(__file__).resolve().parents[2]
    log_dir = root / "data" / "server_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "backend.log"

    logger = logging.getLogger()
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    logger.setLevel(logging.DEBUG)
    
    if use_json:
        file_formatter = JSONFormatter()
        console_formatter = JSONFormatter()
    else:
        file_formatter = HumanReadableFormatter()
        console_formatter = HumanReadableFormatter()
    
    fh = RotatingFileHandler(
        log_file, 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3, 
        encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_formatter)
    
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(console_formatter)
    
    logger.addHandler(fh)
    logger.addHandler(sh)
    
    logger.info(f"Logging initialized (JSON mode: {use_json})")
    
    return log_file


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
