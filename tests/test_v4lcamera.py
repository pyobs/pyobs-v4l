"""Unit tests for the non-hardware logic in v4lCamera: constructor state, the _run_blocking
timeout wrapper, device opening and frames(). cv2.VideoCapture is replaced by a fake.
"""

import asyncio
import threading
from typing import Any

import cv2
import numpy as np
import numpy.typing as npt
import pytest

from pyobs_v4l import v4lCamera


class FakeCapture:
    """Stands in for cv2.VideoCapture: frames come from a list, a failed read once it's empty."""

    def __init__(self, frames: list[npt.NDArray[Any]] | None = None, opened: bool = True) -> None:
        self.frames = [] if frames is None else frames
        self.opened = opened
        self.released = threading.Event()

    def isOpened(self) -> bool:
        return self.opened

    def read(self) -> tuple[bool, npt.NDArray[Any] | None]:
        if self.frames:
            return True, self.frames.pop(0)
        return False, None

    def release(self) -> None:
        self.released.set()


def _bgr(b: int, g: int, r: int) -> npt.NDArray[Any]:
    frame = np.zeros((2, 3, 3), dtype=np.uint8)
    frame[:, :] = (b, g, r)
    return frame


def test_constructor_defaults() -> None:
    camera = v4lCamera()
    assert camera._device == 0
    assert camera._color is False


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


@pytest.mark.asyncio
async def test_open_camera_raises_if_not_opened(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCapture(opened=False)
    monkeypatch.setattr(cv2, "VideoCapture", lambda device: fake)

    with pytest.raises(RuntimeError, match="Could not open"):
        await v4lCamera()._open_camera()
    assert fake.released.is_set()


@pytest.mark.asyncio
async def test_frames_yields_greyscale_and_releases_on_close(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCapture([_bgr(0, 0, 255), _bgr(255, 0, 0)] + [_bgr(0, 0, 0)] * 100)
    monkeypatch.setattr(cv2, "VideoCapture", lambda device: fake)
    camera = v4lCamera()

    iterator = camera.frames()
    first, second = await anext(iterator), await anext(iterator)
    await iterator.aclose()

    assert first.data.shape == (2, 3) and second.data.shape == (2, 3)
    # BGR, not RGB: pure red is brighter than pure blue in greyscale
    assert int(first.data[0, 0]) > int(second.data[0, 0])
    assert first.start is None and first.exposure_time is None
    assert fake.released.wait(1.0)


@pytest.mark.asyncio
async def test_frames_keeps_colour_as_rgb(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCapture([_bgr(1, 2, 3)] * 10)
    monkeypatch.setattr(cv2, "VideoCapture", lambda device: fake)
    camera = v4lCamera(color=True)

    iterator = camera.frames()
    frame = await anext(iterator)
    await iterator.aclose()

    assert frame.data.shape == (2, 3, 3)
    assert tuple(frame.data[0, 0]) == (3, 2, 1)


@pytest.mark.asyncio
async def test_frames_raises_on_failed_read(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeCapture([])
    monkeypatch.setattr(cv2, "VideoCapture", lambda device: fake)
    camera = v4lCamera()

    iterator = camera.frames()
    with pytest.raises(RuntimeError, match="Could not read frame"):
        await anext(iterator)
    assert fake.released.wait(1.0)
