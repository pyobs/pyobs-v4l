import asyncio
import sys
import threading
from pathlib import Path
from typing import Any

import cv2
import qasync  # type: ignore[import-untyped]
from astropy.io import fits
from pyobs.utils.gui.camera import DataDisplayWidget, ExposeWidget
from PySide6 import QtWidgets  # type: ignore[import-untyped]


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, device: int) -> None:
        super().__init__()
        self.setWindowTitle(f"V4L Camera — /dev/video{device}")

        self._device = device
        self._camera: cv2.VideoCapture | None = None
        self._lock = threading.Lock()
        self._last_frame: cv2.typing.MatLike | None = None
        self._preview_task: asyncio.Task[None] | None = None

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)

        controls = QtWidgets.QGroupBox("Camera")
        controls_layout = QtWidgets.QVBoxLayout(controls)
        self.expose = ExposeWidget(can_abort_exposure=False)
        controls_layout.addWidget(self.expose)
        controls_layout.addStretch()

        self.display = DataDisplayWidget()
        layout.addWidget(controls)
        layout.addWidget(self.display)

        self.expose.expose_clicked.connect(self._grab_clicked)

        self._preview_task = asyncio.ensure_future(self._live_preview())

    async def _open_camera(self) -> cv2.VideoCapture:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, cv2.VideoCapture, self._device)

    def _read_frame(self) -> tuple[bool, Any]:
        with self._lock:
            if self._camera is None:
                return False, None
            return self._camera.read()

    async def _live_preview(self) -> None:
        loop = asyncio.get_running_loop()
        self._camera = await self._open_camera()
        while True:
            ret, frame = await loop.run_in_executor(None, self._read_frame)
            if ret:
                self._last_frame = frame
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                self.display.set_data(fits.PrimaryHDU(gray))
            await asyncio.sleep(0.05)

    @qasync.asyncSlot(int)  # type: ignore[misc]
    async def _grab_clicked(self, count: int) -> None:
        if self._last_frame is None:
            return
        self.expose.start_exposure(0.0)
        for _ in range(count):
            loop = asyncio.get_running_loop()
            ret, frame = await loop.run_in_executor(None, self._read_frame)
            if ret:
                self._last_frame = frame
        gray = cv2.cvtColor(self._last_frame, cv2.COLOR_BGR2GRAY)
        self.display.set_data(fits.PrimaryHDU(gray))
        self.expose.set_exposures_left()

    def closeEvent(self, event: Any) -> None:
        if self._preview_task is not None:
            self._preview_task.cancel()
        if self._camera is not None:
            self._camera.release()
        super().closeEvent(event)


async def async_main(app: QtWidgets.QApplication) -> None:
    devices = sorted(p for p in Path("/dev").glob("video*") if p.is_char_device())
    if not devices:
        QtWidgets.QMessageBox.critical(None, "Error", "No V4L devices found.")
        return

    device_name, ok = QtWidgets.QInputDialog.getItem(
        None, "Select Device", "V4L device:", [str(d) for d in devices], 0, False
    )
    if not ok:
        return

    device_index = int(device_name.replace("/dev/video", ""))

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    window = MainWindow(device_index)
    window.show()
    await app_close_event.wait()


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    with qasync.QEventLoop(app) as loop:
        loop.run_until_complete(async_main(app))


if __name__ == "__main__":
    main()
