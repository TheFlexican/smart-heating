"""Tests for efficiency API handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp.test_utils import make_mocked_request
from smart_heating.api.handlers.efficiency import (
    handle_get_area_efficiency_history,
    handle_get_efficiency_report,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    return MagicMock()


@pytest.fixture
def mock_area_manager():
    """Create a mock AreaManager."""
    manager = MagicMock()
    manager.get_all_areas.return_value = {}
    return manager


@pytest.fixture
def mock_efficiency_calculator():
    """Create a mock EfficiencyCalculator."""
    calculator = MagicMock()

    # Mock single area efficiency response
    calculator.calculate_area_efficiency = AsyncMock(
        return_value={
            "area_id": "test_area",
            "period": "week",
            "start_time": "2025-12-02T00:00:00",
            "end_time": "2025-12-09T00:00:00",
            "energy_score": 75.0,
            "heating_time_percentage": 45.0,
            "heating_cycles": 8,
            "average_temperature_delta": 1.2,
            "temperature_stability": 0.8,
            "data_points": 100,
            "recommendations": ["System is operating efficiently."],
        }
    )

    # Mock all areas efficiency response
    calculator.calculate_all_areas_efficiency = AsyncMock(
        return_value=[
            {
                "area_id": "area_1",
                "period": "week",
                "start_time": "2025-12-02T00:00:00",
                "end_time": "2025-12-09T00:00:00",
                "energy_score": 80.0,
                "heating_time_percentage": 40.0,
                "heating_cycles": 5,
                "average_temperature_delta": 1.0,
                "temperature_stability": 0.9,
                "data_points": 100,
                "recommendations": ["Good efficiency."],
            },
            {
                "area_id": "area_2",
                "period": "week",
                "start_time": "2025-12-02T00:00:00",
                "end_time": "2025-12-09T00:00:00",
                "energy_score": 60.0,
                "heating_time_percentage": 65.0,
                "heating_cycles": 12,
                "average_temperature_delta": 2.5,
                "temperature_stability": 0.6,
                "data_points": 100,
                "recommendations": ["Consider improving insulation."],
            },
        ]
    )

    return calculator


@pytest.mark.asyncio
async def test_handle_get_efficiency_report_single_area(
    mock_hass, mock_area_manager, mock_efficiency_calculator
):
    """Test getting efficiency report for a single area."""
    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/all_areas?area_id=test_area&period=week",
    )

    response = await handle_get_efficiency_report(
        mock_hass, mock_area_manager, mock_efficiency_calculator, request
    )

    assert response.status == 200
    data = response.body

    # Verify response structure matches TypeScript interface
    assert b"area_id" in data
    assert b"period" in data
    assert b"metrics" in data
    assert b"recommendations" in data
    assert b"energy_score" in data  # Inside metrics
    assert b"heating_time_percentage" in data

    mock_efficiency_calculator.calculate_area_efficiency.assert_called_once_with(
        "test_area", "week"
    )


@pytest.mark.asyncio
async def test_handle_get_efficiency_report_all_areas(
    mock_hass, mock_area_manager, mock_efficiency_calculator
):
    """Test getting efficiency report for all areas."""
    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/all_areas?period=week",
    )

    response = await handle_get_efficiency_report(
        mock_hass, mock_area_manager, mock_efficiency_calculator, request
    )

    assert response.status == 200
    data = response.body

    # Verify response structure
    assert b"period" in data
    assert b"summary_metrics" in data
    assert b"area_reports" in data
    assert b"recommendations" in data
    assert b"energy_score" in data  # In summary_metrics

    mock_efficiency_calculator.calculate_all_areas_efficiency.assert_called_once_with(
        mock_area_manager, "week"
    )


@pytest.mark.asyncio
async def test_handle_get_efficiency_report_default_period(
    mock_hass, mock_area_manager, mock_efficiency_calculator
):
    """Test getting efficiency report with default period."""
    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/all_areas",
    )

    response = await handle_get_efficiency_report(
        mock_hass, mock_area_manager, mock_efficiency_calculator, request
    )

    assert response.status == 200

    # Should use default period "day"
    mock_efficiency_calculator.calculate_all_areas_efficiency.assert_called_once_with(
        mock_area_manager, "day"
    )


@pytest.mark.asyncio
async def test_handle_get_efficiency_report_response_structure(
    mock_hass, mock_area_manager, mock_efficiency_calculator
):
    """Test that response structure matches frontend expectations."""
    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/all_areas?period=week",
    )

    response = await handle_get_efficiency_report(
        mock_hass, mock_area_manager, mock_efficiency_calculator, request
    )

    import json

    data = json.loads(response.body.decode())

    # Verify top-level structure
    assert "period" in data
    assert "summary_metrics" in data
    assert "area_reports" in data
    assert "recommendations" in data

    # Verify summary_metrics structure
    assert "energy_score" in data["summary_metrics"]
    assert "heating_time_percentage" in data["summary_metrics"]
    assert "heating_cycles" in data["summary_metrics"]
    assert "avg_temp_delta" in data["summary_metrics"]

    # Verify area_reports structure
    assert len(data["area_reports"]) == 2
    for report in data["area_reports"]:
        assert "area_id" in report
        assert "period" in report
        assert "metrics" in report
        assert "recommendations" in report

        # Verify nested metrics structure
        assert "energy_score" in report["metrics"]
        assert "heating_time_percentage" in report["metrics"]
        assert "heating_cycles" in report["metrics"]
        assert "avg_temp_delta" in report["metrics"]


@pytest.mark.asyncio
async def test_handle_get_efficiency_report_error_handling(
    mock_hass, mock_area_manager, mock_efficiency_calculator
):
    """Test error handling in efficiency report."""
    mock_efficiency_calculator.calculate_all_areas_efficiency.side_effect = Exception("Test error")

    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/all_areas?period=week",
    )

    response = await handle_get_efficiency_report(
        mock_hass, mock_area_manager, mock_efficiency_calculator, request
    )

    assert response.status == 500
    data = response.body
    assert b"error" in data


@pytest.mark.asyncio
async def test_handle_get_efficiency_report_low_efficiency(
    mock_hass, mock_area_manager, mock_efficiency_calculator
):
    """Test summary recommendations when efficiency is low and heating time high."""
    # Prepare a low efficiency response
    mock_efficiency_calculator.calculate_all_areas_efficiency = AsyncMock(
        return_value=[
            {
                "area_id": "area_low",
                "period": "week",
                "start_time": "2025-12-02T00:00:00",
                "end_time": "2025-12-09T00:00:00",
                "energy_score": 30.0,
                "heating_time_percentage": 70.0,
                "heating_cycles": 10,
                "average_temperature_delta": 3.0,
                "recommendations": ["Low efficiency."],
            }
        ]
    )

    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/all_areas?period=week",
    )

    response = await handle_get_efficiency_report(
        mock_hass, mock_area_manager, mock_efficiency_calculator, request
    )

    assert response.status == 200
    import json

    data = json.loads(response.body.decode())
    assert "Overall efficiency is low" in " ".join(data["recommendations"]) or any(
        "heating time is high" in s for s in data["recommendations"]
    )


@pytest.mark.asyncio
async def test_handle_get_efficiency_report_no_areas(
    mock_hass, mock_area_manager, mock_efficiency_calculator
):
    """Test all-areas report with no data returns default summary and recommendations."""
    mock_efficiency_calculator.calculate_all_areas_efficiency = AsyncMock(return_value=[])

    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/all_areas?period=week",
    )

    response = await handle_get_efficiency_report(
        mock_hass, mock_area_manager, mock_efficiency_calculator, request
    )

    assert response.status == 200
    import json

    data = json.loads(response.body.decode())
    assert data["summary_metrics"]["energy_score"] == 0
    assert data["recommendations"] == ["No area data available."]


@pytest.mark.asyncio
async def test_handle_get_area_efficiency_history(mock_hass, mock_efficiency_calculator):
    """Test getting efficiency history for an area."""
    mock_efficiency_calculator.calculate_area_efficiency = AsyncMock(
        return_value={
            "area_id": "test_area",
            "period": "day",
            "start_time": "2025-12-08T00:00:00",
            "end_time": "2025-12-09T00:00:00",
            "energy_score": 75.0,
            "heating_time_percentage": 45.0,
            "heating_cycles": 8,
            "average_temperature_delta": 1.2,
            "temperature_stability": 0.8,
            "data_points": 100,
            "recommendations": ["System is operating efficiently."],
        }
    )

    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/history/test_area?periods=7&period_type=day",
    )

    response = await handle_get_area_efficiency_history(
        mock_hass, mock_efficiency_calculator, request, "test_area"
    )

    assert response.status == 200
    data = response.body
    assert b"history" in data

    # Should call calculate_area_efficiency for each period (7 times)
    assert mock_efficiency_calculator.calculate_area_efficiency.call_count == 7


@pytest.mark.asyncio
async def test_handle_get_area_efficiency_history_default_params(
    mock_hass, mock_efficiency_calculator
):
    """Test getting efficiency history with default parameters."""
    mock_efficiency_calculator.calculate_area_efficiency = AsyncMock(
        return_value={
            "area_id": "test_area",
            "period": "day",
            "energy_score": 75.0,
            "heating_time_percentage": 45.0,
            "heating_cycles": 8,
            "average_temperature_delta": 1.2,
            "recommendations": [],
        }
    )

    request = make_mocked_request(
        "GET",
        "/api/smart_heating/efficiency/history/test_area",
    )

    response = await handle_get_area_efficiency_history(
        mock_hass, mock_efficiency_calculator, request, "test_area"
    )

    assert response.status == 200

    # Should use default: 7 periods of type "day"
    assert mock_efficiency_calculator.calculate_area_efficiency.call_count == 7
