"""API route handlers for Smart Heating."""
from .areas import AreasHandler
from .devices import DevicesHandler
from .schedules import SchedulesHandler
from .config import ConfigHandler
from .history import HistoryHandler
from .safety import SafetyHandler
from .sensors import SensorsHandler

__all__ = [
    "AreasHandler",
    "DevicesHandler",
    "SchedulesHandler",
    "ConfigHandler",
    "HistoryHandler",
    "SafetyHandler",
    "SensorsHandler",
]
