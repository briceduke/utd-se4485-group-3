from __future__ import annotations
import logging, os, time
from dataclasses import dataclass
from logging.handlers import SysLogHandler

_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR":    logging.ERROR,
    "WARNING":  logging.WARNING,
    "INFO":     logging.INFO,
    "DEBUG":    logging.DEBUG,
}

@dataclass(frozen=True)
class LogConfig:
    name: str = "downloader"
    level: str = "INFO"              
    log_file: str | None = None      
    to_syslog: bool = False
    to_console: bool = True           
def _fmt() -> logging.Formatter:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s",
                            "%Y-%m-%dT%H:%M:%SZ")
    fmt.converter = time.gmtime  # UTC timestamps
    return fmt

def get_logger(cfg: LogConfig) -> logging.Logger:
    logger = logging.getLogger(cfg.name)
    if getattr(logger, "_initialized_ok", False):
        return logger
    logger.setLevel(_LEVELS.get(cfg.level.upper(), logging.INFO))
    fmt = _fmt()

    if cfg.log_file:
        os.makedirs(os.path.dirname(os.path.abspath(cfg.log_file)), exist_ok=True)
        fh = logging.FileHandler(cfg.log_file)
        fh.setFormatter(fmt)
        fh.setLevel(logger.level)
        logger.addHandler(fh)

    if cfg.to_syslog:
        try:
            sh = SysLogHandler(address="/dev/log")
            sh.setFormatter(fmt)
            sh.setLevel(logger.level)
            logger.addHandler(sh)
        except Exception:
            pass  

    if cfg.to_console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logger.level)
        logger.addHandler(ch)

    logger.propagate = False
    setattr(logger, "_initialized_ok", True)
    return logger
