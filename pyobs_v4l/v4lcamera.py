import asyncio
import logging
import threading
from collections.abc import AsyncGenerator, Callable
from typing import Any

import cv2
from pyobs.modules.camera import BaseVideo, Frame

log = logging.getLogger(__name__)

# cv2's V4L2 backend calls are blocking and are made directly on the event loop thread (see
# _run_blocking). If the camera has gone unresponsive, they can hang indefinitely, so they're
# bounded with a timeout rather than let a single dead camera freeze the whole module.
_SDK_CALL_TIMEOUT = 5.0

# frames() warns if no frame arrived for this long. Frames legitimately take up to the camera's
# own frame interval, so this is much more generous than _SDK_CALL_TIMEOUT.
_FRAME_WAIT_TIMEOUT = 30.0

# frames queued between the reader thread and the event loop; latest wins beyond that
_QUEUE_SIZE = 5


class v4lCamera(BaseVideo):
    """A pyobs module for V4L2 cameras, e.g. webcams.

    The device is opened while the module is active and released when it goes to sleep. V4L2
    gives no reliable exposure time or exposure start via OpenCV, so frames carry neither and
    DATE-OBS is the frame's arrival time.
    """

    __module__ = "pyobs_v4l"

    def __init__(self, device: int = 0, color: bool = False, **kwargs: Any):
        """Initializes a new v4lCamera.

        Args:
            device: Index of the V4L2 device, i.e. N in /dev/videoN.
            color: Keep colour frames (RGB, colour as last axis) instead of converting them to
                greyscale. Colour frames work for the live view, but not for grab_stack(), and
                are stored as 3D FITS files.
        """
        BaseVideo.__init__(self, **kwargs)

        # store
        self._device = device
        self._color = color

    async def open(self) -> None:
        """Open module."""
        await BaseVideo.open(self)

        # start streaming
        await self.activate_camera()

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

        def _finish() -> None:
            # wait_for cancels the future on timeout, so guard set_result to avoid an
            # InvalidStateError from the loop thread once the orphaned call finally ends.
            if not future.done():
                future.set_result(None)

        def _wrapper() -> None:
            try:
                func()
            finally:
                try:
                    loop.call_soon_threadsafe(_finish)
                except RuntimeError:
                    # event loop closed (shutdown)
                    pass

        threading.Thread(target=_wrapper, daemon=True).start()
        try:
            await asyncio.wait_for(future, timeout=timeout)
            return True
        except TimeoutError:
            return False

    async def _open_camera(self) -> Any:
        """Open the V4L2 camera device, without blocking the event loop.

        Raises:
            TimeoutError: If opening didn't finish in time.
            RuntimeError: If the device could not be opened.
        """
        result: list[Any] = []
        lock = threading.Lock()
        timed_out = False

        def _open() -> None:
            camera = cv2.VideoCapture(self._device)
            with lock:
                if timed_out:
                    # timed out while still opening; release the handle nobody will use
                    camera.release()
                else:
                    result.append(camera)

        if not await self._run_blocking(_open):
            with lock:
                timed_out = True
                if result:
                    result.pop().release()
            raise TimeoutError(f"Timed out opening camera device after {_SDK_CALL_TIMEOUT}s.")

        # VideoCapture() doesn't raise for a missing/busy device, it just isn't opened
        camera = result[0]
        if not camera.isOpened():
            camera.release()
            raise RuntimeError(f"Could not open camera device {self._device}.")
        return camera

    def _convert(self, frame: Any) -> Any:
        """Convert a frame from OpenCV's BGR to greyscale, or to RGB if colour is kept."""
        if frame.ndim != 3:
            return frame
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB if self._color else cv2.COLOR_BGR2GRAY)

    async def frames(self) -> AsyncGenerator[Frame, None]:
        """Open the device and yield frames until BaseVideo closes the iterator.

        A single reader thread owns the device for the whole activation, reads frames and hands
        them to the event loop, and releases the device when it's told to stop. A failed read ends
        the iterator with an error, so BaseVideo restarts it with a back-off.
        """
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Frame | BaseException] = asyncio.Queue(maxsize=_QUEUE_SIZE)
        stop = threading.Event()
        camera = await self._open_camera()

        def _put(item: Frame | BaseException) -> None:
            # latest wins: a stalled event loop mustn't grow memory
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(item)

        def _read() -> None:
            try:
                while not stop.is_set():
                    item: Frame | BaseException
                    try:
                        # read() returns a fresh array per call, so no copy needed
                        ok, frame = camera.read()
                        if ok and frame is not None:
                            item = Frame(data=self._convert(frame))
                        else:
                            item = RuntimeError(f"Could not read frame from camera device {self._device}.")
                    except Exception as e:
                        item = e
                    if stop.is_set():
                        return
                    try:
                        loop.call_soon_threadsafe(_put, item)
                    except RuntimeError:
                        # event loop closed (shutdown)
                        return
                    if isinstance(item, BaseException):
                        return
            finally:
                camera.release()

        threading.Thread(target=_read, daemon=True).start()
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=_FRAME_WAIT_TIMEOUT)
                except TimeoutError:
                    log.warning("No frame from camera for %.1fs.", _FRAME_WAIT_TIMEOUT)
                    continue
                if isinstance(item, BaseException):
                    raise item
                yield item
        finally:
            # don't join the reader: if it hangs in read(), it must not block deactivation; it
            # releases the device itself once read() returns
            stop.set()


__all__ = ["v4lCamera"]
