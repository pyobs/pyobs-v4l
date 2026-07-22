import asyncio
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import cv2
from pyobs.modules.camera import BaseVideo

log = logging.getLogger(__name__)

# cv2's V4L2 backend calls are blocking and are made directly on the event loop thread (see
# _run_blocking). If the camera has gone unresponsive, they can hang indefinitely, so they're
# bounded with a timeout rather than let a single dead camera freeze the whole module.
_SDK_CALL_TIMEOUT = 5.0

# read() waits for the next frame, which can legitimately take a while depending on the camera's
# own frame rate -- a more generous timeout than _SDK_CALL_TIMEOUT so normal operation never trips it.
_FRAME_WAIT_TIMEOUT = 30.0


class v4lCamera(BaseVideo):
    def __init__(self, device: int = 0, **kwargs: Any):
        BaseVideo.__init__(self, **kwargs)

        # store
        self._device = device

        # thread
        self.add_background_task(self._capture)

    @staticmethod
    async def _run_blocking(func: Callable[[], None], timeout: float = _SDK_CALL_TIMEOUT) -> bool:
        """Run a blocking cv2/V4L2 call in a daemon thread, so a hung call can't freeze the module.

        A plain executor isn't used here, since its worker threads are non-daemon and Python joins
        them on interpreter shutdown -- a hung call would then just move the freeze to process exit.

        Returns:
            True if func completed within timeout, False if it's still running in the background.
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[None] = loop.create_future()

        def _wrapper() -> None:
            try:
                func()
            finally:
                loop.call_soon_threadsafe(future.set_result, None)

        threading.Thread(target=_wrapper, daemon=True).start()
        try:
            await asyncio.wait_for(future, timeout=timeout)
            return True
        except TimeoutError:
            return False

    async def _open_camera(self) -> Any:
        """Open the V4L2 camera device, without blocking the event loop."""
        result: list[Any] = []

        def _open() -> None:
            result.append(cv2.VideoCapture(self._device))

        if not await self._run_blocking(_open):
            raise TimeoutError(f"Timed out opening camera device after {_SDK_CALL_TIMEOUT}s.")
        return result[0]

    async def _read_frame(self, camera: Any) -> Any:
        """Read the next frame from the camera, without blocking the event loop.

        Returns:
            The next frame, or None if the read timed out.
        """
        result: list[Any] = []

        def _read() -> None:
            _, frame = camera.read()
            result.append(frame)

        if not await self._run_blocking(_read, timeout=_FRAME_WAIT_TIMEOUT):
            log.error("Timed out reading frame after %.1fs.", _FRAME_WAIT_TIMEOUT)
            return None
        return result[0]

    async def _capture(self) -> None:
        # open camera
        camera = await self._open_camera()

        # loop until closing
        last = time.time()
        while True:
            # read frame
            frame = await self._read_frame(camera)
            if frame is None:
                continue

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
