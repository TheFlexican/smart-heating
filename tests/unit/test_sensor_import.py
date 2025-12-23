"""Smoke test to ensure sensor module imports correctly (covers simple stub)."""

import importlib


def test_import_sensor_module():
    mod = importlib.import_module("smart_heating.sensor")
    assert mod is not None
