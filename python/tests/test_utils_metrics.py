"""Tests for metrics utilities."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from utils.metrics import measure_time, measure_performance


def test_measure_time():
    """Test measure_time context manager."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):
        with measure_time("test_operation"):
            # Simulate some work
            sum([i for i in range(1000)])

        assert mock_logger.info.called
        log_message = mock_logger.info.call_args[0][0]
        assert "test_operation took" in log_message
        assert "seconds" in log_message


def test_measure_time_with_error():
    """Test measure_time context manager with error."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):
        with pytest.raises(ValueError):
            with measure_time("failing_operation"):
                raise ValueError("Test error")

        assert mock_logger.info.called
        log_message = mock_logger.info.call_args[0][0]
        assert "failing_operation took" in log_message


@pytest.mark.asyncio
async def test_measure_performance_decorator():
    """Test measure_performance decorator."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):

        @measure_performance
        async def test_function():
            await asyncio.sleep(0.1)
            return "success"

        result = await test_function()

        assert result == "success"
        assert mock_logger.info.called
        log_message = mock_logger.info.call_args[0][0]
        assert "test_function took" in log_message
        assert "seconds" in log_message


@pytest.mark.asyncio
async def test_measure_performance_with_error():
    """Test measure_performance decorator with error."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):

        @measure_performance
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

        assert mock_logger.info.called
        log_message = mock_logger.info.call_args[0][0]
        assert "failing_function took" in log_message


@pytest.mark.asyncio
async def test_measure_performance_with_args():
    """Test measure_performance decorator with arguments."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):

        @measure_performance
        async def test_function(x, y, z=None):
            await asyncio.sleep(0.1)
            return x + y + (z or 0)

        result = await test_function(1, 2, z=3)

        assert result == 6
        assert mock_logger.info.called
        log_message = mock_logger.info.call_args[0][0]
        assert "test_function took" in log_message


@pytest.mark.asyncio
async def test_nested_performance_measurement():
    """Test nested performance measurements."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):

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
        assert mock_logger.info.call_count == 2

        # Check order of logging calls
        calls = mock_logger.info.call_args_list
        assert "inner_function took" in calls[0][0][0]
        assert "outer_function took" in calls[1][0][0]


@pytest.mark.asyncio
async def test_concurrent_performance_measurement():
    """Test performance measurement with concurrent operations."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):

        @measure_performance
        async def concurrent_function(delay):
            await asyncio.sleep(delay)
            return delay

        tasks = [concurrent_function(0.1), concurrent_function(0.2)]
        results = await asyncio.gather(*tasks)

        assert results == [0.1, 0.2]
        assert mock_logger.info.call_count == 2


def test_measure_time_zero_duration():
    """Test measure_time with very fast operation."""
    mock_logger = Mock()

    with patch("utils.metrics.logger", mock_logger):
        with measure_time("fast_operation"):
            pass  # No operation

        assert mock_logger.info.called
        log_message = mock_logger.info.call_args[0][0]
        assert "fast_operation took" in log_message
