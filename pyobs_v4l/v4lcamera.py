import asyncio
import time
import logging
from typing import Any
import cv2

from pyobs.modules.camera import BaseVideo


log = logging.getLogger(__name__)


class v4lCamera(BaseVideo):
    def __init__(self, device: int = 0, **kwargs: Any):
        BaseVideo.__init__(self, **kwargs)

        # store
        self._device = device

        # thread
        self.add_background_task(self._capture)

    async def _capture(self) -> None:
        # open camera
        camera = cv2.VideoCapture(self._device)

        # loop until closing
        last = time.time()
        while True:
            # read frame
            _, frame = camera.read()

            # if time since last image is too short, wait a little
            if time.time() - last < self._interval:
                await asyncio.sleep(0.01)
                continue
            last = time.time()

            # process it
            await self._set_image(frame)

        # release camera
        camera.release()


__all__ = ["v4lCamera"]
