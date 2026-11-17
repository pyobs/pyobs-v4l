"""Tests for the FITS header cards of the module and the GUI."""

from __future__ import annotations

from unittest.mock import AsyncMock

import numpy as np
import pytest
from pyobs.images import Image
from pyobs.modules.camera import BaseVideo
from pyobs.utils.enums import ImageType

from pyobs_v4l import v4lCamera


@pytest.mark.asyncio
async def test_module_header_has_the_device_as_instrument(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(BaseVideo, "_finish_image", AsyncMock(side_effect=lambda image, *a: (image, "x")))
    camera = v4lCamera(device=2)

    image, _ = await camera._finish_image(Image(np.zeros((2, 2), dtype=np.uint8)), False, ImageType.OBJECT)

    assert image.header["INSTRUME"] == "/dev/video2"


def test_gui_header_has_the_device_and_statistics() -> None:
    gui = pytest.importorskip("pyobs_v4l.gui")
    h = gui.make_header(0, np.array([[1, 2], [3, 6]], dtype=np.uint8))
    assert h["INSTRUME"] == "/dev/video0"
    assert (h["DATAMIN"], h["DATAMAX"], h["DATAMEAN"]) == (1.0, 6.0, 3.0)
