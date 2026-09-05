"""
Logger de métricas de uso local (OBS-01).
Escribe eventos en logs/usage.log sin envío externo.

Uso:
    from core.usage_logger import usage_log
    usage_log("NAV", section="Calendario")
    usage_log("GEN_CPSAT", resultado="ok", tiempo=12.3, guardias=45)
"""

import logging
from typing import Any

from core.paths import get_logs_directory

_logger: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logs_dir = get_logs_directory()
    logs_dir.mkdir(parents=True, exist_ok=True)

    log = logging.getLogger("usage")
    log.setLevel(logging.INFO)
    log.propagate = False

    if not log.handlers:
        handler = logging.FileHandler(logs_dir / "usage.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))
        log.addHandler(handler)

    _logger = log
    return _logger


def usage_log(event: str, **kwargs: Any) -> None:
    try:
        parts = [event] + [f"{k}={v}" for k, v in kwargs.items()]
        _get_logger().info(" | ".join(parts))
    except Exception:
        pass
