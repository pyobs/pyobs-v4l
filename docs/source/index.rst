pyobs-v4l
#########

This is a `pyobs <https://www.pyobs.org>`_ (`documentation <https://docs.pyobs.org>`_) module for USB webcams and
other Video4Linux cameras.


Example configuration
*********************

This is an example configuration::

    class: pyobs_v4l.v4lCamera
    device: 0

    # file naming
    filenames: /webcam/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}.fits
    video_path: /webcam/video.mjpg

    # location
    timezone: utc
    location:
      longitude: 9.944333
      latitude: 51.560583
      elevation: 201.

    # communication
    comm:
      jid: test@example.com
      password: ***

    # virtual file system
    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        webcam:
          class: pyobs.vfs.HttpFile
          upload: http://localhost:37075/


Available classes
*****************

There is one single class for Video4Linux cameras.

v4lCamera
=========
.. autoclass:: pyobs_v4l.v4lCamera
   :members:
   :show-inheritance:
