import time
import logging

from pyobs.modules.camera import BaseVideo
import cv2

log = logging.getLogger(__name__)


class v4lCamera(BaseVideo):
    def __init__(self, device: int = 0, *args, **kwargs):
        BaseVideo.__init__(self, *args, **kwargs)

        # store
        self._device = device

        # thread
        self.add_thread_func(self._capture)

    def _capture(self):
        # open camera
        camera = cv2.VideoCapture(self._device)

        # loop until closing
        last = time.time()
        while not self.closing.is_set():
            # read frame
            _, frame = camera.read()

            # if time since last image is too short, wait a little
            if time.time() - last < self._interval:
                self.closing.wait(0.01)
                continue
            last = time.time()

            # process it
            self._set_image(frame)

        # release camera
        camera.release()


__all__ = ['v4lCamera']
