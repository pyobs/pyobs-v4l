"""Smoke tests: import the driver and instantiate it without hardware, asserting it
advertises the interfaces it claims.

The V4L2 device is only opened inside the capture loop (after open()), so
instantiation is safe. ``pyobs_v4l.gui`` is deliberately not imported here -- it pulls
in PySide6/qasync at module load and needs a display.
"""

from pyobs.interfaces import IImageType, IVideo
from pyobs.modules import Module

from pyobs_v4l import v4lCamera


def test_instantiate_camera() -> None:
    camera = v4lCamera()
    assert isinstance(camera, Module)
    assert isinstance(camera, IVideo)
    assert isinstance(camera, IImageType)
