from __future__ import annotations
import logging
import logging.handlers
import os
import sys
from pathlib import Path

def _level_from_str(level: str | None) -> int:
    if not level:
        return logging.INFO
    return getattr(logging, str(level).upper(), logging.INFO)

def get_logger(level: str | None = None, file: str | None = None) -> logging.Logger:
    log = logging.getLogger("deployer")
    lvl = _level_from_str(level)
    log.setLevel(lvl)

    if log.handlers:
        for h in log.handlers:
            h.setLevel(lvl)
        return log

    fmt = logging.Formatter("[%(levelname)s] %(message)s")

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(lvl)
    sh.setFormatter(fmt)
    log.addHandler(sh)

    if file:
        try:
            p = Path(file)
            p.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(p)
            fh.setLevel(lvl)
            fh.setFormatter(fmt)
            log.addHandler(fh)
        except Exception:
            pass

    if os.path.exists("/dev/log"):
        try:
            syslog = logging.handlers.SysLogHandler(address="/dev/log")
            syslog.setLevel(lvl)
            syslog.setFormatter(logging.Formatter("deployer: %(levelname)s %(message)s"))
            log.addHandler(syslog)
        except Exception:
            pass

    return log
