"""Unit tests for the non-hardware logic in v4lCamera: constructor state and the
_run_blocking timeout wrapper.

Opening the V4L2 device and reading frames is out of scope here.
"""

import asyncio
import threading

import pytest

from pyobs_v4l import v4lCamera


def test_constructor_defaults() -> None:
    camera = v4lCamera()
    assert camera._device == 0


def test_constructor_device() -> None:
    camera = v4lCamera(device=3)
    assert camera._device == 3


@pytest.mark.asyncio
async def test_run_blocking_runs_func_and_returns_true() -> None:
    ran: list[bool] = []

    def fast() -> None:
        ran.append(True)

    assert await v4lCamera._run_blocking(fast) is True
    assert ran == [True]


@pytest.mark.asyncio
async def test_run_blocking_times_out() -> None:
    done = threading.Event()

    def slow() -> None:
        done.wait()

    assert await v4lCamera._run_blocking(slow, timeout=0.01) is False
    done.set()
    await asyncio.sleep(0.05)  # let the daemon thread drain before the loop closes
