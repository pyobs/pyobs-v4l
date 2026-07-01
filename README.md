*pyobs* module for Video4Linux cameras
=======================================

This is a [pyobs](https://www.pyobs.org) module for USB webcams and other Video4Linux cameras.


System dependencies
--------------------
On Debian/Ubuntu:

    sudo apt install libv4l-dev


Install *pyobs-v4l*
---------------------
Clone the repository:

    git clone https://github.com/pyobs/pyobs-v4l.git
    cd pyobs-v4l

Install it with [uv](https://docs.astral.sh/uv/):

    uv sync

Alternatively, with plain `venv`/`pip`:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install .


Configuration
-------------
The *v4lCamera* class is derived from *BaseVideo* (see *pyobs* documentation) and adds a single new parameter:

    device:
        Index of the /dev/videoN device to use (default: 0).

A basic module configuration would look like this:

    class: pyobs_v4l.v4lCamera
    name: V4L camera
    device: 0


GUI
---
For testing a camera without a full *pyobs* setup, install the optional `gui` extra:

    uv sync --extra gui

and run:

    uv run v4l-gui


Dependencies
------------
* [pyobs-core](https://github.com/pyobs/pyobs-core) for the core functionality.
* [OpenCV](https://github.com/opencv/opencv-python) for accessing the camera.
