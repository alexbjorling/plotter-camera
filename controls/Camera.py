import cv2

class Camera(object):
    """
    Class representing the hardware camera, wrapping the 
    picamera.PiCamera class if useful.
    """

    def __init__(self):
        pass

    def get_image(self):
        """
        Acquire an image from the camera and return ndarray. Dummy for now.
        """
        return cv2.cvtColor(
                cv2.imread('drawing/image.jpg', cv2.IMREAD_UNCHANGED), 
                cv2.COLOR_BGR2RGB)
