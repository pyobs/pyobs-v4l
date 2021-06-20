*pyobs* mddule for Video4Linux cameras
======================================

Install *pyobs-v4l*
-------------------
Install dependencies, e.g. in Ubuntu:

    sudo apt install libv4l-dev


Clone the repository:

    git clone https://github.com/pyobs/pyobs-v4l.git


Install dependencies:

    cd pytel-v4l
    pip3 install -r requirements
        
And install it:

    python3 setup.py install


Dependencies
------------
* **pyobs** for the core funcionality. It is not included in the *requirements.txt*, so needs to be installed 
  separately.
* [cv2](https://github.com/opencv/opencv-python) for accessing the camera.
