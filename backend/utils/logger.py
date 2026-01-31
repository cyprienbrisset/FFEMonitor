"""
Configuration du système de logging pour EngageWatch.
"""

import logging
import sys
from datetime import datetime


def setup_logger(name: str = "engagewatch", level: str = "INFO") -> logging.Logger:
    """
    Configure et retourne un logger formaté.

    Args:
        name: Nom du logger
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)

    # Éviter les doublons de handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Format du log
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Retourne un logger enfant pour un module spécifique.

    Args:
        module_name: Nom du module (ex: "auth", "surveillance")

    Returns:
        Logger configuré
    """
    return logging.getLogger(f"engagewatch.{module_name}")
