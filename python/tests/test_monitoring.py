"""Tests for monitoring functionality."""

import pytest
import asyncio
from datetime import datetime, timedelta
from monitoring import measure_performance, PerformanceMetrics
from unittest.mock import patch, Mock


@pytest.mark.asyncio
async def test_measure_performance_decorator():
    """Test the measure_performance decorator with a successful function."""
    mock_logger = Mock()

    with patch("monitoring.logger", mock_logger):

        @measure_performance
        async def test_function():
            await asyncio.sleep(0.1)
            return "success"

        result = await test_function()

        assert result == "success"
        assert mock_logger.info.called
        log_message = mock_logger.info.call_args[0][0]
        assert "test_function succeeded" in log_message
        assert "Duration:" in log_message


@pytest.mark.asyncio
async def test_measure_performance_with_error():
    """Test the measure_performance decorator with a failing function."""
    mock_logger = Mock()

    with patch("monitoring.logger", mock_logger):

        @measure_performance
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

        assert mock_logger.error.called
        log_message = mock_logger.error.call_args[0][0]
        assert "failing_function failed with error: Test error" in log_message


def test_performance_metrics_creation():
    """Test creation of PerformanceMetrics object."""
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=1)
    duration = timedelta(seconds=1)

    metrics = PerformanceMetrics(
        function_name="test_func",
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        success=True,
    )

    assert metrics.function_name == "test_func"
    assert metrics.start_time == start_time
    assert metrics.end_time == end_time
    assert metrics.duration == duration
    assert metrics.success is True
    assert metrics.error is None


def test_performance_metrics_with_error():
    """Test PerformanceMetrics with error information."""
    error = ValueError("Test error")
    metrics = PerformanceMetrics(
        function_name="test_func",
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration=timedelta(seconds=1),
        success=False,
        error=error,
    )

    assert metrics.success is False
    assert metrics.error == error


@pytest.mark.asyncio
async def test_measure_performance_concurrent_calls():
    """Test measure_performance with concurrent function calls."""
    mock_logger = Mock()

    with patch("monitoring.logger", mock_logger):

        @measure_performance
        async def concurrent_function(delay: float):
            await asyncio.sleep(delay)
            return delay

        tasks = [
            concurrent_function(0.1),
            concurrent_function(0.2),
            concurrent_function(0.3),
        ]
        results = await asyncio.gather(*tasks)

        assert results == [0.1, 0.2, 0.3]
        assert mock_logger.info.call_count == 3  # One log per function call


@pytest.mark.asyncio
async def test_measure_performance_nested_calls():
    """Test measure_performance with nested function calls."""
    mock_logger = Mock()

    with patch("monitoring.logger", mock_logger):

        @measure_performance
        async def inner_function():
            await asyncio.sleep(0.1)
            return "inner"

        @measure_performance
        async def outer_function():
            await asyncio.sleep(0.1)
            result = await inner_function()
            return f"outer-{result}"

        result = await outer_function()

        assert result == "outer-inner"
        assert mock_logger.info.call_count == 2  # One log each for inner and outer


@pytest.mark.asyncio
async def test_measure_performance_zero_duration():
    """Test measure_performance with very fast function."""
    mock_logger = Mock()

    with patch("monitoring.logger", mock_logger):

        @measure_performance
        async def fast_function():
            return "fast"

        result = await fast_function()

        assert result == "fast"
        log_message = mock_logger.info.call_args[0][0]
        assert "Duration:" in log_message
